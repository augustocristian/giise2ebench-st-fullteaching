// Ported from functional/test/UserTest.java.
const { getTestUsers } = require("../support/testData");

describe("User login", () => {
  getTestUsers().forEach(({ mail, password, role }) => {
    // A simple login acknowledgement: log in, confirm it worked, log out, confirm that too.
    // Resources (RETORCH @AccessMode in the Java suite, informational only here):
    // loginservice(READONLY,10) openvidu(NOACCESS,10) executor/webbrowser/webserver(READWRITE,1).
    it(`logs in and out as ${role.toLowerCase()} (${mail})`, () => {
      cy.slowLogin(mail, password);
      cy.checkLogin(mail);

      cy.logout();
      cy.checkLogOut();
    });
  });
});
