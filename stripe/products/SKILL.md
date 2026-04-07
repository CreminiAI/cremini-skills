---
name: stripe-products
description: List Stripe products, prices, and invoices. Use when the user asks about products, pricing, plans, or invoices.
---

# Stripe Products

List products, prices, and invoices.

## Commands

### List products
```bash
python3 products/scripts/stripe_products.py products --limit 20
```

### List prices for a product
```bash
python3 products/scripts/stripe_products.py prices --product <product-id>
python3 products/scripts/stripe_products.py prices --all
```

### List invoices
```bash
python3 products/scripts/stripe_products.py invoices --limit 10
python3 products/scripts/stripe_products.py invoices --customer <customer-id>
python3 products/scripts/stripe_products.py invoices --status open
```

## Follow-Up Questions

- "**List** all my **products** and their prices"
- "**Show** the pricing for my **Pro plan**"
- "**Find** all **open invoices**"
- "**Show** invoices for **customer** john@example.com"
