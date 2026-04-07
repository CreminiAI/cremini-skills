---
name: stripe-customers
description: List, search, and view Stripe customers and their subscriptions. Use when the user asks about customers, subscribers, churn, or customer payment history.
---

# Stripe Customers

List, search, and view customer details and subscriptions.

## Commands

### List recent customers
```bash
python3 customers/scripts/stripe_customers.py list --limit 10
```

### Search customers by email
```bash
python3 customers/scripts/stripe_customers.py search "john@example.com"
```

### Get customer details (including subscriptions)
```bash
python3 customers/scripts/stripe_customers.py get <customer-id>
```

### List active subscriptions
```bash
python3 customers/scripts/stripe_customers.py subscriptions --status active --limit 20
```

### Subscription summary (counts by status)
```bash
python3 customers/scripts/stripe_customers.py sub-summary
```

## Follow-Up Questions

- "**List** my most recent **customers**"
- "**Search** for customer **john@example.com**"
- "**Show** all **active subscriptions**"
- "**How many** subscribers do I have by **status**?"
