// Session navigation commands, ported from common/SessionNavigationUtilities.java.

const constants = require("./constants");

function sessionTitlesIn($content) {
  return $content
    .find(constants.SESSION_LIST_SESSION_ROW)
    .toArray()
    .map((row) => Cypress.$(row).find(constants.SESSION_LIST_SESSION_NAME).text().trim());
}

Cypress.Commands.add("getFullSessionList", () => {
  return cy.getTabContent(constants.SESSION_ICON).then(($content) => sessionTitlesIn($content));
});

// Yields the session row element with the given title; retries until found.
Cypress.Commands.add("getSession", (sessionName) => {
  return cy
    .getTabContent(constants.SESSION_ICON)
    .should(($content) => {
      expect(sessionTitlesIn($content), `session "${sessionName}" to be found`).to.include(sessionName);
    })
    .then(($content) => {
      const row = $content
        .find(constants.SESSION_LIST_SESSION_ROW)
        .toArray()
        .find((el) => Cypress.$(el).find(constants.SESSION_LIST_SESSION_NAME).text().trim() === sessionName);
      return cy.wrap(row);
    });
});
