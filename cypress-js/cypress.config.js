const fs = require("fs");
const path = require("path");
const { defineConfig } = require("cypress");

const SUT_URL = process.env.SUT_URL || "https://localhost:5000";

const XML_ESCAPES = { "<": "&lt;", ">": "&gt;", "&": "&amp;", "'": "&apos;", '"': "&quot;" };
const escapeXml = (value) => String(value ?? "").replace(/[<>&'"]/g, (char) => XML_ESCAPES[char]);

// On CI, write one JUnit file per spec for the job summary (Cypress' own console reporter stays on).
function writeJunit(spec, results) {
  if (!results?.tests) return;
  const cases = results.tests.map((test) => {
    const attempts = test.attempts ?? [];
    const last = attempts[attempts.length - 1];
    const seconds = (last?.duration ?? last?.wallClockDuration ?? 0) / 1000;
    const suite = test.title.slice(0, -1).join(" › ") || spec.name;
    const open = `<testcase classname="${escapeXml(suite)}" name="${escapeXml(test.title.at(-1))}" time="${seconds}">`;
    if (test.state === "failed") {
      return `${open}<failure message="${escapeXml(test.displayError?.split("\n")[0])}">${escapeXml(test.displayError)}</failure></testcase>`;
    }
    if (test.state === "pending" || test.state === "skipped") return `${open}<skipped/></testcase>`;
    return `${open}</testcase>`;
  });
  const dir = path.join(__dirname, "results");
  fs.mkdirSync(dir, { recursive: true });
  const file = `junit-${spec.relative.split(path.sep).join("_").split("/").join("_")}.xml`;
  const xml = `<?xml version="1.0" encoding="UTF-8"?>\n<testsuite name="${escapeXml(spec.relative)}" tests="${cases.length}" time="${(results.stats?.duration ?? 0) / 1000}">\n${cases.join("\n")}\n</testsuite>\n`;
  fs.writeFileSync(path.join(dir, file), xml);
}

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
      if (process.env.CI) on("after:spec", writeJunit);

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
