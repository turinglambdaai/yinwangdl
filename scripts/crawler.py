#!/usr/bin/env python3
"""
Yin Wang Blog Crawler
Downloads blog posts from yinwang.org API and saves as formatted Markdown.
"""

import json
import os
import re
import sys
import time
import urllib.parse
from pathlib import Path

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = "https://www.yinwang.org"
API_BASE = f"{BASE_URL}/api/v1"
POSTS_DIR = Path(__file__).resolve().parent.parent / "posts"
IMAGES_DIR = Path(__file__).resolve().parent.parent / "images"
INDEX_FILE = Path(__file__).resolve().parent.parent / "index.json"
DELAY = 1  # seconds between requests

session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0 (compatible; yinwangdl-crawler/2.0)"})
session.verify = False


def fetch_all_slugs() -> list[dict]:
    """Fetch all post slugs from the API with pagination."""
    all_posts = []
    skip = 0
    limit = 20

    while True:
        resp = session.get(f"{API_BASE}/posts", params={"skip": skip, "limit": limit})
        resp.raise_for_status()
        data = resp.json()
        posts = data.get("posts", [])
        total = data.get("total", 0)
        all_posts.extend(posts)
        print(f"  Fetched {len(posts)} posts (skip={skip}, total={total})")
        skip += limit
        if skip >= total or not posts:
            break
        time.sleep(DELAY)

    # Deduplicate by slug
    seen = set()
    unique = []
    for p in all_posts:
        if p["slug"] not in seen:
            seen.add(p["slug"])
            unique.append(p)

    print(f"  Total unique posts: {len(unique)}")
    return unique


def fetch_post(slug: str) -> dict | None:
    """Fetch a single post by slug."""
    try:
        resp = session.get(f"{API_BASE}/posts/{slug}")
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        print(f"  ERROR fetching post '{slug}': {e}")
        return None


def download_image(url: str, dest_dir: Path) -> str | None:
    """Download an image and return the local filename, or None on failure."""
    if not url:
        return None

    # Resolve relative URLs
    if url.startswith("/"):
        url = BASE_URL + url

    # Extract filename from URL
    parsed = urllib.parse.urlparse(url)
    filename = os.path.basename(parsed.path)
    if not filename:
        return None

    dest_path = dest_dir / filename
    if dest_path.exists():
        return filename

    try:
        resp = session.get(url, timeout=30)
        resp.raise_for_status()
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_path.write_bytes(resp.content)
        print(f"    Downloaded image: {filename}")
        return filename
    except requests.RequestException as e:
        print(f"    WARNING: Failed to download image {url}: {e}")
        return None


def extract_images(content: str) -> list[str]:
    """Extract image URLs from both HTML <img> and Markdown ![]() syntax."""
    urls = []
    # Markdown images: ![alt](url)
    urls.extend(re.findall(r"!\[[^\]]*\]\(([^)]+)\)", content))
    # HTML images: <img src="url">
    urls.extend(re.findall(r'<img[^>]*src=["\x27]([^"\x27]+)["\x27]', content))
    return [u for u in urls if not u.startswith("data:")]


def replace_image_paths(content: str, slug: str) -> str:
    """Replace image URLs with relative local paths."""
    # Replace Markdown images: ![alt](/images/...)
    def md_replacer(m):
        alt = m.group(1)
        url = m.group(2)
        if url.startswith("/images/"):
            filename = os.path.basename(url)
            return f"![{alt}](/images/{slug}/{filename})"
        elif url.startswith("/"):
            filename = os.path.basename(url)
            return f"![{alt}](/images/{slug}/{filename})"
        return m.group(0)

    content = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", md_replacer, content)

    # Replace HTML images: <img src="/images/...">
    # Groups: 1=prefix, 2=src=", 3=URL, 4="suffix>
    def html_replacer(m):
        prefix = m.group(1)
        src_attr = m.group(2)
        url = m.group(3)
        suffix = m.group(4)
        if url.startswith("/"):
            filename = os.path.basename(url)
            return f'{prefix}{src_attr}/images/{slug}/{filename}{suffix}'
        return m.group(0)

    content = re.sub(r"(<img[^>]*)(src=[\"\x27])([^\"\x27]+)([\"\x27][^>]*>)", html_replacer, content)

    return content


def format_content(content: str) -> str:
    """Apply tlai-format style formatting rules to content."""
    # Remove excessive blank lines (3+ consecutive -> 2)
    content = re.sub(r"\n{3,}", "\n\n", content)

    # Add space between Chinese and English/numbers
    # Chinese char followed by English letter/number
    content = re.sub(r"([一-鿿])([a-zA-Z0-9])", r"\1 \2", content)
    # English letter/number followed by Chinese char
    content = re.sub(r"([a-zA-Z0-9])([一-鿿])", r"\1 \2", content)

    # Remove blank lines between consecutive list items
    lines = content.split("\n")
    result = []
    i = 0
    while i < len(lines):
        result.append(lines[i])
        # If current line is a list item and next is blank followed by list item
        if (
            i + 2 < len(lines)
            and re.match(r"^\s*[-*+]\s", lines[i])
            and lines[i + 1].strip() == ""
            and re.match(r"^\s*[-*+]\s", lines[i + 2])
        ):
            i += 2  # Skip the blank line
        else:
            i += 1
    content = "\n".join(result)

    return content


def generate_frontmatter(post: dict) -> str:
    """Generate YAML frontmatter for a post."""
    title = post.get("title", "").replace('"', '\\"')
    return (
        "---\n"
        "dg-publish: false\n"
        f"title: \"{title}\"\n"
        f"author: 王垠\n"
        f"created: {post.get('publish_date', '')}\n"
        f"source: {BASE_URL}/posts/{post['slug']}\n"
        "---\n"
    )


def save_post(post: dict, content: str) -> None:
    """Save a post as a markdown file."""
    slug = post["slug"]
    frontmatter = generate_frontmatter(post)
    formatted = format_content(content)
    content_with_images = replace_image_paths(formatted, slug)

    POSTS_DIR.mkdir(parents=True, exist_ok=True)
    filepath = POSTS_DIR / f"{slug}.md"
    filepath.write_text(frontmatter + content_with_images, encoding="utf-8")
    print(f"  Saved: {slug}.md")


def download_post_images(slug: str, content: str) -> list[str]:
    """Download all images for a post and return list of failures."""
    image_urls = extract_images(content)
    failures = []

    for url in image_urls:
        if url.startswith("/"):
            full_url = BASE_URL + url
        elif url.startswith("http"):
            full_url = url
        else:
            continue

        dest_dir = IMAGES_DIR / slug
        result = download_image(full_url, dest_dir)
        if result is None and not url.startswith("/images/"):
            # Only report failure for absolute URLs or non-standard paths
            failures.append(url)

        time.sleep(0.5)

    return failures


def load_index() -> dict:
    """Load the index file tracking downloaded posts."""
    if INDEX_FILE.exists():
        with open(INDEX_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {"posts": {}}


def save_index(index: dict) -> None:
    """Save the index file."""
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)


def crawl(force: bool = False):
    """Main crawl function."""
    print("Fetching post list from API...")
    all_posts = fetch_all_slugs()
    index = load_index()

    new_count = 0
    updated_count = 0
    skip_count = 0
    image_failures = []

    for i, post_meta in enumerate(all_posts):
        slug = post_meta["slug"]
        existing = index["posts"].get(slug)
        updated_at = post_meta.get("updated_at", "")

        # Skip if file already exists on disk (vault posts take priority)
        post_file = POSTS_DIR / f"{slug}.md"
        if not force and post_file.exists() and existing and existing.get("updated_at") == updated_at:
            skip_count += 1
            continue

        print(f"[{i + 1}/{len(all_posts)}] Processing: {slug}")

        post = fetch_post(slug)
        if not post or not post.get("content"):
            print(f"  Skipping (no content)")
            continue

        content = post["content"]
        failures = download_post_images(slug, content)
        image_failures.extend(failures)

        save_post(post, content)

        index["posts"][slug] = {
            "title": post.get("title", ""),
            "slug": slug,
            "publish_date": post.get("publish_date", ""),
            "updated_at": updated_at,
            "tags": post.get("tags", []),
            "has_images": len(extract_images(content)) > 0,
        }

        if existing:
            updated_count += 1
        else:
            new_count += 1

        time.sleep(DELAY)

    save_index(index)
    print(f"\nDone! New: {new_count}, Updated: {updated_count}, Skipped: {skip_count}")
    if image_failures:
        print(f"Image download failures: {len(image_failures)}")
        for f in image_failures:
            print(f"  - {f}")


if __name__ == "__main__":
    force = "--force" in sys.argv
    crawl(force=force)
