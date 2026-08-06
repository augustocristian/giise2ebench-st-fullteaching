const { getTestUsers } = require("../support/testData");

describe("User login", () => {
  getTestUsers().forEach(({ mail, password, role }) => {
    describe(`as ${role.toLowerCase()} (${mail})`, () => {
      beforeEach(() => {
        cy.login(mail, password);
      });

      // Resources: loginservice(READONLY,10) openvidu(NOACCESS,10)
      it("shows the account after login and the login link after logout", () => {
        cy.checkLogin(mail);

        cy.logout();
        cy.checkLogOut();
      });
    });
  });
});
