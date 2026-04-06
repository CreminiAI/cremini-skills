---
name: notion-databases
description: Query, list, and create entries in Notion databases. Use when the user wants to query tasks, projects, or any structured data in Notion. Also use for listing all databases in the workspace.
---

# Notion Databases

Query structured data, list databases, and add entries.

## Prerequisites

Run `notion-connect --check` first. If not configured, load `notion-connect/SKILL.md`.

## Commands

### List all databases
```bash
python3 databases/scripts/notion_databases.py list
```

### Query a database
```bash
# All entries
python3 databases/scripts/notion_databases.py query <database-id>

# With filter
python3 databases/scripts/notion_databases.py query <database-id> --filter '{"property": "Status", "select": {"equals": "In Progress"}}'

# With sort
python3 databases/scripts/notion_databases.py query <database-id> --sort '{"property": "Created", "direction": "descending"}'

# Limit results
python3 databases/scripts/notion_databases.py query <database-id> --limit 5
```

### Create a database entry
```bash
python3 databases/scripts/notion_databases.py create <database-id> --props '{"Name": "New Task", "Status": "To Do", "Priority": "High"}'
```

### Get database schema (see what properties exist)
```bash
python3 databases/scripts/notion_databases.py schema <database-id>
```

## Common Filters

```json
// Select property
{"property": "Status", "select": {"equals": "Done"}}

// Checkbox
{"property": "Completed", "checkbox": {"equals": true}}

// Date (after)
{"property": "Due Date", "date": {"after": "2026-04-01"}}

// Text contains
{"property": "Name", "rich_text": {"contains": "meeting"}}
```

## Follow-Up Questions

- "**List** all my Notion **databases**"
- "**Query** my tasks database for items **due this week**"
- "**Add** a new entry to my **projects** database"
- "**Show** the schema of my **CRM** database"
