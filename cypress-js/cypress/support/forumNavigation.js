// Forum navigation commands, ported from common/ForumNavigationUtilities.java.
//
// `cy.isForumEnabled($content).should("eq", true)` below checks a value resolved once, not
// re-queried on each retry (unlike the `cy.get().should(callback)` pattern used for genuine
// wait-for-eventual-truth cases elsewhere) - that's intentional and matches the Java source,
// which likewise does a single assertTrue() at each of these call sites, relying on a
// preceding wait (go2Tab's tab-content visibility, or a modal-closed wait) to have already
// settled the DOM.

const constants = require("./constants");

Cypress.Commands.add("isForumEnabled", (forumTabContent) => {
  cy.log("Checking if the forum is enabled");
  return cy.wrap(forumTabContent).then(($content) => $content.find(constants.FORUM_NEW_ENTRY_ICON).length > 0);
});

Cypress.Commands.add("getFullEntryList", () => {
  cy.get(constants.FORUM_ICON).should("be.visible");
  return cy.getTabContent(constants.FORUM_ICON).then(($content) =>
    $content
      .find(constants.FORUM_ENTRY_ROW)
      .toArray()
      .map((entry) => Cypress.$(entry).find(constants.FORUM_ENTRY_LIST_ENTRY_TITLE).text().trim())
  );
});

Cypress.Commands.add("getUserEntries", (userName) => {
  return cy.getTabContent(constants.FORUM_ICON).then(($content) =>
    $content
      .find(constants.FORUM_ENTRY_ROW)
      .toArray()
      .filter((entry) => Cypress.$(entry).text().includes(userName))
      .map((entry) => Cypress.$(entry).find(constants.FORUM_ENTRY_LIST_ENTRY_TITLE).text().trim())
  );
});

// Yields the entry element with the given title, mirrors ForumNavigationUtilities.getEntry;
// retries until found.
Cypress.Commands.add("getEntry", (entryName) => {
  cy.log(`Getting the entry with title ${entryName}`);
  cy.get(constants.FORUM_ICON).should("be.visible");
  return cy
    .getTabContent(constants.FORUM_ICON)
    .should(($content) => {
      const titles = $content
        .find(constants.FORUM_ENTRY_ROW)
        .toArray()
        .map((entry) => Cypress.$(entry).find(constants.FORUM_ENTRY_LIST_ENTRY_TITLE).text().trim());
      expect(titles, `entry "${entryName}" to exist`).to.include(entryName);
    })
    .then(($content) => {
      const entry = $content
        .find(constants.FORUM_ENTRY_ROW)
        .toArray()
        .find((el) => Cypress.$(el).find(constants.FORUM_ENTRY_LIST_ENTRY_TITLE).text().trim() === entryName);
      return cy.wrap(entry);
    });
});

Cypress.Commands.add("getComments", () => {
  cy.log("Getting entry comments");
  cy.get(constants.FORUM_COMMENT_LIST_COMMENT, { timeout: 20000 }).should("have.length.greaterThan", 0);
  return cy.get(constants.FORUM_COMMENT_LIST_COMMENT);
});

Cypress.Commands.add("getUserComments", (userName) => {
  cy.getComments();
  return cy.get(constants.FORUM_COMMENT_LIST_COMMENT).then(($comments) =>
    $comments
      .toArray()
      .filter((c) => Cypress.$(c).find(constants.FORUM_COMMENT_LIST_COMMENT_USER).text().trim() === userName)
  );
});

Cypress.Commands.add("newEntry", (title, content) => {
  cy.log("Creating a new entry");
  cy.go2Tab(constants.FORUM_ICON);
  cy.getTabContent(constants.FORUM_ICON).then(($content) => {
    cy.isForumEnabled($content).should("eq", true);
  });
  cy.get(constants.FORUM_NEW_ENTRY_ICON).click();
  cy.get(constants.FORUM_NEW_ENTRY_MODAL).should("be.visible");

  cy.get(constants.FORUM_NEW_ENTRY_MODAL_TITLE).should("be.visible").type(title);
  cy.get(constants.FORUM_NEW_ENTRY_MODAL_CONTENT).should("be.visible").type(content);

  cy.log("Click the publish button");
  cy.get(constants.FORUM_NEW_ENTRY_MODAL_POST_BUTTON).click();

  cy.get(".entries-side-view").should("be.visible");
  cy.getEntry(title);
});

Cypress.Commands.add("getReplies", (commentEl) => {
  cy.log("Get all the replies of the selected comment");
  return cy.wrap(commentEl).then(($comment) => {
    const nested = $comment.find(constants.FORUM_COMMENT_LIST_COMMENT_DIV).toArray();
    // ignore first, it is the original comment
    return nested.slice(1);
  });
});

Cypress.Commands.add("enableForum", () => {
  cy.log("Checking that the forum is enable, click into the edit button");
  cy.get(constants.FORUM_EDIT_ENTRY_ICON).should("be.visible").click();
  cy.get(constants.ENABLE_FORUM_MODAL).should("be.visible");

  cy.log("Click the enable button");
  cy.get(constants.ENABLE_FORUM_MODAL).find(constants.ENABLE_FORUM_BUTTON).click();
  cy.get(constants.ENABLE_FORUM_MODAL).find(constants.ENABLE_FORUM_MODAL_SAVE_BUTTON).click();
  cy.get(constants.ENABLE_FORUM_MODAL).should("not.exist");

  cy.log("Checking that the forum is enabled");
  cy.getTabContent(constants.FORUM_ICON).then(($content) => {
    cy.isForumEnabled($content).should("eq", true);
  });
});

Cypress.Commands.add("disableForum", () => {
  cy.log("Checking that the forum is disabled, click into the edit button");
  cy.get(constants.FORUM_EDIT_ENTRY_ICON).should("be.visible").click();
  cy.get(constants.ENABLE_FORUM_MODAL).should("be.visible");

  cy.log("Click into the disable button");
  cy.get(constants.ENABLE_FORUM_MODAL).find(constants.DISABLE_FORUM_BUTTON).click();
  cy.get(constants.ENABLE_FORUM_MODAL).find(constants.ENABLE_FORUM_MODAL_SAVE_BUTTON).click();
  cy.get(constants.ENABLE_FORUM_MODAL).should("not.exist");

  cy.log("Finally checks that the Forum is disabled");
  cy.getTabContent(constants.FORUM_ICON).then(($content) => {
    cy.isForumEnabled($content).should("eq", false);
  });
});
