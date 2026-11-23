//
// sessionTest creates a video session and has the teacher plus every student in
// fixtures/videoSessionStudents.json join it simultaneously, then leave and delete it. Same
// constraint as echat.cy.js: Cypress cannot drive multiple concurrent authenticated sessions
// in one spec. Session creation alone is not split out because Java has no standalone test
// for it either.
const { getTestTeachers } = require("../support/testData");

describe("Video session with a teacher and multiple students", () => {
  getTestTeachers().forEach(({ mail, password, role }) => {
    it.skip(`teacher creates a session and every student joins it (${role.toLowerCase()} ${mail}) - requires simultaneous multi-user sessions`, () => {
      cy.login(mail, password);
    });
  });
});
