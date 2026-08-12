require("dotenv").config();

module.exports = function (eleventyConfig) {
  // Passthrough copies
  eleventyConfig.addPassthroughCopy("images");
  eleventyConfig.addPassthroughCopy({ "src/site/styles": "styles" });
  eleventyConfig.addPassthroughCopy({ "src/site/ads.txt": "ads.txt" });
  eleventyConfig.addPassthroughCopy({ "src/site/robots.txt": "robots.txt" });
  eleventyConfig.addPassthroughCopy({ "src/site/favicon.svg": "favicon.svg" });
  eleventyConfig.addPassthroughCopy({ "src/site/CNAME": "CNAME" });

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

  // Sort posts by created date descending (normalize to ISO string)
  eleventyConfig.addCollection("post", function (collectionApi) {
    return collectionApi
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
