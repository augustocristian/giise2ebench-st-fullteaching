// Login/logout/dialog custom commands, ported from the protected methods of
// common/BaseLoggedTest.java.
//
// Java models these as instance methods inherited by every test class; the Cypress idiom is
// custom commands registered on `cy`, composed directly in specs (`cy.slowLogin(...)`).
// Most of Wait.java's explicit ExpectedConditions collapse away here: `cy.get()` and
// `.should()` already retry until the default command timeout (see cypress.config.js's
// defaultCommandTimeout, set to Wait.notTooMuch's 20s) elapses.

const constants = require("./constants");

const A_LITTLE_MS = 4000;

function login(email, password, slow) {
  cy.get(constants.DOWNLOAD_BUTTON, { timeout: A_LITTLE_MS }).should("be.visible");
  cy.openDialog(constants.DOWNLOAD_BUTTON);
  cy.get(constants.LOGIN_USER_FIELD).should("exist");
  cy.get(constants.LOGIN_PASSWORD_FIELD).should("exist");

  cy.get(constants.LOGIN_USER_FIELD).type(email);
  cy.get(constants.LOGIN_PASSWORD_FIELD).type(password);

  if (slow) {
    // Wait for the login button to be enabled (Angular validates the form) rather than sleeping
    cy.get(constants.LOGIN_BUTTON).should("not.be.disabled");
  }

  // Ensure fields contain what has been entered
  cy.get(constants.LOGIN_USER_FIELD).should("have.value", email);
  cy.get(constants.LOGIN_PASSWORD_FIELD).should("have.value", password);
  cy.get(constants.LOGIN_BUTTON).click();

  cy.get(constants.COURSE_LIST).should("exist");
  cy.get(constants.COURSE_LIST_ID).should("exist");

  return cy.getUserName();
}

Cypress.Commands.add("slowLogin", (email, password) => {
  cy.log(`Slow login as ${email}`);
  return login(email, password, true);
});

Cypress.Commands.add("quickLogin", (email, password) => {
  cy.log(`Quick login as ${email}`);
  return login(email, password, false);
});

Cypress.Commands.add("logout", () => {
  cy.get("body").then(($body) => {
    if ($body.find("#fixed-icon").length > 0) {
      // Get out of video session page - ensure side menu is open so exit-icon is visible
      if ($body.find(constants.SESSION_EXIT_ICON).length === 0) {
        cy.get("#fixed-icon").click();
      }
      cy.get(constants.SESSION_EXIT_ICON, { timeout: 20000 }).should("exist");
      // Force-click bypasses any overlay that would intercept a native click
      cy.get(constants.SESSION_EXIT_ICON).click({ force: true });
    }
  });

  cy.get("body").then(($body) => {
    const loggedIn = $body.find(constants.MAIN_MENU_ARROW).length > 0 || $body.find("a.button-collapse").length > 0;
    if (!loggedIn) {
      cy.log("logout(): not logged in, nothing to do");
      return;
    }
    cy.window().then((win) => win.scrollTo(0, 0));
    cy.get("body").then(($b) => {
      if ($b.find(constants.MAIN_MENU_ARROW).length > 0) {
        cy.get(constants.MAIN_MENU_ARROW).click({ force: true });
        cy.get(constants.LOGOUT_BUTTON).click();
      } else {
        // Shrunk menu
        cy.get("a.button-collapse").click();
        cy.get("#nav-mobile a").contains("Logout").click();
      }
    });
  });
});

Cypress.Commands.add("openDialog", (target) => {
  if (typeof target === "string") {
    cy.log(`Opening dialog by clicking CSS '${target}'`);
    cy.get(target).should("be.visible").click();
  } else {
    cy.log("Opening dialog by web element");
    cy.wrap(target).click();
  }
  return cy.get(constants.MODAL_OVERLAY_OPENING, { timeout: 20000 }).should("exist");
});

Cypress.Commands.add("waitForDialogClosed", (dialogId, errorMessage) => {
  cy.log(`Waiting for dialog '${dialogId}' to close: ${errorMessage}`);
  cy.get(constants.modalClosedSelector(dialogId), { timeout: 20000 }).should("exist");
  cy.get(constants.MODAL_OPEN).should("not.exist");
  cy.get(constants.MODAL_OVERLAY).should("not.exist");
});

Cypress.Commands.add("getUserName", (options = {}) => {
  const goBack = options.goBack !== false;
  return cy.location("pathname").then((pathname) => {
    const notOnSettings = !pathname.endsWith("/settings");
    cy.get(constants.SETTINGS_BUTTON).should("be.visible");
    if (notOnSettings) {
      cy.get(constants.SETTINGS_BUTTON).click();
    }
    return cy
      .get(constants.USERNAME_FIELD)
      .should("be.visible")
      .invoke("text")
      .then((text) => {
        const userName = text.trim();
        if (goBack && notOnSettings) {
          cy.go("back");
        }
        return userName;
      });
  });
});
