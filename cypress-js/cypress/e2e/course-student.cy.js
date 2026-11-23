const { getTestStudents } = require("../support/testData");
const constants = require("../support/constants");

const COURSE_TABS = [
  constants.HOME_ICON,
  constants.SESSION_ICON,
  constants.FORUM_ICON,
  constants.FILES_ICON,
  constants.ATTENDERS_ICON,
];

describe("Student course main flow", () => {
  getTestStudents().forEach(({ mail, password, role }) => {
    describe(`as ${role.toLowerCase()} (${mail})`, () => {
      beforeEach(() => {
        cy.login(mail, password);
        cy.toCoursesHome();
      });

      // Resources: course(READONLY,15) loginservice(READONLY,10) openvidumock(NOACCESS,10)
      it("opens the first course and every tab", () => {
        cy.getCoursesList().should("have.length.greaterThan", 0);
        cy.getCoursesList().then((courses) => {
          cy.getCourseByName(courses[0]).find(constants.COURSE_TITLE).click();
        });
        cy.get(constants.COURSE_TABS).should("be.visible");

        COURSE_TABS.forEach((icon) => cy.go2Tab(icon));
      });
    });
  });
});
