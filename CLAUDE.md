# 项目概述

王垠博客（yinwang.org）文章备份。通过 API 爬取博文，保存为 Markdown 文件。posts 目录下的文件需要能直接放入 Obsidian vault 而无需修改。

## 文件命名（最重要）

- **文件名 = 文章中文标题**（如 `计算机科学视频班课程介绍.md`）
- **禁止使用英文 slug** 作为文件名（如 `cs-video-course.md`）
- 理由：Obsidian 以文件名作为标题，英文 slug 在 Obsidian 中无意义
- 英文 slug 存放在 frontmatter 的 `slug` 字段中，11ty 用它生成 URL（`/posts/{slug}/`）
- 11ty 已有 fallback 逻辑（`posts.11tydata.js`）从文件名提取 title，切换中文文件名不会破坏网站

## 去重

- 新增文章前，**必须**通过 `source` URL 字段检查是否已存在相同文章
- 禁止同一篇文章以不同文件名存在两份（英文 slug + 中文标题 = 重复）
- 如果已有中文标题版本，删除英文 slug 版本

## frontmatter

正确格式：

```yaml
---
slug: cs-video-course
author: 王垠
created: 2025-05-12
source: https://www.yinwang.org/posts/cs-video-course
---
```

- **不需要 `title` 字段**（文件名即标题）
- **不需要 `dg-publish` 字段**（11ty 不使用此字段）
- 必需字段：`slug`、`author`、`created`、`source`
- `slug` 用于生成 URL（`/posts/{slug}/`），值来自源站 URL 的最后一段
- 字段顺序与 Base-Note 模板一致（`slug` → `author` → `created` → `source`）
- frontmatter 结束的 `---` 后直接接正文，不插入空行

## 标题层级

- 正文从 `##` 开始（Obsidian 文件名即标题，不需要 `#` 一级标题）
- `##` 用于大节，`###` 用于小节
- 避免 `####` 及更深，改用加粗段首词
- 正文中的 `#` 如果不是标题而是代码（如 `#define`），必须用行内代码包裹

## 图片

- 图片存放在 `images/{slug}/` 目录（slug = URL 中的英文标识符，用于目录命名）
- 正文中的图片引用使用标准 Markdown：`![描述](/images/{slug}/文件名.png)`
- 图片目录名使用英文 slug（与 URL 对应），仅文件名使用中文

## 排版规范

遵循 `~/.claude/skills/tlai-article/references/formatting-rules.md` 的排版规则。关键要点：

- 段落之间空 1 行，段落内部无空行
- 列表项之间不加空行，直接排列
- 代码块必须标注语言类型
- CJK 与半角字符之间加空格（如 `使用 C++ 编程`，不是 `使用C++编程`）

## Crawler 修改要点

`scripts/crawler.py` 的 `save_post()` 函数需要修改：

1. 文件名使用 API 返回的中文 `title` 而非 `slug`
2. 保存前检查同 source URL 的文件是否已存在
3. frontmatter 包含 `slug`、`author`、`created`、`source`（按此顺序）
4. 图片目录仍用 slug 命名（`images/{slug}/`）
