#!/usr/bin/env python3
"""
Add slug field to all existing posts.
Extracts slug from the source URL and inserts it into frontmatter.
"""

import re
import unicodedata
from pathlib import Path

POSTS_DIR = Path(__file__).resolve().parent.parent / "posts"


def extract_slug(source_url: str) -> str | None:
    """Extract slug from various source URL formats."""
    # Remove trailing slash and query strings
    url = source_url.rstrip("/").split("?")[0].split("#")[0]

    # Pattern 1: /posts/{slug}
    m = re.search(r"/posts/([^/]+)$", url)
    if m:
        slug = m.group(1)
        return slug.removesuffix(".html")

    # Pattern 2: /blog-cn/YYYY/MM/DD/{slug}
    m = re.search(r"/blog-cn/\d{4}/\d{2}/\d{2}/([^/]+)$", url)
    if m:
        slug = m.group(1)
        return slug.removesuffix("/").removesuffix(".html")

    # Pattern 3: Sina blog — no meaningful slug, fall through
    # Pattern 4: Root URL like yinwang.org — no slug
    return None


def title_to_slug(title: str) -> str:
    """Generate a slug from Chinese title as last resort."""
    # Remove file extension
    title = title.removesuffix(".md")
    # Keep only ASCII alphanumeric, CJK, replace rest with hyphens
    slug = re.sub(r"[^\w一-鿿㐀-䶿]+", "-", title).strip("-")
    return slug.lower()


def process_file(filepath: Path) -> bool:
    """Add slug to a single post file. Returns True if modified."""
    text = filepath.read_text(encoding="utf-8")

    # Must start with frontmatter
    if not text.startswith("---"):
        return False

    end = text.find("\n---", 3)
    if end == -1:
        return False

    fm = text[3:end]
    body = text[end + 4:]  # skip the closing ---

    # Already has slug
    if re.search(r"^slug:", fm, re.MULTILINE):
        return False

    # Extract source URL
    m = re.search(r"^source:\s*(.+)$", fm, re.MULTILINE)
    slug = None
    if m:
        source_url = m.group(1).strip()
        slug = extract_slug(source_url)
    if not slug:
        # Fallback: generate slug from filename (Chinese title)
        slug = title_to_slug(filepath.stem)
        print(f"  ~ generated slug: {filepath.name} -> {slug}")

    # Insert slug after opening ---, before author
    new_fm = f"\nslug: {slug}{fm}"
    filepath.write_text(f"---{new_fm}\n---{body}", encoding="utf-8")
    return True


def main():
    md_files = sorted(POSTS_DIR.glob("*.md"))
    print(f"Found {len(md_files)} posts")

    updated = 0
    for f in md_files:
        if process_file(f):
            updated += 1
            print(f"  + slug: {f.name}")

    print(f"\nDone! Updated: {updated}/{len(md_files)}")


if __name__ == "__main__":
    main()
