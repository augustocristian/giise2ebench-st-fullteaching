// Login/logout assertions, ported from common/UserUtilities.java.

const constants = require("./constants");

Cypress.Commands.add("checkLogin", (email) => {
  cy.get(constants.SETTINGS_BUTTON).should("be.visible").click();
  cy.get(constants.SETTINGS_USER_EMAIL)
    .invoke("text")
    .should((text) => {
      expect(text.trim()).to.eq(email.trim());
    });
});

Cypress.Commands.add("checkLogOut", () => {
  cy.get(constants.LOGIN_MENU_LINK).should("be.visible");
});
