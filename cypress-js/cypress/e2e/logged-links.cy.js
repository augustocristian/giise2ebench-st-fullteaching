// Ported from functional/test/LoggedLinksTests.java.
const { getTestUsers } = require("../support/testData");
const constants = require("../support/constants");

describe("Logged link crawl", () => {
  getTestUsers().forEach(({ mail, password, role }) => {
    // Logs in, then crawls every same-origin link and asserts none are broken.
    // Resources: loginservice(READONLY,10) openvidumock(NOACCESS,10) course(READWRITE,15)
    // executor/webbrowser/webserver(READWRITE,1).
    it(`crawls every same-origin link as ${role.toLowerCase()} (${mail})`, () => {
      cy.slowLogin(mail, password);
      cy.get(constants.FOOTER).should("exist");
      cy.crawlSameOriginLinks(Cypress.config("baseUrl"), constants.SPIDER_DEPTH);
    });
  });
});
