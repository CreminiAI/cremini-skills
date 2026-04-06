---
name: web-fetch
description: Fetch web page content via Chrome DevTools Protocol (CDP). Full JS rendering, handles redirects (including Google News). Use when you need to read the text content of a web page, scrape articles, or extract information from URLs. Zero dependencies — Python 3 stdlib only. Cross-platform (Mac, Windows, Linux).
---

# Web Fetch

Controls a headless Chrome instance via **Chrome DevTools Protocol (CDP)** to fetch web pages with full JavaScript rendering. Handles JS redirects, SPAs, and dynamic content. Extracts clean text from any URL.

## Prerequisites

- **Google Chrome or Chromium**: Must be installed on the system.
  - macOS: `brew install --cask google-chrome`
  - Ubuntu/Debian: `sudo apt install google-chrome-stable`
  - Windows: `winget install Google.Chrome`
- **Python 3**: Standard library only. Zero pip dependencies. Optionally `trafilatura` for better content extraction.
- No API keys or tokens required.

## Usage

### Single URL

```bash
python <skill-path>/scripts/web_fetch.py --url "https://example.com/article"
```

### Multiple URLs (single Chrome session, efficient)

```bash
python <skill-path>/scripts/web_fetch.py --url "https://example.com/a" --url "https://example.com/b"
```

### Piped input (one URL per line)

```bash
echo "https://example.com/article" | python <skill-path>/scripts/web_fetch.py
```

### JSON output to file (recommended for multiple URLs)

```bash
# Cross-platform temp dir
TMPDIR=$(python -c "import tempfile; print(tempfile.gettempdir())")
python <skill-path>/scripts/web_fetch.py --url "https://example.com" --format json -o "$TMPDIR/results.json"
```

## Options

| Flag | Default | Description |
|---|---|---|
| `--url` | — | URL to fetch (repeatable) |
| `--format` | `text` | Output format: `text` or `json` |
| `-o, --output` | stdout | Write to file instead of stdout (recommended for large results) |
| `--wait-ms` | `1500` | Wait time for JS rendering in milliseconds |
| `--timeout` | `15` | Per-URL timeout in seconds |
| `--max-chars` | `15000` | Max characters per page |
| `--batch-size` | `3` | URLs per batch (Chrome restarts between batches for stability) |
| `--port` | auto | CDP debugging port (default: auto-detect free port) |

## Output

### Text mode (default)

Plain text content of each URL, separated by `---`.

### JSON mode

```json
[
  {
    "url": "https://news.google.com/rss/articles/...",
    "final_url": "https://www.theguardian.com/actual-article",
    "success": true,
    "content": "Article text content..."
  }
]
```

On failure:

```json
[
  {
    "url": "https://example.com/broken",
    "success": false,
    "error": "Page load timeout"
  }
]
```

## How It Works

1. **Finds Chrome** — Checks platform-specific paths, then searches PATH
2. **Launches isolated Chrome** — `--headless=new --remote-debugging-port=PORT --user-data-dir=TMPDIR` (never conflicts with your running Chrome)
3. **Controls via CDP** — Connects over WebSocket using a pure-Python CDP client (no dependencies)
4. **Navigates & waits** — Uses `Page.navigate`, listens for `loadEventFired`, then waits for JS rendering
5. **Captures content** — Gets final URL via `Runtime.evaluate`, extracts DOM via `DOM.getOuterHTML`
6. **Extracts text** — Uses `trafilatura` (if installed) or falls back to HTML tag stripping
7. **Cleans up** — Terminates Chrome and removes temp profile

## Key Advantages

- **No profile conflicts** — Uses isolated `--user-data-dir`, works alongside your running Chrome
- **Handles JS redirects** — Google News, URL shorteners, SPA routing all work
- **Zero dependencies** — Pure Python 3 stdlib (WebSocket client included)
- **Single Chrome session** — Multiple URLs reuse one instance (fast)
- **Cross-platform** — Mac, Windows, Linux

## Cross-Platform Support

| Platform | Chrome Paths Checked |
|---|---|
| macOS | `/Applications/Google Chrome.app/...`, Chromium.app |
| Linux | `/usr/bin/google-chrome`, chromium, snap chromium |
| Windows | `%ProgramFiles%\Google\Chrome\...`, `%LocalAppData%\...` |

Falls back to searching `PATH` on all platforms.

## Notes

- **No configuration needed** — Just have Chrome installed. No need to enable "remote debugging" or change any Chrome settings. The script handles everything automatically.
- **macOS first run** — The system may show a popup asking "Do you want the application Google Chrome to accept incoming network connections?" Click **Allow**. This is because CDP uses a local port (`127.0.0.1`) — no external network traffic is involved.
