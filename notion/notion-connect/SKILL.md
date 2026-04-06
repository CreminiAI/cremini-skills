---
name: notion-connect
description: Set up Notion integration token. Use when Notion commands fail with auth errors, or when user wants to connect their Notion workspace. Takes 2 minutes — user creates an integration at notion.so/my-integrations and pastes the token.
---

# Notion Connect

Connect your Notion workspace. One token, two minutes.

## How to Set Up

1. User goes to [notion.so/my-integrations](https://www.notion.so/my-integrations)
2. Clicks **+ New integration**
3. Names it anything (e.g. "AI Assistant")
4. Selects the workspace
5. Clicks **Submit** → copies the **Internal Integration Secret** (starts with `ntn_`)
6. Pastes it in the chat

**Important:** After creating the integration, the user must also share specific pages/databases with it:
- Open a Notion page → click `...` menu → **Connections** → select the integration
- This grants the integration access to that page and its children

## AI Agent Flow

### Check if configured:
```bash
python3 notion-connect/scripts/notion_connect.py --check
```

Returns JSON: `{"configured": true, "workspace": "..."}` or `{"configured": false}`.

### Save token (after user pastes it):
```bash
python3 notion-connect/scripts/notion_connect.py --set-token "ntn_xxxxxxxxxxxxx"
```

Saves to `~/.config/notion/config.json` and verifies the token works by calling the Notion API.

### When Notion is not configured, tell the user EXACTLY this:

"To connect Notion, I just need your Integration Token. It takes about 2 minutes:

1. Open this page: https://www.notion.so/my-integrations
2. Create a new integration (name it anything, like 'AI Assistant')
3. After creating, go to **Content access** tab → **Edit access** → select the pages you want me to access
4. Copy the **Internal Integration Secret** (starts with `ntn_`)
5. Paste it here

For a detailed guide with screenshots: https://skillpack.gitbook.io/skillpack-docs/integrations/notion"

## CRITICAL RULES

1. **NEVER ask the user for OAuth credentials** — Notion internal integrations only need one token
2. **Always mention Content access** — users must grant page access after creating the integration, otherwise it can't see anything
3. **Token starts with `ntn_`** — if the user pastes something else, it's wrong
4. **Always show the Gitbook link** when guiding setup

## Credential Storage

| File | Path |
|------|------|
| Config | `~/.config/notion/config.json` |
| Format | `{"token": "ntn_...", "workspace_name": "...", "workspace_id": "..."}` |
| Permissions | `0600` (user-only read) |

## Follow-Up Questions

- "**Search** my Notion workspace for **recent pages**"
- "**List** my Notion **databases**"
- "**Create** a new **page** with meeting notes"
