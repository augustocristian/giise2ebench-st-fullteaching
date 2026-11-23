// Login / logout commands.
// cy.get()/.should() already retry until defaultCommandTimeout (20s, see cypress.config.js),
// so no explicit waits are needed.

const { common, login, course, session } = require("../selectors");

/** Logs in through the login modal and yields the user's display name. */
Cypress.Commands.add("login", (email, password) => {
  cy.log(`Login as ${email}`);
  // Materialize leaves the floating <label> over the input, so Cypress sees it as covered; force bypasses that check.
  cy.get(login.downloadButton).should("be.visible");
  cy.openDialog(login.downloadButton);
  cy.get(login.userField).type(email, { force: true });
  cy.get(login.passwordField).type(password, { force: true });
  // Fields must hold the typed text and Angular must have enabled the button.
  cy.get(login.userField).should("have.value", email);
  cy.get(login.passwordField).should("have.value", password);
  cy.get(login.button).should("not.be.disabled").click();

  cy.get(course.list).should("exist");
  cy.get(course.listId).should("exist");
  return cy.getUserName();
});

// If inside a video session, leaves it first (opening the side menu if needed).
function leaveVideoSession($body) {
  if ($body.find(session.fixedIcon).length === 0) {
    return;
  }
  if ($body.find(session.exitIcon).length === 0) {
    cy.get(session.fixedIcon).click();
  }
  // Force-click bypasses any overlay that would intercept a native click.
  cy.get(session.exitIcon).should("exist").click({ force: true });
}

/** Logs out if (and only if) a user is logged in; safe to call at any time. */
Cypress.Commands.add("logout", () => {
  cy.get("body").then(leaveVideoSession);

  cy.get("body").then(($body) => {
    const hasMenu = $body.find(common.mainMenuArrow).length > 0;
    const hasShrunkMenu = $body.find("a.button-collapse").length > 0;
    if (!hasMenu && !hasShrunkMenu) {
      cy.log("logout(): not logged in, nothing to do");
      return;
    }
    cy.window().then((win) => win.scrollTo(0, 0));
    if (hasMenu) {
      cy.get(common.mainMenuArrow).click({ force: true });
      cy.get(common.logoutButton).click();
    } else {
      cy.get("a.button-collapse").click();
      cy.get("#nav-mobile a").contains("Logout").click();
    }
  });
});
