# Yinwang Blog Archive

Auto-crawled archive of [yinwang.org](https://www.yinwang.org) blog posts by Wang Yin. The crawler runs weekly via GitHub Actions, saving every post as Markdown with images. Deleted articles are preserved through Git history.

![Python](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white) [![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

**English** · [中文](README.zh-CN.md)

## Features

- **Automated weekly crawl** via GitHub Actions (every Monday at 03:00 UTC)
- **Incremental updates** — only downloads new or modified posts
- **Full content archival** — posts saved as Markdown, images downloaded locally
- **Self-contained Markdown** — file name = URL slug, Chinese title in frontmatter, body starts with an H1 heading
- **Deduplication** — prevents duplicate files by tracking source URLs
- **Static site generation** — builds a searchable website with Eleventy and deploys to Vercel/GitHub Pages

## Project Structure

```
yinwangdl/
├── posts/           # Markdown articles (file name = Chinese title)
├── images/          # Post images (organized by URL slug)
├── scripts/         # Crawler and utility scripts
├── src/site/        # Eleventy static site source
└── index.json       # Post metadata index
```

## Requirements

- Python 3.12+
- [requests](https://pypi.org/project/requests/) (`pip install requests`)

## Quick Start

### 1. Clone

```bash
git clone https://github.com/turinglambdaai/yinwangdl.git
cd yinwangdl
```

### 2. Run the crawler manually

```bash
# Install dependencies
pip install -r scripts/requirements.txt

# Incremental crawl (only new/updated posts)
python scripts/crawler.py

# Force re-download all posts
python scripts/crawler.py --force
```

### 3. Build the static site

```bash
npm install
npm run build    # Output goes to dist/
npm run dev      # Local dev server with live reload
```

## How It Works

1. **Fetch post list** — The crawler calls `https://www.yinwang.org/api/v1/posts` with pagination (`skip`/`limit`) to get all post slugs.
2. **Deduplicate** — It builds an index of existing posts by `source` URL to avoid duplicates.
3. **Download each post** — For each slug, it fetches the full post content from `https://www.yinwang.org/api/v1/posts/{slug}`.
4. **Download images** — All images referenced in the post are downloaded to `images/{slug}/`.
5. **Format and save** — The content is reformatted (CJK spacing, heading normalization, code block language hints) and saved as a Markdown file with YAML frontmatter.
6. **Update index** — `index.json` is updated with metadata for each processed post.

### Post format

Each Markdown file is named after its URL slug and is fully self-contained:

```markdown
---
title: "My Blog Post"
slug: my-blog-post
author: 王垠
created: 2025-01-15
source: https://www.yinwang.org/posts/my-blog-post
---
# My Blog Post

## First Section

Body text...
```

- File name = `slug` (= URL `/posts/{slug}/` = image dir `images/{slug}/`).
- The Chinese title lives in frontmatter; the body starts with an H1 heading.
- Top-level sections use H2; the crawler normalizes heading depth and code fences automatically.

## Update Notifications (optional)

When the weekly crawl finds new posts, the workflow can email you a
summary so you can decide whether to share them. Configure via repo
secrets (Settings → Secrets and variables → Actions):

| Secret      | Value                                        |
| ----------- | -------------------------------------------- |
| `SMTP_HOST` | e.g. `smtp.qq.com`                           |
| `SMTP_USER` | the from-account, e.g. `you@qq.com`          |
| `SMTP_PASS` | SMTP authorization code (not login password) |
| `NOTIFY_TO` | recipient, usually the same address          |

Without the secrets the step is a harmless dry run.

## RSS

The site publishes an Atom feed at `/feed.xml` (latest 20 posts, title +
link + short excerpt). Full text is intentionally not re-published —
the content belongs to its author.

## License

The code (scripts & workflows) is licensed under the MIT License; the
archived posts remain copyrighted by their author — see [LICENSE](LICENSE).

## Copyright & Takedown

All archived posts are copyrighted by their original author. This archive
is kept for reading convenience; no content is sold or relicensed. If you
are the copyright holder and want any content removed, please
[open an issue](https://github.com/turinglambdaai/yinwangdl/issues) and it
will be taken down promptly.
