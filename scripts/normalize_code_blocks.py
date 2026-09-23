#!/usr/bin/env python3
"""
Normalize legacy indented code blocks to fenced ones.

The site build pipeline (Eleventy) mangles TOP-LEVEL indented code blocks
(tab or 4-space) into plain paragraphs, while fenced blocks render fine.
This script rewrites top-level indented blocks into ```text fences and
leaves list-context indentation (list items' own content) untouched.

Usage:
    python scripts/normalize_code_blocks.py             # convert all posts
    python scripts/normalize_code_blocks.py --check     # exit 1 if any remain
    python scripts/normalize_code_blocks.py --dedent-tab <file>
                                                        # strip one leading
                                                        # tab from every line
"""

import re
import sys
from pathlib import Path

POSTS_DIR = Path(__file__).resolve().parent.parent / "posts"

FENCE_LINE_RE = re.compile(r"^\s*`{3,}[^`]*$")
INDENT_RE = re.compile(r"^(?:\t|    )(\S.*)$")
LIST_ITEM_RE = re.compile(r"^\s*(?:\d+\.|[-*+])\s")


def strip_one_indent(line: str) -> str:
    if line.startswith("\t"):
        return line[1:]
    if line.startswith("    "):
        return line[4:]
    return line


def dedent_tab(content: str) -> str:
    """Remove exactly one leading tab from every line."""
    return "\n".join(l[1:] if l.startswith("\t") else l for l in content.split("\n"))


def indented_code_to_fences(content: str) -> str:
    """Rewrite top-level indented code blocks as ```text fences."""
    lines = content.split("\n")
    out = []
    i = 0
    in_fence = False
    while i < len(lines):
        line = lines[i]
        if FENCE_LINE_RE.match(line):
            in_fence = not in_fence
            out.append(line)
            i += 1
            continue
        m = INDENT_RE.match(line) if not in_fence else None
        if m:
            # Collect the full indented run.
            block = []
            while i < len(lines):
                if lines[i].strip() and not INDENT_RE.match(lines[i]):
                    break
                if not lines[i].strip() and i + 1 < len(lines):
                    # Blank line inside block only if indented content follows.
                    if not INDENT_RE.match(lines[i + 1] or ""):
                        break
                block.append(lines[i])
                i += 1
            # List-context? Last non-blank line before the block decides.
            prev = next((l for l in reversed(out) if l.strip()), "")
            if LIST_ITEM_RE.match(prev):
                out.extend(block)  # list item content, leave untouched
            else:
                out.append("```text")
                out.extend(strip_one_indent(l) for l in block if l.strip())
                out.append("```")
            continue
        out.append(line)
        i += 1
    return "\n".join(out)


def main() -> int:
    args = sys.argv[1:]
    if args and args[0] == "--dedent-tab":
        f = Path(args[1])
        f.write_text(dedent_tab(f.read_text(encoding="utf-8")), encoding="utf-8")
        print(f"dedented: {f.name}")
        return 0

    check = "--check" in args
    changed = 0
    for f in sorted(POSTS_DIR.glob("*.md")):
        original = f.read_text(encoding="utf-8")
        fixed = indented_code_to_fences(original)
        if fixed == original:
            continue
        changed += 1
        if check:
            print(f"NEEDS FIX: {f.name}")
        else:
            f.write_text(fixed, encoding="utf-8")
            print(f"normalized: {f.name}")
    print(f"\n{changed} file(s) {'damaged' if check else 'normalized'}")
    return 1 if (check and changed) else 0


if __name__ == "__main__":
    sys.exit(main())
