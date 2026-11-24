// Steps are not wrapped in try/catch + fail(label) as in Java: Cypress's command log already
// pinpoints the failing step.
const { getTestTeachers } = require("../support/testData");
const constants = require("../support/constants");

const COURSE_TABS = [
  constants.HOME_ICON,
  constants.SESSION_ICON,
  constants.FORUM_ICON,
  constants.FILES_ICON,
  constants.ATTENDERS_ICON,
];
const RENAME_TIMEOUT_MS = 20000;
const COURSE_ITEM = ".course-list-item";
const DESCRIPTION_VIEW = ".ql-editor-custom";
// The rendered description also carries the ql-editor class; the editable one is the other.
const QUILL_EDITOR = ".ql-editor:not(.ql-editor-custom)";

// Timestamp keeps names unique across runs sharing the same SUT.
function timestampedName(prefix) {
  return `${prefix}_${Date.now()}`;
}

function openCourse(courseName) {
  cy.getCourseByName(courseName).find(constants.COURSE_LIST_COURSE_TITLE).click();
  cy.get(constants.TABS_DIV).should("be.visible");
}

function assertDescriptionRendered(phase) {
  const expectedByTag = {
    h1: ["Heading", "New Title"],
    h2: ["Subheading", "New SubHeading"],
    p: ["Normal content", "This is the normal content"],
  };
  Object.entries(expectedByTag).forEach(([tag, [label, expected]]) => {
    // Every rendering of the description (preview and saved view) must show the text.
    cy.get(`${DESCRIPTION_VIEW} ${tag}`).should(($els) => {
      $els.each((_, el) => {
        // Quill renders spaces as non-breaking ones.
        const text = el.textContent.replaceAll("\u00a0", " ");
        expect(text, `${label} ${phase} not properly rendered`).to.eq(expected);
      });
    });
  });
}

function rewriteHomeDescription() {
  cy.go2Tab(constants.HOME_ICON);
  cy.get(constants.EDIT_DESCRIPTION_BUTTON).click();
  cy.get(constants.EDIT_DESCRIPTION_CONTENT_BOX).should("be.visible");

  cy.get(QUILL_EDITOR).click();
  cy.get(QUILL_EDITOR).type("{selectall}{backspace}");

  cy.get(".ql-picker.ql-header").click();
  cy.get(".ql-picker-options").should("be.visible");
  cy.get('.ql-picker-item[data-label="Heading"]').click();

  // Injected as HTML because typing formatted rich text through the Quill toolbar is flaky.
  cy.get(QUILL_EDITOR).invoke("html", "<h1>New Title</h1><h2>New SubHeading</h2><p>This is the normal content</p>");
  // The preview toggle is the only floated (left) control of the editor's button row.
  cy.get("#textEditorRowButtons .left").click();

  cy.get(DESCRIPTION_VIEW).should("be.visible");
  assertDescriptionRendered("preview");

  cy.get(constants.EDIT_DESCRIPTION_SAVE_BUTTON).click();
  cy.get(DESCRIPTION_VIEW).should("be.visible");
  assertDescriptionRendered("saved");
}

function assertForumControlsExist($content) {
  cy.wrap($content).find(constants.FORUM_NEW_ENTRY_ICON).should("exist");
  cy.wrap($content).find(constants.FORUM_EDIT_ENTRY_ICON).should("exist");
}

// Leaves the forum in its original state: whichever way it starts, it is toggled and restored.
// $content stays valid across the toggles because Angular replaces only its children.
function toggleForum() {
  cy.go2Tab(constants.FORUM_ICON);
  cy.getTabContent(constants.FORUM_ICON).then(($content) => {
    cy.isForumEnabled($content).then((enabled) => {
      if (enabled) {
        assertForumControlsExist($content);
        cy.disableForum();
        cy.enableForum();
      } else {
        cy.enableForum();
        assertForumControlsExist($content);
        cy.disableForum();
      }
    });
  });
}

describe("Teacher course main flow", () => {
  getTestTeachers().forEach(({ mail, password, role }) => {
    describe(`as ${role.toLowerCase()} (${mail})`, () => {
      beforeEach(() => {
        cy.login(mail, password).as("userName");
        cy.toCoursesHome();
      });

      // Resources: loginservice(READONLY,10) openvidumock(NOACCESS,10) course(READONLY,15)
      it("opens the first course and every tab", () => {
        cy.get(constants.COURSE_LIST).find("li").first().find(constants.COURSE_LIST_COURSE_TITLE).click();
        cy.get(constants.TABS_DIV).should("be.visible");

        COURSE_TABS.forEach((icon) => cy.go2Tab(icon));
      });

      // Resources: loginservice(READONLY,10) openvidumock(NOACCESS,10) course(DYNAMIC,15)
      it("creates and deletes a course", () => {
        const courseTitle = timestampedName("Test Course");

        cy.newCourse(courseTitle);
        cy.assertCourseExists(courseTitle);

        cy.deleteCourse(courseTitle);
        cy.assertCourseNotExists(courseTitle);
      });

      // Resources: loginservice(READONLY,10) openvidumock(NOACCESS,10) course(READWRITE,1,exclusive)
      it("decreases the course count by one when deleting a freshly created course", () => {
        const courseName = timestampedName("Test Course");
        cy.newCourse(courseName);

        cy.get(COURSE_ITEM)
          .its("length")
          .then((countBefore) => {
            cy.deleteCourse(courseName);
            cy.get(COURSE_ITEM).should("have.length", countBefore - 1);
          });
      });

      // These tests edit the shared forum-test course and need exclusive access to it:
      // configuration(READWRITE,1,exclusive).
      describe("editing the forum test course", () => {
        it("renames the course and restores its original name", () => {
          const editionName = timestampedName("EDITION TEST");

          cy.getCourseByName(constants.FORUM_TEST_COURSE_NAME)
            .find(constants.COURSE_TITLE)
            .invoke("text")
            .then((text) => {
              const oldName = text.trim();

              cy.changeCourseName(oldName, editionName);
              cy.assertCourseExists(editionName, { timeout: RENAME_TIMEOUT_MS });
              cy.changeCourseName(editionName, oldName);
              cy.assertCourseExists(oldName, { timeout: RENAME_TIMEOUT_MS });
            });
        });

        it("rewrites the rich-text description", () => {
          openCourse(constants.FORUM_TEST_COURSE_NAME);
          rewriteHomeDescription();
        });

        it("toggles the forum off and on", () => {
          openCourse(constants.FORUM_TEST_COURSE_NAME);
          toggleForum();
        });

        it("lists the current user, highlighted, among the attenders", function () {
          openCourse(constants.FORUM_TEST_COURSE_NAME);
          cy.go2Tab(constants.ATTENDERS_ICON);
          cy.getTabContent(constants.ATTENDERS_ICON);
          cy.isUserInAttendersList(this.userName).should("eq", true);
          cy.getHighlightedAttender().should("eq", this.userName);
        });
      });
    });
  });
});
