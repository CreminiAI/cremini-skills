---
name: notion-pages
description: Search, read, create, update, and append content to Notion pages. Use when the user wants to find pages, read content, create new docs, or edit existing pages in Notion.
---

# Notion Pages

Search, read, create, and edit Notion pages.

## Prerequisites

Run `notion-connect --check` first. If not configured, load `notion-connect/SKILL.md`.

## Commands

### Search pages
```bash
python3 pages/scripts/notion_pages.py search "meeting notes"
python3 pages/scripts/notion_pages.py search "Q2 planning" --limit 5
```

### Get page content
```bash
python3 pages/scripts/notion_pages.py get <page-id>
```

### Create a new page
```bash
python3 pages/scripts/notion_pages.py create --parent <page-id-or-database-id> --title "Meeting Notes" --content "## Attendees\n- Alice\n- Bob"
```

### Update page properties
```bash
python3 pages/scripts/notion_pages.py update <page-id> --title "New Title"
```

### Append content to existing page
```bash
python3 pages/scripts/notion_pages.py append <page-id> --content "## Action Items\n- Follow up with client"
```

## Output

All commands output JSON to stdout. Page content is returned as markdown-like text extracted from Notion blocks.

## Follow-Up Questions

- "**Search** for pages about **product roadmap**"
- "**Create** a new **meeting notes** page"
- "**Append** action items to **today's meeting page**"
- "**Read** the content of my **project brief**"
