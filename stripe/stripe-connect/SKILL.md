---
name: stripe-connect
description: Set up Stripe API key. Use when Stripe commands fail with auth errors or when user wants to connect their Stripe account. Takes 1 minute — user copies their API key from the Stripe Dashboard.
---

# Stripe Connect

Connect your Stripe account. One API key, one minute.

## How to Set Up

1. User goes to [dashboard.stripe.com/apikeys](https://dashboard.stripe.com/apikeys)
2. Copies the **Secret key** (starts with `sk_live_` or `sk_test_`)
3. Pastes it in the chat

> ⚠️ **Use a Restricted key for safety.** In the Stripe Dashboard, click **+ Create restricted key**, give it **Read** permissions only, and use that key instead of the full secret key. This way the AI can view data but can't create charges or modify anything.

## AI Agent Flow

### Check if configured:
```bash
python3 stripe-connect/scripts/stripe_connect.py --check
```

Returns JSON: `{"configured": true, "mode": "live", "account": "..."}` or `{"configured": false}`.

### Save key (after user pastes it):
```bash
python3 stripe-connect/scripts/stripe_connect.py --set-key "sk_live_xxxxxxxxxxxxx"
```

Saves to `~/.config/stripe/config.json` and verifies the key works by calling the Stripe API.

### When Stripe is not configured, tell the user EXACTLY this:

"To connect Stripe, I just need your API key. It takes about 1 minute:

1. Open this page: https://dashboard.stripe.com/apikeys
2. Copy an API key — either:
   - The **Secret key** (starts with `sk_live_` or `sk_test_`) — has full access
   - Or better: create a **Restricted key** (starts with `rk_live_` or `rk_test_`) with Read-only permissions
3. Paste the key here

For a detailed guide: https://skillpack.gitbook.io/skillpack-docs/integrations/stripe"

## CRITICAL RULES

1. **NEVER ask for OAuth or client_id** — Stripe uses a single API key
2. **Key starts with `sk_live_`, `sk_test_`, `rk_live_`, or `rk_test_`** — if the user pastes a publishable key (`pk_`), that's wrong
3. **Recommend restricted keys** — always suggest read-only restricted keys for safety
4. **Always show the Gitbook link** when guiding setup

## Credential Storage

| File | Path |
|------|------|
| Config | `~/.config/stripe/config.json` |
| Format | `{"api_key": "sk_...", "mode": "live/test", "account_id": "acct_..."}` |
| Permissions | `0600` (user-only read) |

## Follow-Up Questions

- "**Show** me this month's **revenue**"
- "**List** my recent **customers**"
- "**Check** for **failed** payments"
