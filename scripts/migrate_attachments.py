#!/usr/bin/env python3
"""
migrate_attachments.py — Migrate attachments from CFP Foswiki to Pyroswiki.

Scans all topics in the CFP web for attachment references in the raw TML,
downloads each from the source, and uploads to pyroswiki via the API.

Usage:
    python3 scripts/migrate_attachments.py [--dry-run] [--topic TOPIC]
"""

from __future__ import annotations

import argparse
import re
import sys
import time
from typing import Optional

import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

SRC_BASE = "https://cfp-foswiki.performiq.com"
SRC_USER = "admin"
SRC_PASS = "floating"

DST_API  = "https://pyroswiki.performiq.com:8443/api/v1"
DST_USER = "windsurf"
DST_PASS = "Automation-2026"

WEB = "CFP"


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------

def get_src_session() -> requests.Session:
    s = requests.Session()
    s.verify = False
    s.get(f"{SRC_BASE}/bin/view/Main/WebHome")
    s.post(f"{SRC_BASE}/bin/login",
           data={"username": SRC_USER, "password": SRC_PASS,
                 "foswiki_redirect_cache": ""},
           allow_redirects=True)
    return s


def get_dst_token() -> str:
    resp = requests.post(
        f"{DST_API}/auth/token",
        data={"username": DST_USER, "password": DST_PASS},
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


# ---------------------------------------------------------------------------
# Discover attachments referenced in TML content
# ---------------------------------------------------------------------------

# Patterns that reference attachments in Foswiki TML:
#   %PUBURL%/CFP/WebHome/filename.pdf
#   %ATTACHURL%/filename.pdf  (relative to current topic)
#   [[%PUBURL%/CFP/SomeTopic/file.pdf][...]]
#   [[%ATTACHURL%/file.pdf][...]]

PUBURL_RE    = re.compile(r'%PUBURL%/CFP/([A-Za-z0-9_]+)/([^\s\]\[%"\']+)')
ATTACHURL_RE = re.compile(r'%ATTACHURL%/([^\s\]\[%"\']+)')


def find_attachments_in_tml(topic: str, content: str) -> list[tuple[str, str]]:
    """Return list of (topic, filename) pairs referenced in TML."""
    results = []
    seen = set()

    for m in PUBURL_RE.finditer(content):
        t, fname = m.group(1), m.group(2)
        key = (t, fname)
        if key not in seen:
            seen.add(key)
            results.append(key)

    for m in ATTACHURL_RE.finditer(content):
        fname = m.group(1)
        key = (topic, fname)
        if key not in seen:
            seen.add(key)
            results.append(key)

    return results


# ---------------------------------------------------------------------------
# Main migration
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--topic", default=None, help="Only process this topic")
    args = parser.parse_args()

    if args.dry_run:
        print("*** DRY RUN ***\n")

    src = get_src_session()
    print("[src] Logged in")

    token = get_dst_token()
    dst_headers = {"Authorization": f"Bearer {token}"}
    print("[dst] Got token\n")

    # Get list of topics from pyroswiki (already migrated)
    resp = requests.get(f"{DST_API}/webs/{WEB}/topics", headers=dst_headers)
    resp.raise_for_status()
    all_topics = [t["name"] for t in resp.json()]

    if args.topic:
        all_topics = [args.topic]

    print(f"Scanning {len(all_topics)} topics for attachment references...\n")

    # Collect all (topic, filename) pairs across all topics
    all_attachments: dict[tuple[str,str], list[str]] = {}  # (src_topic, fname) -> [referenced_in]

    for topic_name in all_topics:
        resp = requests.get(f"{DST_API}/webs/{WEB}/topics/{topic_name}", headers=dst_headers)
        if resp.status_code != 200:
            continue
        content = resp.json().get("content", "")
        refs = find_attachments_in_tml(topic_name, content)
        for (src_topic, fname) in refs:
            key = (src_topic, fname)
            if key not in all_attachments:
                all_attachments[key] = []
            all_attachments[key].append(topic_name)

    print(f"Found {len(all_attachments)} unique attachment references:\n")
    for (src_topic, fname), referenced_in in sorted(all_attachments.items()):
        print(f"  CFP/{src_topic}/{fname}  (referenced in: {', '.join(referenced_in)})")

    if args.dry_run:
        print("\n*** DRY RUN — stopping here ***")
        return

    print("\nDownloading and uploading attachments...\n")

    ok = fail = skip = 0

    for (src_topic, fname), referenced_in in sorted(all_attachments.items()):
        src_url = f"{SRC_BASE}/pub/{WEB}/{src_topic}/{fname}"
        print(f"  [{src_topic}/{fname}]")

        # Download from source
        dl = src.get(src_url)
        if dl.status_code != 200:
            print(f"    SKIP — source returned {dl.status_code}")
            skip += 1
            continue

        print(f"    Downloaded {len(dl.content):,} bytes")

        # Upload to each topic that references it (usually just one)
        # We upload to the src_topic so %PUBURL%/CFP/src_topic/fname resolves correctly
        dst_topic = src_topic

        # Ensure the topic exists on dst; if not, create a stub
        check = requests.get(f"{DST_API}/webs/{WEB}/topics/{dst_topic}", headers=dst_headers)
        if check.status_code == 404:
            print(f"    Creating stub topic {WEB}/{dst_topic}")
            requests.post(
                f"{DST_API}/webs/{WEB}/topics",
                json={"name": dst_topic, "content": f"Stub topic for attachments."},
                headers=dst_headers,
            )

        up = requests.post(
            f"{DST_API}/webs/{WEB}/topics/{dst_topic}/attachments",
            files={"file": (fname, dl.content)},
            headers=dst_headers,
        )
        if up.status_code in (200, 201):
            print(f"    Uploaded OK → {WEB}/{dst_topic}/{fname}")
            ok += 1
        else:
            print(f"    FAILED: {up.status_code} {up.text[:200]}")
            fail += 1

        time.sleep(0.2)

    print(f"\nDone: {ok} uploaded, {skip} skipped (not on source), {fail} failed")


if __name__ == "__main__":
    main()
