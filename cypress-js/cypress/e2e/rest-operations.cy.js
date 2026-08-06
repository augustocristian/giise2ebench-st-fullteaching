// Ported from functional/test/media/FullTeachingEndToEndRESTTests.java.
//
// Covers course/session/forum/file/attenders CRUD through the UI. Selectors here are inline
// strings rather than named constants, matching how the Java source keeps them local to this
// test class rather than in common/Constants.java.
const { getTestTeachers } = require("../support/testData");
const constants = require("../support/constants");

const COURSE_NAME = "TEST_COURSE";
const EDITED = " EDITED";
const TEST_COURSE_INFO = "TEST_COURSE_INFO";

function loginAndCreateNewCourse(mail, password) {
  cy.slowLogin(mail, password);
  cy.newCourse(COURSE_NAME);
}

function editCourse() {
  const editedCourseName = COURSE_NAME + EDITED;
  cy.get(".course-put-icon")
    .last()
    .then(($icon) => cy.openDialog($icon));
  cy.get("#input-put-course-name").should("be.visible").clear();
  cy.get("#input-put-course-name").type(editedCourseName);
  cy.get("#submit-put-course-btn").click();
  cy.waitForDialogClosed("put-delete-course-modal", "Edition of course failed");
  cy.get("#course-list .course-list-item:last-child div.course-title span")
    .invoke("text")
    .should((text) => expect(text).to.eq(editedCourseName));
}

function enterCourseAndNavigateTab(courseName, tabId) {
  // These tests always create a new course, so wait for 3 courses in the main page (more than 2)
  cy.get("#course-list .course-list-item div.course-title span").should("have.length.greaterThan", 2);
  cy.get("#course-list .course-list-item div.course-title span").then(($spans) => {
    const span = $spans.toArray().find((el) => Cypress.$(el).text().trim() === courseName);
    expect(span, `The course with the name '${courseName}' could not be found`).to.exist;
    cy.wrap(span).click();
  });
  cy.get("#main-course-title")
    .invoke("text")
    .should((text) => expect(text).to.eq(courseName));
  cy.get(`#${tabId}`).click();
}

describe("Course REST operations", () => {
  getTestTeachers().forEach(({ mail, password, role }) => {
    // Create -> edit -> delete a course through the REST-backed UI forms.
    // Resources: loginservice(READONLY,10) openvidumock(NOACCESS,10) configuration(READWRITE,1)
    // executor/webbrowser/webserver(READWRITE,1).
    it(`creates, edits and deletes a course as ${role.toLowerCase()} (${mail})`, () => {
      loginAndCreateNewCourse(mail, password);
      editCourse();
      cy.deleteCourse(COURSE_NAME + EDITED);
    });
  });
});

describe("Course info REST operations", () => {
  getTestTeachers().forEach(({ mail, password, role }) => {
    // Edits a course's Home-tab description and checks it renders back.
    // Resources: loginservice(READONLY,10) openvidumock(NOACCESS,10) information(READWRITE,1)
    // executor/webbrowser/webserver(READWRITE,1).
    it(`edits course info as ${role.toLowerCase()} (${mail})`, () => {
      loginAndCreateNewCourse(mail, password);
      enterCourseAndNavigateTab(COURSE_NAME, "info-tab-icon");

      cy.get(".md-tab-body.md-tab-active .card-panel.warning").should("be.visible");
      cy.get("#edit-course-info").click();
      cy.get(".ql-editor").type(TEST_COURSE_INFO);
      cy.get("#send-info-btn").click();

      cy.get(".ql-editor p")
        .invoke("text")
        .should((text) => expect(text).to.eq(TEST_COURSE_INFO));
      cy.deleteCourse(COURSE_NAME);
    });
  });
});

const DATE_FORMAT_OPTIONS = { month: "2-digit", day: "2-digit", year: "numeric" };

function formatDateChrome(date) {
  // MM/dd/yyyy, matching BROWSER_NAME === "chrome" branch of Java's fillSessionForm
  // (Cypress's Chromium-only, like pyppeteer's, so that's always the applicable branch here).
  return date.toLocaleDateString("en-US", DATE_FORMAT_OPTIONS);
}

function formatTimeChrome({ hour, minute }) {
  // hh:mmA/P, e.g. "03:10PM"
  let hours12 = hour % 12;
  if (hours12 === 0) hours12 = 12;
  const ampm = hour < 12 ? "AM" : "PM";
  return `${String(hours12).padStart(2, "0")}:${String(minute).padStart(2, "0")}${ampm}`;
}

function fillSessionForm(title, comment, date, time, edit) {
  const titleField = edit ? "#input-put-title" : "#input-post-title";
  const commentField = edit ? "#input-put-comment" : "#input-post-comment";
  const dateField = edit ? "#input-put-date" : "#input-post-date";
  const timeField = edit ? "#input-put-time" : "#input-post-time";
  if (edit) {
    cy.get(titleField).clear();
    cy.get(commentField).clear();
  }
  cy.get(titleField).type(title);
  cy.get(commentField).type(comment);
  cy.get(dateField).type(formatDateChrome(date));
  cy.get(timeField).type(formatTimeChrome(time));
  cy.get(edit ? "#put-modal-btn" : "#post-modal-btn").click();
}

function verifySessionDetails(expectedTitle, expectedComment, ...expectedDateTimes) {
  cy.get("li.session-data .session-title")
    .invoke("text")
    .should((text) => expect(text).to.eq(expectedTitle));
  cy.get("li.session-data .session-description")
    .invoke("text")
    .should((text) => expect(text).to.eq(expectedComment));
  cy.get("li.session-data .session-datetime")
    .invoke("text")
    .should((text) => expect(expectedDateTimes).to.include(text));
}

describe("Session REST operations", () => {
  getTestTeachers().forEach(({ mail, password, role }) => {
    // Create -> edit -> delete a video session through the REST-backed UI forms.
    // Resources: loginservice(READONLY,10) openvidumock(NOACCESS,10) session(READWRITE,1)
    // executor/webbrowser/webserver(READWRITE,1).
    it(`creates, edits and deletes a session as ${role.toLowerCase()} (${mail})`, () => {
      loginAndCreateNewCourse(mail, password);
      enterCourseAndNavigateTab(COURSE_NAME, "sessions-tab-icon");

      cy.openDialog("#add-session-icon");
      fillSessionForm(
        "TEST LESSON NAME",
        "TEST LESSON COMMENT",
        new Date(2018, 2, 1),
        { hour: 15, minute: 10 },
        false
      );
      cy.waitForDialogClosed("course-details-modal", "Addition of session failed");
      verifySessionDetails("TEST LESSON NAME", "TEST LESSON COMMENT", "Jan 3, 2018 - 03:10", "Mar 1, 2018 - 15:10");

      cy.openDialog(".edit-session-icon");
      fillSessionForm(
        "TEST LESSON NAME EDITED",
        "TEST LESSON COMMENT EDITED",
        new Date(2019, 3, 2),
        { hour: 5, minute: 10 },
        true
      );
      cy.waitForDialogClosed("put-delete-modal", "Edition of session failed");
      verifySessionDetails("TEST LESSON NAME EDITED", "TEST LESSON COMMENT EDITED", "Feb 4, 2019 - 05:10", "Apr 2, 2019 - 05:10");

      cy.openDialog(".edit-session-icon");
      cy.get("#label-delete-checkbox").click();
      cy.get("#delete-session-btn").click();
      cy.waitForDialogClosed("put-delete-modal", "Deletion of session failed");
      cy.get("li.session-data").should("not.exist");

      cy.deleteCourse(COURSE_NAME);
    });
  });
});

describe("Forum REST operations", () => {
  getTestTeachers().forEach(({ mail, password, role }) => {
    // Add a forum entry, comment on it, reply to that comment, then deactivate the forum.
    // Resources: loginservice(READONLY,10) openvidumock(NOACCESS,10) forum(READWRITE,1)
    // executor/webbrowser/webserver(READWRITE,1).
    it(`adds/replies to/deactivates a forum entry as ${role.toLowerCase()} (${mail})`, () => {
      loginAndCreateNewCourse(mail, password);
      enterCourseAndNavigateTab(COURSE_NAME, "forum-tab-icon");

      const title = "TEST FORUM ENTRY";
      const comment = "TEST FORUM COMMENT";
      const entryDate = "a few seconds ago";
      cy.openDialog("#add-entry-icon");
      cy.get("#input-post-title").type(title);
      cy.get("#input-post-comment").type(comment);
      cy.get("#post-modal-btn").click();
      cy.waitForDialogClosed("course-details-modal", "Addition of entry failed");

      cy.get("li.entry-title .forum-entry-title")
        .invoke("text")
        .should((text) => expect(text).to.eq(title));
      cy.get("li.entry-title .forum-entry-author")
        .invoke("text")
        .should((text) => expect(text).to.eq(constants.TEACHER_NAME));
      cy.get("li.entry-title .forum-entry-date")
        .invoke("text")
        .should((text) => expect(text).to.eq(entryDate));

      cy.get("li.entry-title").click();
      cy.get(".comment-block > app-comment:first-child > div.comment-div .message-itself")
        .invoke("text")
        .should((text) => expect(text).to.eq(comment));
      cy.get(".comment-block > app-comment:first-child > div.comment-div .forum-comment-author")
        .invoke("text")
        .should((text) => expect(text).to.eq(constants.TEACHER_NAME));

      const reply = "TEST FORUM REPLY";
      cy.openDialog(".replay-icon");
      cy.get("#input-post-comment").type(reply);
      cy.get("#post-modal-btn").click();
      cy.waitForDialogClosed("course-details-modal", "Addition of entry reply failed");
      cy.get(".comment-block > app-comment:first-child > div.comment-div div.comment-div .message-itself")
        .invoke("text")
        .should((text) => expect(text).to.eq(reply));
      cy.get(".comment-block > app-comment:first-child > div.comment-div div.comment-div .forum-comment-author")
        .invoke("text")
        .should((text) => expect(text).to.eq(constants.TEACHER_NAME));

      cy.get("#entries-sml-btn").click();
      cy.openDialog("#edit-forum-icon");
      cy.get("#label-forum-checkbox").click();
      cy.get("#put-modal-btn").click();
      cy.waitForDialogClosed("put-delete-modal", "Deactivation of forum failed");
      cy.get("app-error-message .card-panel.warning").should("be.visible");

      cy.deleteCourse(COURSE_NAME);
    });
  });
});

describe("Files REST operations", () => {
  getTestTeachers().forEach(({ mail, password, role }) => {
    // Add a file group, a sub-group and a file to it, edit their names, then delete the group.
    // Resources: loginservice(READONLY,10) openvidumock(NOACCESS,10) files(READWRITE,1)
    // executor/webbrowser/webserver(READWRITE,1).
    it(`adds, edits and deletes files as ${role.toLowerCase()} (${mail})`, () => {
      loginAndCreateNewCourse(mail, password);
      enterCourseAndNavigateTab(COURSE_NAME, "files-tab-icon");

      cy.get("app-error-message .card-panel.warning").should("be.visible");

      const fileGroup = "TEST FILE GROUP";
      cy.openDialog("#add-files-icon");
      cy.get("#input-post-title").type(fileGroup);
      cy.get("#post-modal-btn").click();
      cy.waitForDialogClosed("course-details-modal", "Addition of file group failed");
      cy.get(".file-group-title h5")
        .invoke("text")
        .should((text) => expect(text).to.eq(fileGroup));

      cy.openDialog("#edit-filegroup-icon");
      cy.get("#input-file-title").clear();
      cy.get("#input-file-title").type(fileGroup + EDITED);
      cy.get("#put-modal-btn").click();
      cy.waitForDialogClosed("put-delete-modal", "Edition of file group failed");
      cy.get("app-file-group .file-group-title h5")
        .invoke("text")
        .should((text) => expect(text).to.eq(fileGroup + EDITED));

      const fileSubGroup = "TEST FILE SUBGROUP";
      cy.openDialog(".add-subgroup-btn");
      cy.get("#input-post-title").type(fileSubGroup);
      cy.get("#post-modal-btn").click();
      cy.waitForDialogClosed("course-details-modal", "Addition of file sub-group failed");
      cy.get("app-file-group app-file-group .file-group-title h5")
        .invoke("text")
        .should((text) => expect(text).to.eq(fileSubGroup));

      cy.openDialog("app-file-group app-file-group .add-file-btn");
      const fileName = "testFile.txt";
      cy.get(".input-file-uploader").selectFile("cypress/fixtures/testFile.txt", { force: true });
      cy.get("#upload-all-btn").click();
      cy.get(".determinate[style*='width: 100']", { timeout: 20000 }).should("exist");
      cy.get("i[class*='icon-status-upload']")
        .invoke("text")
        .should((text) => expect(text).to.eq("done"));

      cy.get("#close-upload-modal-btn").click();
      cy.waitForDialogClosed("course-details-modal", "Upload of file failed");
      cy.get("app-file-group app-file-group .chip .file-name-div")
        .invoke("text")
        .should((text) => expect(text).to.eq(fileName));

      cy.openDialog("app-file-group app-file-group .edit-file-name-icon");
      const editedFileName = "testFileEDITED.txt";
      cy.get("#input-file-title").clear();
      cy.get("#input-file-title").type(editedFileName);
      cy.get("#put-modal-btn").click();
      cy.waitForDialogClosed("put-delete-modal", "Edition of file failed");
      cy.get("app-file-group app-file-group .chip .file-name-div")
        .invoke("text")
        .should((text) => expect(text).to.eq(editedFileName));

      cy.get("app-file-group .delete-filegroup-icon").click();
      cy.get("app-error-message .card-panel.warning").should("be.visible");

      cy.deleteCourse(COURSE_NAME);
    });
  });
});

describe("Attenders REST operations", () => {
  getTestTeachers().forEach(({ mail, password, role }) => {
    // Fails to add an unregistered attender, adds a real one, then removes them.
    // Resources: loginservice(READONLY,10) openvidumock(NOACCESS,10) attenders(READWRITE,1)
    // executor/webbrowser/webserver(READWRITE,1).
    it(`adds and removes an attender as ${role.toLowerCase()} (${mail})`, () => {
      loginAndCreateNewCourse(mail, password);
      enterCourseAndNavigateTab(COURSE_NAME, "attenders-tab-icon");

      cy.get(".attender-row-div").should("have.length", 1);
      cy.get(".attender-row-div .attender-name-p")
        .invoke("text")
        .should((text) => expect(text).to.eq(constants.TEACHER_NAME));

      // Add attender fail
      cy.openDialog("#add-attenders-icon");
      cy.get("#input-attender-simple").type("studentFail@gmail.com");
      cy.get("#put-modal-btn").click();
      cy.waitForDialogClosed("put-delete-modal", "Addition of attender fail");
      cy.get("app-error-message .card-panel.fail").should("be.visible");
      cy.get(".attender-row-div").should("have.length", 1);
      cy.get("app-error-message .card-panel.fail .material-icons").click();

      // Add attender success
      cy.openDialog("#add-attenders-icon");
      cy.get("#input-attender-simple").type("student1@gmail.com");
      cy.get("#put-modal-btn").click();
      cy.waitForDialogClosed("put-delete-modal", "Addition of attender failed");
      cy.get("app-error-message .card-panel.correct").should("be.visible");
      cy.get(".attender-row-div").should("have.length", 2);
      cy.get("app-error-message .card-panel.correct .material-icons").click();

      // Remove attender
      cy.get("#edit-attenders-icon").click();
      cy.get(".del-attender-icon").click();
      cy.get(".attender-row-div").should("have.length", 1);

      cy.deleteCourse(COURSE_NAME);
    });
  });
});
