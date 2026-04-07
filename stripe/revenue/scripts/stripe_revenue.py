#!/usr/bin/env python3
"""Stripe Revenue — charges, balance, refunds, failed payments.

Usage:
    python3 stripe_revenue.py charges --days 30
    python3 stripe_revenue.py charges --start 2026-03-01 --end 2026-03-31
    python3 stripe_revenue.py balance
    python3 stripe_revenue.py refunds --days 30 --limit 20
    python3 stripe_revenue.py failed --days 7 --limit 20

Zero external dependencies — stdlib only.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional, Sequence


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CONFIG_FILE = Path.home() / ".config" / "stripe" / "config.json"
STRIPE_API = "https://api.stripe.com/v1"


# ---------------------------------------------------------------------------
# Auth + API
# ---------------------------------------------------------------------------

def _load_key() -> str:
    if not CONFIG_FILE.exists():
        print("Error: Stripe not configured. Run: stripe-connect --set-key <KEY>", file=sys.stderr)
        sys.exit(1)
    data = json.loads(CONFIG_FILE.read_text())
    key = data.get("api_key", "")
    if not key:
        print("Error: API key is empty. Run: stripe-connect --set-key <KEY>", file=sys.stderr)
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
        if exc.code == 401:
            print("Error: Invalid Stripe API key. Run: stripe-connect --set-key <KEY>", file=sys.stderr)
        else:
            print(f"Error: Stripe API {exc.code}: {body[:300]}", file=sys.stderr)
        sys.exit(1)


def _ts(days_ago: int = 0, date_str: str = "") -> int:
    """Convert to Unix timestamp."""
    if date_str:
        dt = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    else:
        dt = datetime.now(timezone.utc) - timedelta(days=days_ago)
    return int(dt.timestamp())


def _cents_to_dollars(cents: int) -> str:
    return f"${cents / 100:,.2f}"


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_charges(days: int = 30, start: str = "", end: str = "", limit: int = 100) -> int:
    key = _load_key()

    params: dict[str, Any] = {"limit": min(limit, 100)}
    if start:
        params["created[gte]"] = _ts(date_str=start)
    else:
        params["created[gte]"] = _ts(days_ago=days)
    if end:
        params["created[lte]"] = _ts(date_str=end)

    result = _api_get("/charges", key, params)
    charges = result.get("data", [])

    total_amount = sum(c.get("amount", 0) for c in charges if c.get("status") == "succeeded")
    total_count = sum(1 for c in charges if c.get("status") == "succeeded")
    failed_count = sum(1 for c in charges if c.get("status") == "failed")
    refunded_amount = sum(c.get("amount_refunded", 0) for c in charges)

    currency = charges[0].get("currency", "usd").upper() if charges else "USD"

    print(json.dumps({
        "period": f"Last {days} days" if not start else f"{start} to {end or 'now'}",
        "total_revenue": _cents_to_dollars(total_amount),
        "total_revenue_cents": total_amount,
        "successful_charges": total_count,
        "failed_charges": failed_count,
        "total_refunded": _cents_to_dollars(refunded_amount),
        "currency": currency,
        "charges_returned": len(charges),
    }, indent=2))
    return 0


def cmd_balance() -> int:
    key = _load_key()
    result = _api_get("/balance", key)

    available = result.get("available", [])
    pending = result.get("pending", [])

    output: dict[str, Any] = {"available": [], "pending": []}
    for item in available:
        output["available"].append({
            "amount": _cents_to_dollars(item.get("amount", 0)),
            "currency": item.get("currency", "").upper(),
        })
    for item in pending:
        output["pending"].append({
            "amount": _cents_to_dollars(item.get("amount", 0)),
            "currency": item.get("currency", "").upper(),
        })

    print(json.dumps(output, indent=2))
    return 0


def cmd_refunds(days: int = 30, limit: int = 20) -> int:
    key = _load_key()

    params = {
        "limit": min(limit, 100),
        "created[gte]": _ts(days_ago=days),
    }
    result = _api_get("/refunds", key, params)
    refunds = result.get("data", [])

    total_refunded = sum(r.get("amount", 0) for r in refunds)

    items = []
    for r in refunds:
        items.append({
            "id": r.get("id", ""),
            "amount": _cents_to_dollars(r.get("amount", 0)),
            "currency": r.get("currency", "").upper(),
            "status": r.get("status", ""),
            "reason": r.get("reason", ""),
            "created": datetime.fromtimestamp(r.get("created", 0), tz=timezone.utc).isoformat(),
        })

    print(json.dumps({
        "period": f"Last {days} days",
        "total_refunded": _cents_to_dollars(total_refunded),
        "count": len(items),
        "refunds": items,
    }, indent=2))
    return 0


def cmd_failed(days: int = 7, limit: int = 20) -> int:
    key = _load_key()

    params = {
        "limit": min(limit, 100),
        "created[gte]": _ts(days_ago=days),
    }
    # Get all charges, then filter failed
    result = _api_get("/charges", key, params)
    failed = [c for c in result.get("data", []) if c.get("status") == "failed"]

    items = []
    for c in failed:
        items.append({
            "id": c.get("id", ""),
            "amount": _cents_to_dollars(c.get("amount", 0)),
            "currency": c.get("currency", "").upper(),
            "failure_code": c.get("failure_code", ""),
            "failure_message": c.get("failure_message", ""),
            "customer": c.get("customer", ""),
            "created": datetime.fromtimestamp(c.get("created", 0), tz=timezone.utc).isoformat(),
        })

    print(json.dumps({
        "period": f"Last {days} days",
        "failed_count": len(items),
        "charges": items,
    }, indent=2))
    return 0


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Stripe Revenue — charges, balance, refunds, failed")
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_charges = subparsers.add_parser("charges", help="Revenue summary")
    p_charges.add_argument("--days", type=int, default=30, help="Look back N days (default: 30)")
    p_charges.add_argument("--start", default="", help="Start date (YYYY-MM-DD)")
    p_charges.add_argument("--end", default="", help="End date (YYYY-MM-DD)")
    p_charges.add_argument("--limit", type=int, default=100, help="Max charges to fetch")

    subparsers.add_parser("balance", help="Current balance")

    p_refunds = subparsers.add_parser("refunds", help="Recent refunds")
    p_refunds.add_argument("--days", type=int, default=30, help="Look back N days")
    p_refunds.add_argument("--limit", type=int, default=20, help="Max results")

    p_failed = subparsers.add_parser("failed", help="Failed payments")
    p_failed.add_argument("--days", type=int, default=7, help="Look back N days")
    p_failed.add_argument("--limit", type=int, default=20, help="Max results")

    args = parser.parse_args(argv)

    if args.command == "charges":
        return cmd_charges(args.days, args.start, args.end, args.limit)
    elif args.command == "balance":
        return cmd_balance()
    elif args.command == "refunds":
        return cmd_refunds(args.days, args.limit)
    elif args.command == "failed":
        return cmd_failed(args.days, args.limit)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
