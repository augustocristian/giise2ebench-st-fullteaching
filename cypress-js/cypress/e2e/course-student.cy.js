// Ported from functional/test/student/CourseStudentTest.java.
const { getTestStudents } = require("../support/testData");
const constants = require("../support/constants");

describe("Student course main flow", () => {
  getTestStudents().forEach(({ mail, password, role }) => {
    // Logs in as a student, opens the first course and checks every tab loads.
    // Resources: course(READONLY,15) loginservice(READONLY,10) openvidumock(NOACCESS,10)
    // executor/webbrowser/webserver(READWRITE,1).
    it(`opens the first course and every tab as ${role.toLowerCase()} (${mail})`, () => {
      cy.slowLogin(mail, password);
      cy.toCoursesHome();

      cy.getCoursesList().should("have.length.greaterThan", 0);
      cy.getCoursesList().then((courses) => {
        cy.getCourseByName(courses[0]).find(constants.COURSE_TITLE).click();
      });
      cy.get(constants.COURSE_TABS).should("be.visible");

      cy.go2Tab(constants.HOME_ICON);
      cy.go2Tab(constants.SESSION_ICON);
      cy.go2Tab(constants.FORUM_ICON);
      cy.go2Tab(constants.FILES_ICON);
      cy.go2Tab(constants.ATTENDERS_ICON);
    });
  });
});
