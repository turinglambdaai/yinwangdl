#!/usr/bin/env python3
"""
Fix malformed Markdown emphasis produced by over-eager Pangu spacing.

`** text **` / `* text *` (marker separated from content by spaces) is NOT
emphasis in CommonMark, so the site renders literal asterisks. This script
rewrites them to `**text**` / `*text*` while leaving fenced code blocks and
inline code spans untouched.

Usage:
    python scripts/fix_bold_spacing.py            # apply in place
    python scripts/fix_bold_spacing.py --dry-run  # show diff, change nothing
    python scripts/fix_bold_spacing.py --check    # exit 1 if damage remains
"""

import re
import sys
from pathlib import Path

POSTS_DIR = Path(__file__).resolve().parent.parent / "posts"

# Whole-line fences only (like crawler.py); a lone ```code``` run stays
# inline text and is protected by INLINE_CODE_RE instead.
FENCE_RE = re.compile(r"^\s{0,3}`{3,}[^`]*$")
BOLD_RE = re.compile(r"\*\*\s*([^*\n]+?)\s*\*\*")
# Stray spaces Pangu inserted between ** and full-width punctuation.
BOLD_CLOSE_PUNCT_RE = re.compile(r"\*\* +([，。！？；：）】」])")
BOLD_OPEN_PUNCT_RE = re.compile(r"([，。！？；：（【「]) +\*\*")
# Only rewrap whole lines like `* intro text *` (italic lead-ins), never
# inline single asterisks (too easy to hit multiplication or footnotes).
ITALIC_LINE_RE = re.compile(r"^\*\s+(.+?)\s+\*$")
INLINE_CODE_RE = re.compile(r"(`+)([^`]|[^`][\s\S]*?[^`])\1(?!`)")


def fix_text_outside_code(content: str) -> str:
    """Fix emphasis spacing in one chunk known to be outside code blocks."""
    # Stash inline code spans so their asterisks are never touched.
    stash = []

    def _stash(m):
        stash.append(m.group(0))
        return f"\x00{len(stash) - 1}\x00"

    def _unstash(m):
        return stash[int(m.group(1))]

    protected = INLINE_CODE_RE.sub(_stash, content)
    protected = BOLD_RE.sub(r"**\1**", protected)
    protected = BOLD_CLOSE_PUNCT_RE.sub(r"**\1", protected)
    protected = BOLD_OPEN_PUNCT_RE.sub(r"\1**", protected)
    protected = "\n".join(
        ITALIC_LINE_RE.sub(r"*\1*", line) for line in protected.split("\n")
    )
    return re.sub(r"\x00(\d+)\x00", _unstash, protected)


def fix_emphasis_spacing(content: str) -> str:
    """Apply fixes to a full Markdown document, skipping fenced code blocks."""
    lines = content.split("\n")
    in_code = False
    out = []
    for line in lines:
        if FENCE_RE.match(line):
            in_code = not in_code
            out.append(line)
            continue
        out.append(line if in_code else fix_text_outside_code(line))
    return "\n".join(out)


def main() -> int:
    dry_run = "--dry-run" in sys.argv
    check = "--check" in sys.argv
    changed = 0
    for f in sorted(POSTS_DIR.glob("*.md")):
        original = f.read_text(encoding="utf-8")
        fixed = fix_emphasis_spacing(original)
        if fixed == original:
            continue
        changed += 1
        if check:
            print(f"NEEDS FIX: {f.name}")
        elif dry_run:
            print(f"would fix: {f.name}")
            for i, (a, b) in enumerate(zip(original.split("\n"), fixed.split("\n"))):
                if a != b:
                    print(f"  - {a}")
                    print(f"  + {b}")
        else:
            f.write_text(fixed, encoding="utf-8")
            print(f"fixed: {f.name}")
    mode = "damaged" if check else "fixed" if not dry_run else "would fix"
    print(f"\n{changed} file(s) {mode}")
    return 1 if (check and changed) else 0


if __name__ == "__main__":
    sys.exit(main())
