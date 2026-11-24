// Native <dialog> modal helpers.

const { modal } = require("../selectors");

/** Clicks a CSS selector (or a wrapped element) and waits until a dialog is shown. */
Cypress.Commands.add("openDialog", (target) => {
  if (typeof target === "string") {
    cy.log(`Opening dialog by clicking CSS '${target}'`);
    cy.get(target).should("be.visible").click();
  } else {
    cy.log("Opening dialog by web element");
    cy.wrap(target).click();
  }
  return cy.get(modal.open).should("exist");
});

/**
 * Waits until the dialog with id `dialogId` is closed (or gone: some dialogs are removed from the DOM,
 * for example the course edit dialog once there are no courses).
 */
Cypress.Commands.add("waitForDialogClosed", (dialogId, errorMessage) => {
  cy.log(`Waiting for dialog '${dialogId}' to close: ${errorMessage}`);
  cy.get(modal.openById(dialogId)).should("not.exist");
  cy.get(modal.open).should("not.exist");
});
