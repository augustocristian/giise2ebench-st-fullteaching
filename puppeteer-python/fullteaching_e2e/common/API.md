# Public API of `fullteaching_e2e.common` and `fullteaching_e2e.utils`

Everything is `async` unless noted. `user` is a `BrowserUser`. Elements are **lazy `Locator`s** of
`fullteaching_e2e.browser` (never element handles): they auto-wait on actions (`click`, `fill`,
`text`, `wait_for`...). A locator waits on the FIRST element its CSS matches, so tests should use
specific selectors. `await page.url()` is a coroutine (not a property); there is no `page.goBack()`
(use `navigation_utilities.go_back`) and no XPath/text selectors: all selectors are CSS.

Every helper that used to take `(page, host, ...)` now takes `(user, ...)`: the host is `user.app_url`.

## common/config.py
- `AppConfig(app_url, tjob_name, teacher_browser, student_browser)` frozen dataclass (browser names informational: Chromium only).
- `load_app_config() -> AppConfig` resolves `SUT_URL` / `tjob_name` (tjob only honoured with SUT_URL) / `app.url` / default `https://localhost:5000`.
- `is_headed() -> bool` (`HEADED`), `browser_executable_path() -> str | None` (`PUPPETEER_EXECUTABLE_PATH`), `browser_args() -> list[str]` (`BROWSER_ARGS`).
- `ROOT_DIR`, `RESOURCES_DIR`, `INPUTS_DIR`: `Path`s of the project, `resources/` and `resources/inputs/`.

## common/browser_user.py
- `CHROMIUM_ARGS`: fake media stream + ignore-certificate-errors flags.
- `launch_browser() -> Browser`: session-wide Chrome with `CHROMIUM_ARGS` + `BROWSER_ARGS` (use in the `browser` fixture; close it with `await browser.close()`).
- `BrowserUser` dataclass: fields `client_data`, `browser`, `context` (BrowserContext), `page` (Page), `app_url`, `timeout_ms`, `test_name`, `is_on_session`.
  - `locator(selector, timeout_ms=None) -> Locator`: `page.locator` with the user's timeout (30 s by default, 150 s for media users). Prefer it over `user.page.locator`.
  - `run_javascript(script, *args)`: `page.evaluate`; `script` is a JS *function expression* (`"(a) => a + 1"`).
  - `wait_until(action, error_message)`: awaits `action()`; `ElementTimeoutError` is re-raised prefixed with the user and message.
  - `dispose()`: closes page and context (idempotent).
- `setup_browser(browser, app_url, test_name, user_identifier, seconds_of_wait=WAIT_SECONDS) -> BrowserUser`: new context + page, opens `app_url`, injects the `window.MY_FUNC` video probe.

## common/base_logged_test.py
- `slow_login(user, email, password) -> str` / `quick_login(...) -> str`: log in through the welcome dialog; return the user's display name; set `user.is_on_session = True`.
- `logout(user)`: leaves a video session if needed, uses the collapsed navbar if the desktop menu is not shown; sets `is_on_session = False`.
- `open_dialog(user, target: str | Locator)`: click the opener, wait for a native `dialog[open]`.
- `wait_for_dialog_closed(user, dialog_id, error_message)`: waits for `dialog#<id>` to be closed or gone.
- `get_user_name(user, go_back=True) -> str`: reads the Name row of `/settings`, going there (and back) if needed; `NotLoggedException` if logged out.
- `UserFactory(browser, config: AppConfig, test_name)`: per-test user lifecycle.
  - `create(user_identifier, seconds_of_wait=WAIT_SECONDS) -> BrowserUser` (any number of users, all in the same Chrome; the first one created is the teacher/primary).
  - `users -> list[BrowserUser]`.
  - `close_all(screenshots_dir: Path | None = None)`: optional failure screenshots, logout of users on session, dispose all; raises `ExceptionGroup` after trying every user.

## common/constants.py
Selectors (CSS, see file) plus `WAIT_SECONDS = 30`, `MEDIA_WAIT_SECONDS = 150` (use for video-session users; before, `WAIT_SECONDS` was 150), `SPIDER_DEPTH`, `LOCALHOST`, `STUDENT_NAME`, `TEACHER_NAME`, `FORUM_TEST_COURSE_NAME`, `COURSES_PATH`, `modal_open_selector(dialog_id) -> str`.
Renamed/removed vs. the pyppeteer version: `USERNAME_XPATH` -> `SETTINGS_USER_NAME`; `MODAL_OVERLAY_OPENING`/`MODAL_OVERLAY`/`modal_closed_xpath` -> `MODAL_OPEN` / `modal_open_selector`; `COURSES_URL` -> `COURSES_PATH`; `FORUM_TAB_XPATH`, `GO_TO_COURSE_XPATH`, `*_XPATH` deletion constants removed; new `NEW_COURSE_ICON`, `COURSE_LIST_ITEM`, `COURSE_LIST_ID`, `FORUM_ENTRY_ROW`, `DESCRIPTION_VIEW`, `DESCRIPTION_VIEW_TEXT`, `SESSION_FIXED_ICON`, `MOBILE_MENU_BUTTON`, `MOBILE_LOGOUT_BUTTON`.

## common/navigation_utilities.py
- `FindOption` enum: `CLASS`, `TEXT`, `VALUE`, `ATTRIBUTE`.
- `am_i_not_here(current_url, url) -> bool` (sync, pure): URLs differ, ignoring a trailing slash.
- `get_url_and_wait_footer(page, url)`: goto + footer visible (takes a `Page`).
- `go_back(page)`: history back, returns after the URL changed (takes a `Page`).
- `to_courses_home(user)`: navbar Courses button unless already on `/courses`; waits for the dashboard.
- `get_option(options: list[Locator], find, find_type, attribute="") -> Locator | None` (no `page` argument any more).

## common/course_navigation_utilities.py
- `new_course(user, course_name) -> str`; `delete_course(user, course_name)`; `change_course_name(user, old, new)`.
- `get_courses_list(user) -> list[str]`; `get_course_by_name(user, name) -> Locator` (the `li.course-list-item`; `ElementNotFoundException` if missing; use `.within(c.COURSE_LIST_COURSE_TITLE)`, `.within(c.EDIT_COURSE_BUTTON)`...).
- `check_if_course_exists(user, title) -> bool` (one-shot); `check_if_course_exists_with_retries(user, title, retries) -> bool` (~1 s per retry); `assert_course_exists(user, title, timeout_s=20)` / `assert_course_not_exists(...)` (raise `ElementTimeoutError`).
- Tabs: `get_tab_element_from_icon(user, icon_selector) -> Locator` (sync, the `li.tab`); `get_tab_id(user, icon) -> str`; `go2_tab(user, icon)`; `get_tab_content(user, icon) -> Locator` (content container, only in the DOM for the active tab); `wait4_tab_content(user, icon) -> Locator` (waits visible).
- Attenders: `is_user_in_attenders_list(user, name) -> bool`; `get_highlighted_attender(user) -> str`.

## common/forum_navigation_utilities.py
- `is_forum_enabled(forum_tab_content: Locator) -> bool`.
- `get_full_entry_list(user) -> list[str]`; `get_user_entries(user, user_name) -> list[str]`; `get_entry(user, title) -> Locator` (row; waits for a fresh entry; `ElementNotFoundException`).
- `get_comments(user) -> list[Locator]` (waits for the first comment, one locator per top-level `.comment-block`); `get_user_comments(user, user_name) -> list[Locator]`; `get_replies(comment: Locator) -> list[Locator]` (takes no user).
- `new_entry(user, title, content)`; `enable_forum(user)`; `disable_forum(user)` (raise `AssertionError` if the state does not follow).
- `get_high_lighted_comments` was removed (duplicate of `get_user_comments`).

## common/session_navigation_utilities.py
- `get_full_session_list(user) -> list[str]`; `get_session(user, name) -> Locator` (row; `ElementNotFoundException`).

## common/spider_navigation.py (take a `Page`, links are `href` strings)
- `get_page_links(page, host=None) -> list[str]`; `get_unexplored_page_links(page, explored, host=None) -> list[str]`;
  `explore_links(page, page_links, explored, depth, host=None) -> dict[str, str]` (`"OK"`/`"KO"` per href). `host` defaults to the app URL.

## common/user_utilities.py
- `check_login(user, email)` (`NotLoggedException`, `BadUserException`); `check_log_out(user)` (`ElementNotFoundException`).

## common/exceptions.py
`ElementNotFoundException`, `NotLoggedException`, `BadUserException` (`TimeOutException` removed; timeouts are `fullteaching_e2e.browser.ElementTimeoutError`).

## utils/
- `wait.poll_until(factory, description="condition", timeout_s=20.0)`: retries an async factory until it returns something other than `False`/`None` without raising; raises `ElementTimeoutError`. Use only for computed conditions; selector conditions use `locator.wait_for(...)`. (`not_too_much`, `a_little`, `footer`, `wait_for_page_loaded` are gone: locators auto-wait.)
- `element.all_of(locator) -> list[Locator]` (one `nth` locator per current match); `element.texts(locator) -> list[str]`; `element.find_row_by_child_text(rows, child_selector, text) -> Locator | None`. (`find_one`, `find_all`, `get_text`, `get_attribute`, `get_dom_property`, `get_tag_name`: use the Locator methods `within`, `text`, `attribute`, `property`.)
- `click.by_js(page, selector)`: DOM `click()` on the first match (when an overlay blocks the real click). (`click.element` is gone: `await locator.click()`.)
- Removed: `keyboard` (`await locator.fill("")` clears; `locator.press`), `scroll`, `dom_manager` (click the child, or use `within`).
- `parameter_loader.get_test_users() / get_test_students() / get_test_teachers() -> list[tuple[str, str, str]]` (sync, for `parametrize("mail,password,role", ...)`).
- `user.User` frozen dataclass (`name`, `password`, `role`, `is_student`, `is_teacher`, `csv()`).
- `user_loader`: `DEFAULT_USER_FILE`, `parse_user(line)`, `load_users(path=DEFAULT_USER_FILE) -> dict[str, User]` (cached), `retrieve_user(name)`, `get_all_users() -> list[User]`.
- `properties.load_properties(path: Path) -> dict[str, str]`.
