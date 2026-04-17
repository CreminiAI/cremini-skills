---
name: amazon-product
description: Fetch Amazon product details by ASIN via `skillpack-cli amazon product`. Use whenever the user gives an Amazon ASIN and wants listing details, product attributes, delivery-aware info, or a quick product lookup from Amazon data.
---

# Amazon Product

Retrieve Amazon product details by ASIN through `skillpack-cli`.

## Execution Order

Use this order so the workflow stays fast:

1. Extract the ASIN and decide whether `--delivery-zip` is needed.
2. Run the target command directly. Do not pre-check `skillpack-cli` or `npm` before the first attempt.
3. If the command fails because `skillpack-cli` is missing, install it with:

```bash
npm install -g @cermini/skillpack-cli
```

4. After installation, rerun the same `skillpack-cli amazon product ...` command.
5. If installation fails because `npm` is missing, stop and tell the user that Node.js/npm must be installed first.
6. If the command fails because login or credentials are missing, stop and tell the user to run `skillpack-cli login`, then retry.

## Commands

```bash
skillpack-cli amazon product B0D5XWJQ5R
skillpack-cli amazon product B0D5XWJQ5R --delivery-zip 10001
```

## Output

`skillpack-cli` returns the Amazon product payload to stdout. If the ASIN is invalid or auth is missing, it returns an error on stderr with a non-zero exit code.

## Usage Notes

- Ask the user for the ASIN if they only provide a product name or Amazon URL.
- Start with `skillpack-cli amazon product <ASIN>` immediately instead of doing a separate availability check first.
- Only run the install command when the command output shows that `skillpack-cli` is missing.
- If `npm` is unavailable when installation is needed, stop and tell the user to install Node.js and npm first.
- If the command reports that the user is not logged in, authorization failed, or credentials are missing, stop and tell the user to run `skillpack-cli login`.
- Use `--delivery-zip` when delivery availability or localized offer details matter.
- Summarize the key fields the user actually cares about instead of dumping raw JSON unless they ask for the full payload.

## Follow-Up Questions

- "Look up ASIN **B0D5XWJQ5R** and summarize the listing"
- "Fetch Amazon product details for **B0D5XWJQ5R**"
- "Check whether ASIN **B0D5XWJQ5R** has different delivery info for ZIP **10001**"
