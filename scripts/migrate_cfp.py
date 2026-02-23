#!/usr/bin/env python3
"""
migrate_cfp.py — Migrate CFP web from cfp-foswiki.performiq.com to pyroswiki.

Usage:
    python3 scripts/migrate_cfp.py [--dry-run]

Source:  https://cfp-foswiki.performiq.com  (admin / floating)
Target:  https://pyroswiki.performiq.com    (admin user via API)
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

SRC_BASE   = "https://cfp-foswiki.performiq.com"
SRC_USER   = "admin"
SRC_PASS   = "floating"

DST_API    = "https://pyroswiki.performiq.com:8443/api/v1"
DST_WEB    = "https://pyroswiki.performiq.com"
DST_USER   = "windsurf"
DST_PASS   = "Automation-2026"    # set via --dst-password

# Webs to migrate from source
WEBS_TO_MIGRATE = ["CFP"]

# Topics to skip (boilerplate Foswiki system topics)
SKIP_TOPICS = {
    "WebAtom", "WebChanges", "WebCreateNewTopic", "WebHome",
    "WebIndex", "WebLeftBar", "WebLeftBarExample", "WebLinks",
    "WebNotify", "WebPreferences", "WebRss", "WebSearch",
    "WebSearchAdvanced", "WebStatistics", "WebTopicList",
}


# ---------------------------------------------------------------------------
# Source Foswiki client
# ---------------------------------------------------------------------------

class FoswikiSource:
    def __init__(self, base: str, username: str, password: str):
        self.base = base.rstrip("/")
        self.session = requests.Session()
        self.session.verify = False
        self._login(username, password)

    def _login(self, username: str, password: str):
        print(f"[src] Logging in as {username}...")
        # First GET to get initial cookie
        self.session.get(f"{self.base}/bin/view/Main/WebHome")
        # POST login
        resp = self.session.post(
            f"{self.base}/bin/login",
            data={"username": username, "password": password,
                  "foswiki_redirect_cache": ""},
            allow_redirects=True,
        )
        print(f"[src] Login response: {resp.status_code}")

    def list_topics(self, web: str) -> list[str]:
        """Return list of topic names in the given web."""
        resp = self.session.get(
            f"{self.base}/bin/view/{web}/WebTopicList",
            params={"skin": "text"},
        )
        # Parse topic names from HTML links like href="/CFP/TopicName"
        pattern = rf'href="/{re.escape(web)}/([A-Za-z0-9_]+)"'
        topics = re.findall(pattern, resp.text)
        # Deduplicate, preserve order
        seen = set()
        result = []
        for t in topics:
            if t not in seen:
                seen.add(t)
                result.append(t)
        return result

    def get_topic_raw(self, web: str, topic: str) -> Optional[str]:
        """Fetch raw TML text for a topic."""
        resp = self.session.get(
            f"{self.base}/bin/view/{web}/{topic}",
            params={"raw": "text"},
        )
        if resp.status_code == 200 and not resp.text.strip().startswith("<!DOCTYPE"):
            return resp.text
        return None

    def get_topic_meta(self, web: str, topic: str) -> dict:
        """Fetch topic metadata (title, parent) by scraping the view page."""
        resp = self.session.get(f"{self.base}/bin/view/{web}/{topic}")
        meta = {}
        # Try to extract title from <title> tag
        m = re.search(r"<title[^>]*>([^<|]+)", resp.text)
        if m:
            meta["title"] = m.group(1).strip()
        return meta

    def list_attachments(self, web: str, topic: str) -> list[dict]:
        """Return list of attachments for a topic."""
        resp = self.session.get(
            f"{self.base}/bin/view/{web}/{topic}",
            params={"raw": "debug"},
        )
        attachments = []
        # Parse META:FILEATTACHMENT lines
        for line in resp.text.splitlines():
            if line.startswith("%META:FILEATTACHMENT{"):
                name_m = re.search(r'name="([^"]+)"', line)
                if name_m:
                    attachments.append({"name": name_m.group(1)})
        return attachments

    def download_attachment(self, web: str, topic: str, filename: str) -> Optional[bytes]:
        """Download an attachment file."""
        resp = self.session.get(
            f"{self.base}/pub/{web}/{topic}/{filename}"
        )
        if resp.status_code == 200:
            return resp.content
        return None


# ---------------------------------------------------------------------------
# Target Pyroswiki client
# ---------------------------------------------------------------------------

class PyroswikiTarget:
    def __init__(self, api_base: str, username: str, password: str):
        self.api = api_base.rstrip("/")
        self.session = requests.Session()
        self.token = self._login(username, password)
        self.session.headers["Authorization"] = f"Bearer {self.token}"

    def _login(self, username: str, password: str) -> str:
        print(f"[dst] Logging in as {username}...")
        resp = self.session.post(
            f"{self.api}/auth/token",
            data={"username": username, "password": password},
        )
        resp.raise_for_status()
        token = resp.json()["access_token"]
        print(f"[dst] Got token: {token[:20]}...")
        return token

    def ensure_web(self, web: str, description: str = "") -> bool:
        """Create web if it doesn't exist. Returns True if created."""
        # Check if exists
        resp = self.session.get(f"{self.api}/webs/{web}")
        if resp.status_code == 200:
            print(f"[dst] Web '{web}' already exists.")
            return False
        # Create
        resp = self.session.post(
            f"{self.api}/webs",
            json={"name": web, "description": description or f"Migrated from Foswiki: {web}"},
        )
        if resp.status_code in (200, 201):
            print(f"[dst] Created web '{web}'.")
            return True
        print(f"[dst] WARNING: Failed to create web '{web}': {resp.status_code} {resp.text[:200]}")
        return False

    def topic_exists(self, web: str, topic: str) -> bool:
        resp = self.session.get(f"{self.api}/webs/{web}/topics/{topic}")
        return resp.status_code == 200

    def create_or_update_topic(self, web: str, topic: str, content: str, dry_run: bool = False) -> bool:
        if dry_run:
            print(f"  [dry-run] Would create/update {web}/{topic} ({len(content)} chars)")
            return True

        if self.topic_exists(web, topic):
            resp = self.session.put(
                f"{self.api}/webs/{web}/topics/{topic}",
                json={"content": content},
            )
        else:
            resp = self.session.post(
                f"{self.api}/webs/{web}/topics",
                json={"name": topic, "content": content},
            )

        if resp.status_code in (200, 201):
            return True
        print(f"  [dst] WARNING: {web}/{topic} → {resp.status_code}: {resp.text[:200]}")
        return False

    def upload_attachment(self, web: str, topic: str, filename: str,
                          data: bytes, dry_run: bool = False) -> bool:
        if dry_run:
            print(f"  [dry-run] Would upload attachment {filename} to {web}/{topic}")
            return True
        resp = self.session.post(
            f"{self.api}/webs/{web}/topics/{topic}/attachments",
            files={"file": (filename, data)},
        )
        if resp.status_code in (200, 201):
            return True
        print(f"  [dst] WARNING: attachment {filename} → {resp.status_code}: {resp.text[:200]}")
        return False


# ---------------------------------------------------------------------------
# Migration logic
# ---------------------------------------------------------------------------

def migrate_web(src: FoswikiSource, dst: PyroswikiTarget,
                web: str, dry_run: bool = False):
    print(f"\n{'='*60}")
    print(f"Migrating web: {web}")
    print(f"{'='*60}")

    if not dry_run:
        dst.ensure_web(web)

    topics = src.list_topics(web)
    print(f"[src] Found {len(topics)} topics in {web}: {topics[:10]}{'...' if len(topics)>10 else ''}")

    ok = 0
    skip = 0
    fail = 0

    for topic in topics:
        if topic in SKIP_TOPICS:
            skip += 1
            continue

        print(f"\n  → {web}/{topic}")

        # Fetch raw content
        content = src.get_topic_raw(web, topic)
        if content is None:
            print(f"    [skip] Could not fetch raw content")
            skip += 1
            continue

        # Create/update topic
        if dst.create_or_update_topic(web, topic, content, dry_run=dry_run):
            print(f"    [ok] {len(content)} chars")
            ok += 1
        else:
            fail += 1

        # Fetch and upload attachments
        attachments = src.list_attachments(web, topic)
        for att in attachments:
            fname = att["name"]
            print(f"    [att] {fname}")
            att_data = src.download_attachment(web, topic, fname)
            if att_data:
                dst.upload_attachment(web, topic, fname, att_data, dry_run=dry_run)
            else:
                print(f"    [att] WARNING: could not download {fname}")

        time.sleep(0.1)  # be polite

    print(f"\n[{web}] Done: {ok} ok, {skip} skipped, {fail} failed")
    return ok, skip, fail


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Migrate CFP Foswiki → Pyroswiki")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would be migrated without writing anything")
    parser.add_argument("--web", default=None,
                        help="Migrate only this web (default: all configured webs)")
    parser.add_argument("--dst-password", default=DST_PASS,
                        help="Admin password for pyroswiki")
    parser.add_argument("--topic", default=None,
                        help="Migrate only this topic (requires --web)")
    args = parser.parse_args()

    if args.dry_run:
        print("*** DRY RUN — no changes will be written ***\n")

    src = FoswikiSource(SRC_BASE, SRC_USER, SRC_PASS)
    dst = PyroswikiTarget(DST_API, DST_USER, args.dst_password)

    webs = [args.web] if args.web else WEBS_TO_MIGRATE

    total_ok = total_skip = total_fail = 0
    for web in webs:
        if args.topic:
            # Single topic mode
            if not args.dry_run:
                dst.ensure_web(web)
            content = src.get_topic_raw(web, args.topic)
            if content:
                dst.create_or_update_topic(web, args.topic, content, dry_run=args.dry_run)
                print(f"[ok] {web}/{args.topic}")
            else:
                print(f"[fail] Could not fetch {web}/{args.topic}")
        else:
            ok, skip, fail = migrate_web(src, dst, web, dry_run=args.dry_run)
            total_ok += ok
            total_skip += skip
            total_fail += fail

    if not args.topic:
        print(f"\n{'='*60}")
        print(f"TOTAL: {total_ok} ok, {total_skip} skipped, {total_fail} failed")


if __name__ == "__main__":
    main()
