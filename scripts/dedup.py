#!/usr/bin/env python3
"""
Deduplicate posts:
1. Find files with the same source URL (English slug + Chinese title)
2. Keep the Chinese version, delete the English slug version
3. For English-only files, fetch Chinese title from API and rename
4. Clean frontmatter (remove dg-publish, title)
"""

import os
import re
import time
from pathlib import Path

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = "https://www.yinwang.org"
API_BASE = f"{BASE_URL}/api/v1"
POSTS_DIR = Path(__file__).resolve().parent.parent / "posts"

session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0 (compatible; yinwangdl-dedup/1.0)"})
session.verify = False


def is_chinese(name):
    return bool(re.search(r"[一-鿿]", name))


def parse_frontmatter(text):
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    fm_text = text[4:end]
    body = text[end + 4 :]
    if body.startswith("\n"):
        body = body[1:]
    meta = {}
    for line in fm_text.split("\n"):
        line = line.strip()
        if ":" in line and not line.startswith("#"):
            key, _, val = line.partition(":")
            meta[key.strip()] = val.strip()
    return meta, body


def build_frontmatter(meta):
    lines = ["---"]
    if meta.get("author"):
        lines.append(f"author: {meta['author']}")
    if meta.get("created"):
        lines.append(f"created: {meta['created']}")
    if meta.get("source"):
        lines.append(f"source: {meta['source']}")
    lines.append("---")
    return "\n".join(lines)


def clean_frontmatter(text):
    meta, body = parse_frontmatter(text)
    new_fm = build_frontmatter(meta)
    return new_fm + "\n" + body


def fetch_all_titles():
    print("Fetching titles from API...")
    titles = {}
    skip = 0
    limit = 20
    while True:
        try:
            resp = session.get(f"{API_BASE}/posts", params={"skip": skip, "limit": limit})
            resp.raise_for_status()
            data = resp.json()
            posts = data.get("posts", [])
            total = data.get("total", 0)
            for p in posts:
                titles[p["slug"]] = p.get("title", "")
            print(f"  Fetched {len(posts)} posts (skip={skip}, total={total})")
            skip += limit
            if skip >= total or not posts:
                break
            time.sleep(0.5)
        except Exception as e:
            print(f"  API error: {e}")
            break
    print(f"  Got {len(titles)} titles")
    return titles


def sanitize_filename(name):
    for ch in ['\\', '/', ':', '*', '?', '<', '>']:
        name = name.replace(ch, '')
    name = name.replace('"', '')
    name = name.strip()
    if not name:
        name = "untitled"
    return name


def extract_slug(url):
    """Extract slug from both new (/posts/{slug}) and old (/blog-cn/.../{slug}) URLs."""
    m = re.search(r"/posts/([^/?]+)", url)
    if m:
        return m.group(1)
    m = re.search(r"/blog-cn/\d{4}/\d{2}/\d{2}/([^/?]+)", url)
    if m:
        return m.group(1).rstrip("/")
    return None


def main():
    dry_run = "--dry-run" in os.sys.argv

    if dry_run:
        print("DRY RUN - no changes will be made\n")

    files = sorted(POSTS_DIR.glob("*.md"))
    print(f"Total .md files: {len(files)}")

    # Group by source URL
    by_source = {}
    for f in files:
        text = f.read_text(encoding="utf-8")
        meta, _ = parse_frontmatter(text)
        source = meta.get("source", "")
        if source:
            by_source.setdefault(source, []).append(f)

    # --- Phase 1: Remove duplicates (keep Chinese, delete English slug) ---
    print("\n=== Phase 1: Remove same-URL duplicates ===")
    deleted = 0
    cleaned = 0

    for source, group in sorted(by_source.items()):
        if len(group) < 2:
            continue

        zh_files = [f for f in group if is_chinese(f.name)]
        en_files = [f for f in group if not is_chinese(f.name)]

        # Determine which file to keep
        if zh_files:
            keep = zh_files[0]
        else:
            titled = [f for f in group if " " in f.stem or any(c.isupper() for c in f.stem[:5])]
            keep = titled[0] if titled else group[0]

        to_delete = [f for f in group if f != keep]

        text = keep.read_text(encoding="utf-8")
        if "dg-publish" in text or ("title:" in text):
            new_text = clean_frontmatter(text)
            if new_text != text:
                if not dry_run:
                    keep.write_text(new_text, encoding="utf-8")
                print(f"  Cleaned FM: {keep.name}")
                cleaned += 1

        for f in to_delete:
            print(f"  Delete: {f.name} (keep: {keep.name})")
            if not dry_run:
                f.unlink()
            deleted += 1

    print(f"  Deleted: {deleted}, Cleaned FM: {cleaned}")

    # --- Phase 1.5: Remove cross-URL duplicates (same slug, different URL format) ---
    print("\n=== Phase 1.5: Remove cross-URL duplicates ===")
    files = sorted(POSTS_DIR.glob("*.md"))
    by_slug = {}
    for f in files:
        text = f.read_text(encoding="utf-8")
        meta, _ = parse_frontmatter(text)
        source = meta.get("source", "")
        slug = extract_slug(source) if source else None
        if slug:
            by_slug.setdefault(slug, []).append(f)

    cross_deleted = 0
    for slug, group in sorted(by_slug.items()):
        if len(group) < 2:
            continue
        zh_files = [f for f in group if is_chinese(f.name)]
        en_files = [f for f in group if not is_chinese(f.name)]
        if zh_files and en_files:
            for f in en_files:
                zh_name = zh_files[0].name
                print(f"  Delete cross-URL: {f.name} (keep: {zh_name})")
                if not dry_run:
                    f.unlink()
                cross_deleted += 1
    print(f"  Cross-URL deleted: {cross_deleted}")

    # --- Phase 2: Rename English-only files to Chinese titles ---
    print("\n=== Phase 2: Rename English-only files ===")
    files = sorted(POSTS_DIR.glob("*.md"))
    en_only = [f for f in files if not is_chinese(f.name)]
    print(f"  English-only files remaining: {len(en_only)}")

    if en_only:
        api_titles = fetch_all_titles()
        renamed = 0
        for f in en_only:
            slug = f.stem
            title = api_titles.get(slug, "")
            if not title:
                text = f.read_text(encoding="utf-8")
                meta, _ = parse_frontmatter(text)
                title = meta.get("title", "").strip('"').strip("'")
            if title:
                new_name = sanitize_filename(title) + ".md"
                new_path = POSTS_DIR / new_name
                if new_path.exists() and new_path != f:
                    # Target exists (e.g., cross-URL Chinese version already present)
                    print(f"  Delete (Chinese exists): {f.name} -> {new_name}")
                    if not dry_run:
                        f.unlink()
                    continue
                print(f"  Rename: {f.name} -> {new_name}")
                if not dry_run:
                    text = f.read_text(encoding="utf-8")
                    new_text = clean_frontmatter(text)
                    f.write_text(new_text, encoding="utf-8")
                    f.rename(new_path)
                renamed += 1
            else:
                print(f"  No title found for: {f.name}")
        print(f"  Renamed: {renamed}")

    # --- Phase 3: Clean frontmatter of all remaining files ---
    print("\n=== Phase 3: Final frontmatter cleanup ===")
    files = sorted(POSTS_DIR.glob("*.md"))
    final_cleaned = 0
    for f in files:
        text = f.read_text(encoding="utf-8")
        if "dg-publish" in text or ("title:" in text):
            new_text = clean_frontmatter(text)
            if new_text != text:
                if not dry_run:
                    f.write_text(new_text, encoding="utf-8")
                print(f"  Cleaned: {f.name}")
                final_cleaned += 1
    print(f"  Final cleaned: {final_cleaned}")

    # --- Summary ---
    files = sorted(POSTS_DIR.glob("*.md"))
    en_remaining = sum(1 for f in files if not is_chinese(f.name))
    print(f"\n=== Summary ===")
    print(f"Files remaining: {len(files)} (English: {en_remaining}, Chinese: {len(files) - en_remaining})")
    if dry_run:
        print("This was a DRY RUN. Run without --dry-run to apply changes.")


if __name__ == "__main__":
    main()
