---
name: stripe-revenue
description: View Stripe revenue metrics — MRR, total charges, balance, refunds, and payouts. Use when the user asks about revenue, income, MRR, charges, refunds, or financial overview.
---

# Stripe Revenue

View revenue metrics, charges, balance, refunds, and payouts.

## Prerequisites

Run `stripe-connect --check` first. If not configured, load `stripe-connect/SKILL.md`.

## Commands

### Revenue summary (charges in a date range)
```bash
python3 revenue/scripts/stripe_revenue.py charges --days 30
python3 revenue/scripts/stripe_revenue.py charges --start 2026-03-01 --end 2026-03-31
```

### Current balance
```bash
python3 revenue/scripts/stripe_revenue.py balance
```

### Recent refunds
```bash
python3 revenue/scripts/stripe_revenue.py refunds --days 30 --limit 20
```

### Failed payments
```bash
python3 revenue/scripts/stripe_revenue.py failed --days 7 --limit 20
```

## Follow-Up Questions

- "**Show** me this month's total **revenue**"
- "**Check** my current Stripe **balance**"
- "**List** recent **refunds**"
- "**Find** all **failed payments** this week"
