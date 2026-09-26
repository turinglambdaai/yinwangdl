const fs = require("fs");

// Build-time description extraction: strip frontmatter/markdown/html and
// take the leading characters of the actual prose. Keeps every post's
// <meta description> and OG card unique without hand-written excerpts.
function extractDescription(inputPath) {
  try {
    let text = fs.readFileSync(inputPath, "utf8");
    text = text.replace(/^---\r?\n[\s\S]*?\r?\n---\r?\n/, "");
    text = text.replace(/```[\s\S]*?```/g, " ");
    text = text.replace(/^#{1,6} .*$/gm, " ");
    text = text.replace(/<[^>]+>/g, " ");
    text = text.replace(/[*_`>|]/g, " ");
    text = text.replace(/\s+/g, " ").trim();
    return text.length > 140 ? text.slice(0, 140) + "…" : text || undefined;
  } catch {
    return undefined;
  }
}

module.exports = {
  eleventyComputed: {
    description: (data) => extractDescription(data.page.inputPath),
    title: (data) => data.title || data.page.fileSlug || "",
    permalink: (data) => {
      if (data.slug) return `/posts/${data.slug}/index.html`;
      return false;
    },
  },
};
