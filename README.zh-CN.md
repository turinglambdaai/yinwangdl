# yinwangdl

[English](README.md) | [中文](README.zh-CN.md)

王垠博客（[yinwang.org](https://www.yinwang.org)）文章自动备份。通过 GitHub Actions 每周自动爬取，将所有博文保存为 Markdown 文件并下载图片。已删除的文章通过 Git 历史保留。

## 功能特点

- **每周自动爬取** — 通过 GitHub Actions 执行（每周一 UTC 03:00）
- **增量更新** — 仅下载新增或修改的文章
- **完整内容归档** — 文章保存为 Markdown，图片下载到本地
- **Obsidian 兼容** — 文件名为中文标题，frontmatter 遵循 Obsidian 规范
- **自动去重** — 通过 source URL 跟踪，避免重复文件
- **静态站点生成** — 使用 Eleventy 构建可搜索的网站，部署到 Vercel/GitHub Pages

## 仓库结构

```
posts/           # Markdown 文章（文件名 = 中文标题）
images/          # 文章图片（按 URL slug 分目录）
scripts/         # 爬虫和工具脚本
src/site/        # Eleventy 静态站点源码
index.json       # 文章元数据索引
```

## 环境要求

- Python 3.12+
- [requests](https://pypi.org/project/requests/)（`pip install requests`）

## 使用方法

### 手动运行爬虫

```bash
# 安装依赖
pip install -r scripts/requirements.txt

# 增量爬取（仅新增/更新的文章）
python scripts/crawler.py

# 强制重新下载所有文章
python scripts/crawler.py --force
```

### 构建静态站点

```bash
npm install
npm run build    # 输出到 dist/
npm run dev      # 本地开发服务器，支持热重载
```

## 工作原理

1. **获取文章列表** — 爬虫调用 `https://www.yinwang.org/api/v1/posts` 接口，通过分页参数（`skip`/`limit`）获取所有文章 slug。
2. **去重检查** — 根据已有的 `source` URL 构建索引，避免生成重复文件。
3. **逐篇下载** — 对每个 slug，从 `https://www.yinwang.org/api/v1/posts/{slug}` 获取完整文章内容。
4. **下载图片** — 文章中引用的所有图片下载到 `images/{slug}/` 目录。
5. **格式化并保存** — 对内容进行排版处理（CJK 间距、标题层级规范化、代码块语言标注），生成带 YAML frontmatter 的 Markdown 文件。
6. **更新索引** — 将每篇已处理文章的元数据更新到 `index.json`。

### 文章格式

每篇 Markdown 文件包含 YAML frontmatter：

```yaml
---
slug: my-blog-post
author: 王垠
created: 2025-01-15
source: https://www.yinwang.org/posts/my-blog-post
---
```

- 文件名使用 API 返回的中文标题（兼容 Obsidian）。
- 正文从 `##` 级别开始（文件名即一级标题）。

## 许可证

本项目基于 [Apache License 2.0](LICENSE) 许可。
