#!/usr/bin/env python3
"""
One-shot migration: Obsidian-compatible layout -> site-native layout.

Before: posts/{中文标题}.md, title implied by file name, body starts at
        ##/### level (file name acted as H1).
After:  posts/{slug}.md (file name == URL slug == images dir name),
        explicit `title` in frontmatter, body starts with `# {title}`,
        heading levels normalized (top body level is H2: if a post has no
        H2 but has H3s, H3s are promoted).

Usage:
    python scripts/migrate_to_slug_filenames.py --dry-run
    python scripts/migrate_to_slug_filenames.py            # apply (git mv)
"""

import re
import subprocess
import sys
from pathlib import Path

POSTS_DIR = Path(__file__).resolve().parent.parent / "posts"

FM_RE = re.compile(r"\A---\n(.*?)\n---\n", re.S)
FENCE_RE = re.compile(r"^\s*`{3,}")


def field(fm: str, name: str) -> str | None:
    m = re.search(rf"^{name}:\s*(.+)$", fm, re.M)
    return m.group(1).strip() if m else None


def promote_h3_to_h2(body: str) -> tuple[str, bool]:
    """If the body has no H2 but has H3s, promote H3 -> H2 (fence-aware)."""
    in_fence = False
    has_h2 = has_h3 = False
    for line in body.split("\n"):
        if FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if re.match(r"^## ", line):
            has_h2 = True
        elif re.match(r"^### ", line):
            has_h3 = True
    if has_h2 or not has_h3:
        return body, False
    in_fence = False
    out = []
    for line in body.split("\n"):
        if FENCE_RE.match(line):
            in_fence = not in_fence
            out.append(line)
            continue
        out.append(re.sub(r"^### ", "## ", line) if not in_fence else line)
    return "\n".join(out), True


def migrate(dry_run: bool) -> int:
    seen = {}
    renamed = promoted = normalized_only = 0
    for f in sorted(POSTS_DIR.glob("*.md")):
        text = f.read_text(encoding="utf-8")
        m = FM_RE.match(text)
        if not m:
            print(f"SKIP (no frontmatter): {f.name}")
            continue
        fm, body = m.group(1), text[m.end():]

        slug = field(fm, "slug")
        title = field(fm, "title") or f.stem
        if not slug:
            print(f"ERROR no slug: {f.name}")
            return 1
        if slug in seen:
            print(f"ERROR duplicate slug {slug}: {f.name} vs {seen[slug]}")
            return 1
        seen[slug] = f.name

        title_safe = title.replace('"', '\\"')
        fm_lines = [f'title: "{title_safe}"', f"slug: {slug}"]
        if field(fm, "author"):
            fm_lines.append(f"author: {field(fm, 'author')}")
        if field(fm, "created"):
            fm_lines.append(f"created: {field(fm, 'created')}")
        if field(fm, "updated"):
            fm_lines.append(f"updated: {field(fm, 'updated')}")
        if field(fm, "source"):
            fm_lines.append(f"source: {field(fm, 'source')}")

        body, did_promote = promote_h3_to_h2(body)
        promoted += int(did_promote)
        # Every post gets an explicit H1 title unless one is already there
        if body.lstrip().startswith("# "):
            new_text = "---\n" + "\n".join(fm_lines) + "\n---\n" + body
        else:
            new_text = "---\n" + "\n".join(fm_lines) + "\n---\n" + f"# {title}\n\n" + body

        if slug == f.stem:
            # Chinese-slug posts keep their (Chinese) file name; normalize only
            if dry_run:
                print(f"would normalize (keep name): {f.name}"
                      + (" (+H3->H2)" if did_promote else ""))
            else:
                f.write_text(new_text, encoding="utf-8")
            normalized_only += 1
            continue

        dest = POSTS_DIR / f"{slug}.md"
        renamed += 1
        if dry_run:
            print(f"would rename: {f.name} -> {slug}.md"
                  + (" (+H3->H2)" if did_promote else ""))
        else:
            subprocess.run(["git", "mv", str(f), str(dest)], check=True,
                           cwd=POSTS_DIR.parent)
            dest.write_text(new_text, encoding="utf-8")
    print(f"\n{renamed} file(s) {'would be ' if dry_run else ''}renamed; "
          f"{normalized_only} normalized in place; "
          f"{promoted} promoted H3->H2")
    return 0


if __name__ == "__main__":
    sys.exit(migrate("--dry-run" in sys.argv))
