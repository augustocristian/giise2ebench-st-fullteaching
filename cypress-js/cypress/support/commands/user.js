// Current-user commands: display name and login-state assertions.

const { common, settings } = require("../selectors");

/**
 * Yields the logged-in user's display name, read from the settings page.
 * @param {{goBack?: boolean}} [options] goBack (default true) returns to the previous page.
 */
Cypress.Commands.add("getUserName", (options = {}) => {
  const goBack = options.goBack !== false;
  return cy.location("pathname").then((pathname) => {
    const notOnSettings = !pathname.endsWith("/settings");
    cy.get(common.settingsButton).should("be.visible");
    if (notOnSettings) {
      cy.get(common.settingsButton).click();
    }
    return cy
      .get(settings.userName)
      .should("be.visible")
      .invoke("text")
      .then((text) => {
        if (goBack && notOnSettings) {
          cy.go("back");
        }
        // cy.go() is queued above, so the value must be yielded through cy.wrap.
        return cy.wrap(text.trim(), { log: false });
      });
  });
});

/** Asserts the settings page shows `email` as the logged-in user. */
Cypress.Commands.add("checkLogin", (email) => {
  cy.get(common.settingsButton).should("be.visible").click();
  cy.get(settings.userEmail).should(($el) => {
    expect($el.text().trim()).to.eq(email.trim());
  });
});

/** Asserts the logged-out navbar (login link) is visible. */
Cypress.Commands.add("checkLogOut", () => {
  cy.get(common.loginMenuLink).should("be.visible");
});
