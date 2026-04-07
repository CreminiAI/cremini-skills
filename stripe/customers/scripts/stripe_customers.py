#!/usr/bin/env python3
"""Stripe Customers — list, search, get details, subscriptions.

Usage:
    python3 stripe_customers.py list --limit 10
    python3 stripe_customers.py search "email@example.com"
    python3 stripe_customers.py get <customer-id>
    python3 stripe_customers.py subscriptions --status active --limit 20
    python3 stripe_customers.py sub-summary

Zero external dependencies — stdlib only.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional, Sequence


CONFIG_FILE = Path.home() / ".config" / "stripe" / "config.json"
STRIPE_API = "https://api.stripe.com/v1"


def _load_key() -> str:
    if not CONFIG_FILE.exists():
        print("Error: Stripe not configured. Run: stripe-connect --set-key <KEY>", file=sys.stderr)
        sys.exit(1)
    data = json.loads(CONFIG_FILE.read_text())
    key = data.get("api_key", "")
    if not key:
        print("Error: API key is empty.", file=sys.stderr)
        sys.exit(1)
    return key


def _api_get(path: str, key: str, params: Optional[dict] = None) -> dict:
    url = f"{STRIPE_API}{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params, doseq=True)
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {key}"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        body = exc.read().decode() if exc.fp else ""
        print(f"Error: Stripe API {exc.code}: {body[:300]}", file=sys.stderr)
        sys.exit(1)


def _cents(amount: int) -> str:
    return f"${amount / 100:,.2f}"


def _ts_to_iso(ts: int) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat() if ts else ""


def cmd_list(limit: int = 10) -> int:
    key = _load_key()
    result = _api_get("/customers", key, {"limit": min(limit, 100)})

    customers = []
    for c in result.get("data", []):
        customers.append({
            "id": c.get("id", ""),
            "email": c.get("email", ""),
            "name": c.get("name", ""),
            "created": _ts_to_iso(c.get("created", 0)),
            "currency": (c.get("currency") or "").upper(),
        })

    print(json.dumps({"count": len(customers), "customers": customers}, indent=2))
    return 0


def cmd_search(query: str) -> int:
    key = _load_key()
    params = {"query": f"email:'{query}'", "limit": 10}
    result = _api_get("/customers/search", key, params)

    customers = []
    for c in result.get("data", []):
        customers.append({
            "id": c.get("id", ""),
            "email": c.get("email", ""),
            "name": c.get("name", ""),
            "created": _ts_to_iso(c.get("created", 0)),
        })

    print(json.dumps({"query": query, "count": len(customers), "customers": customers}, indent=2))
    return 0


def cmd_get(customer_id: str) -> int:
    key = _load_key()
    customer = _api_get(f"/customers/{customer_id}", key)

    # Get subscriptions
    subs_result = _api_get("/subscriptions", key, {"customer": customer_id, "limit": 10})
    subs = []
    for s in subs_result.get("data", []):
        items = s.get("items", {}).get("data", [])
        plan_name = ""
        if items:
            plan_name = items[0].get("price", {}).get("nickname", "") or items[0].get("plan", {}).get("nickname", "")

        subs.append({
            "id": s.get("id", ""),
            "status": s.get("status", ""),
            "plan": plan_name,
            "amount": _cents(s.get("items", {}).get("data", [{}])[0].get("price", {}).get("unit_amount", 0)) if items else "",
            "interval": items[0].get("price", {}).get("recurring", {}).get("interval", "") if items else "",
            "current_period_end": _ts_to_iso(s.get("current_period_end", 0)),
        })

    print(json.dumps({
        "id": customer.get("id", ""),
        "email": customer.get("email", ""),
        "name": customer.get("name", ""),
        "created": _ts_to_iso(customer.get("created", 0)),
        "balance": _cents(customer.get("balance", 0)),
        "currency": (customer.get("currency") or "").upper(),
        "subscriptions": subs,
    }, indent=2))
    return 0


def cmd_subscriptions(status: str = "active", limit: int = 20) -> int:
    key = _load_key()
    params: dict[str, Any] = {"limit": min(limit, 100)}
    if status != "all":
        params["status"] = status

    result = _api_get("/subscriptions", key, params)

    subs = []
    for s in result.get("data", []):
        items = s.get("items", {}).get("data", [])
        subs.append({
            "id": s.get("id", ""),
            "customer": s.get("customer", ""),
            "status": s.get("status", ""),
            "amount": _cents(items[0].get("price", {}).get("unit_amount", 0)) if items else "",
            "interval": items[0].get("price", {}).get("recurring", {}).get("interval", "") if items else "",
            "created": _ts_to_iso(s.get("created", 0)),
            "current_period_end": _ts_to_iso(s.get("current_period_end", 0)),
        })

    print(json.dumps({"status_filter": status, "count": len(subs), "subscriptions": subs}, indent=2))
    return 0


def cmd_sub_summary() -> int:
    key = _load_key()

    counts: dict[str, int] = {}
    for status in ("active", "past_due", "canceled", "trialing", "incomplete"):
        result = _api_get("/subscriptions", key, {"status": status, "limit": 1})
        counts[status] = result.get("total_count", len(result.get("data", [])))

    print(json.dumps({"subscription_counts": counts, "total": sum(counts.values())}, indent=2))
    return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Stripe Customers")
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_list = subparsers.add_parser("list", help="List recent customers")
    p_list.add_argument("--limit", type=int, default=10)

    p_search = subparsers.add_parser("search", help="Search by email")
    p_search.add_argument("query", help="Email to search")

    p_get = subparsers.add_parser("get", help="Get customer details")
    p_get.add_argument("customer_id", help="Customer ID (cus_xxx)")

    p_subs = subparsers.add_parser("subscriptions", help="List subscriptions")
    p_subs.add_argument("--status", default="active", help="Filter: active, past_due, canceled, trialing, all")
    p_subs.add_argument("--limit", type=int, default=20)

    subparsers.add_parser("sub-summary", help="Subscription counts by status")

    args = parser.parse_args(argv)

    handlers = {
        "list": lambda: cmd_list(args.limit),
        "search": lambda: cmd_search(args.query),
        "get": lambda: cmd_get(args.customer_id),
        "subscriptions": lambda: cmd_subscriptions(args.status, args.limit),
        "sub-summary": cmd_sub_summary,
    }
    return handlers[args.command]()


if __name__ == "__main__":
    raise SystemExit(main())
