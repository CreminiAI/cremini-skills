---
name: notion
description: Read, create, and manage Notion pages and databases through conversation. Search workspace content, create new pages, query databases, and update existing content. Use when the user asks about Notion, their notes, docs, wikis, project boards, or any Notion database.
---

# Notion

Manage your Notion workspace through conversation — search pages, create docs, query databases, and update content.

## Authentication

Requires a Notion Integration Token. If not configured, load `notion-connect/SKILL.md` to guide the user through setup.

Check: `python3 notion-connect/scripts/notion_connect.py --check`

## Routing

| User wants to... | Load |
|---|---|
| Connect Notion / fix auth errors | `notion-connect/SKILL.md` |
| Search, read, create, edit pages | `pages/SKILL.md` |
| Query databases, add entries, list databases | `databases/SKILL.md` |

## How Scripts Access Notion

All scripts read the token from `~/.config/notion/config.json`:

```json
{"token": "ntn_xxx..."}
```

Scripts use the Notion REST API (`https://api.notion.com/v1/`) with this token in the `Authorization: Bearer` header.

## Follow-Up Questions

- "**Search** my Notion for notes about **Q2 planning**"
- "**Create** a new **page** in my workspace with today's meeting notes"
- "**Query** my **tasks database** for items due this week"
- "**Add** a new entry to my **projects database**"
