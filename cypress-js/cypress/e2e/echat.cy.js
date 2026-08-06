// Ported from functional/test/media/FullTeachingEndToEndEChatTests.java - NOT runnable as-is.
//
// oneToOneChatInSessionChrome logs in as a teacher AND a student simultaneously, in two
// separate browser sessions, and has them exchange chat messages live in the same video
// session. Cypress fundamentally does not support driving two concurrent authenticated
// sessions/tabs within a single spec (this is a documented platform constraint, not a
// missing configuration) - see cypress.config.js and support/login.js for everything that
// *is* portable (login, navigation, DOM assertions), which a real implementation of this
// spec would still need.
//
// This is intentionally left unimplemented rather than worked around (e.g. spawning a second
// browser via a Node-side cy.task()), per the project decision to keep this suite pure
// Cypress and treat the gap itself as a useful, honest data point for the RETORCH framework
// comparison. See selenium-java's version and puppeteer-python/tests/test_echat.py, both of
// which *can* run this scenario by launching two independent browser instances.
const { getTestTeachers } = require("../support/testData");

describe("One-to-one chat in a video session", () => {
  getTestTeachers().forEach(({ mail, password, role }) => {
    it.skip(
      `teacher and student exchange chat messages in a session (${role.toLowerCase()} ${mail}) ` +
        "- requires two simultaneous sessions, not supported by Cypress",
      () => {
        cy.slowLogin(mail, password);
      }
    );
  });
});
