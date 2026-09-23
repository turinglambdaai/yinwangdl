module.exports = {
  eleventyComputed: {
    title: (data) => data.title || data.page.fileSlug || "",
    permalink: (data) => {
      if (data.slug) return `/posts/${data.slug}/index.html`;
      return false;
    },
  },
};
