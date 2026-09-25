#!/usr/bin/env python3
"""
Notify the site owner by email about newly crawled posts.

Detects posts/*.md that are new (untracked in git — just crawled, not
yet committed) and sends a summary email via SMTP. Configure through
environment variables (repo secrets in CI):

  SMTP_HOST   e.g. smtp.qq.com
  SMTP_USER   the from-account, e.g. you@qq.com
  SMTP_PASS   SMTP authorization code (not the login password)
  NOTIFY_TO   recipient, usually the same address

No new posts -> silent exit 0. Any var missing -> dry-run print only.
"""

import os
import re
import smtplib
import subprocess
import sys
from email.header import Header
from email.mime.text import MIMEText
from email.utils import formataddr
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SITE_BASE = "https://yinwang.jrtx.site"
FM_RE = re.compile(r"\A---\n(.*?)\n---\n", re.S)


def new_post_files() -> list[Path]:
    out = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard", "posts"],
        capture_output=True, text=True, cwd=REPO, check=True,
    ).stdout
    # paths are relative to the repo root
    return sorted(REPO / f for f in out.splitlines() if f.endswith(".md"))


def post_info(path: Path) -> tuple[str, str]:
    m = FM_RE.match(path.read_text(encoding="utf-8"))
    fm = m.group(1) if m else ""
    t = re.search(r'^title:\s*"?(.+?)"?\s*$', fm, re.M)
    s = re.search(r"^slug:\s*(\S+)", fm, re.M)
    return (t.group(1) if t else path.stem, s.group(1) if s else path.stem)


def main() -> int:
    files = new_post_files()
    if not files:
        print("no new posts")
        return 0

    lines = [f"本周爬取新增 {len(files)} 篇文章：", ""]
    for i, f in enumerate(files, 1):
        title, slug = post_info(f)
        lines.append(f"{i}. {title}")
        lines.append(f"   {SITE_BASE}/posts/{slug}/")
    body = "\n".join(lines)
    print(body)

    host = os.environ.get("SMTP_HOST", "").strip()
    user = os.environ.get("SMTP_USER", "").strip()
    password = os.environ.get("SMTP_PASS", "").strip()
    to = os.environ.get("NOTIFY_TO", "").strip()
    if not all([host, user, password, to]):
        print("(dry-run: set SMTP_HOST/SMTP_USER/SMTP_PASS/NOTIFY_TO to deliver)")
        return 0

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = Header(f"王垠博客归档站：新增 {len(files)} 篇文章", "utf-8")
    msg["From"] = formataddr(("yinwangdl", user))
    msg["To"] = to

    with smtplib.SMTP(host, 587, timeout=20) as smtp:
        smtp.starttls()
        smtp.login(user, password)
        smtp.sendmail(user, [to], msg.as_string())
    print(f"\nmail sent to {to}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
