# FullTeaching E2E — Playwright + C#

Playwright/.NET (C#) port of the [`selenium-java`](../selenium-java) end-to-end test suite for
FullTeaching, the RETORCH benchmark application under [`../sut`](../sut). Same test cases,
same page-navigation logic, different stack: NUnit + Microsoft.Playwright instead of JUnit 5 +
Selenium WebDriver.

## Layout

Mirrors the package split of `selenium-java/src/test/java/.../{common,utils,functional/test}`:

```
playwright-csharp/
├── Common/          # Constants, navigation helpers, exceptions, BrowserUser (≈ common/*.java)
├── Utils/           # User/UserLoader/ParameterLoader (≈ utils/*.java)
├── Tests/           # One test class per Java test class (≈ functional/test/**)
├── Resources/       # Same CSV/properties fixtures as selenium-java/src/test/resources
└── PlaywrightTests.csproj
```

| selenium-java (Java class)                    | playwright-csharp (C# class)                        |
|-----------------------------------------------|-------------------------------------------------------|
| `common.Constants`                            | `Common.Constants`                                      |
| `common.BrowserUser` / `ChromeUser`           | `Common.BrowserUser`                                     |
| `common.BaseLoggedTest`                       | `Common.BaseTest` + `Common.LoginHelper`                  |
| `common.CourseNavigationUtilities`            | `Common.CourseNavigationUtilities`                        |
| `common.ForumNavigationUtilities`             | `Common.ForumNavigationUtilities`                          |
| `common.SessionNavigationUtilities`           | `Common.SessionNavigationUtilities`                        |
| `common.SpiderNavigation`                     | `Common.SpiderNavigation`                                   |
| `common.UserUtilities`                        | `Common.UserUtilities`                                        |
| `common.exception.*`                          | `Common.Exceptions.*`                                           |
| `utils.Click` / `Scroll` / `Wait` / `DOMManager` | Not ported as separate classes - see "Where Playwright simplifies things" |
| `utils.User` / `UserLoader` / `ParameterLoader`  | `Utils.User` / `UserLoader` / `ParameterLoader` (NUnit `[TestCaseSource]`) |
| `functional.test.UserTest`                    | `Tests.UserTests`                                              |
| `functional.test.UnLoggedLinksTests`          | `Tests.UnloggedLinksTests`                                       |
| `functional.test.LoggedLinksTests`            | `Tests.LoggedLinksTests`                                          |
| `functional.test.LoggedForumTest`             | `Tests.LoggedForumTests`                                            |
| `functional.test.student.CourseStudentTest`   | `Tests.CourseStudentTests`                                           |
| `functional.test.teacher.CourseTeacherTest`   | `Tests.CourseTeacherTests`                                             |
| `functional.test.media.FullTeachingEndToEndRESTTests`             | `Tests.RestOperationsTests`               |
| `functional.test.media.FullTeachingEndToEndEChatTests`            | `Tests.EChatTests` - **fully implemented**, see below |
| `functional.test.media.FullTeachingTestEndToEndVideoSessionTests` | `Tests.VideoSessionTests` - **fully implemented** |
| `functional.test.media.FullTeachingLoggedVideoSessionTests`       | `Tests.LoggedVideoSessionTests` - **fully implemented** |
| `functional.test.RetorchGenerateJenkinfileTest`                   | **Not ported** - generates a Jenkinsfile via the Java-only `retorch-orchestration` library; disabled by default upstream too, and there is no .NET RETORCH client to call instead. |

## Multi-user tests: fully implemented, unlike the Cypress port

`EChatTests`, `VideoSessionTests` and `LoggedVideoSessionTests` need a teacher and one or more
students logged in and interacting **simultaneously** (live chat, a shared video call). The
[Cypress port](../cypress-js) cannot do this at all - Cypress drives exactly one browser tab
per test by design - so those three specs are written but skipped there.

Playwright has no such limitation: its `IBrowserContext` is an isolated session (own cookies,
storage, permissions) within a single shared `IBrowser` process, and running several contexts
concurrently in one test is the documented Playwright pattern for exactly this scenario. So
here, unlike in Cypress, all three are fully implemented - `Common/BrowserUser.cs` wraps one
context+page per simulated user, and `BaseTest.CreateSecondaryUserAsync` spins up as many as a
test needs (mirroring `BaseLoggedTest.setupBrowser()`/`studentBrowserUserList`), all
auto-disposed in `[TearDown]`. This capability gap between Cypress and Playwright is itself a
useful data point for the RETORCH framework comparison this suite exists to support.

## Where Playwright simplifies things

Several Java utility classes have no direct counterpart here because Playwright's locator
model already does what they exist for:

- **`utils.Wait` / most retry loops**: Playwright's locator actions (`ClickAsync`, `FillAsync`,
  ...) auto-wait for the element to be attached, visible, stable and enabled before acting,
  and `Assertions.Expect(locator).ToXxxAsync()` retries until its timeout (`BrowserContext`'s
  default timeout is set to `Wait.notTooMuch`'s 20s in `BrowserUser.SetupBrowserAsync`).
  `Common/PollHelper.cs` covers the one gap: Playwright (unlike Cypress's
  `cy.get().should(callback)`) has no built-in way to retry an arbitrary multi-element
  computation such as "does this list of course titles contain X" - see its doc comment.
- **`utils.Scroll`**: locator actions auto-scroll the element into view before acting.
- **`utils.DOMManager.getParent`**: Playwright locators support relative XPath, so
  `.Locator("xpath=..")` chained off any locator is the parent.
- **`utils.Click.byJS`**: `ClickAsync(new() { Force = true })` is Playwright's idiomatic escape
  hatch for bypassing an intercepting overlay - used in `LoginHelper.LogoutAsync`.
- **`common/Constants.java`'s XPath locators**: Playwright's selector engine understands the
  `xpath=` prefix natively, so - unlike the Cypress port, which has no XPath support and had
  to translate every one to CSS - these are kept exactly as they were in Java.
- **File uploads** (`FilesRestOperations`): Java forces the hidden `<input type=file>` visible
  via JS before `sendKeys()` can target it. Playwright's `SetInputFilesAsync` doesn't simulate
  a real click, so it works on hidden inputs directly - that workaround isn't needed.
- **`utils.ExceptionsHelper`**: worked around Java's verbose assertion failures; NUnit's own
  failure output already points at the exact failing step.

## Running

```bash
cd playwright-csharp
dotnet restore
dotnet build
pwsh bin/Debug/net8.0/playwright.ps1 install --with-deps chromium   # first run only

# Point at a running FullTeaching instance (see ../deploy.sh / ../deploy.ps1)
export SUT_URL=https://localhost:5000
export tjob_name=local

dotnet test --settings .runsettings
```

Environment variables (same names as `selenium-java`'s `BaseLoggedTest`):

| Variable    | Meaning                                                          | Default                 |
|-------------|-----------------------------------------------------------------------|---------------------------|
| `SUT_URL`   | Base URL of the running FullTeaching app                                | `https://localhost:5000`  |
| `tjob_name` | RETORCH test-job name, used to namespace test/user identifiers            | `TJobDef`                  |
| `HEADED`    | Set to `true` to launch Chromium headed (default: headless)                | unset (headless)            |

Test data fixtures live in `Resources/Inputs/` — same CSV/properties files as
`selenium-java/src/test/resources/inputs/`, so both suites exercise the same users/sessions
against the same SUT. `Resources/` is copied next to the built test assembly by the `.csproj`,
so paths resolve regardless of the working directory `dotnet test` is invoked from.
