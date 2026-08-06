// The scenario needs a teacher and a student logged in simultaneously, in two separate browser
// sessions, exchanging chat messages in the same video session. Cypress cannot drive two
// concurrent authenticated sessions within one spec, so the test is left skipped rather than
// worked around (e.g. a second browser spawned via cy.task()). The gap is kept as a data point
// for the RETORCH framework comparison; the selenium-java and puppeteer-python suites run it.
const { getTestTeachers } = require("../support/testData");

describe("One-to-one chat in a video session", () => {
  getTestTeachers().forEach(({ mail, password, role }) => {
    it.skip(`teacher and student exchange chat messages in a session (${role.toLowerCase()} ${mail}) - requires two simultaneous sessions`, () => {
      cy.login(mail, password);
    });
  });
});
