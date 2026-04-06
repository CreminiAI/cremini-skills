#!/usr/bin/env python3
"""Notion Pages — search, get, create, update, append.

Usage:
    python3 notion_pages.py search "query" [--limit N]
    python3 notion_pages.py get <page-id>
    python3 notion_pages.py create --parent <id> --title "Title" [--content "markdown"]
    python3 notion_pages.py update <page-id> --title "New Title"
    python3 notion_pages.py append <page-id> --content "markdown content"

Zero external dependencies — stdlib only.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional, Sequence


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CONFIG_FILE = Path.home() / ".config" / "notion" / "config.json"
NOTION_API = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

def _load_token() -> str:
    """Load token from config. Exits with error if not configured."""
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
    """Make a Notion API request. Returns parsed JSON response."""
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
            print(f"Error: Not found. Make sure the page is shared with your integration.", file=sys.stderr)
        else:
            print(f"Error: Notion API {exc.code}: {body_text[:300]}", file=sys.stderr)
        sys.exit(1)


# ---------------------------------------------------------------------------
# Block content extraction
# ---------------------------------------------------------------------------

def _blocks_to_text(blocks: list[dict]) -> str:
    """Convert Notion blocks to readable text."""
    lines: list[str] = []
    for block in blocks:
        btype = block.get("type", "")
        bdata = block.get(btype, {})

        if btype in ("paragraph", "heading_1", "heading_2", "heading_3",
                      "bulleted_list_item", "numbered_list_item", "quote",
                      "callout", "toggle"):
            rich_text = bdata.get("rich_text", [])
            text = "".join(rt.get("plain_text", "") for rt in rich_text)

            if btype == "heading_1":
                lines.append(f"# {text}")
            elif btype == "heading_2":
                lines.append(f"## {text}")
            elif btype == "heading_3":
                lines.append(f"### {text}")
            elif btype == "bulleted_list_item":
                lines.append(f"- {text}")
            elif btype == "numbered_list_item":
                lines.append(f"1. {text}")
            elif btype == "quote":
                lines.append(f"> {text}")
            else:
                lines.append(text)

        elif btype == "code":
            rich_text = bdata.get("rich_text", [])
            text = "".join(rt.get("plain_text", "") for rt in rich_text)
            lang = bdata.get("language", "")
            lines.append(f"```{lang}\n{text}\n```")

        elif btype == "divider":
            lines.append("---")

        elif btype == "to_do":
            rich_text = bdata.get("rich_text", [])
            text = "".join(rt.get("plain_text", "") for rt in rich_text)
            checked = "x" if bdata.get("checked") else " "
            lines.append(f"- [{checked}] {text}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Markdown to blocks conversion
# ---------------------------------------------------------------------------

def _text_to_blocks(content: str) -> list[dict]:
    """Convert simple markdown text to Notion blocks."""
    blocks: list[dict] = []
    for line in content.split("\n"):
        stripped = line.strip()
        if not stripped:
            continue

        if stripped.startswith("### "):
            blocks.append(_heading_block("heading_3", stripped[4:]))
        elif stripped.startswith("## "):
            blocks.append(_heading_block("heading_2", stripped[3:]))
        elif stripped.startswith("# "):
            blocks.append(_heading_block("heading_1", stripped[2:]))
        elif stripped.startswith("- [ ] ") or stripped.startswith("- [x] "):
            checked = stripped[3] == "x"
            blocks.append(_todo_block(stripped[6:], checked))
        elif stripped.startswith("- "):
            blocks.append(_list_block("bulleted_list_item", stripped[2:]))
        elif stripped.startswith("> "):
            blocks.append(_quote_block(stripped[2:]))
        elif stripped == "---":
            blocks.append({"object": "block", "type": "divider", "divider": {}})
        else:
            blocks.append(_paragraph_block(stripped))

    return blocks


def _rich_text(text: str) -> list[dict]:
    return [{"type": "text", "text": {"content": text}}]


def _paragraph_block(text: str) -> dict:
    return {"object": "block", "type": "paragraph", "paragraph": {"rich_text": _rich_text(text)}}


def _heading_block(level: str, text: str) -> dict:
    return {"object": "block", "type": level, level: {"rich_text": _rich_text(text)}}


def _list_block(list_type: str, text: str) -> dict:
    return {"object": "block", "type": list_type, list_type: {"rich_text": _rich_text(text)}}


def _todo_block(text: str, checked: bool = False) -> dict:
    return {"object": "block", "type": "to_do", "to_do": {"rich_text": _rich_text(text), "checked": checked}}


def _quote_block(text: str) -> dict:
    return {"object": "block", "type": "quote", "quote": {"rich_text": _rich_text(text)}}


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_search(query: str, limit: int = 10) -> int:
    """Search Notion workspace."""
    token = _load_token()
    body = {"query": query, "page_size": min(limit, 100)}
    result = _api_request("POST", "/search", token, body)

    pages = []
    for item in result.get("results", []):
        if item.get("object") == "page":
            title_prop = item.get("properties", {}).get("title", {})
            title_array = title_prop.get("title", []) if title_prop else []
            title = "".join(t.get("plain_text", "") for t in title_array) if title_array else "Untitled"

            pages.append({
                "id": item["id"],
                "title": title,
                "url": item.get("url", ""),
                "last_edited": item.get("last_edited_time", ""),
                "created": item.get("created_time", ""),
            })

    print(json.dumps({"query": query, "count": len(pages), "pages": pages}, indent=2))
    return 0


def cmd_get(page_id: str) -> int:
    """Get page content."""
    token = _load_token()

    # Get page metadata
    page = _api_request("GET", f"/pages/{page_id}", token)

    # Get title
    title_prop = page.get("properties", {}).get("title", {})
    title_array = title_prop.get("title", []) if title_prop else []
    title = "".join(t.get("plain_text", "") for t in title_array) if title_array else "Untitled"

    # Get blocks (content)
    blocks_resp = _api_request("GET", f"/blocks/{page_id}/children?page_size=100", token)
    blocks = blocks_resp.get("results", [])
    content = _blocks_to_text(blocks)

    print(json.dumps({
        "id": page_id,
        "title": title,
        "url": page.get("url", ""),
        "last_edited": page.get("last_edited_time", ""),
        "content": content,
    }, indent=2))
    return 0


def cmd_create(parent_id: str, title: str, content: str = "") -> int:
    """Create a new page."""
    token = _load_token()

    # Determine parent type (page or database)
    body: dict[str, Any] = {
        "parent": {"page_id": parent_id},
        "properties": {
            "title": {"title": _rich_text(title)},
        },
    }

    if content:
        body["children"] = _text_to_blocks(content)

    result = _api_request("POST", "/pages", token, body)

    print(json.dumps({
        "id": result["id"],
        "url": result.get("url", ""),
        "title": title,
        "created": True,
    }, indent=2))
    return 0


def cmd_update(page_id: str, title: str) -> int:
    """Update page title."""
    token = _load_token()

    body = {
        "properties": {
            "title": {"title": _rich_text(title)},
        },
    }

    result = _api_request("PATCH", f"/pages/{page_id}", token, body)

    print(json.dumps({
        "id": result["id"],
        "title": title,
        "updated": True,
    }, indent=2))
    return 0


def cmd_append(page_id: str, content: str) -> int:
    """Append content to an existing page."""
    token = _load_token()

    blocks = _text_to_blocks(content)
    body = {"children": blocks}

    result = _api_request("PATCH", f"/blocks/{page_id}/children", token, body)

    print(json.dumps({
        "page_id": page_id,
        "blocks_added": len(blocks),
        "appended": True,
    }, indent=2))
    return 0


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Notion Pages — search, get, create, update, append")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # search
    p_search = subparsers.add_parser("search", help="Search pages in workspace")
    p_search.add_argument("query", help="Search query")
    p_search.add_argument("--limit", type=int, default=10, help="Max results (default: 10)")

    # get
    p_get = subparsers.add_parser("get", help="Get page content")
    p_get.add_argument("page_id", help="Page ID")

    # create
    p_create = subparsers.add_parser("create", help="Create a new page")
    p_create.add_argument("--parent", required=True, help="Parent page or database ID")
    p_create.add_argument("--title", required=True, help="Page title")
    p_create.add_argument("--content", default="", help="Page content (markdown)")

    # update
    p_update = subparsers.add_parser("update", help="Update page title")
    p_update.add_argument("page_id", help="Page ID")
    p_update.add_argument("--title", required=True, help="New title")

    # append
    p_append = subparsers.add_parser("append", help="Append content to a page")
    p_append.add_argument("page_id", help="Page ID")
    p_append.add_argument("--content", required=True, help="Content to append (markdown)")

    args = parser.parse_args(argv)

    if args.command == "search":
        return cmd_search(args.query, args.limit)
    elif args.command == "get":
        return cmd_get(args.page_id)
    elif args.command == "create":
        return cmd_create(args.parent, args.title, args.content)
    elif args.command == "update":
        return cmd_update(args.page_id, args.title)
    elif args.command == "append":
        return cmd_append(args.page_id, args.content)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
