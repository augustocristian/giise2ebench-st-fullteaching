// Ported from functional/test/teacher/CourseTeacherTest.java.
//
// Unlike the Java source, steps are not individually wrapped in try/catch + fail(label):
// Cypress's own command log and error output already pinpoint the failing step, so a manual
// per-step label adds noise rather than clarity (same call made in the Python port).
const { getTestTeachers } = require("../support/testData");
const constants = require("../support/constants");

function timestampedName(prefix) {
  return `${prefix}_${Date.now()}`;
}

describe("Teacher course main flow", () => {
  getTestTeachers().forEach(({ mail, password, role }) => {
    // Opens the first course and clicks through every tab.
    // Resources: loginservice(READONLY,10) openvidumock(NOACCESS,10) course(READONLY,15)
    // executor/webbrowser/webserver(READWRITE,1).
    it(`opens the first course and every tab as ${role.toLowerCase()} (${mail})`, () => {
      cy.slowLogin(mail, password);
      cy.toCoursesHome();
      cy.get(constants.COURSE_LIST).find("li").first().find(constants.COURSE_LIST_COURSE_TITLE).click();
      cy.get(constants.TABS_DIV).should("be.visible");

      [constants.HOME_ICON, constants.SESSION_ICON, constants.FORUM_ICON, constants.FILES_ICON, constants.ATTENDERS_ICON].forEach(
        (icon) => cy.go2Tab(icon)
      );
    });
  });
});

describe("Teacher create and delete course", () => {
  getTestTeachers().forEach(({ mail, password, role }) => {
    // Creates a course, confirms it exists, deletes it, confirms it's gone.
    // Resources: loginservice(READONLY,10) openvidumock(NOACCESS,10) course(DYNAMIC,15)
    // executor/webbrowser/webserver(READWRITE,1).
    it(`creates and deletes a course as ${role.toLowerCase()} (${mail})`, () => {
      cy.slowLogin(mail, password);
      const courseTitle = timestampedName("Test Course");

      cy.newCourse(courseTitle);
      cy.assertCourseExists(courseTitle);

      cy.deleteCourse(courseTitle);
      cy.assertCourseNotExists(courseTitle);

      cy.visit("/");
    });
  });
});

describe("Teacher edit course values", () => {
  getTestTeachers().forEach(({ mail, password, role }) => {
    // Renames a course and back, rewrites its rich-text description, toggles its forum, and
    // checks the current user shows up (highlighted) in its attenders list.
    // Resources: loginservice(READONLY,10) openvidumock(NOACCESS,10) configuration(READWRITE,1,exclusive)
    // executor/webbrowser/webserver(READWRITE,1).
    it(`edits course name/description/forum/attenders as ${role.toLowerCase()} (${mail})`, () => {
      cy.slowLogin(mail, password).then((userName) => {
        cy.toCoursesHome();

        cy.getCourseByName(constants.FORUM_TEST_COURSE_NAME)
          .find(constants.COURSE_TITLE)
          .invoke("text")
          .then((oldNameRaw) => {
            const oldName = oldNameRaw.trim();
            const editionName = timestampedName("EDITION TEST");

            cy.changeCourseName(oldName, editionName);
            cy.assertCourseExists(editionName, { timeout: 20000 });
            cy.changeCourseName(editionName, oldName);
            cy.assertCourseExists(oldName, { timeout: 20000 });
          });

        cy.getCourseByName(constants.FORUM_TEST_COURSE_NAME).find(constants.COURSE_LIST_COURSE_TITLE).click();
        cy.get(constants.TABS_DIV).should("be.visible");

        editHomeDescription();

        cy.go2Tab(constants.SESSION_ICON);
        // new/delete session are covered by rest-operations.cy.js's session test

        toggleForum();

        cy.get(constants.ATTENDERS_ICON).should("be.visible");
        cy.go2Tab(constants.ATTENDERS_ICON);
        cy.getTabContent(constants.ATTENDERS_ICON);
        cy.isUserInAttendersList(userName).should("eq", true);
        cy.getHighlightedAttender().should("eq", userName);

        // At the end of this test the header isn't reliably loaded; wait for it before finishing.
        cy.get(constants.MAIN_MENU_ARROW).should("be.visible");
      });
    });
  });
});

function editHomeDescription() {
  cy.go2Tab(constants.HOME_ICON);
  cy.get(constants.EDIT_DESCRIPTION_BUTTON).click();
  cy.get(constants.EDIT_DESCRIPTION_CONTENT_BOX).should("be.visible");

  cy.get(".ql-editor").click();
  cy.get(".ql-editor").type("{selectall}{backspace}");

  cy.get(".ql-header").click();
  cy.get(".ql-picker-options").should("be.visible");
  cy.get('.ql-picker-item[data-label="Heading"]').click();

  cy.get(".ql-editor").invoke(
    "html",
    "<h1>New Title</h1><h2>New SubHeading</h2><p>This is the normal content</p>"
  );
  cy.get("#textEditorRowButtons a").eq(1).click();

  cy.get(".ql-editor-custom").should("be.visible");
  assertDescriptionRendered("preview");

  cy.get(constants.EDIT_DESCRIPTION_SAVE_BUTTON).click();
  cy.get(".ql-editor-custom").should("be.visible");
  assertDescriptionRendered("saved");
}

function assertDescriptionRendered(phase) {
  cy.get(".ql-editor-custom h1")
    .invoke("text")
    .should((text) => expect(text, `Heading ${phase} not properly rendered`).to.eq("New Title"));
  cy.get(".ql-editor-custom h2")
    .invoke("text")
    .should((text) => expect(text, `Subheading ${phase} not properly rendered`).to.eq("New SubHeading"));
  cy.get(".ql-editor-custom p")
    .invoke("text")
    .should((text) => expect(text, `Normal ${phase} content not properly rendered`).to.eq("This is the normal content"));
}

function toggleForum() {
  cy.go2Tab(constants.FORUM_ICON);
  // $content is reused after enable/disableForum() mutate the DOM below (in the `else`
  // branch); this only works because the tab-content container itself is never replaced by
  // Angular, only its children - the same assumption CourseTeacherTest.java's Java version
  // relies on by reusing its `forum_tab_content` WebElement the same way.
  cy.getTabContent(constants.FORUM_ICON).then(($content) => {
    cy.isForumEnabled($content).then((enabled) => {
      if (enabled) {
        cy.wrap($content).find(constants.FORUM_NEW_ENTRY_ICON).should("exist");
        cy.wrap($content).find(constants.FORUM_EDIT_ENTRY_ICON).should("exist");
        cy.disableForum();
        cy.enableForum();
      } else {
        cy.enableForum();
        cy.wrap($content).find(constants.FORUM_NEW_ENTRY_ICON).should("exist");
        cy.wrap($content).find(constants.FORUM_EDIT_ENTRY_ICON).should("exist");
        cy.disableForum();
      }
    });
  });
}

describe("Teacher delete course", () => {
  getTestTeachers().forEach(({ mail, password, role }) => {
    // Creates a dummy course and deletes it, checking the course count drops by exactly one.
    // Resources: loginservice(READONLY,10) openvidumock(NOACCESS,10) course(READWRITE,1,exclusive)
    // executor/webbrowser/webserver(READWRITE,1).
    it(`deletes a freshly created course as ${role.toLowerCase()} (${mail})`, () => {
      cy.slowLogin(mail, password);
      cy.toCoursesHome();
      const courseName = timestampedName("Test Course");

      cy.newCourse(courseName);

      cy.get(".course-list-item")
        .its("length")
        .then((countBefore) => {
          cy.deleteCourse(courseName);
          cy.get(".course-list-item").should("have.length", countBefore - 1);
        });
    });
  });
});
