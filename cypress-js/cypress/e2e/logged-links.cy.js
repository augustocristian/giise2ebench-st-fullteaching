const { getTestUsers } = require("../support/testData");
const constants = require("../support/constants");

describe("Logged link crawl", () => {
  getTestUsers().forEach(({ mail, password, role }) => {
    describe(`as ${role.toLowerCase()} (${mail})`, () => {
      beforeEach(() => {
        cy.login(mail, password);
        cy.get(constants.FOOTER).should("exist");
      });

      // Resources: loginservice(READONLY,10) openvidumock(NOACCESS,10) course(READWRITE,15)
      it("reaches a page with a footer from every same-origin link", () => {
        cy.crawlSameOriginLinks(Cypress.config("baseUrl"), constants.SPIDER_DEPTH);
      });
    });
  });
});
