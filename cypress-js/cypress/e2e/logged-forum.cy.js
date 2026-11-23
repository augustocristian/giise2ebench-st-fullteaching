const { getTestUsers } = require("../support/testData");
const constants = require("../support/constants");

const ENTRY_TITLE = constants.FORUM_ENTRY_LIST_ENTRY_TITLE;
const COMMENT = constants.FORUM_COMMENT_LIST_COMMENT;

// Compact timestamp that makes titles unique across runs
function stamp(now) {
  return `${now.getDate()}${now.getMonth()}${now.getFullYear()}${now.getHours()}${now.getMinutes()}${now.getSeconds()}`;
}

// e.g. "This is the reply written on the 3 of May, 10:5,7"
function writtenOn(kind, now) {
  const month = now.toLocaleString("en-US", { month: "long" });
  return `This is the ${kind} written on the ${now.getDate()} of ${month}, ${now.getHours()}:${now.getMinutes()},${now.getSeconds()}`;
}

function createEntry(prefix) {
  const now = new Date();
  const title = `${prefix} ${stamp(now)}`;
  const content = writtenOn("content", now);
  cy.newEntry(title, content);
  return { title, content };
}

function enterForumTestCourseForum() {
  cy.toCoursesHome();
  cy.getCourseByName(constants.FORUM_TEST_COURSE_NAME).find(constants.COURSE_LIST_COURSE_TITLE).click();
  cy.get(constants.TABS_DIV).should("be.visible");
  cy.go2Tab(constants.FORUM_ICON);
  cy.getTabContent(constants.FORUM_ICON).then(($content) => {
    cy.isForumEnabled($content).should("eq", true);
  });
}

// Opens the first forum entry, creating one first if the forum has none yet.
function openFirstEntryOrNew(prefix) {
  cy.getFullEntryList().then((entries) => {
    const entryName = entries.length === 0 ? createEntry(prefix).title : entries[0];
    cy.getEntry(entryName).find(ENTRY_TITLE).click();
  });
  cy.get(constants.FORUM_COMMENT_LIST).should("be.visible");
}

function commentsWithContent(content) {
  return cy
    .get(COMMENT)
    .filter((_, c) => Cypress.$(c).find(constants.FORUM_COMMENT_LIST_COMMENT_CONTENT).text() === content);
}

describe("Logged forum", () => {
  getTestUsers().forEach(({ mail, password, role }) => {
    // Resources: loginservice(READONLY,10) openvidumock(NOACCESS,10) forum(READONLY,10)
    // executor/webbrowser/webserver(READWRITE,1).
    it(`loads forum entries across courses as ${role.toLowerCase()} (${mail})`, () => {
      let activatedForumOnSomeCourse = false;
      let hasComments = false;

      cy.login(mail, password).then((userName) => {
        cy.getCoursesList()
          .should("have.length.greaterThan", 0)
          .then((courses) => {
            courses.forEach((courseName) => {
              cy.getCourseByName(courseName).find(constants.COURSE_LIST_COURSE_TITLE).click();
              cy.get(constants.TABS_DIV).should("be.visible");

              cy.go2Tab(constants.FORUM_ICON);
              cy.getTabContent(constants.FORUM_ICON).then(($content) => {
                cy.isForumEnabled($content).then((enabled) => {
                  if (!enabled) return;
                  activatedForumOnSomeCourse = true;
                  cy.getFullEntryList().then((entries) => {
                    entries.forEach((entryName) => {
                      cy.getEntry(entryName).find(ENTRY_TITLE).click();
                      cy.get(constants.FORUM_COMMENT_LIST).should("be.visible");
                      cy.getComments().then(($comments) => {
                        if ($comments.length > 0) {
                          hasComments = true;
                          cy.getUserComments(userName);
                        }
                      });
                      cy.get(constants.BACK_TO_ENTRIES_LIST_ICON).click();
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
          activatedForumOnSomeCourse && hasComments,
          "No usable forum found: it must be activated and have entries with comments"
        ).to.be.true;
      });
    });
  });

  getTestUsers().forEach(({ mail, password, role }) => {
    // Resources: loginservice(READONLY,10) openvidumock(NOACCESS,10) forum(READWRITE,1,exclusive)
    // executor/webbrowser/webserver(READWRITE,1).
    it(`creates a new forum entry as ${role.toLowerCase()} (${mail})`, () => {
      cy.login(mail, password).then((userName) => {
        enterForumTestCourseForum();
        const { title, content } = createEntry("New Entry Test");

        cy.getEntry(title).then(($entry) => {
          cy.wrap($entry).find(constants.FORUM_ENTRY_LIST_ENTRY_USER).should("have.text", userName);
          cy.wrap($entry).find(ENTRY_TITLE).click();
        });

        cy.get(constants.FORUM_COMMENT_LIST).should("be.visible");
        // The title is the first cell; the second one holds author and date.
        cy.get(constants.FORUM_COMMENT_LIST_ENTRY_TITLE).children().first().should("have.text", title);
        cy.get(constants.FORUM_COMMENT_LIST_ENTRY_TITLE)
          .find(constants.FORUM_COMMENT_LIST_ENTRY_USER)
          .first()
          .should("have.text", userName);

        cy.getComments().should("have.length.greaterThan", 0);
        cy.get(COMMENT)
          .first()
          .within(() => {
            cy.get(constants.FORUM_COMMENT_LIST_COMMENT_CONTENT).should("have.text", content);
            cy.get(constants.FORUM_COMMENT_LIST_COMMENT_USER).should("have.text", userName);
          });
      });

      // Navigate to the main page first to avoid a flaky logout
      cy.visit("/");
    });
  });

  getTestUsers().forEach(({ mail, password, role }) => {
    // Resources: loginservice(READONLY,10) openvidumock(NOACCESS,10) forum(READWRITE,1,exclusive)
    // executor/webbrowser/webserver(READWRITE,1).
    it(`adds a new forum comment as ${role.toLowerCase()} (${mail})`, () => {
      cy.login(mail, password).then((userName) => {
        enterForumTestCourseForum();
        openFirstEntryOrNew("New Comment Test");

        cy.getComments()
          .its("length")
          .then((numberCommentsOld) => {
            // First icon = text comment; the second one records a video comment.
            cy.get(constants.FORUM_COMMENT_LIST).find(constants.FORUM_COMMENT_LIST_NEW_COMMENT_ICON).first().click();
            cy.get(constants.FORUM_NEW_COMMENT_MODAL).should("be.visible");

            const now = new Date();
            const newCommentContent = `COMMENT TEST${stamp(now)}. ${writtenOn("comment", now)}`;
            cy.get(constants.FORUM_NEW_COMMENT_MODAL_TEXT_FIELD).type(newCommentContent, { force: true });
            cy.get(constants.FORUM_NEW_COMMENT_MODAL_POST_BUTTON).click();

            cy.get(constants.FORUM_COMMENT_LIST).should("be.visible");
            cy.get(COMMENT).should("have.length.greaterThan", numberCommentsOld);
            commentsWithContent(newCommentContent).should("have.length", 1);
            commentsWithContent(newCommentContent)
              .find(constants.FORUM_COMMENT_LIST_COMMENT_USER)
              .should("have.text", userName);
          });
      });
    });
  });

  getTestUsers().forEach(({ mail, password, role }) => {
    // Resources: loginservice(READONLY,10) openvidumock(NOACCESS,10) forum(READWRITE,1,exclusive)
    // executor/webbrowser/webserver(READWRITE,1).
    it(`replies to a forum comment as ${role.toLowerCase()} (${mail})`, () => {
      cy.login(mail, password).then((userName) => {
        enterForumTestCourseForum();
        openFirstEntryOrNew("New Comment Test");

        cy.get(COMMENT).first().find(constants.FORUM_COMMENT_LIST_COMMENT_REPLY_ICON).first().click();

        const newReplyContent = writtenOn("reply", new Date());
        cy.get(constants.FORUM_COMMENT_LIST_MODAL_NEW_REPLY).should("be.visible");
        cy.get(constants.FORUM_COMMENT_LIST_MODAL_NEW_REPLY_TEXT_FIELD).type(newReplyContent, { force: true });
        cy.get(constants.FORUM_NEW_COMMENT_MODAL_POST_BUTTON).click();

        cy.get(constants.FORUM_COMMENT_LIST_MODAL_NEW_REPLY).should("not.be.visible");
        cy.get(constants.FORUM_COMMENT_LIST).should("be.visible");

        cy.get(COMMENT)
          .first()
          .then(($comment) => {
            cy.getReplies($comment).then((replies) => {
              // Cypress yields the array of elements as a jQuery object.
              const newReply = Array.from(replies).find((el) => Cypress.$(el).text().includes(newReplyContent));
              expect(newReply, "Reply not found").to.not.be.undefined;
              cy.wrap(newReply).find(constants.FORUM_COMMENT_LIST_COMMENT_USER).should("have.text", userName);
            });
          });
      });
    });
  });
});
