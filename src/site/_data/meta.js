require("dotenv").config();

module.exports = () => ({
  siteName: process.env.SITE_NAME || "王垠博客备份",
  siteBaseUrl: process.env.SITE_BASE_URL || "https://yinwang.jrtx.site",
  mainLanguage: process.env.SITE_MAIN_LANGUAGE || "zh",
  buildDate: new Date(),
});
