# yinwangdl

[English](README.md) | [中文](README.zh-CN.md)

Auto-crawled archive of [yinwang.org](https://www.yinwang.org) blog posts by Wang Yin. The crawler runs weekly via GitHub Actions, saving every post as Markdown with images. Deleted articles are preserved through Git history.

## Features

- **Automated weekly crawl** via GitHub Actions (every Monday at 03:00 UTC)
- **Incremental updates** — only downloads new or modified posts
- **Full content archival** — posts saved as Markdown, images downloaded locally
- **Obsidian compatible** — file names are Chinese titles, frontmatter follows Obsidian conventions
- **Deduplication** — prevents duplicate files by tracking source URLs
- **Static site generation** — builds a searchable website with Eleventy and deploys to Vercel/GitHub Pages

## Repository Structure

```
posts/           # Markdown articles (file name = Chinese title)
images/          # Post images (organized by URL slug)
scripts/         # Crawler and utility scripts
src/site/        # Eleventy static site source
index.json       # Post metadata index
```

## Requirements

- Python 3.12+
- [requests](https://pypi.org/project/requests/) (`pip install requests`)

## Usage

### Run the crawler manually

```bash
# Install dependencies
pip install -r scripts/requirements.txt

# Incremental crawl (only new/updated posts)
python scripts/crawler.py

# Force re-download all posts
python scripts/crawler.py --force
```

### Build the static site

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

Each Markdown file includes YAML frontmatter:

```yaml
---
slug: my-blog-post
author: 王垠
created: 2025-01-15
source: https://www.yinwang.org/posts/my-blog-post
---
```

- File name uses the Chinese title from the API (Obsidian-friendly).
- Body text starts at `##` level (the file name acts as the `#` heading).

## License

This project is licensed under the [Apache License 2.0](LICENSE).
