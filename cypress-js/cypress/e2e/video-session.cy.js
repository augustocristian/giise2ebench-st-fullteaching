//
// The scenario needs a teacher and a student simultaneously in the same video session (join,
// request/grant intervention, verify both sides' <video> elements). Same constraint as
// echat.cy.js: Cypress cannot drive two concurrent authenticated sessions in one spec.
const { getTestTeachers } = require("../support/testData");

describe("One-to-one video/audio session", () => {
  getTestTeachers().forEach(({ mail, password, role }) => {
    it.skip(`teacher and student join a video session and exchange intervention control (${role.toLowerCase()} ${mail}) - requires two simultaneous sessions`, () => {
      cy.login(mail, password);
    });
  });
});
