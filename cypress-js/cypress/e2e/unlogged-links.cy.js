const { getTestTeachers } = require("../support/testData");
const constants = require("../support/constants");

describe("Unlogged link crawl", () => {
  // The Java suite parametrizes over teachers but never logs in, so the same anonymous crawl
  // runs once per teacher; kept for parity.
  getTestTeachers().forEach(({ mail }) => {
    // Resources: loginservice(READONLY,10) openvidumock(NOACCESS,10) course(READWRITE,15)
    it(`reaches a page with a footer from every same-origin link without logging in (parametrized by ${mail})`, () => {
      cy.get(constants.FOOTER).should("exist");
      cy.crawlSameOriginLinks(Cypress.config("baseUrl"), constants.SPIDER_DEPTH);
    });
  });
});
