// Ported from functional/test/UnLoggedLinksTests.java.
const { getTestTeachers } = require("../support/testData");
const constants = require("../support/constants");

describe("Unlogged link crawl", () => {
  // mail/password/role are unused in the test body below, matching the Java source: it
  // parametrizes over teachers but never logs in, just re-runs the same crawl once per teacher.
  getTestTeachers().forEach(({ mail }) => {
    // Crawls every same-origin link from the home page (no login) and asserts none are broken.
    // Resources: loginservice(READONLY,10) openvidumock(NOACCESS,10) course(READWRITE,15)
    // executor/webbrowser/webserver(READWRITE,1).
    it(`crawls every same-origin link with no login (parametrized by ${mail})`, () => {
      cy.get(constants.FOOTER).should("exist");
      cy.crawlSameOriginLinks(Cypress.config("baseUrl"), constants.SPIDER_DEPTH);
    });
  });
});
