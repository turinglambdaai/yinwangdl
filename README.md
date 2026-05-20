# yinwangdl

王垠博客（[yinwang.org](https://www.yinwang.org)）文章备份。自动每周爬取，通过 Git 历史保留已删除文章。

## 仓库结构

```
posts/           # Markdown 文章（文件名 = 中文标题）
images/          # 文章中引用的图片（按 slug 分目录）
scripts/         # 爬虫和去重脚本
index.json       # 文章元数据索引
.github/         # GitHub Actions 自动爬取
```

## 文章格式

- 文件名使用中文标题（Obsidian 兼容，文件名即标题）
- Frontmatter 仅含 `author`、`created`、`source` 三个字段
- 正文从 `##` 开始（文件名已是一级标题）
- 所有文章可直接放入 Obsidian vault 无需修改

## 文章来源

- **用户格式化版本**：来自 Obsidian 笔记库的已排版文章（优先保留）
- **API 自动下载**：从博客 API 获取的最新文章，按 tlai-format 规范排版

## 自动爬取

GitHub Actions 每周一 03:00 UTC 自动执行，检查新文章和更新。也支持手动触发。

## 手动运行

```bash
pip install -r scripts/requirements.txt
python scripts/crawler.py            # 增量更新
python scripts/crawler.py --force    # 强制重新下载所有文章
```

## 技术细节

- 数据源：`https://www.yinwang.org/api/v1/posts`（分页：`skip`/`limit`）
- 文件命名：中文标题（API `title` 字段），不再使用 URL slug
- 去重：按 `source` URL 检查，避免重复文章
- 图片：下载到 `images/{slug}/` 目录，使用标准 Markdown 引用
