# FullTeaching E2E - Python + Puppeteer

Python port of the [`selenium-java`](../selenium-java) end-to-end test suite for FullTeaching, the
RETORCH benchmark application under [`../sut`](../sut). Same test cases, same page-navigation
logic, different stack: pytest + pytest-asyncio + the **current Puppeteer** (pinned to 25.18.1)
instead of JUnit 5 + Selenium WebDriver.

Puppeteer only exists for Node.js and the Python port `pyppeteer` is abandoned (obsolete Chromium),
so the tests stay in Python and talk to a small Node process (the *bridge*) that runs the real
Puppeteer. The architecture is the one of the DevorApp and ClimaNuvem Puppeteer suites.

## Architecture

```
 pytest (Python 3.12+, asyncio, one session-wide loop)
   |  tests/*  ->  fullteaching_e2e/{common,utils}  ->  fullteaching_e2e/browser (Browser, Page, Locator)
   |
   |  newline-delimited JSON-RPC over stdin/stdout  (asyncio subprocess, request ids)
   v
 Node bridge  (bridge/server.mjs, Node >= 22.12, puppeteer 25.18.1)
   |  Puppeteer Locators API (auto-waiting), browser contexts, evaluateOnNewDocument
   v
 Google Chrome (system install, channel "chrome", headless by default)  ->  FullTeaching + OpenVidu
```

- Auto-waiting comes from Puppeteer Locators on the Node side; there are no polling waiters in Python.
- Selectors are CSS, or XPath when prefixed with `xpath=` (or built with `Page.xpath`). `nth` and `within` scoping uses a Puppeteer custom query handler (`scope/...`), so scoped locators auto-wait too.
- One Chrome per test session. Every simulated user (teacher, students of a video session) gets its own
  isolated browser context (own cookies, storage, permissions) from `browser.new_page(...)`; any number of
  them can be open at once.
- Chrome starts with `--use-fake-ui-for-media-stream --use-fake-device-for-media-stream` and
  `--ignore-certificate-errors` (self-signed SUT); camera and microphone are also granted to the SUT origin.
- The bridge exits (and closes Chrome) when Python closes its stdin, so a crashed run does not leave Chrome behind.
- No deprecated Puppeteer API is used (no `waitForTimeout`, `$x`, `waitFor`, legacy `overridePermissions`,
  `headless: 'new'`/`'old'`); permissions use `BrowserContext.setPermission`, XPath goes through the `xpath=` handler.

## Layout

```
puppeteer-python/
├── bridge/                 # Node bridge: package.json, package-lock.json, server.mjs
├── fullteaching_e2e/
│   ├── browser/            # Python client of the bridge: Browser, BrowserContext, Page, Locator, TestId, errors
│   ├── common/             # Constants, navigation helpers, exceptions, BrowserUser (≈ common/*.java)
│   └── utils/              # Click/Wait/Scroll/DOM/CSV-loading helpers (≈ utils/*.java)
├── tests/
│   ├── bridge/             # smoke test of the Python-Node bridge (no SUT needed)
│   ├── conftest.py         # fixtures: app_config, sut_url, browser (session), page, user, browser_factory
│   └── test_*.py           # one module per Java test class (≈ functional/test/**)
├── resources/inputs/       # Same CSV/properties fixtures as selenium-java/src/test/resources
└── pyproject.toml          # dependencies (exact versions), pytest, asyncio and logging config
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
| `functional.test.RetorchGenerateJenkinfileTest` | **Not ported** - generates a Jenkinsfile via the Java-only `retorch-orchestration` library; disabled by default upstream too, and there is no Python RETORCH client to call instead. |

## Known deviations from the Selenium suite

- **Chromium/Chrome only.** Puppeteer only automates Chrome. The Java suite's `ChromeUser`/`FirefoxUser`/`EdgeUser`
  split has no equivalent here. `TEACHER_BROWSER`/`STUDENT_BROWSER` are still read for parity with the Java
  configuration surface, but a non-Chrome value just logs a warning and falls back to Chrome.
- **No RETORCH `@AccessMode` annotations.** These drive the Java RETORCH scheduler's parallel-execution resource
  locking and have no Python client library. The concurrency intent is kept as a `Resources: ...` docstring on each test.
- **No `ExceptionsHelper` stack-line lookup.** pytest's own traceback already reports the failing file and line.

## Requirements

| Tool | Purpose |
| :--- | :--- |
| Python 3.12+ | pytest suite |
| Node.js 22.12+ (Node 22 in CI) | runs the bridge |
| Google Chrome | driven by Puppeteer (no browser is downloaded) |
| Docker (Compose v2) | runs the SUT |

## Install

```bash
# Bridge: Puppeteer without downloading a browser (the system Chrome is used)
cd bridge && PUPPETEER_SKIP_DOWNLOAD=true npm ci && cd ..

# Python
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\Activate.ps1
pip install .                        # all dependencies pinned in pyproject.toml (or: poetry install)
```

To use a different Chrome/Chromium binary, set `PUPPETEER_EXECUTABLE_PATH`. Set `NODE_BINARY` if `node` is not on the PATH.

## Run

Start the SUT first (`../deploy.sh` or `..\deploy.ps1`), then:

```bash
export SUT_URL=https://localhost:5000
export tjob_name=local

python -m pytest                       # everything, headless
HEADED=1 python -m pytest              # show the browser
python -m pytest -m bridge             # bridge smoke test only (no SUT needed)
python -m pytest -m e2e                # tests against the SUT
python -m pytest -m video              # also: echat, forum, course, links, rest, user
python -m pytest --html=results/report.html --self-contained-html
```

pytest markers (declared in `pyproject.toml`, `--strict-markers` is on): `e2e`, `bridge`, `video`, `echat`,
`forum`, `course`, `links`, `rest`, `user`. `tests/conftest.py` tags tests automatically (`bridge` for
`tests/bridge`, `e2e` for the rest, plus the area marker from the file name).

Output: JUnit XML in `results/puppeteer.xml` (always), coverage in `coverage.xml`, logs in `logs/pytest.log`,
screenshots of failed `page` tests in `reports/screenshots/`. All of them are gitignored.

| Variable | Effect | Default |
| :--- | :--- | :--- |
| `SUT_URL` | Base URL of the running FullTeaching app | `https://localhost:5000` |
| `tjob_name` | RETORCH test-job name, used to namespace logs and reports | `TJobDef` |
| `TEACHER_BROWSER` / `STUDENT_BROWSER` | Browser key (Chrome is always used) | `chrome` |
| `HEADED=1` | Shows the browser | headless |
| `PUPPETEER_EXECUTABLE_PATH` | Chrome binary instead of the system Chrome | system Chrome |
| `BROWSER_ARGS` | Extra Chrome flags, space separated | none |
| `VIEWPORT` | `WIDTHxHEIGHT` of the pages | `1920x1080` |
| `NODE_BINARY` | Node executable | `node` on the PATH |
| `USE_SYSTEM_PROXY=1` | Do not force `--no-proxy-server` (Windows proxy auto-detection can add 20-30 s per navigation) | forced off |
| `CI` | Adds `--no-sandbox` to Chrome (Linux runners) | unset |

## Browser API (`fullteaching_e2e.browser`)

All methods are `async` unless noted. Waiting actions use a default auto-wait timeout of 10 s, set per locator with `with_timeout`.
`Page.evaluate` and `Locator.evaluate` take a JS **function expression** (`"(a, b) => a + b"`) plus JSON-serializable args and await promises.

### `Browser`

| Member | Description |
| :--- | :--- |
| `await Browser.launch(headless=True, executable_path=None, args=None, node_binary=None, fake_media=True, accept_insecure_certs=True, viewport=None)` | Starts the bridge and Chrome. `fake_media` adds the fake camera/microphone flags, `accept_insecure_certs` ignores HTTPS certificate errors, `viewport=(w, h)` defaults to 1280x800 |
| `await browser.new_context(media_origin=None)` | Isolated `BrowserContext`; with `media_origin` (the SUT URL) it is granted camera and microphone there |
| `await browser.new_page(media_origin=None)` | Page in a fresh context; closing the page closes the context. Call once per simulated user |
| `await browser.close()` | Closes Chrome and the bridge (also via `async with`) |
| `browser.version` | Chrome version string (attribute) |

`BrowserContext`: `await new_page(owns_context=False)`, `await grant_permissions(origin, permissions=("camera", "microphone"))`, `await close()`.

### `Page`

| Method | Description |
| :--- | :--- |
| `locator(selector, timeout_ms=10000) -> Locator` (sync) | Lazy locator for CSS; `"xpath=..."` is taken as XPath |
| `xpath(expression, timeout_ms=10000) -> Locator` (sync) | Lazy locator for an XPath expression |
| `goto(url, timeout_ms=30000) -> int \| None` | Navigates, waits for DOMContentLoaded, returns the HTTP status (an error status does not raise) |
| `go_back(timeout_ms=30000)` / `go_forward(timeout_ms=30000)` | History navigation; returns the status or `None` (page restored from cache) |
| `reload(timeout_ms=30000)` | Reloads the page |
| `fetch_status(url, method="GET") -> int` | HTTP status of a request made from the page (cookies sent, redirects followed), `0` on network error; for link checking |
| `url() -> str` / `title() -> str` | Current URL / document title |
| `evaluate(script, *args)` | Runs a JS function expression with JSON args |
| `evaluate_expression(expression)` | Runs a raw JS expression or statements as is (for example the video-playing probe) |
| `wait_for_function(script, *args, timeout_ms=10000)` | Waits until a JS function expression is truthy and returns its value |
| `wait_for_url(fragment, timeout_ms=10000)` | Waits until the URL contains `fragment` |
| `add_init_script(script, *args)` | Runs a JS function expression in every new document before page scripts |
| `set_dialog_policy(policy="accept")` | `"accept"`, `"dismiss"` or `"ignore"` for alert/confirm/prompt |
| `press_key(key)` | Presses a key on whatever has focus |
| `set_viewport(width, height)` | Resizes the viewport |
| `bring_to_front()` | Activates the tab |
| `clear_storage()` | Clears localStorage, sessionStorage and IndexedDB of the current origin |
| `clear_cookies()` / `cookies()` | Deletes / lists the cookies of the page's context |
| `screenshot(path, full_page=True) -> Path` | Saves a PNG |
| `diagnostics(clear=True)` | Console errors/warnings, page errors, failed requests and dialogs captured so far |
| `close()` | Closes the page |

### `Locator` (immutable and lazy; Puppeteer auto-waits when an action runs)

| Method | Description |
| :--- | :--- |
| `nth(i)` / `first()` / `last()` (sync) | The i-th match (0-based, negative counts from the end) |
| `within(selector)` / `within_xpath(expression)` (sync) | Matches below this locator's elements; XPath `//a` is relative (`.//a`) |
| `with_timeout(timeout_ms)` (sync) | Same locator with another auto-wait timeout |
| `all() -> list[Locator]` | One locator per current match (never waits) |
| `click()` / `double_click()` | Waits for visible, enabled and stable, scrolls into view, clicks |
| `js_click()` | `element.click()` inside the page (covered or off-screen elements) |
| `fill(value)` | Clears and sets the value; `""` really clears |
| `type(text, delay_ms=0)` / `press(key)` | Types key by key / presses a key on the focused element |
| `hover()` / `scroll_into_view()` | Hovers / scrolls into view |
| `upload_file(*paths)` | Sets the files of an `<input type=file>` (hidden inputs work) |
| `select(*values)` / `select_by_text(text)` | Selects `<option>` by value / visible text; returns the selected value(s) |
| `evaluate(script, *args)` | Runs a JS function expression with the element as first argument |
| `text()` / `inner_text()` | Text content / rendered text (waits for the element to exist) |
| `all_texts() -> list[str]` | Text content of every current match (never waits) |
| `input_value()` | Value of an input, textarea or select |
| `attribute(name)` / `property(name)` | DOM attribute (for example `href`) / property (for example `checked`) |
| `count()` | Number of current matches (never waits) |
| `is_visible()` / `is_enabled()` | State of the first match (never waits) |
| `wait_for(state="visible")` | Waits for `visible`, `hidden`, `attached` or `detached` |
| `wait_for_text(text, exact=False)` | Waits until some match contains (or, with `exact`, equals) the text |

Video playing probe example:

```python
await page.wait_for_function(
    "() => { const v = document.querySelector('video'); return !!v && !v.paused && v.readyState >= 2 && v.currentTime > 0; }",
    timeout_ms=15_000)
```

### `TestId`, errors

`TestId` (`of`, `indexed`, `element_id` and the DevorApp-specific builders) is kept for parity with the reference package; FullTeaching has no `data-testid` contract, so use plain CSS or XPath.

`BrowserError` is the base class. `ElementTimeoutError` is a Puppeteer timeout (element, state, function or navigation). `BridgeProtocolError` is any other error reported by the bridge (bad selector, JS exception, net error). `BridgeTimeoutError` means no answer at all. `BridgeCrashedError` means the Node process died and carries its stderr.

## CI

```bash
cd puppeteer-python && pip install .
cd bridge && PUPPETEER_SKIP_DOWNLOAD=true npm ci
cd .. && python -m pytest -m bridge          # no SUT needed
python -m pytest -m e2e                       # needs the SUT at SUT_URL
```

Test data fixtures live in `resources/inputs/`, the same CSV/properties files as
`selenium-java/src/test/resources/inputs/`, so both suites exercise the same users and sessions against the same SUT.
