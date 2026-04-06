#!/usr/bin/env python3
"""
Fetch web page content via Chrome DevTools Protocol (CDP).

Launches an isolated headless Chrome instance with --remote-debugging-port,
controls it over CDP WebSocket, and extracts page content.
Zero external dependencies — Python 3 stdlib only.
Cross-platform: Mac, Windows, Linux.
"""

import argparse
import hashlib
import json
import os
import platform
import re
import shutil
import socket
import struct
import subprocess
import sys
import tempfile
import time
import urllib.parse
import urllib.request

try:
    import trafilatura
    USE_TRAFILATURA = True
except ImportError:
    USE_TRAFILATURA = False


def _log(msg):
    """Print progress to stderr so stdout stays clean for output."""
    print(f"[web-fetch] {msg}", file=sys.stderr, flush=True)


# ---------------------------------------------------------------------------
# Chrome discovery
# ---------------------------------------------------------------------------

CHROME_CANDIDATES = {
    "Darwin": [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
    ],
    "Linux": [
        "/usr/bin/google-chrome",
        "/usr/bin/google-chrome-stable",
        "/usr/bin/chromium",
        "/usr/bin/chromium-browser",
        "/snap/bin/chromium",
    ],
    "Windows": [
        os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%LocalAppData%\Google\Chrome\Application\chrome.exe"),
    ],
}


def find_chrome():
    """Find Chrome/Chromium binary across Mac, Windows, Linux."""
    system = platform.system()
    for path in CHROME_CANDIDATES.get(system, []):
        if os.path.isfile(path):
            return path
    for name in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome"):
        found = shutil.which(name)
        if found:
            return found
    return None


def _find_free_port():
    """Find a free TCP port on localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


# ---------------------------------------------------------------------------
# Minimal WebSocket client (RFC 6455) — stdlib only
# ---------------------------------------------------------------------------

class CDPWebSocket:
    """Minimal WebSocket client for Chrome DevTools Protocol."""

    def __init__(self, ws_url, timeout=10):
        parsed = urllib.parse.urlparse(ws_url)
        self.host = parsed.hostname
        self.port = parsed.port or 80
        self.path = parsed.path
        self._sock = socket.create_connection((self.host, self.port), timeout=timeout)
        self._handshake()
        self._msg_id = 0

    def _handshake(self):
        key = hashlib.sha1(os.urandom(16)).hexdigest()[:24]
        req = (
            f"GET {self.path} HTTP/1.1\r\n"
            f"Host: {self.host}:{self.port}\r\n"
            f"Upgrade: websocket\r\n"
            f"Connection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {key}\r\n"
            f"Sec-WebSocket-Version: 13\r\n"
            f"\r\n"
        )
        self._sock.sendall(req.encode())
        resp = b""
        while b"\r\n\r\n" not in resp:
            chunk = self._sock.recv(4096)
            if not chunk:
                raise ConnectionError("WebSocket handshake failed: connection closed")
            resp += chunk
        if b"101" not in resp.split(b"\r\n")[0]:
            raise ConnectionError(f"WebSocket handshake failed: {resp[:200]}")

    def send(self, data):
        """Send a text frame."""
        payload = data.encode("utf-8")
        frame = bytearray()
        frame.append(0x81)  # FIN + text opcode
        mask_bit = 0x80
        length = len(payload)
        if length < 126:
            frame.append(mask_bit | length)
        elif length < 65536:
            frame.append(mask_bit | 126)
            frame.extend(struct.pack(">H", length))
        else:
            frame.append(mask_bit | 127)
            frame.extend(struct.pack(">Q", length))
        mask_key = os.urandom(4)
        frame.extend(mask_key)
        masked = bytearray(b ^ mask_key[i % 4] for i, b in enumerate(payload))
        frame.extend(masked)
        self._sock.sendall(frame)

    def recv(self):
        """Receive a complete text frame. Returns string."""
        header = self._recv_exact(2)
        opcode = header[0] & 0x0F
        masked = (header[1] & 0x80) != 0
        length = header[1] & 0x7F
        if length == 126:
            length = struct.unpack(">H", self._recv_exact(2))[0]
        elif length == 127:
            length = struct.unpack(">Q", self._recv_exact(8))[0]
        if masked:
            mask_key = self._recv_exact(4)
        data = self._recv_exact(length)
        if masked:
            data = bytearray(b ^ mask_key[i % 4] for i, b in enumerate(data))
        if opcode == 0x08:  # close
            raise ConnectionError("WebSocket closed by server")
        if opcode == 0x09:  # ping
            self._send_pong(data)
            return self.recv()
        return data.decode("utf-8", errors="replace")

    def _send_pong(self, data):
        """Send a masked pong frame (RFC 6455 requires client masking)."""
        frame = bytearray()
        frame.append(0x8A)  # FIN + pong opcode
        mask_bit = 0x80
        frame.append(mask_bit | len(data))
        mask_key = os.urandom(4)
        frame.extend(mask_key)
        masked = bytearray(b ^ mask_key[i % 4] for i, b in enumerate(data))
        frame.extend(masked)
        self._sock.sendall(frame)

    def _recv_exact(self, n):
        buf = bytearray()
        while len(buf) < n:
            chunk = self._sock.recv(n - len(buf))
            if not chunk:
                raise ConnectionError("WebSocket connection closed")
            buf.extend(chunk)
        return bytes(buf)

    def send_command(self, method, params=None, timeout=15):
        """Send a CDP command and return the result."""
        self._msg_id += 1
        msg = {"id": self._msg_id, "method": method}
        if params:
            msg["params"] = params
        self.send(json.dumps(msg))
        deadline = time.time() + timeout
        while time.time() < deadline:
            remaining = deadline - time.time()
            if remaining <= 0:
                break
            self._sock.settimeout(min(2.0, remaining))
            try:
                resp = json.loads(self.recv())
            except socket.timeout:
                continue
            if resp.get("id") == self._msg_id:
                if "error" in resp:
                    raise RuntimeError(f"CDP error: {resp['error']}")
                return resp.get("result", {})
        raise TimeoutError(f"CDP command '{method}' timed out after {timeout}s")

    def close(self):
        try:
            self._sock.close()
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Chrome CDP session manager
# ---------------------------------------------------------------------------

class ChromeCDP:
    """Manages a headless Chrome instance controlled via CDP."""

    def __init__(self, chrome_path, port=None):
        self.chrome_path = chrome_path
        self.port = port or _find_free_port()
        self.tmp_dir = tempfile.mkdtemp(prefix="web_fetch_chrome_")
        self.process = None

    def start(self):
        """Launch headless Chrome with remote debugging."""
        cmd = [
            self.chrome_path,
            "--headless=new",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-background-networking",
            "--disable-sync",
            "--disable-translate",
            "--disable-extensions",
            "--disable-popup-blocking",
            "--metrics-recording-only",
            "--no-sandbox",
            "--disable-gpu",
            f"--remote-debugging-port={self.port}",
            f"--user-data-dir={self.tmp_dir}",
            "about:blank",
        ]
        if platform.system() == "Linux":
            cmd.insert(-1, "--disable-dev-shm-usage")

        self.process = subprocess.Popen(
            cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )

        # Wait for CDP to be ready
        for _ in range(50):  # up to 5 seconds
            try:
                resp = urllib.request.urlopen(
                    f"http://127.0.0.1:{self.port}/json/version", timeout=2
                )
                resp.read()
                return
            except Exception:
                time.sleep(0.1)
        raise RuntimeError("Chrome failed to start with CDP")

    def get_ws_url(self):
        """Get the WebSocket debugger URL for the first page tab."""
        resp = urllib.request.urlopen(
            f"http://127.0.0.1:{self.port}/json", timeout=5
        )
        tabs = json.loads(resp.read())
        for tab in tabs:
            if tab.get("type") == "page":
                return tab["webSocketDebuggerUrl"]
        raise RuntimeError("No page target found")

    def stop(self):
        """Terminate Chrome and clean up."""
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except Exception:
                try:
                    self.process.kill()
                except Exception:
                    pass
        try:
            shutil.rmtree(self.tmp_dir, ignore_errors=True)
        except Exception:
            pass

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *args):
        self.stop()


# ---------------------------------------------------------------------------
# Page fetcher — single URL
# ---------------------------------------------------------------------------

def fetch_page(cdp, url, wait_ms=3000, timeout_s=30):
    """Navigate to URL via CDP, wait for JS, return result dict.

    Returns dict with: url, success, content/error, final_url.
    """
    ws = None
    try:
        ws_url = cdp.get_ws_url()
        ws = CDPWebSocket(ws_url, timeout=timeout_s)

        ws.send_command("Page.enable")
        # Note: Network.enable intentionally NOT called — it floods the
        # WebSocket with thousands of events that slow down recv loops.

        nav_result = ws.send_command("Page.navigate", {"url": url})
        if nav_result.get("errorText"):
            return {"url": url, "success": False, "error": nav_result["errorText"]}

        # Wait for load event with hard deadline
        deadline = time.time() + timeout_s
        loaded = False
        while time.time() < deadline:
            remaining = deadline - time.time()
            if remaining <= 0:
                break
            ws._sock.settimeout(min(2.0, remaining))
            try:
                msg = json.loads(ws.recv())
                if msg.get("method") == "Page.loadEventFired":
                    loaded = True
                    break
            except socket.timeout:
                continue
            except ConnectionError:
                break

        if not loaded:
            return {"url": url, "success": False, "error": "Page load timeout"}

        # Wait for JS rendering
        time.sleep(min(wait_ms / 1000.0, max(0, deadline - time.time())))

        # Get final URL
        loc = ws.send_command(
            "Runtime.evaluate",
            {"expression": "document.location.href", "returnByValue": True},
        )
        final_url = loc.get("result", {}).get("value", url)

        # Get HTML
        doc = ws.send_command("DOM.getDocument", {"depth": 0})
        root_id = doc["root"]["nodeId"]
        html_result = ws.send_command("DOM.getOuterHTML", {"nodeId": root_id})
        html = html_result.get("outerHTML", "")

        if not html.strip():
            return {"url": url, "success": False, "error": "Empty page content"}

        text = extract_text(html)
        if not text.strip():
            return {"url": url, "success": False, "error": "No text extracted"}

        return {"url": url, "final_url": final_url, "success": True, "content": text}

    except Exception as e:
        return {"url": url, "success": False, "error": str(e)}
    finally:
        if ws:
            ws.close()
        # Reset tab for reuse
        try:
            ws2 = CDPWebSocket(cdp.get_ws_url(), timeout=5)
            ws2.send_command("Page.navigate", {"url": "about:blank"})
            ws2.close()
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Text extraction
# ---------------------------------------------------------------------------

def extract_text(html):
    """Extract main text content from HTML."""
    if USE_TRAFILATURA:
        text = trafilatura.extract(html)
        if text:
            return text

    text = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL)
    text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL)
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n", "\n\n", text)
    return text.strip()[:15000]


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Fetch web page content via Chrome DevTools Protocol (CDP)",
        epilog="URLs can be passed via --url flags or piped via stdin (one per line).",
    )
    parser.add_argument("--url", action="append", default=[], help="URL to fetch (repeatable)")
    parser.add_argument("--wait-ms", type=int, default=1500, help="JS render wait in ms (default: 1500)")
    parser.add_argument("--timeout", type=int, default=15, help="Per-URL timeout in seconds (default: 15)")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format (default: text)")
    parser.add_argument("--max-chars", type=int, default=15000, help="Max chars per page (default: 15000)")
    parser.add_argument("--output", "-o", help="Write output to file instead of stdout")
    parser.add_argument("--batch-size", type=int, default=3, help="URLs per batch (default: 3)")
    parser.add_argument("--port", type=int, default=0, help="CDP port (default: auto)")
    args = parser.parse_args()

    # Collect URLs
    urls = list(args.url)
    if not sys.stdin.isatty():
        stdin_text = sys.stdin.read().strip()
        if stdin_text:
            urls.extend(line.strip() for line in stdin_text.split("\n") if line.strip())

    if not urls:
        print("ERROR: No URLs provided. Use --url or pipe via stdin.", file=sys.stderr)
        sys.exit(1)

    chrome_path = find_chrome()
    if not chrome_path:
        print("ERROR: Chrome/Chromium not found.", file=sys.stderr)
        print("Install Google Chrome or Chromium:", file=sys.stderr)
        print("  macOS:   brew install --cask google-chrome", file=sys.stderr)
        print("  Ubuntu:  sudo apt install google-chrome-stable", file=sys.stderr)
        print("  Windows: winget install Google.Chrome", file=sys.stderr)
        sys.exit(1)

    port = args.port if args.port > 0 else None
    total = len(urls)
    _log(f"Fetching {total} URL(s) in batches of {args.batch_size}")

    # Open output file for streaming writes
    out_file = None
    if args.output:
        out_file = open(args.output, "w", encoding="utf-8")

    results = []
    # Process in batches — restart Chrome between batches for stability
    for batch_start in range(0, total, args.batch_size):
        batch = urls[batch_start:batch_start + args.batch_size]
        batch_num = batch_start // args.batch_size + 1
        _log(f"Batch {batch_num}: {len(batch)} URL(s)")

        try:
            with ChromeCDP(chrome_path, port=port) as cdp:
                for i, url in enumerate(batch):
                    idx = batch_start + i + 1
                    _log(f"  [{idx}/{total}] {url[:80]}...")
                    result = fetch_page(cdp, url, wait_ms=args.wait_ms, timeout_s=args.timeout)
                    if result.get("content"):
                        result["content"] = result["content"][:args.max_chars]

                    status = "OK" if result["success"] else f"FAIL: {result.get('error', '?')}"
                    content_len = len(result.get("content", ""))
                    _log(f"  [{idx}/{total}] {status} ({content_len} chars)")
                    results.append(result)
        except Exception as e:
            # If Chrome crashes mid-batch, mark remaining URLs as failed
            _log(f"  Chrome error: {e}")
            for j in range(len(results) - batch_start, len(batch)):
                failed_url = batch[j]
                results.append({"url": failed_url, "success": False, "error": f"Chrome crashed: {e}"})

    _log(f"Done: {sum(1 for r in results if r['success'])}/{total} succeeded")

    # Write output
    if args.format == "json":
        output_text = json.dumps(results, indent=2, ensure_ascii=False)
    else:
        parts = []
        for r in results:
            if r["success"]:
                parts.append(r["content"])
            else:
                parts.append(f"ERROR ({r['url']}): {r['error']}")
        output_text = "\n---\n".join(parts)

    if out_file:
        out_file.write(output_text)
        out_file.close()
        _log(f"Output written to {args.output}")
    else:
        print(output_text)


if __name__ == "__main__":
    main()
