# FullTeaching E2E — Python + Puppeteer

Python/[pyppeteer](https://github.com/pyppeteer/pyppeteer) port of the
[`selenium-java`](../selenium-java) end-to-end test suite for FullTeaching, the
RETORCH benchmark application under [`../sut`](../sut). Same test cases, same
page-navigation logic, different stack: pytest + pytest-asyncio + pyppeteer
instead of JUnit 5 + Selenium WebDriver.

## Layout

Mirrors the package split of `selenium-java/src/test/java/.../{common,utils,functional/test}`:

```
puppeteer-python/
├── fullteaching_e2e/
│   ├── common/         # Constants, navigation helpers, exceptions, BrowserUser (≈ common/*.java)
│   └── utils/          # Click/Wait/Scroll/DOM/CSV-loading helpers (≈ utils/*.java)
├── tests/               # One test module per Java test class (≈ functional/test/**)
├── resources/inputs/   # Same CSV/properties fixtures as selenium-java/src/test/resources
└── pyproject.toml
```

| selenium-java (Java class)                   | puppeteer-python (Python module)                      |
|-----------------------------------------------|--------------------------------------------------------|
| `common.Constants`                            | `fullteaching_e2e.common.constants`                     |
| `common.BrowserUser` / `ChromeUser`           | `fullteaching_e2e.common.browser_user.BrowserUser`      |
| `common.BaseLoggedTest`                       | `tests.conftest` fixtures + `common.base_logged_test`   |
| `common.NavigationUtilities`                  | `fullteaching_e2e.common.navigation_utilities`           |
| `common.CourseNavigationUtilities`            | `fullteaching_e2e.common.course_navigation_utilities`    |
| `common.ForumNavigationUtilities`             | `fullteaching_e2e.common.forum_navigation_utilities`     |
| `common.SessionNavigationUtilities`           | `fullteaching_e2e.common.session_navigation_utilities`   |
| `common.SpiderNavigation`                     | `fullteaching_e2e.common.spider_navigation`              |
| `common.UserUtilities`                        | `fullteaching_e2e.common.user_utilities`                 |
| `common.exception.*`                          | `fullteaching_e2e.common.exceptions`                     |
| `utils.Click` / `Scroll` / `Wait` / `DOMManager` | `fullteaching_e2e.utils.click` / `scroll` / `wait` / `dom_manager` |
| `utils.User` / `UserLoader` / `ParameterLoader`  | `fullteaching_e2e.utils.user` / `user_loader` / `parameter_loader` |
| `functional.test.UserTest`                    | `tests/test_user.py`                                     |
| `functional.test.UnLoggedLinksTests`          | `tests/test_unlogged_links.py`                            |
| `functional.test.LoggedLinksTests`            | `tests/test_logged_links.py`                              |
| `functional.test.LoggedForumTest`             | `tests/test_logged_forum.py`                               |
| `functional.test.student.CourseStudentTest`   | `tests/test_course_student.py`                             |
| `functional.test.teacher.CourseTeacherTest`   | `tests/test_course_teacher.py`                              |
| `functional.test.media.FullTeachingEndToEndRESTTests`   | `tests/test_rest_operations.py`                     |
| `functional.test.media.FullTeachingEndToEndEChatTests`  | `tests/test_echat.py`                                |
| `functional.test.media.FullTeachingTestEndToEndVideoSessionTests` | `tests/test_video_session.py`             |
| `functional.test.media.FullTeachingLoggedVideoSessionTests`       | `tests/test_logged_video_session.py`      |
| `functional.test.RetorchGenerateJenkinfileTest` | **Not ported** — generates a Jenkinsfile via the Java-only `retorch-orchestration` library; disabled by default upstream too, and there is no Python RETORCH client to call instead. |

## Known deviations from the Selenium suite

- **Chromium only.** Puppeteer (and therefore pyppeteer) only automates Chromium.
  The Java suite's `ChromeUser`/`FirefoxUser`/`EdgeUser` split has no equivalent
  here — `BrowserUser` always launches Chromium. `TEACHER_BROWSER`/`STUDENT_BROWSER`
  env vars are still read for parity with the Java suite's configuration surface,
  but a non-Chromium value just logs a warning and falls back to Chromium.
- **No RETORCH `@AccessMode` annotations.** These drive the Java RETORCH scheduler's
  parallel-execution resource locking and have no Python client library. The
  concurrency intent behind them is preserved as a docstring on each test
  (`Resources: ...`) so it can be ported if/when a Python RETORCH client exists.
- **No `ExceptionsHelper` stack-line lookup.** That helper worked around Java's
  verbose assertion failures; pytest's own traceback already reports the failing
  file/line, so ported tests just let exceptions propagate (or use `pytest.fail`).
- pyppeteer bundles its own (dated) Chromium build. Set `PYPPETEER_EXECUTABLE_PATH`
  to point at a system Chrome/Chromium if you need a newer engine.

## Running

```bash
cd puppeteer-python
poetry install
poetry run pyppeteer-install        # first run only: downloads pyppeteer's Chromium

# Point at a running FullTeaching instance (see ../deploy.sh / ../deploy.ps1)
export SUT_URL=https://localhost:5000
export tjob_name=local

poetry run pytest
```

Environment variables (same names as `selenium-java`'s `BaseLoggedTest`):

| Variable          | Meaning                                              | Default                  |
|-------------------|-------------------------------------------------------|---------------------------|
| `SUT_URL`         | Base URL of the running FullTeaching app               | `https://localhost:5000`  |
| `tjob_name`       | RETORCH test-job name, used to namespace log/report dirs | `TJobDef`                |
| `TEACHER_BROWSER` | Browser key for the primary user (Chromium always used) | `chrome`                  |
| `STUDENT_BROWSER` | Browser key for secondary users (Chromium always used)  | `chrome`                  |
| `PYPPETEER_EXECUTABLE_PATH` | Optional path to a system Chrome/Chromium binary | pyppeteer's bundled build |

Test data fixtures live in `resources/inputs/` — same CSV/properties files as
`selenium-java/src/test/resources/inputs/`, so both suites exercise the same
users/sessions against the same SUT.
