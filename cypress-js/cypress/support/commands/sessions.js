// Session-list commands.

const { tabs, session } = require("../selectors");
const { rowTitles, getRowByTitle } = require("../helpers");

const sessionTab = () => cy.getTabContent(tabs.sessionIcon);

/** Yields the titles of all sessions in the Sessions tab. */
Cypress.Commands.add("getFullSessionList", () => {
  return sessionTab().then(($content) => rowTitles($content, session.row, session.name));
});

/** Yields the session row titled `sessionName`; retries until found. */
Cypress.Commands.add("getSession", (sessionName) => {
  return getRowByTitle(sessionTab, session.row, session.name, sessionName, "session");
});
