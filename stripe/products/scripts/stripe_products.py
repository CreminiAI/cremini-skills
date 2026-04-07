#!/usr/bin/env python3
"""Stripe Products — products, prices, invoices.

Usage:
    python3 stripe_products.py products --limit 20
    python3 stripe_products.py prices --product <id>
    python3 stripe_products.py prices --all
    python3 stripe_products.py invoices --limit 10
    python3 stripe_products.py invoices --customer <id> --status open

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


def _cents(amount: Any) -> str:
    if amount is None:
        return ""
    return f"${int(amount) / 100:,.2f}"


def _ts_to_iso(ts: int) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat() if ts else ""


def cmd_products(limit: int = 20) -> int:
    key = _load_key()
    result = _api_get("/products", key, {"limit": min(limit, 100), "active": "true"})

    products = []
    for p in result.get("data", []):
        products.append({
            "id": p.get("id", ""),
            "name": p.get("name", ""),
            "description": p.get("description", ""),
            "active": p.get("active", False),
            "created": _ts_to_iso(p.get("created", 0)),
            "default_price": p.get("default_price", ""),
        })

    print(json.dumps({"count": len(products), "products": products}, indent=2))
    return 0


def cmd_prices(product_id: str = "", all_prices: bool = False) -> int:
    key = _load_key()
    params: dict[str, Any] = {"limit": 100, "active": "true"}
    if product_id:
        params["product"] = product_id

    result = _api_get("/prices", key, params)

    prices = []
    for p in result.get("data", []):
        recurring = p.get("recurring") or {}
        prices.append({
            "id": p.get("id", ""),
            "product": p.get("product", ""),
            "nickname": p.get("nickname", ""),
            "unit_amount": _cents(p.get("unit_amount")),
            "currency": (p.get("currency") or "").upper(),
            "type": p.get("type", ""),
            "interval": recurring.get("interval", ""),
            "interval_count": recurring.get("interval_count", ""),
            "active": p.get("active", False),
        })

    print(json.dumps({"count": len(prices), "prices": prices}, indent=2))
    return 0


def cmd_invoices(limit: int = 10, customer: str = "", status: str = "") -> int:
    key = _load_key()
    params: dict[str, Any] = {"limit": min(limit, 100)}
    if customer:
        params["customer"] = customer
    if status:
        params["status"] = status

    result = _api_get("/invoices", key, params)

    invoices = []
    for inv in result.get("data", []):
        invoices.append({
            "id": inv.get("id", ""),
            "customer": inv.get("customer", ""),
            "customer_email": inv.get("customer_email", ""),
            "status": inv.get("status", ""),
            "amount_due": _cents(inv.get("amount_due")),
            "amount_paid": _cents(inv.get("amount_paid")),
            "currency": (inv.get("currency") or "").upper(),
            "created": _ts_to_iso(inv.get("created", 0)),
            "due_date": _ts_to_iso(inv.get("due_date", 0)),
            "hosted_invoice_url": inv.get("hosted_invoice_url", ""),
        })

    print(json.dumps({"count": len(invoices), "invoices": invoices}, indent=2))
    return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Stripe Products — products, prices, invoices")
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_products = subparsers.add_parser("products", help="List products")
    p_products.add_argument("--limit", type=int, default=20)

    p_prices = subparsers.add_parser("prices", help="List prices")
    p_prices.add_argument("--product", default="", help="Filter by product ID")
    p_prices.add_argument("--all", action="store_true", help="Show all prices")

    p_invoices = subparsers.add_parser("invoices", help="List invoices")
    p_invoices.add_argument("--limit", type=int, default=10)
    p_invoices.add_argument("--customer", default="", help="Filter by customer ID")
    p_invoices.add_argument("--status", default="", help="Filter: draft, open, paid, void, uncollectible")

    args = parser.parse_args(argv)

    if args.command == "products":
        return cmd_products(args.limit)
    elif args.command == "prices":
        return cmd_prices(args.product, args.all)
    elif args.command == "invoices":
        return cmd_invoices(args.limit, args.customer, args.status)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
