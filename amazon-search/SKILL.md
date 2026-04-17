---
name: amazon-search
description: Search Amazon products by keyword via `skillpack-cli amazon search`. Use whenever the user wants Amazon search results, product discovery, keyword-based listing lookup, pagination, or delivery-aware search results from Amazon data.
---

# Amazon Search

Search Amazon product listings by keyword through `skillpack-cli`.

## Execution Order

Use this order so the workflow stays fast:

1. Extract the search keyword and decide whether `--page` or `--delivery-zip` is needed.
2. Run the target command directly. Do not pre-check `skillpack-cli` or `npm` before the first attempt.
3. If the command fails because `skillpack-cli` is missing, install it with:

```bash
npm install -g @cremini/skillpack-cli
```

4. After installation, rerun the same `skillpack-cli amazon search ...` command.
5. If installation fails because `npm` is missing, stop and tell the user that Node.js/npm must be installed first.
6. If the command fails because login or credentials are missing, stop and tell the user to run `skillpack-cli login`, then retry.

## Commands

```bash
skillpack-cli amazon search --query "wireless earbuds"
skillpack-cli amazon search --query "wireless earbuds" --page 2
skillpack-cli amazon search --query "wireless earbuds" --delivery-zip 10001
skillpack-cli amazon search --query "wireless earbuds" --page 2 --delivery-zip 10001
```

## Output

`skillpack-cli` returns the Amazon search payload to stdout as JSON. If the query is invalid or auth is missing, it returns an error on stderr with a non-zero exit code.

## Usage Notes

- Ask the user for the keyword if they only say "search Amazon for this" without the actual query.
- Start with `skillpack-cli amazon search --query "<keyword>"` immediately instead of doing a separate availability check first.
- Use `--page` when the user asks for later results or more options beyond the first page.
- Use `--delivery-zip` when localized offer availability or delivery messaging matters.
- Only run the install command when the command output shows that `skillpack-cli` is missing.
- If `npm` is unavailable when installation is needed, stop and tell the user to install Node.js and npm first.
- If the command reports that the user is not logged in, authorization failed, or credentials are missing, stop and tell the user to run `skillpack-cli login`.
- Summarize the listings the user actually cares about instead of dumping raw JSON unless they ask for the full payload.
- When the user is comparing options, highlight the top few results with key fields such as title, ASIN, price, rating, and delivery-related notes when present.

## Follow-Up Questions

- "Search Amazon for **wireless earbuds**"
- "Show me page **2** of Amazon search results for **standing desk**"
- "Search Amazon for **air fryer liners** with delivery ZIP **10001**"
- "Find Amazon listings for **ergonomic office chair** and summarize the best options"
