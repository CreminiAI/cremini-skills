#!/usr/bin/env python3
"""Notion Databases — list, query, create entries, get schema.

Usage:
    python3 notion_databases.py list
    python3 notion_databases.py query <database-id> [--filter JSON] [--sort JSON] [--limit N]
    python3 notion_databases.py create <database-id> --props JSON
    python3 notion_databases.py schema <database-id>

Zero external dependencies — stdlib only.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Optional, Sequence


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CONFIG_FILE = Path.home() / ".config" / "notion" / "config.json"
NOTION_API = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"


# ---------------------------------------------------------------------------
# Auth + API
# ---------------------------------------------------------------------------

def _load_token() -> str:
    if not CONFIG_FILE.exists():
        print("Error: Notion not configured. Run: notion-connect --set-token <TOKEN>", file=sys.stderr)
        sys.exit(1)
    data = json.loads(CONFIG_FILE.read_text())
    token = data.get("token", "")
    if not token:
        print("Error: Token is empty. Run: notion-connect --set-token <TOKEN>", file=sys.stderr)
        sys.exit(1)
    return token


def _api_request(
    method: str,
    path: str,
    token: str,
    body: Optional[dict] = None,
) -> dict:
    url = f"{NOTION_API}{path}"
    data = json.dumps(body).encode() if body else None

    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Notion-Version": NOTION_VERSION,
            "Content-Type": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        body_text = exc.read().decode() if exc.fp else ""
        if exc.code == 401:
            print("Error: Invalid Notion token. Run: notion-connect --set-token <TOKEN>", file=sys.stderr)
        elif exc.code == 404:
            print("Error: Not found. Make sure the database is shared with your integration.", file=sys.stderr)
        else:
            print(f"Error: Notion API {exc.code}: {body_text[:300]}", file=sys.stderr)
        sys.exit(1)


# ---------------------------------------------------------------------------
# Property extraction
# ---------------------------------------------------------------------------

def _extract_property_value(prop: dict) -> Any:
    """Extract a readable value from a Notion property object."""
    ptype = prop.get("type", "")

    if ptype == "title":
        return "".join(t.get("plain_text", "") for t in prop.get("title", []))
    elif ptype == "rich_text":
        return "".join(t.get("plain_text", "") for t in prop.get("rich_text", []))
    elif ptype == "number":
        return prop.get("number")
    elif ptype == "select":
        sel = prop.get("select")
        return sel.get("name", "") if sel else ""
    elif ptype == "multi_select":
        return [s.get("name", "") for s in prop.get("multi_select", [])]
    elif ptype == "status":
        status = prop.get("status")
        return status.get("name", "") if status else ""
    elif ptype == "date":
        date = prop.get("date")
        if date:
            start = date.get("start", "")
            end = date.get("end", "")
            return f"{start} → {end}" if end else start
        return ""
    elif ptype == "checkbox":
        return prop.get("checkbox", False)
    elif ptype == "url":
        return prop.get("url", "")
    elif ptype == "email":
        return prop.get("email", "")
    elif ptype == "phone_number":
        return prop.get("phone_number", "")
    elif ptype == "people":
        return [p.get("name", p.get("id", "")) for p in prop.get("people", [])]
    elif ptype == "relation":
        return [r.get("id", "") for r in prop.get("relation", [])]
    elif ptype == "formula":
        formula = prop.get("formula", {})
        ftype = formula.get("type", "")
        return formula.get(ftype)
    elif ptype == "rollup":
        rollup = prop.get("rollup", {})
        rtype = rollup.get("type", "")
        return rollup.get(rtype)
    elif ptype == "created_time":
        return prop.get("created_time", "")
    elif ptype == "last_edited_time":
        return prop.get("last_edited_time", "")

    return f"<{ptype}>"


# ---------------------------------------------------------------------------
# Property building for create
# ---------------------------------------------------------------------------

def _build_property(name: str, value: Any, schema: dict) -> dict:
    """Build a Notion property object from a simple value, using schema to determine type."""
    prop_schema = schema.get(name, {})
    ptype = prop_schema.get("type", "rich_text")

    if ptype == "title":
        return {"title": [{"text": {"content": str(value)}}]}
    elif ptype == "rich_text":
        return {"rich_text": [{"text": {"content": str(value)}}]}
    elif ptype == "number":
        return {"number": float(value) if value else None}
    elif ptype == "select":
        return {"select": {"name": str(value)}}
    elif ptype == "multi_select":
        items = value if isinstance(value, list) else [str(value)]
        return {"multi_select": [{"name": item} for item in items]}
    elif ptype == "status":
        return {"status": {"name": str(value)}}
    elif ptype == "date":
        return {"date": {"start": str(value)}}
    elif ptype == "checkbox":
        return {"checkbox": bool(value)}
    elif ptype == "url":
        return {"url": str(value)}
    elif ptype == "email":
        return {"email": str(value)}

    # Fallback to rich_text
    return {"rich_text": [{"text": {"content": str(value)}}]}


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_list() -> int:
    """List all databases in workspace."""
    token = _load_token()
    body = {"filter": {"value": "database", "property": "object"}, "page_size": 100}
    result = _api_request("POST", "/search", token, body)

    databases = []
    for item in result.get("results", []):
        title_array = item.get("title", [])
        title = "".join(t.get("plain_text", "") for t in title_array) if title_array else "Untitled"

        databases.append({
            "id": item["id"],
            "title": title,
            "url": item.get("url", ""),
            "last_edited": item.get("last_edited_time", ""),
        })

    print(json.dumps({"count": len(databases), "databases": databases}, indent=2))
    return 0


def cmd_schema(database_id: str) -> int:
    """Get database schema (properties and their types)."""
    token = _load_token()
    result = _api_request("GET", f"/databases/{database_id}", token)

    properties = {}
    for name, prop in result.get("properties", {}).items():
        prop_info: dict[str, Any] = {"type": prop.get("type", "")}

        # Include options for select/multi_select/status
        if prop.get("type") == "select":
            prop_info["options"] = [o.get("name", "") for o in prop.get("select", {}).get("options", [])]
        elif prop.get("type") == "multi_select":
            prop_info["options"] = [o.get("name", "") for o in prop.get("multi_select", {}).get("options", [])]
        elif prop.get("type") == "status":
            prop_info["options"] = [o.get("name", "") for o in prop.get("status", {}).get("options", [])]

        properties[name] = prop_info

    title_array = result.get("title", [])
    title = "".join(t.get("plain_text", "") for t in title_array)

    print(json.dumps({
        "id": database_id,
        "title": title,
        "properties": properties,
    }, indent=2))
    return 0


def cmd_query(database_id: str, filter_json: str = "", sort_json: str = "", limit: int = 50) -> int:
    """Query a database."""
    token = _load_token()

    body: dict[str, Any] = {"page_size": min(limit, 100)}

    if filter_json:
        try:
            body["filter"] = json.loads(filter_json)
        except json.JSONDecodeError:
            print(f"Error: Invalid filter JSON: {filter_json}", file=sys.stderr)
            return 1

    if sort_json:
        try:
            sort_obj = json.loads(sort_json)
            body["sorts"] = [sort_obj] if isinstance(sort_obj, dict) else sort_obj
        except json.JSONDecodeError:
            print(f"Error: Invalid sort JSON: {sort_json}", file=sys.stderr)
            return 1

    result = _api_request("POST", f"/databases/{database_id}/query", token, body)

    entries = []
    for page in result.get("results", []):
        entry: dict[str, Any] = {
            "id": page["id"],
            "url": page.get("url", ""),
            "created": page.get("created_time", ""),
            "last_edited": page.get("last_edited_time", ""),
            "properties": {},
        }

        for prop_name, prop_data in page.get("properties", {}).items():
            entry["properties"][prop_name] = _extract_property_value(prop_data)

        entries.append(entry)

    print(json.dumps({
        "database_id": database_id,
        "count": len(entries),
        "entries": entries,
    }, indent=2))
    return 0


def cmd_create(database_id: str, props_json: str) -> int:
    """Create a new entry in a database."""
    token = _load_token()

    try:
        props_input = json.loads(props_json)
    except json.JSONDecodeError:
        print(f"Error: Invalid props JSON: {props_json}", file=sys.stderr)
        return 1

    # Get schema to determine property types
    schema_resp = _api_request("GET", f"/databases/{database_id}", token)
    schema = schema_resp.get("properties", {})

    # Build properties
    properties: dict[str, Any] = {}
    for name, value in props_input.items():
        properties[name] = _build_property(name, value, schema)

    body = {
        "parent": {"database_id": database_id},
        "properties": properties,
    }

    result = _api_request("POST", "/pages", token, body)

    print(json.dumps({
        "id": result["id"],
        "url": result.get("url", ""),
        "created": True,
    }, indent=2))
    return 0


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Notion Databases — list, query, create, schema")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # list
    subparsers.add_parser("list", help="List all databases")

    # schema
    p_schema = subparsers.add_parser("schema", help="Get database schema")
    p_schema.add_argument("database_id", help="Database ID")

    # query
    p_query = subparsers.add_parser("query", help="Query a database")
    p_query.add_argument("database_id", help="Database ID")
    p_query.add_argument("--filter", default="", help="Filter JSON")
    p_query.add_argument("--sort", default="", help="Sort JSON")
    p_query.add_argument("--limit", type=int, default=50, help="Max results (default: 50)")

    # create
    p_create = subparsers.add_parser("create", help="Create a database entry")
    p_create.add_argument("database_id", help="Database ID")
    p_create.add_argument("--props", required=True, help='Properties JSON, e.g. \'{"Name": "Task", "Status": "To Do"}\'')

    args = parser.parse_args(argv)

    if args.command == "list":
        return cmd_list()
    elif args.command == "schema":
        return cmd_schema(args.database_id)
    elif args.command == "query":
        return cmd_query(args.database_id, args.filter, args.sort, args.limit)
    elif args.command == "create":
        return cmd_create(args.database_id, args.props)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
