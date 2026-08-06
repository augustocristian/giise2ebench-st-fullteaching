// Ported from functional/test/media/FullTeachingTestEndToEndVideoSessionTests.java - NOT
// runnable as-is.
//
// oneToOneVideoAudioSessionChrome needs a teacher and a student simultaneously present in the
// same video session (join, request/grant intervention, verify both sides' <video> elements).
// Same constraint as echat.cy.js: Cypress cannot drive two concurrent authenticated sessions
// in one spec. See that file's header for the full rationale and the sibling
// puppeteer-python/tests/test_video_session.py for a suite that *can* run this scenario.
const { getTestTeachers } = require("../support/testData");

describe("One-to-one video/audio session", () => {
  getTestTeachers().forEach(({ mail, password, role }) => {
    it.skip(
      `teacher and student join a video session and exchange intervention control ` +
        `(${role.toLowerCase()} ${mail}) - requires two simultaneous sessions, not supported by Cypress`,
      () => {
        cy.slowLogin(mail, password);
      }
    );
  });
});
