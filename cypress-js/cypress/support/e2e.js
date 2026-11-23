// Global test lifecycle
require("./commands");

// FullTeaching (Angular) logs benign uncaught errors unrelated to the assertions under test.
Cypress.on("uncaught:exception", () => false);

beforeEach(() => {
  cy.visit("/");
  // Lets tests probe "is a <video> actually playing": window.MY_FUNC() appends a marker div.
  cy.window().then((win) => {
    win.MY_FUNC = function videoPlayingProbe() {
      const marker = document.createElement("div");
      marker.id = "video-playing-div";
      marker.innerText = "VIDEO PLAYING";
      document.body.appendChild(marker);
    };
  });
});

// No-op if the test never logged in.
afterEach(() => {
  cy.logout();
});
