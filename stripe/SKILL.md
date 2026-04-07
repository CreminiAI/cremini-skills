---
name: stripe
description: View Stripe revenue, subscriptions, customers, payments, and products through conversation. Check MRR, find failed payments, list recent customers, and review pricing. Use when the user asks about revenue, payments, subscriptions, invoices, or anything related to Stripe.
---

# Stripe

View your Stripe data through conversation — revenue, subscriptions, customers, payments, and products.

## Authentication

Requires a Stripe API key. If not configured, load `stripe-connect/SKILL.md` to guide the user through setup.

Check: `python3 stripe-connect/scripts/stripe_connect.py --check`

## Routing

| User wants to... | Load |
|---|---|
| Connect Stripe / fix auth errors | `stripe-connect/SKILL.md` |
| MRR, revenue, charges, balance, refunds | `revenue/SKILL.md` |
| List customers, view subscriptions, payment history | `customers/SKILL.md` |
| List products, prices, invoices | `products/SKILL.md` |

## How Scripts Access Stripe

All scripts read the API key from `~/.config/stripe/config.json`:

```json
{"api_key": "sk_live_xxx...", "mode": "live"}
```

Scripts call the Stripe REST API (`https://api.stripe.com/v1/`) with this key in the `Authorization: Bearer` header.

## Follow-Up Questions

- "**Show** me this month's **revenue**"
- "**List** my recent **customers**"
- "**Check** for **failed payments** in the last 7 days"
- "**Show** my **products** and pricing"
