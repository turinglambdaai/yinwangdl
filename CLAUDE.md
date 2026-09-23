# 项目概述

王垠博客（yinwang.org）文章备份站。通过 API 爬取博文，保存为 Markdown，Eleventy 构建静态站部署（Vercel/GitHub Actions 每周一爬取）。posts 目录为**站点源文件**（不再考虑导回 Obsidian）。

## 文件命名（最重要）

- **文件名 = frontmatter 的 `slug`**（如 `mites.md`），与站点 URL（`/posts/{slug}/`）、图片目录（`images/{slug}/`）三统一
- 中文标题只存在于 frontmatter 的 `title` 字段，不出现在文件名
- 少数文章源站 slug 本身是中文（如 `论研究.md`），保持原样——文件名即 slug，URL 不变

## frontmatter

```yaml
---
title: "我和螨虫的故事"
slug: mites
author: 王垠
created: 2026-07-15
updated: 2026-09-01
source: https://www.yinwang.org/posts/mites
---
```

- `title` 必填，双引号包裹（YAML 安全），值来自 API 返回的中文标题
- `slug` 必填（URL 最后一段）；`author`、`created`（API 的 publish_date）、`source` 必填
- `updated` 可选（API 的 updated_at，有则写入）
- 字段顺序固定：title → slug → author → created → updated → source

## 正文结构

- 正文以 `# {title}` 开始（每篇文件自包含）
- 大节用 `##`，小节用 `###`
- 避免 `####` 及更深：爬虫会自动转为加粗段首词
- 若全文无 `##` 而有 `###`，爬虫自动把 `###` 升为 `##`（顶层小节统一 H2）
- 正文中的 `#` 如果不是标题而是代码（如 `#define`），必须用行内代码包裹

## 图片

- 图片存放在 `images/{slug}/` 目录
- 正文引用标准 Markdown 或 HTML：`![描述](/images/{slug}/文件名.png)`、`<img src="/images/{slug}/文件名.png" width="400">`

## 排版规范

- 段落之间空 1 行，段落内部无空行；列表项之间不加空行
- 代码块必须标注语言类型；**顶层缩进代码块会被构建管线破坏，必须用围栏**（爬虫自动转换）
- CJK 与半角字符之间加空格（如 `使用 C++ 编程`），但 Markdown 标记（`*` `_` `~`）与内容之间**禁止**插空格，否则强调失效

## scripts

- `crawler.py`：主爬虫。`format_content()` 含自愈链（坏强调修复、顶层缩进代码转围栏、层级规范化、盘古空格），新爬内容自动规范化
- `fix_bold_spacing.py`：修复 `** 文字 **` 坏强调；`--check` 模式可供 CI 校验，应恒为 0
- `normalize_code_blocks.py`：顶层缩进代码块转围栏；`--check` 模式同理
- `migrate_to_slug_filenames.py`：一次性迁移工具（中文文件名 → slug 文件名），2026-09-23 已执行完毕，仅留档

## 去重

- 新增文章前，通过 frontmatter 的 `source` URL 检查是否已存在（`build_source_index()`）
- 爬虫默认增量：`updated_at` 未变的文章跳过，不会重写本地已修复的文件

## 站点（src/site）

- 布局 `base.njk`（全站框架/搜索/进度条/lightbox）+ `post.njk`（文章页：公众号卡片、上/下一篇、文末广告）
- 文章页集合 `collections.post` 由 `posts.json` 打 tag，prev/next 已在 `.eleventy.js` 的 collection 里挂好（`olderPost`/`newerPost`）
- 商业定调：内容归王垠，公众号卡片只做「站长原创」引流定位；页脚有删除请求通道；措辞避免「非商业」声明（与广告冲突）
