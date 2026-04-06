#!/usr/bin/env python3
"""Notion Connect — token setup and verification.

Usage:
    python3 notion_connect.py --check          # Check if configured
    python3 notion_connect.py --set-token TOKEN # Save and verify token

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

CONFIG_DIR = Path.home() / ".config" / "notion"
CONFIG_FILE = CONFIG_DIR / "config.json"
NOTION_API = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"


# ---------------------------------------------------------------------------
# Immutable types
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CheckResult:
    configured: bool
    workspace_name: str = ""
    workspace_id: str = ""
    bot_name: str = ""
    error: str = ""


@dataclass(frozen=True)
class SaveResult:
    success: bool
    workspace_name: str = ""
    workspace_id: str = ""
    error: str = ""


# ---------------------------------------------------------------------------
# Config management
# ---------------------------------------------------------------------------

def load_token() -> Optional[str]:
    """Load token from config file. Returns None if not configured."""
    if not CONFIG_FILE.exists():
        return None
    try:
        data = json.loads(CONFIG_FILE.read_text())
        return data.get("token")
    except (json.JSONDecodeError, KeyError):
        return None


def save_config(token: str, workspace_name: str = "", workspace_id: str = "") -> None:
    """Save token and workspace info to config file."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    config = {
        "token": token,
        "workspace_name": workspace_name,
        "workspace_id": workspace_id,
    }
    CONFIG_FILE.write_text(json.dumps(config, indent=2))
    os.chmod(CONFIG_FILE, 0o600)


# ---------------------------------------------------------------------------
# API verification
# ---------------------------------------------------------------------------

def verify_token(token: str) -> tuple[bool, str, str, str]:
    """Verify token by calling Notion API. Returns (ok, workspace_name, workspace_id, error)."""
    req = urllib.request.Request(
        f"{NOTION_API}/users/me",
        headers={
            "Authorization": f"Bearer {token}",
            "Notion-Version": NOTION_VERSION,
            "Content-Type": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())

        bot = data.get("bot", {})
        workspace_name = bot.get("workspace_name", "")
        workspace_id = bot.get("workspace_id", "")

        return True, workspace_name, workspace_id, ""

    except urllib.error.HTTPError as exc:
        if exc.code == 401:
            return False, "", "", "Invalid token. Make sure it starts with 'ntn_' and was copied correctly."
        if exc.code == 403:
            return False, "", "", "Token is valid but doesn't have access. Check integration permissions in Notion."
        body = exc.read().decode() if exc.fp else ""
        return False, "", "", f"HTTP {exc.code}: {body[:200]}"
    except Exception as exc:
        return False, "", "", f"Connection error: {exc}"


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_check() -> int:
    """Check if Notion is configured and token is valid."""
    token = load_token()

    if not token:
        result = CheckResult(configured=False, error="No token configured")
        print(json.dumps(asdict(result)))
        return 1

    ok, workspace_name, workspace_id, error = verify_token(token)

    if ok:
        result = CheckResult(
            configured=True,
            workspace_name=workspace_name,
            workspace_id=workspace_id,
        )
        print(json.dumps(asdict(result)))
        return 0

    result = CheckResult(configured=False, error=error)
    print(json.dumps(asdict(result)))
    return 1


def cmd_set_token(token: str) -> int:
    """Save token, verify it, and store workspace info."""
    token = token.strip()

    if not token.startswith("ntn_") and not token.startswith("secret_"):
        print(json.dumps(asdict(SaveResult(
            success=False,
            error="Token should start with 'ntn_'. Get it from notion.so/my-integrations.",
        ))))
        return 1

    ok, workspace_name, workspace_id, error = verify_token(token)

    if not ok:
        print(json.dumps(asdict(SaveResult(success=False, error=error))))
        return 1

    save_config(token, workspace_name, workspace_id)

    result = SaveResult(
        success=True,
        workspace_name=workspace_name,
        workspace_id=workspace_id,
    )
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
        if arg == "--set-token" and i + 1 < len(args):
            return cmd_set_token(args[i + 1])

    print("Usage:")
    print("  python3 notion_connect.py --check")
    print("  python3 notion_connect.py --set-token <TOKEN>")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
