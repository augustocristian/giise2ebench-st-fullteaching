// Covers course/session/forum/file/attenders CRUD through the REST-backed UI forms. Selectors are
// local strings, as in the Java class, rather than shared constants.
const { getTestTeachers } = require("../support/testData");
const constants = require("../support/constants");

const COURSE_NAME = "TEST_COURSE";
const EDITED = " EDITED";
const TEST_COURSE_INFO = "TEST_COURSE_INFO";

const WARNING_PANEL = "app-error-message .card-panel.warning";
const FAIL_PANEL = "app-error-message .card-panel.fail";
const CORRECT_PANEL = "app-error-message .card-panel.correct";

// First comment of the forum entry and the reply nested inside it
const FIRST_COMMENT = ".comment-block > app-comment:first-child > div.comment-div";
const FIRST_REPLY = `${FIRST_COMMENT} div.comment-div`;

const NESTED_FILE_GROUP = "app-file-group app-file-group";

function loginAndCreateNewCourse(mail, password) {
  cy.login(mail, password);
  cy.newCourse(COURSE_NAME);
}

function enterCourseAndNavigateTab(courseName, tabId) {
  // Every test creates its own course, so the list must hold more than the 2 seeded ones
  cy.get("#course-list .course-list-item div.course-title span").should("have.length.greaterThan", 2);
  cy.get("#course-list .course-list-item div.course-title span").then(($spans) => {
    const span = $spans.toArray().find((el) => Cypress.$(el).text().trim() === courseName);
    expect(span, `The course with the name '${courseName}' could not be found`).to.exist;
    cy.wrap(span).click();
  });
  cy.get("#main-course-title").should("have.text", courseName);
  cy.get(`#${tabId}`).click();
}

// Opens a dialog, types each value into its field (clearing it first, so it also serves for edit
// forms) and submits it.
// The rendered course text also carries the ql-editor class; the editable one is the other.
const QUILL_EDITOR = ".ql-editor:not(.ql-editor-custom)";

function submitDialog({ trigger, fields, submit, dialogId, failMessage }) {
  cy.openDialog(trigger);
  Object.entries(fields).forEach(([selector, value]) => {
    cy.get(selector).should("be.visible").clear({ force: true });
    cy.get(selector).type(value, { force: true });
  });
  cy.get(submit).click();
  cy.waitForDialogClosed(dialogId, failMessage);
}

// cy.type() only accepts the ISO values of <input type="date|time">: yyyy-MM-dd and HH:mm.
function formatDate(date) {
  const pad = (n) => String(n).padStart(2, "0");
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
}

function formatTime({ hour, minute }) {
  return `${String(hour).padStart(2, "0")}:${String(minute).padStart(2, "0")}`;
}

function sessionFormFields(prefix, { title, comment, date, time }) {
  return {
    [`#input-${prefix}-title`]: title,
    [`#input-${prefix}-comment`]: comment,
    [`#input-${prefix}-date`]: formatDate(date),
    [`#input-${prefix}-time`]: formatTime(time),
  };
}

// The date format shown depends on the browser locale handling, hence several accepted renderings.
function verifySessionDetails(title, comment, acceptedDateTimes) {
  cy.get("li.session-data .session-title").should("have.text", title);
  cy.get("li.session-data .session-description").should("have.text", comment);
  cy.get("li.session-data .session-datetime").should(($el) => expect(acceptedDateTimes).to.include($el.text().trim()));
}

function dismissPanel(panelSelector) {
  cy.get(`${panelSelector} .material-icons`).click();
}

function addAttender(email, { panel, dialogFailMessage, expectedCount }) {
  submitDialog({
    trigger: "#add-attenders-icon",
    fields: { "#input-attender-simple": email },
    submit: "#put-modal-btn",
    dialogId: "put-delete-modal",
    failMessage: dialogFailMessage,
  });
  cy.get(panel).should("be.visible");
  cy.get(".attender-row-div").should("have.length", expectedCount);
  dismissPanel(panel);
}

describe("Course REST operations", () => {
  getTestTeachers().forEach(({ mail, password, role }) => {
    // Resources: loginservice(READONLY,10) openvidumock(NOACCESS,10) configuration(READWRITE,1)
    // executor/webbrowser/webserver(READWRITE,1).
    it(`creates, edits and deletes a course as ${role.toLowerCase()} (${mail})`, () => {
      const editedCourseName = COURSE_NAME + EDITED;
      loginAndCreateNewCourse(mail, password);

      cy.get(".course-put-icon")
        .last()
        .then(($icon) => {
          submitDialog({
            trigger: $icon,
            fields: { "#input-put-course-name": editedCourseName },
            submit: "#submit-put-course-btn",
            dialogId: "put-delete-course-modal",
            failMessage: "Edition of course failed",
          });
        });
      cy.get("#course-list .course-list-item:last-child div.course-title span").should("have.text", editedCourseName);

      cy.deleteCourse(editedCourseName);
    });
  });
});

describe("Course info REST operations", () => {
  getTestTeachers().forEach(({ mail, password, role }) => {
    // Resources: loginservice(READONLY,10) openvidumock(NOACCESS,10) information(READWRITE,1)
    // executor/webbrowser/webserver(READWRITE,1).
    it(`edits course info as ${role.toLowerCase()} (${mail})`, () => {
      loginAndCreateNewCourse(mail, password);
      enterCourseAndNavigateTab(COURSE_NAME, "info-tab-icon");

      cy.get(".md-tab-body.md-tab-active .card-panel.warning").should("be.visible");
      cy.get("#edit-course-info").click();
      cy.get(QUILL_EDITOR).type(TEST_COURSE_INFO);
      cy.get("#send-info-btn").click();

      cy.get(".ql-editor-custom p").first().should("have.text", TEST_COURSE_INFO);

      cy.deleteCourse(COURSE_NAME);
    });
  });
});

describe("Session REST operations", () => {
  getTestTeachers().forEach(({ mail, password, role }) => {
    // Resources: loginservice(READONLY,10) openvidumock(NOACCESS,10) session(READWRITE,1)
    // executor/webbrowser/webserver(READWRITE,1).
    it(`creates, edits and deletes a session as ${role.toLowerCase()} (${mail})`, () => {
      loginAndCreateNewCourse(mail, password);
      enterCourseAndNavigateTab(COURSE_NAME, "sessions-tab-icon");

      submitDialog({
        trigger: "#add-session-icon",
        fields: sessionFormFields("post", {
          title: "TEST LESSON NAME",
          comment: "TEST LESSON COMMENT",
          date: new Date(2018, 2, 1),
          time: { hour: 15, minute: 10 },
        }),
        submit: "#post-modal-btn",
        dialogId: "course-details-modal",
        failMessage: "Addition of session failed",
      });
      verifySessionDetails("TEST LESSON NAME", "TEST LESSON COMMENT", ["Jan 3, 2018 - 03:10", "Mar 1, 2018 - 15:10"]);

      submitDialog({
        trigger: ".edit-session-icon",
        fields: sessionFormFields("put", {
          title: "TEST LESSON NAME EDITED",
          comment: "TEST LESSON COMMENT EDITED",
          date: new Date(2019, 3, 2),
          time: { hour: 5, minute: 10 },
        }),
        submit: "#put-modal-btn",
        dialogId: "put-delete-modal",
        failMessage: "Edition of session failed",
      });
      verifySessionDetails("TEST LESSON NAME EDITED", "TEST LESSON COMMENT EDITED", [
        "Feb 4, 2019 - 05:10",
        "Apr 2, 2019 - 05:10",
      ]);

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
    // Resources: loginservice(READONLY,10) openvidumock(NOACCESS,10) forum(READWRITE,1)
    // executor/webbrowser/webserver(READWRITE,1).
    it(`adds, replies to and deactivates a forum entry as ${role.toLowerCase()} (${mail})`, () => {
      const title = "TEST FORUM ENTRY";
      const comment = "TEST FORUM COMMENT";
      const reply = "TEST FORUM REPLY";

      loginAndCreateNewCourse(mail, password);
      enterCourseAndNavigateTab(COURSE_NAME, "forum-tab-icon");

      submitDialog({
        trigger: "#add-entry-icon",
        fields: { "#input-post-title": title, "#input-post-comment": comment },
        submit: "#post-modal-btn",
        dialogId: "course-details-modal",
        failMessage: "Addition of entry failed",
      });
      cy.get("li.entry-title .forum-entry-title").should("have.text", title);
      cy.get("li.entry-title .forum-entry-author").should("have.text", constants.TEACHER_NAME);
      cy.get("li.entry-title .forum-entry-date").should("have.text", "a few seconds ago");

      cy.get("li.entry-title").click();
      cy.get(`${FIRST_COMMENT} .message-itself`).should("have.text", comment);
      cy.get(`${FIRST_COMMENT} .forum-comment-author`).should("have.text", constants.TEACHER_NAME);

      submitDialog({
        trigger: ".replay-icon:first", // the second icon records a video reply
        fields: { "#input-post-comment": reply },
        submit: "#post-modal-btn",
        dialogId: "course-details-modal",
        failMessage: "Addition of entry reply failed",
      });
      cy.get(`${FIRST_REPLY} .message-itself`).should("have.text", reply);
      cy.get(`${FIRST_REPLY} .forum-comment-author`).should("have.text", constants.TEACHER_NAME);

      cy.get("#entries-sml-btn").click();
      cy.openDialog("#edit-forum-icon");
      cy.get("#label-forum-checkbox").click();
      cy.get("#put-modal-btn").click();
      cy.waitForDialogClosed("put-delete-modal", "Deactivation of forum failed");
      cy.get(WARNING_PANEL).should("be.visible");

      cy.deleteCourse(COURSE_NAME);
    });
  });
});

describe("Files REST operations", () => {
  getTestTeachers().forEach(({ mail, password, role }) => {
    // Resources: loginservice(READONLY,10) openvidumock(NOACCESS,10) files(READWRITE,1)
    // executor/webbrowser/webserver(READWRITE,1).
    it(`adds, edits and deletes files as ${role.toLowerCase()} (${mail})`, () => {
      const fileGroup = "TEST FILE GROUP";
      const fileSubGroup = "TEST FILE SUBGROUP";
      const fileName = "testFile.txt";
      const editedFileName = "testFileEDITED.txt";

      loginAndCreateNewCourse(mail, password);
      enterCourseAndNavigateTab(COURSE_NAME, "files-tab-icon");
      cy.get(WARNING_PANEL).should("be.visible");

      submitDialog({
        trigger: "#add-files-icon",
        fields: { "#input-post-title": fileGroup },
        submit: "#post-modal-btn",
        dialogId: "course-details-modal",
        failMessage: "Addition of file group failed",
      });
      cy.get(".file-group-title h5").should("have.text", fileGroup);

      submitDialog({
        trigger: "#edit-filegroup-icon",
        fields: { "#input-file-title": fileGroup + EDITED },
        submit: "#put-modal-btn",
        dialogId: "put-delete-modal",
        failMessage: "Edition of file group failed",
      });
      cy.get("app-file-group .file-group-title h5").should("have.text", fileGroup + EDITED);

      submitDialog({
        trigger: ".add-subgroup-btn",
        fields: { "#input-post-title": fileSubGroup },
        submit: "#post-modal-btn",
        dialogId: "course-details-modal",
        failMessage: "Addition of file sub-group failed",
      });
      cy.get(`${NESTED_FILE_GROUP} .file-group-title h5`).should("have.text", fileSubGroup);

      cy.openDialog(`${NESTED_FILE_GROUP} .add-file-btn`);
      cy.get(".input-file-uploader").selectFile(`cypress/fixtures/${fileName}`, { force: true });
      cy.get("#upload-all-btn").click();
      cy.get(".determinate[style*='width: 100']", { timeout: 20000 }).should("exist");
      cy.get("i[class*='icon-status-upload']").should("have.text", "done");
      cy.get("#close-upload-modal-btn").click();
      cy.waitForDialogClosed("course-details-modal", "Upload of file failed");
      cy.get(`${NESTED_FILE_GROUP} .chip .file-name-div`).should("have.text", fileName);

      submitDialog({
        trigger: `${NESTED_FILE_GROUP} .edit-file-name-icon`,
        fields: { "#input-file-title": editedFileName },
        submit: "#put-modal-btn",
        dialogId: "put-delete-modal",
        failMessage: "Edition of file failed",
      });
      cy.get(`${NESTED_FILE_GROUP} .chip .file-name-div`).should("have.text", editedFileName);

      // Outer group first: deleting it removes the nested sub-group as well.
      cy.get("app-file-group .delete-filegroup-icon").first().click();
      cy.get(WARNING_PANEL).should("be.visible");

      cy.deleteCourse(COURSE_NAME);
    });
  });
});

describe("Attenders REST operations", () => {
  getTestTeachers().forEach(({ mail, password, role }) => {
    // Resources: loginservice(READONLY,10) openvidumock(NOACCESS,10) attenders(READWRITE,1)
    // executor/webbrowser/webserver(READWRITE,1).
    it(`adds and removes an attender as ${role.toLowerCase()} (${mail})`, () => {
      loginAndCreateNewCourse(mail, password);
      enterCourseAndNavigateTab(COURSE_NAME, "attenders-tab-icon");

      cy.get(".attender-row-div").should("have.length", 1);
      cy.get(".attender-row-div .attender-name-p").should("have.text", constants.TEACHER_NAME);

      // An unregistered email is rejected and leaves the list untouched
      addAttender("studentFail@gmail.com", {
        panel: FAIL_PANEL,
        dialogFailMessage: "Addition of attender fail",
        expectedCount: 1,
      });

      addAttender("student1@gmail.com", {
        panel: CORRECT_PANEL,
        dialogFailMessage: "Addition of attender failed",
        expectedCount: 2,
      });

      cy.get("#edit-attenders-icon").click();
      cy.get(".del-attender-icon").click();
      cy.get(".attender-row-div").should("have.length", 1);

      cy.deleteCourse(COURSE_NAME);
    });
  });
});
