const path = require("path");

module.exports = {
  eleventyComputed: {
    title: (data) => {
      if (data.title) return data.title;
      // Extract title from filename (without .md extension)
      const inputPath = data.page.inputPath;
      if (inputPath) {
        const basename = path.basename(inputPath, ".md");
        return basename;
      }
      return data.page.fileSlug || "";
    },
    permalink: (data) => {
      if (data.slug) return `/posts/${data.slug}/index.html`;
      return false;
    },
  },
};
