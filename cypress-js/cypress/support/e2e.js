// Global test lifecycle, ported from the @BeforeEach/@AfterEach of common/BaseLoggedTest.java.
require("./commands");

// FullTeaching (Angular) occasionally logs benign uncaught errors unrelated to what a given
// test is asserting; without this, Cypress fails the test on any such error.
Cypress.on("uncaught:exception", () => false);

beforeEach(() => {
  cy.visit("/");
  // Injected once per page so tests can probe "is a <video> actually playing" via JS, mirrors
  // the GLOBAL_JS_FUNCTION literal duplicated in BaseLoggedTest.setup()/setupBrowser(). Unlike
  // the Selenium/pyppeteer ports (which had to ship this as a string evaluated remotely),
  // cy.window() gives direct access to the real window object, so it's just a normal closure.
  cy.window().then((win) => {
    win.MY_FUNC = function videoPlayingProbe() {
      const elem = document.createElement("div");
      elem.id = "video-playing-div";
      elem.innerText = "VIDEO PLAYING";
      document.body.appendChild(elem);
      console.log("Video check function successfully added to DOM by Cypress");
    };
  });
});

afterEach(() => {
  // No-op if the test never logged in - see login.js's logout() for the DOM-presence checks.
  cy.logout();
});
