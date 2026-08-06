// Forum commands.
//
// Note: cy.isForumEnabled() resolves once from the given tab content (not re-queried), like
// the single assertTrue() in the Java source; callers rely on a preceding wait (go2Tab or a
// modal-closed wait) for the DOM to be settled.

const { forum, tabs } = require("../selectors");
const { rowTitles, getRowByTitle } = require("../helpers");

const forumTab = () => cy.getTabContent(tabs.forumIcon);

/** Yields true/false: does the (already resolved) forum tab content show the "new entry" icon. */
Cypress.Commands.add("isForumEnabled", (forumTabContent) => {
  return cy.wrap(forumTabContent).then(($content) => $content.find(forum.newEntryIcon).length > 0);
});

/** Yields the titles of all forum entries. */
Cypress.Commands.add("getFullEntryList", () => {
  cy.get(tabs.forumIcon).should("be.visible");
  return forumTab().then(($content) => rowTitles($content, forum.entryRow, forum.entryTitle));
});

/** Yields the titles of the entries whose row mentions `userName`. */
Cypress.Commands.add("getUserEntries", (userName) => {
  return forumTab().then(($content) =>
    $content
      .find(forum.entryRow)
      .toArray()
      .filter((row) => Cypress.$(row).text().includes(userName))
      .map((row) => Cypress.$(row).find(forum.entryTitle).text().trim())
  );
});

/** Yields the entry row titled `entryName`; retries until found. */
Cypress.Commands.add("getEntry", (entryName) => {
  cy.get(tabs.forumIcon).should("be.visible");
  return getRowByTitle(forumTab, forum.entryRow, forum.entryTitle, entryName, "entry");
});

/** Yields all comment blocks of the open entry (waits for at least one). */
Cypress.Commands.add("getComments", () => {
  cy.get(forum.comment).should("have.length.greaterThan", 0);
  return cy.get(forum.comment);
});

/** Yields (as an array of elements) the comments authored by `userName`. */
Cypress.Commands.add("getUserComments", (userName) => {
  return cy
    .getComments()
    .then(($comments) =>
      $comments.toArray().filter((c) => Cypress.$(c).find(forum.commentUser).first().text().trim() === userName)
    );
});

/** Yields (as an array of elements) the replies of a comment, excluding the comment itself. */
Cypress.Commands.add("getReplies", (commentEl) => {
  return cy.wrap(commentEl).then(($comment) => $comment.find(forum.commentDiv).toArray().slice(1));
});

/** Creates a forum entry and waits for it to be listed. */
Cypress.Commands.add("newEntry", (title, content) => {
  cy.go2Tab(tabs.forumIcon);
  forumTab().then(($content) => {
    cy.isForumEnabled($content).should("eq", true);
  });
  cy.get(forum.newEntryIcon).click();
  cy.get(forum.newEntryModal.root).should("be.visible");
  cy.get(forum.newEntryModal.title).should("be.visible").type(title, { force: true });
  cy.get(forum.newEntryModal.content).should("be.visible").type(content, { force: true });
  cy.get(forum.newEntryModal.postButton).click();

  cy.get(forum.entriesSideView).should("be.visible");
  cy.getEntry(title);
});

// Opens the forum edit modal, ticks the (shared) toggle checkbox and saves.
function toggleForum() {
  cy.get(forum.editIcon).should("be.visible").click();
  cy.get(forum.toggleModal).should("be.visible");
  cy.get(forum.toggleModal).find(forum.toggleCheckbox).click();
  cy.get(forum.toggleModal).find(forum.toggleSave).click();
  cy.get(forum.toggleModal).should("not.be.visible");
}

/** Enables the forum of the current course and asserts it is enabled. */
Cypress.Commands.add("enableForum", () => {
  toggleForum();
  forumTab().then(($content) => {
    cy.isForumEnabled($content).should("eq", true);
  });
});

/** Disables the forum of the current course and asserts it is disabled. */
Cypress.Commands.add("disableForum", () => {
  toggleForum();
  forumTab().then(($content) => {
    cy.isForumEnabled($content).should("eq", false);
  });
});
