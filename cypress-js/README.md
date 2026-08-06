# FullTeaching E2E — Cypress + JavaScript

Cypress/JavaScript port of the [`selenium-java`](../selenium-java) end-to-end test suite for
FullTeaching, the RETORCH benchmark application under [`../sut`](../sut). Same test cases,
same page-navigation logic, different stack: Cypress + Mocha instead of JUnit 5 + Selenium
WebDriver.

## Layout

Cypress convention (`cypress/e2e`, `cypress/support`, `cypress/fixtures`) rather than the
Java suite's Maven layout, but the same functional split - one support module per Java
`common`/`utils` class, one spec per Java test class:

```
cypress-js/
├── cypress/
│   ├── e2e/         # One spec per Java test class (≈ functional/test/**)
│   ├── support/      # Constants, custom commands, navigation helpers (≈ common/*.java, utils/*.java)
│   └── fixtures/     # Same user/session data as selenium-java/src/test/resources
├── cypress.config.js
└── package.json
```

| selenium-java (Java class)                             | cypress-js                                    |
|-----------------------------------------------------------|-------------------------------------------------|
| `common.Constants`                                      | `support/constants.js`                            |
| `common.BaseLoggedTest` (login/logout/dialog methods)     | `support/login.js` custom commands (`cy.slowLogin`, `cy.logout`, ...) + global hooks in `support/e2e.js` |
| `common.CourseNavigationUtilities`                       | `support/courseNavigation.js`                     |
| `common.ForumNavigationUtilities`                        | `support/forumNavigation.js`                      |
| `common.SessionNavigationUtilities`                      | `support/sessionNavigation.js`                    |
| `common.SpiderNavigation`                                | `support/spiderNavigation.js`                     |
| `common.UserUtilities`                                   | `support/userUtilities.js`                        |
| `utils.Click` / `Scroll` / `Wait` / `DOMManager`           | Not ported as separate modules - see "Where Cypress simplifies things" below |
| `utils.User` / `UserLoader` / `ParameterLoader`             | `support/testData.js` + `fixtures/users.json`     |
| `functional.test.UserTest`                               | `e2e/user.cy.js`                                    |
| `functional.test.UnLoggedLinksTests`                     | `e2e/unlogged-links.cy.js`                           |
| `functional.test.LoggedLinksTests`                       | `e2e/logged-links.cy.js`                             |
| `functional.test.LoggedForumTest`                        | `e2e/logged-forum.cy.js`                             |
| `functional.test.student.CourseStudentTest`               | `e2e/course-student.cy.js`                           |
| `functional.test.teacher.CourseTeacherTest`                | `e2e/course-teacher.cy.js`                           |
| `functional.test.media.FullTeachingEndToEndRESTTests`      | `e2e/rest-operations.cy.js`                          |
| `functional.test.media.FullTeachingEndToEndEChatTests`     | `e2e/echat.cy.js` - **written but skipped**, see below |
| `functional.test.media.FullTeachingTestEndToEndVideoSessionTests` | `e2e/video-session.cy.js` - **written but skipped** |
| `functional.test.media.FullTeachingLoggedVideoSessionTests`       | `e2e/logged-video-session.cy.js` - **written but skipped** |
| `functional.test.RetorchGenerateJenkinfileTest`            | **Not ported** - generates a Jenkinsfile via the Java-only `retorch-orchestration` library; disabled by default upstream too, and there is no JS RETORCH client to call instead. |

## Why three specs are skipped

`echat.cy.js`, `video-session.cy.js` and `logged-video-session.cy.js` correspond to Java
tests that need **two or more simultaneous logged-in browser sessions** (a teacher and one
or more students, live in the same video session/chat at once). This isn't a missing
configuration - Cypress is architecturally built around driving a single browser tab per
test, and does not support multiple concurrent authenticated sessions within one spec.

Rather than work around this (e.g. spawning a second, Puppeteer-controlled browser from a
`cy.task()` Node hook), these three specs are kept in the suite with real `describe`/`it.skip`
structure and a header comment explaining why, so the gap is visible and intentional instead
of silently missing. This mirrors how `RetorchGenerateJenkinfileTest` was excluded from the
Python port - and is arguably itself a useful data point for the RETORCH framework
comparison this suite exists to support: `selenium-java` and `puppeteer-python` *can* run
these scenarios (each launches independent browser instances per user), Cypress cannot.

## Where Cypress simplifies things

Several Java utility classes have no direct counterpart here because Cypress's command
model already does what they exist for:

- **`utils.Wait` / retry loops** (`Click.withNRetries`, `checkIfCourseExists(wd, title, retries)`,
  ...): `cy.get()`/`.should()` already retry against the DOM until `defaultCommandTimeout`
  (set to `Wait.notTooMuch`'s 20s in `cypress.config.js`) elapses. `support/courseNavigation.js`'s
  `cy.assertCourseExists`/`cy.assertCourseNotExists` use the idiomatic
  `cy.get(...).should(callback)` pattern for this instead of a manual retry loop.
- **`utils.Scroll`**: `cy.get().click()` auto-scrolls the element into view before acting.
- **`utils.DOMManager.getParent`**: Cypress wraps elements with jQuery, so `.parent()` is built in.
- **`utils.Click.byJS`**: `.click({ force: true })` is Cypress's idiomatic escape hatch for
  bypassing an intercepting overlay - used in `support/login.js`'s `logout()`.
- **`common/Constants.java`'s XPath locators**: Cypress has no built-in XPath support (and
  idiomatic Cypress avoids it). The handful of XPath constants become CSS: structural
  `/div[3]` steps become `div:nth-child(3)`, `contains(@class, x)` becomes `[class*="x"]`,
  and `text() = 'x'` becomes jQuery's `:contains('x')`. See `support/constants.js`'s header
  comment.
- **`utils.ExceptionsHelper`**: worked around Java's verbose assertion failures; Cypress's
  command log and error output already point at the exact failing step.

## Running

```bash
cd cypress-js
npm install

# Point at a running FullTeaching instance (see ../deploy.sh / ../deploy.ps1)
export SUT_URL=https://localhost:5000
export tjob_name=local

npx cypress open   # interactive
npm test            # headless (cypress run)
```

Environment variables (same names as `selenium-java`'s `BaseLoggedTest`):

| Variable    | Meaning                                                | Default                 |
|-------------|-----------------------------------------------------------|---------------------------|
| `SUT_URL`   | Base URL of the running FullTeaching app (becomes Cypress's `baseUrl`) | `https://localhost:5000`  |
| `tjob_name` | RETORCH test-job name, exposed as `Cypress.env('tjobName')` for parity | `TJobDef`                  |

Test data fixtures live in `cypress/fixtures/` - the same users/sessions as
`selenium-java/src/test/resources/inputs/` (as JSON, Cypress's native fixture format), so
both suites exercise the same data against the same SUT.
