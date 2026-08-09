#!/usr/bin/env python3
"""
One-shot fix for malformed code fences produced by a bug in crawler.py's
format_content() (now fixed).

The old fence regex `^```\w*$` failed to recognize opening fences whose
language tag contains non-word characters (e.g. ```c#, ```c++, ```f#). When
such an opening fence went unrecognized, the state machine did not flip, so
the *next* bare ``` (a legitimate closing fence) was misclassified as an
opening fence and rewritten to ```text. Per CommonMark, a closing fence
cannot carry an info string, so that ```text actually *opened* a new code
block, swallowing all following body text.

This script walks every post, tracks fence state with a regex that accepts
any language tag, and reverts any closing fence that incorrectly carries an
info string (```text → ```). Idempotent and minimal: it only touches lines
inside a code block whose closing fence has a non-empty info string.

Usage:
    python3 scripts/fix_code_fences.py [--dry-run]
"""

import argparse
import re
import sys
from pathlib import Path

POSTS_DIR = Path(__file__).resolve().parent.parent / "posts"

# Matches fenced code blocks: up to 3 leading whitespace chars, 3+ ticks,
# then an info string of any non-backtick chars (so ```c#, ```c++ work).
# ```code``` (inline) won't match because info ends before a closing run.
FENCE_RE = re.compile(r"^(\s{0,3})(`{3,})([^`]*)$")


def fix_body(body: str) -> tuple[str, list[str]]:
    """Fix malformed closing fences. Returns (new_body, list_of_changes)."""
    lines = body.split("\n")
    changes = []
    in_block = False
    for i, line in enumerate(lines):
        m = FENCE_RE.match(line)
        if not m:
            continue
        fence, info = m.group(2), m.group(3).strip()
        if not in_block:
            in_block = True
        else:
            # Closing fence: CommonMark forbids info strings here. If present,
            # it is the crawler bug — strip it.
            if info:
                changes.append(f"  line {i + 1}: {line!r} -> {fence!r}")
                lines[i] = fence
            in_block = False
    return "\n".join(lines), changes


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="report without writing")
    args = parser.parse_args()

    if not POSTS_DIR.exists():
        print(f"Posts dir not found: {POSTS_DIR}", file=sys.stderr)
        return 1

    total_fixed = 0
    files_fixed = 0
    for md in sorted(POSTS_DIR.glob("*.md")):
        text = md.read_text(encoding="utf-8")

        # Split off frontmatter (anything before the first ``` block)
        fm_end = 0
        if text.startswith("---"):
            end = text.find("\n---", 3)
            if end != -1:
                fm_end = end + 4  # include the closing ```\n... actually closing '---'
                # content after '---\n'
        frontmatter = text[:fm_end] if fm_end else ""
        body = text[fm_end:]

        new_body, changes = fix_body(body)
        if not changes:
            continue

        files_fixed += 1
        total_fixed += len(changes)
        print(f"{md.name}:")
        for c in changes:
            print(c)
        if not args.dry_run:
            md.write_text(frontmatter + new_body, encoding="utf-8")

    mode = "DRY RUN — " if args.dry_run else ""
    print(f"\n{mode}{files_fixed} file(s), {total_fixed} fence(s) fixed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
