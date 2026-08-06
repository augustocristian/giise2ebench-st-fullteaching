// Ported from functional/test/LoggedForumTest.java.
const { getTestUsers } = require("../support/testData");
const constants = require("../support/constants");

function monthName(date) {
  return date.toLocaleString("en-US", { month: "long" });
}

function newEntryTitleFor(prefix, now) {
  return `${prefix} ${now.getDate()}${now.getMonth()}${now.getFullYear()}${now.getHours()}${now.getMinutes()}${now.getSeconds()}`;
}

function newEntryContentFor(now) {
  return (
    `This is the content written on the ${now.getDate()} of ${monthName(now)}, ` +
    `${now.getHours()}:${now.getMinutes()},${now.getSeconds()}`
  );
}

// Enters the shared FORUM_TEST_COURSE_NAME course and its Forum tab, asserting it's enabled.
function enterForumTestCourseForum() {
  cy.toCoursesHome();
  cy.getCourseByName(constants.FORUM_TEST_COURSE_NAME).find(constants.COURSE_LIST_COURSE_TITLE).click();
  cy.get(constants.TABS_DIV).should("be.visible");
  cy.go2Tab(constants.FORUM_ICON);
  cy.getTabContent(constants.FORUM_ICON).then(($content) => {
    cy.isForumEnabled($content).should("eq", true);
  });
}

// Yields the first forum entry, creating one first if the forum has none yet.
function firstEntryOrNew(prefix) {
  return cy.getFullEntryList().then((entries) => {
    if (entries.length === 0) {
      const now = new Date();
      const title = newEntryTitleFor(prefix, now);
      cy.newEntry(title, newEntryContentFor(now));
      return cy.getEntry(title);
    }
    return cy.getEntry(entries[0]);
  });
}

describe("Logged forum", () => {
  getTestUsers().forEach(({ mail, password, role }) => {
    // Logs in, walks every course's forum (if enabled) and its entries/comments.
    // Resources: loginservice(READONLY,10) openvidumock(NOACCESS,10) forum(READONLY,10)
    // executor/webbrowser/webserver(READWRITE,1).
    it(`loads forum entries across courses as ${role.toLowerCase()} (${mail})`, () => {
      let activatedForumOnSomeTest = false;
      let hasComments = false;

      cy.slowLogin(mail, password).then((userName) => {
        cy.getCoursesList()
          .should("have.length.greaterThan", 0)
          .then((courses) => {
            courses.forEach((courseName) => {
              cy.getCourseByName(courseName).find(constants.COURSE_LIST_COURSE_TITLE).click();
              cy.get(constants.TABS_DIV).should("be.visible");

              cy.go2Tab(constants.FORUM_ICON);
              cy.getTabContent(constants.FORUM_ICON).then(($content) => {
                cy.isForumEnabled($content).then((enabled) => {
                  if (!enabled) {
                    return; // forum not active on this course, go to next
                  }
                  activatedForumOnSomeTest = true;
                  cy.getFullEntryList().then((entries) => {
                    entries.forEach((entryName) => {
                      cy.getEntry(entryName).find(constants.FORUM_ENTRY_LIST_ENTRY_TITLE).click();
                      cy.get(constants.FORUM_COMMENT_LIST).should("be.visible");
                      cy.getComments().then(($comments) => {
                        if ($comments.length > 0) {
                          hasComments = true;
                          cy.getUserComments(userName);
                        }
                      });
                      cy.get(constants.BACK_TO_ENTRIES_LIST_ICON).parent().click();
                    });
                  });
                });
              });

              cy.get(constants.BACK_TO_DASHBOARD).click();
            });
          });
      });

      cy.then(() => {
        expect(
          activatedForumOnSomeTest && hasComments,
          "There isn't any forum that can be used to test this [Or not activated or no entry lists or not comments]"
        ).to.be.true;
      });
    });
  });

  getTestUsers().forEach(({ mail, password, role }) => {
    // Creates a new forum entry and checks it appears with the right author/title/content.
    // Resources: loginservice(READONLY,10) openvidumock(NOACCESS,10) forum(READWRITE,1,exclusive)
    // executor/webbrowser/webserver(READWRITE,1).
    it(`creates a new forum entry as ${role.toLowerCase()} (${mail})`, () => {
      const now = new Date();
      const newEntryTitle = newEntryTitleFor("New Entry Test", now);
      const newEntryContent = newEntryContentFor(now);

      cy.slowLogin(mail, password).then((userName) => {
        enterForumTestCourseForum();
        cy.newEntry(newEntryTitle, newEntryContent);

        cy.getEntry(newEntryTitle).then(($entry) => {
          cy.wrap($entry)
            .find(constants.FORUM_ENTRY_LIST_ENTRY_USER)
            .invoke("text")
            .should((text) => expect(text).to.eq(userName));
          cy.wrap($entry).find(constants.FORUM_ENTRY_LIST_ENTRY_TITLE).click();
        });

        cy.get(constants.FORUM_COMMENT_LIST).should("be.visible");
        cy.get(constants.FORUM_COMMENT_LIST_ENTRY_TITLE)
          .invoke("text")
          .should((text) => expect(text.split("\n")[0]).to.eq(newEntryTitle));
        cy.get(constants.FORUM_COMMENT_LIST_ENTRY_TITLE)
          .find(constants.FORUM_COMMENT_LIST_ENTRY_USER)
          .invoke("text")
          .should((text) => expect(text).to.eq(userName));

        cy.getComments().should("have.length.greaterThan", 0);
        cy.get(constants.FORUM_COMMENT_LIST_COMMENT)
          .first()
          .within(() => {
            cy.get(constants.FORUM_COMMENT_LIST_COMMENT_CONTENT)
              .invoke("text")
              .should((text) => expect(text).to.eq(newEntryContent));
            cy.get(constants.FORUM_COMMENT_LIST_COMMENT_USER)
              .invoke("text")
              .should((text) => expect(text).to.eq(userName));
          });
      });

      // Navigate to the main page first to avoid a flaky logout
      cy.visit("/");
    });
  });

  getTestUsers().forEach(({ mail, password, role }) => {
    // Adds a comment to the course forum's first entry (creating one first if none exist).
    // Resources: loginservice(READONLY,10) openvidumock(NOACCESS,10) forum(READWRITE,1,exclusive)
    // executor/webbrowser/webserver(READWRITE,1).
    it(`adds a new forum comment as ${role.toLowerCase()} (${mail})`, () => {
      cy.slowLogin(mail, password).then((userName) => {
        enterForumTestCourseForum();
        firstEntryOrNew("New Comment Test").then(($entry) => {
          cy.wrap($entry).find(constants.FORUM_ENTRY_LIST_ENTRY_TITLE).click();
        });

        cy.get(constants.FORUM_COMMENT_LIST).should("be.visible");
        cy.getComments()
          .its("length")
          .then((numberCommentsOld) => {
            cy.get(constants.FORUM_COMMENT_LIST).find(constants.FORUM_COMMENT_LIST_NEW_COMMENT_ICON).click();
            cy.get(constants.FORUM_NEW_COMMENT_MODAL).should("be.visible");

            const now = new Date();
            const newCommentContent =
              `COMMENT TEST${now.getDate()}${now.getMonth()}${now.getFullYear()}${now.getHours()}${now.getMinutes()}${now.getSeconds()}. ` +
              `This is the comment written on the ${now.getDate()} of ${monthName(now)}, ` +
              `${now.getHours()}:${now.getMinutes()},${now.getSeconds()}`;
            cy.get(constants.FORUM_NEW_COMMENT_MODAL_TEXT_FIELD).type(newCommentContent);
            cy.get(constants.FORUM_NEW_COMMENT_MODAL_POST_BUTTON).click();

            cy.get(constants.FORUM_COMMENT_LIST).should("be.visible");
            cy.get(constants.FORUM_COMMENT_LIST_COMMENT).should("have.length.greaterThan", numberCommentsOld);

            cy.get(constants.FORUM_COMMENT_LIST_COMMENT).should(($comments) => {
              const found = $comments
                .toArray()
                .some((c) => Cypress.$(c).find(constants.FORUM_COMMENT_LIST_COMMENT_CONTENT).text() === newCommentContent);
              expect(found, "Comment not found").to.be.true;
            });
            cy.get(constants.FORUM_COMMENT_LIST_COMMENT)
              .filter((_, c) => Cypress.$(c).find(constants.FORUM_COMMENT_LIST_COMMENT_CONTENT).text() === newCommentContent)
              .find(constants.FORUM_COMMENT_LIST_COMMENT_USER)
              .invoke("text")
              .should((text) => expect(text).to.eq(userName));
          });
      });
    });
  });

  getTestUsers().forEach(({ mail, password, role }) => {
    // Replies to the first comment of the course forum's first entry.
    // Resources: loginservice(READONLY,10) openvidumock(NOACCESS,10) forum(READWRITE,1,exclusive)
    // executor/webbrowser/webserver(READWRITE,1).
    it(`replies to a forum comment as ${role.toLowerCase()} (${mail})`, () => {
      cy.slowLogin(mail, password).then((userName) => {
        enterForumTestCourseForum();
        firstEntryOrNew("New Comment Test").then(($entry) => {
          cy.wrap($entry).find(constants.FORUM_ENTRY_LIST_ENTRY_TITLE).click();
        });

        cy.get(constants.FORUM_COMMENT_LIST).should("be.visible");
        cy.get(constants.FORUM_COMMENT_LIST_COMMENT)
          .first()
          .find(constants.FORUM_COMMENT_LIST_COMMENT_REPLY_ICON)
          .click();

        const now = new Date();
        const newReplyContent =
          `This is the reply written on the ${now.getDate()} of ${monthName(now)}, ` +
          `${now.getHours()}:${now.getMinutes()},${now.getSeconds()}`;
        cy.get(constants.FORUM_COMMENT_LIST_MODAL_NEW_REPLY).should("be.visible");
        cy.get(constants.FORUM_COMMENT_LIST_MODAL_NEW_REPLY_TEXT_FIELD).type(newReplyContent);
        cy.get(constants.FORUM_NEW_COMMENT_MODAL_POST_BUTTON).click();

        cy.get(constants.FORUM_COMMENT_LIST_MODAL_NEW_REPLY).should("not.exist");
        cy.get(constants.FORUM_COMMENT_LIST).should("be.visible");
        cy.get(constants.FORUM_COMMENT_LIST_COMMENT).should("have.length.greaterThan", 0);

        cy.get(constants.FORUM_COMMENT_LIST_COMMENT)
          .first()
          .then(($comment) => {
            cy.getReplies($comment).then((replies) => {
              const newReply = replies.find((el) => Cypress.$(el).text().includes(newReplyContent));
              expect(newReply, "Reply not found").to.not.be.undefined;
              cy.wrap(newReply)
                .find(constants.FORUM_COMMENT_LIST_COMMENT_USER)
                .invoke("text")
                .should((text) => expect(text).to.eq(userName));
            });
          });
      });
    });
  });
});
