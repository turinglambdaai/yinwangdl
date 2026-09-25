#!/usr/bin/env python3
"""
Post integrity linter — run in CI (crawl workflow + lint workflow) and
locally. Exits non-zero on the first class of damage it finds.

Checks per post:
  1. frontmatter has title/slug/author/created/source (updated optional)
  2. body starts with an H1 heading
  3. no broken emphasis (`** text **` etc.)
  4. no top-level indented code blocks (they break in the build pipeline)
  5. code fences are balanced
"""

import re
import sys
from pathlib import Path

from fix_bold_spacing import fix_emphasis_spacing
from normalize_code_blocks import indented_code_to_fences

POSTS_DIR = Path(__file__).resolve().parent.parent / "posts"

REQUIRED_FIELDS = ["title", "slug", "author", "created", "source"]
FM_RE = re.compile(r"\A---\n(.*?)\n---\n", re.S)
# Whole-line fences only; a lone ```code``` run (info string with
# backticks) is inline text, not a fence, and must not be counted.
FENCE_LINE_RE = re.compile(r"^\s*`{3,}[^`]*$")


def lint_file(path: Path) -> list[str]:
    errors = []
    text = path.read_text(encoding="utf-8")
    m = FM_RE.match(text)
    if not m:
        return [f"{path.name}: missing frontmatter"]
    fm, body = m.group(1), text[m.end():]

    for field in REQUIRED_FIELDS:
        if not re.search(rf"^{field}:\s*\S", fm, re.M):
            errors.append(f"{path.name}: frontmatter missing '{field}'")

    first_line = next((l for l in body.split("\n") if l.strip()), "")
    if not first_line.startswith("# "):
        errors.append(f"{path.name}: body must start with an H1 heading")

    if fix_emphasis_spacing(text) != text:
        errors.append(f"{path.name}: broken emphasis (run fix_bold_spacing.py)")

    if indented_code_to_fences(text) != text:
        errors.append(f"{path.name}: top-level indented code (run normalize_code_blocks.py)")

    fence_count = sum(1 for l in body.split("\n") if FENCE_LINE_RE.match(l))
    if fence_count % 2 != 0:
        errors.append(f"{path.name}: unbalanced code fences ({fence_count})")

    return errors


def main() -> int:
    errors = []
    files = sorted(POSTS_DIR.glob("*.md"))
    for f in files:
        errors.extend(lint_file(f))
    if errors:
        print(f"\n{len(files)} files linted, {len(errors)} error(s):")
        for e in errors:
            print(f"  {e}")
        return 1
    print(f"\n{len(files)} files linted, all clean")
    return 0


if __name__ == "__main__":
    sys.exit(main())
