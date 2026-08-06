// Ported from functional/test/media/FullTeachingLoggedVideoSessionTests.java - NOT runnable
// as-is.
//
// sessionTest creates a video session and has the teacher plus every student in
// fixtures/videoSessionStudents.json join it simultaneously, then leave and delete it. Same
// constraint as echat.cy.js/video-session.cy.js: Cypress cannot drive multiple concurrent
// authenticated sessions in one spec. See that file's header for the full rationale and the
// sibling puppeteer-python/tests/test_logged_video_session.py for a suite that *can* run
// this scenario.
//
// The session-creation half of this test (createNewSession/joinSession as the teacher alone,
// with no students) has no multi-session dependency and *is* portable; it isn't split out
// into its own spec here because Java doesn't test it in isolation either - `createNewSession`
// exists only as a step inside `sessionTest`, not as a standalone test case to port.
const { getTestTeachers } = require("../support/testData");

describe("Video session with a teacher and multiple students", () => {
  getTestTeachers().forEach(({ mail, password, role }) => {
    it.skip(
      `teacher creates a session and every student joins it (${role.toLowerCase()} ${mail}) ` +
        "- requires simultaneous multi-user sessions, not supported by Cypress",
      () => {
        cy.slowLogin(mail, password);
      }
    );
  });
});
