#!/usr/bin/env python3
"""Stripe Connect — API key setup and verification.

Usage:
    python3 stripe_connect.py --check
    python3 stripe_connect.py --set-key sk_live_xxx

Zero external dependencies — stdlib only.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional, Sequence


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CONFIG_DIR = Path.home() / ".config" / "stripe"
CONFIG_FILE = CONFIG_DIR / "config.json"
STRIPE_API = "https://api.stripe.com/v1"


# ---------------------------------------------------------------------------
# Immutable types
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CheckResult:
    configured: bool
    mode: str = ""
    account_id: str = ""
    account_name: str = ""
    error: str = ""


@dataclass(frozen=True)
class SaveResult:
    success: bool
    mode: str = ""
    account_id: str = ""
    account_name: str = ""
    error: str = ""


# ---------------------------------------------------------------------------
# Config management
# ---------------------------------------------------------------------------

def load_key() -> Optional[str]:
    if not CONFIG_FILE.exists():
        return None
    try:
        data = json.loads(CONFIG_FILE.read_text())
        return data.get("api_key")
    except (json.JSONDecodeError, KeyError):
        return None


def save_config(api_key: str, mode: str = "", account_id: str = "", account_name: str = "") -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    config = {
        "api_key": api_key,
        "mode": mode,
        "account_id": account_id,
        "account_name": account_name,
    }
    CONFIG_FILE.write_text(json.dumps(config, indent=2))
    os.chmod(CONFIG_FILE, 0o600)


# ---------------------------------------------------------------------------
# API verification
# ---------------------------------------------------------------------------

def verify_key(api_key: str) -> tuple[bool, str, str, str, str]:
    """Verify key by calling Stripe API. Returns (ok, mode, account_id, account_name, error)."""
    # Use /v1/balance to verify — it works with both full secret keys and restricted keys
    # (/v1/account requires extra permissions that restricted keys may not have)
    req = urllib.request.Request(
        f"{STRIPE_API}/balance",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())

        # Balance endpoint doesn't return account info, so try /v1/account as a bonus
        account_id = ""
        account_name = ""
        try:
            acct_req = urllib.request.Request(
                f"{STRIPE_API}/account",
                headers={"Authorization": f"Bearer {api_key}"},
            )
            with urllib.request.urlopen(acct_req, timeout=10) as acct_resp:
                acct_data = json.loads(acct_resp.read().decode())
                account_id = acct_data.get("id", "")
                account_name = acct_data.get("settings", {}).get("dashboard", {}).get("display_name", "")
                if not account_name:
                    account_name = acct_data.get("business_profile", {}).get("name", "")
        except Exception:
            pass  # Restricted keys may not have account read permission — that's OK

        mode = "test" if api_key.startswith("sk_test_") or api_key.startswith("rk_test_") else "live"

        return True, mode, account_id, account_name, ""

    except urllib.error.HTTPError as exc:
        if exc.code == 401:
            return False, "", "", "", "Invalid API key. Make sure it starts with 'sk_live_', 'sk_test_', or 'rk_'."
        body = exc.read().decode() if exc.fp else ""
        return False, "", "", "", f"HTTP {exc.code}: {body[:200]}"
    except Exception as exc:
        return False, "", "", "", f"Connection error: {exc}"


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_check() -> int:
    api_key = load_key()
    if not api_key:
        result = CheckResult(configured=False, error="No API key configured")
        print(json.dumps(asdict(result)))
        return 1

    ok, mode, account_id, account_name, error = verify_key(api_key)
    if ok:
        result = CheckResult(configured=True, mode=mode, account_id=account_id, account_name=account_name)
        print(json.dumps(asdict(result)))
        return 0

    result = CheckResult(configured=False, error=error)
    print(json.dumps(asdict(result)))
    return 1


def cmd_set_key(api_key: str) -> int:
    api_key = api_key.strip()

    if not (api_key.startswith("sk_") or api_key.startswith("rk_")):
        print(json.dumps(asdict(SaveResult(
            success=False,
            error="Key should start with 'sk_live_', 'sk_test_', or 'rk_'. Get it from dashboard.stripe.com/apikeys.",
        ))))
        return 1

    if api_key.startswith("pk_"):
        print(json.dumps(asdict(SaveResult(
            success=False,
            error="That's a publishable key (pk_). I need the Secret key (sk_) or a Restricted key (rk_).",
        ))))
        return 1

    ok, mode, account_id, account_name, error = verify_key(api_key)
    if not ok:
        print(json.dumps(asdict(SaveResult(success=False, error=error))))
        return 1

    save_config(api_key, mode, account_id, account_name)

    result = SaveResult(success=True, mode=mode, account_id=account_id, account_name=account_name)
    print(json.dumps(asdict(result)))
    return 0


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(argv: Optional[Sequence[str]] = None) -> int:
    args = argv or sys.argv[1:]

    if "--check" in args:
        return cmd_check()

    for i, arg in enumerate(args):
        if arg == "--set-key" and i + 1 < len(args):
            return cmd_set_key(args[i + 1])

    print("Usage:")
    print("  python3 stripe_connect.py --check")
    print("  python3 stripe_connect.py --set-key <API_KEY>")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
