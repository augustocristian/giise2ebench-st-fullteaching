const { defineConfig } = require("cypress");

// Mirrors BaseLoggedTest.setupAll()'s SUT_URL/tjob_name env var resolution.
const SUT_URL = process.env.SUT_URL || "https://localhost:5000";
const TJOB_NAME = process.env.tjob_name || "TJobDef";

module.exports = defineConfig({
  e2e: {
    baseUrl: SUT_URL,
    supportFile: "cypress/support/e2e.js",
    specPattern: "cypress/e2e/**/*.cy.js",
    fixturesFolder: "cypress/fixtures",
    video: false,
    // The SUT serves a self-signed HTTPS certificate.
    chromeWebSecurity: false,
    // Mirrors Wait.notTooMuch's 20s: the default retry window for every cy.get()/should().
    defaultCommandTimeout: 20000,
    pageLoadTimeout: 30000,
    setupNodeEvents(on, config) {
      config.env.tjobName = TJOB_NAME;

      // Mirrors the Chromium args ChromeUser.java/BrowserUser (pyppeteer) set: fake media
      // devices so camera/mic-gated UI can be exercised headlessly.
      on("before:browser:launch", (browser = {}, launchOptions) => {
        if (browser.family === "chromium") {
          launchOptions.args.push("--use-fake-ui-for-media-stream");
          launchOptions.args.push("--use-fake-device-for-media-stream");
          launchOptions.args.push("--ignore-certificate-errors");
        }
        return launchOptions;
      });

      return config;
    },
  },
});
