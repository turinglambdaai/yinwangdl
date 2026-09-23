require("dotenv").config();

const markdownIt = require("markdown-it");
const markdownItAnchor = require("markdown-it-anchor");
const hljs = require("highlight.js");

module.exports = function (eleventyConfig) {
  // Passthrough copies
  eleventyConfig.addPassthroughCopy("images");
  eleventyConfig.addPassthroughCopy({ "src/site/styles": "styles" });
  eleventyConfig.addPassthroughCopy({ "src/site/ads.txt": "ads.txt" });
  eleventyConfig.addPassthroughCopy({ "src/site/robots.txt": "robots.txt" });
  eleventyConfig.addPassthroughCopy({ "src/site/favicon.svg": "favicon.svg" });
  eleventyConfig.addPassthroughCopy({ "src/site/CNAME": "CNAME" });
  eleventyConfig.addPassthroughCopy({ "src/site/wechat-qr.jpg": "wechat-qr.jpg" });

  // Markdown: syntax highlighting + heading anchors (CJK titles keep their
  // text as the id; browsers percent-encode the fragment transparently).
  const md = markdownIt({
    html: true,
    highlight: (str, lang) => {
      if (lang && hljs.getLanguage(lang)) {
        try {
          return hljs.highlight(str, { language: lang }).value;
        } catch (_) { /* fall through */ }
      }
      return ""; // let markdown-it escape it
    },
  }).use(markdownItAnchor, {
    level: [2, 3],
    slugify: (s) => s.trim().toLowerCase().replace(/\s+/g, "-"),
  });
  eleventyConfig.setLibrary("md", md);

  // Date formatting filter
  eleventyConfig.addFilter("isodate", (date) => {
    if (!date) return "";
    if (typeof date === "string") return date.substring(0, 10);
    if (date instanceof Date) return date.toISOString().substring(0, 10);
    return String(date).substring(0, 10);
  });

  // Extract year from date
  eleventyConfig.addFilter("year", (date) => {
    if (!date) return "Unknown";
    const iso = typeof date === "string" ? date.substring(0, 10) : date instanceof Date ? date.toISOString().substring(0, 10) : String(date).substring(0, 10);
    return iso.substring(0, 4);
  });

  // Sort posts by created date descending (normalize to ISO string) and
  // attach older/newer neighbors for post-page navigation.
  eleventyConfig.addCollection("post", function (collectionApi) {
    const list = collectionApi
      .getFilteredByTag("post")
      .sort((a, b) => {
        const toIso = (d) => {
          if (!d) return "0000";
          if (typeof d === "string") return d.substring(0, 10);
          if (d instanceof Date) return d.toISOString().substring(0, 10);
          return String(d).substring(0, 10);
        };
        return toIso(b.data.created).localeCompare(toIso(a.data.created));
      });
    list.forEach((p, i) => {
      p.data.olderPost = list[i + 1] || null;
      p.data.newerPost = list[i - 1] || null;
    });
    return list;
  });

  return {
    dir: {
      input: ".",
      output: "dist",
      includes: "src/site/_includes",
      data: "src/site/_data",
    },
    templateFormats: ["njk", "md"],
    htmlTemplateEngine: "njk",
    markdownTemplateEngine: "njk",
    passthroughFileCopy: true,
  };
};
