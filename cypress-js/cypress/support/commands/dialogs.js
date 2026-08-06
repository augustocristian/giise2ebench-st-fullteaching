// Materialize modal helpers.

const { modal } = require("../selectors");

/** Clicks a CSS selector (or a wrapped element) and waits until the modal overlay is shown. */
Cypress.Commands.add("openDialog", (target) => {
  if (typeof target === "string") {
    cy.log(`Opening dialog by clicking CSS '${target}'`);
    cy.get(target).should("be.visible").click();
  } else {
    cy.log("Opening dialog by web element");
    cy.wrap(target).click();
  }
  return cy.get(modal.overlayOpening).should("exist");
});

/** Waits until the dialog with id `dialogId` is fully closed (animation finished). */
Cypress.Commands.add("waitForDialogClosed", (dialogId, errorMessage) => {
  cy.log(`Waiting for dialog '${dialogId}' to close: ${errorMessage}`);
  cy.get(modal.closed(dialogId)).should("exist");
  cy.get(modal.open).should("not.exist");
  cy.get(modal.overlay).should("not.exist");
});
