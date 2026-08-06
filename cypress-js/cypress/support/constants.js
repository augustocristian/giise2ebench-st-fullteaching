// FullTeaching selectors and timeouts, ported from common/Constants.java.
//
// Cypress has no built-in XPath support (idiomatic Cypress avoids it in favor of CSS), so
// the handful of XPath locators in the Java source are translated to equivalent CSS here:
// structural `/div[3]` steps become `div:nth-child(3)`, `contains(@class, x)`/`contains(@style, x)`
// become `[class*="x"]`/`[style*="x"]` attribute-contains selectors, and `text() = 'x'` becomes
// jQuery's `:contains('x')` (substring match - fine here since each case is unambiguous).

const WAIT_SECONDS = 150;
// Recursion depth for the spider-navigation link crawler, from BaseLoggedTest.DEPTH.
const SPIDER_DEPTH = 3;
const LOCALHOST = "https://localhost:5000";
const STUDENT_NAME = "Student Imprudent";
const TEACHER_NAME = "Teacher Cheater";

const COURSES_URL = "__HOST__/courses";

// LoggedForumTest.java's hardcoded `courseName` field and CourseTeacherTest.java's
// `properties.getProperty("forum.test.course")` (test.properties, kept in fixtures/ for
// parity) resolve to the same literal - unified here into one constant.
const FORUM_TEST_COURSE_NAME = "Pseudoscientific course for treating the evil eye";

// Other elements
const FOOTER = ".page-footer";
const MAIN_MENU_ARROW = "#arrow-drop-down";
const LOGOUT_BUTTON = "#logout-button";

// Login modal
const LOGIN_MODAL = "#login-modal";
const LOGIN_USER_FIELD = "#email";
const LOGIN_PASSWORD_FIELD = "#password";
const LOGIN_BUTTON = "#log-in-btn";
const DOWNLOAD_BUTTON = "#download-button";

// Dashboard / course list
const COURSES_DASHBOARD_TITLE = ".dashboard-title";
const COURSE_LIST_COURSE_TITLE = ".course-title";
const COURSE_LIST = ".dashboard-col";
const COURSE_LIST_ID = "#course-list";
// Inline `By.className("title")` literal used by CourseNavigationUtilities.java, distinct
// from COURSE_LIST_COURSE_TITLE (".course-title") used elsewhere - kept as-is for fidelity.
const COURSE_TITLE = ".title";

const TABS_DIV = "#tabs-course-details";

// New/edit course modals
const NEW_COURSE_BUTTON = "#add-new-course-btn";
const NEW_COURSE_MODAL = "#course-modal";
const NEW_COURSE_MODAL_NAME_FIELD = "#input-post-course-name";
const NEW_COURSE_MODAL_SAVE = "#submit-post-course-btn";

const EDIT_COURSE_BUTTON = ".course-put-icon";
const EDIT_DELETE_MODAL = "#put-delete-course-modal";
const EDIT_COURSE_MODAL_NAME_FIELD = "#input-put-course-name";
const EDIT_COURSE_MODAL_SAVE = "#submit-put-course-btn";
const EDIT_COURSE_DELETE_CHECK = "#label-delete-checkbox";
const EDIT_COURSE_DELETE_BUTTON = "#delete-course-btn";

const BACK_TO_DASHBOARD = ".btn-floating";
const COURSE_TABS = "#tabs-course-details";

// Course tabs
const HOME_ICON = "#info-tab-icon";
const SESSION_ICON = "#sessions-tab-icon";
const FORUM_ICON = "#forum-tab-icon";
const FILES_ICON = "#files-tab-icon";
const ATTENDERS_ICON = "#attenders-tab-icon";

const SESSION_LIST_NEW_SESSION_ICON = ".add-element-icon";

// Course description
const EDIT_DESCRIPTION_BUTTON = "#edit-course-info";
const EDIT_DESCRIPTION_CONTENT_BOX = ".ui-editor-content";
const EDIT_DESCRIPTION_SAVE_BUTTON = "#send-info-btn";

// was: /html/body/app/div/main/app-settings/div/div[3]/div[2]/ul/li[2]/div[2]
const USERNAME_FIELD = "app-settings div div:nth-child(3) div:nth-child(2) ul li:nth-child(2) div:nth-child(2)";
// was: /html/body/app/div/header/navbar/div/nav/div/ul/li[2]/a
const LOGIN_MENU_LINK = "navbar nav ul li:nth-child(2) a";

// Forum enable/disable (same checkbox id, aliased by intent like the Java constants)
const ENABLE_FORUM_BUTTON = "#label-forum-checkbox";
const DISABLE_FORUM_BUTTON = "#label-forum-checkbox";
const ENABLE_FORUM_MODAL_SAVE_BUTTON = "#put-modal-btn";
const ENABLE_FORUM_MODAL = "#put-delete-modal";

const COURSES_BUTTON = "#courses-button";
const SETTINGS_BUTTON = "#settings-button";

// Forum
const FORUM_NEW_ENTRY_ICON = "#add-entry-icon";
const FORUM_EDIT_ENTRY_ICON = "#edit-forum-icon";
const FORUM_ENTRY_LIST_ENTRY_TITLE = ".forum-entry-title";
const FORUM_ENTRY_ROW = ".entry-title";
const FORUM_ENTRY_LIST_ENTRY_USER = ".user-name";
const FORUM_COMMENT_LIST_ENTRY_TITLE = ".comment-section-title";
const FORUM_COMMENT_LIST_ENTRY_USER = ".user-name";
const FORUM_COMMENT_LIST = "#row-of-comments";
const FORUM_COMMENT_LIST_COMMENT = ".comment-block";
const FORUM_COMMENT_LIST_COMMENT_USER = ".user-name";
const FORUM_COMMENT_LIST_COMMENT_CONTENT = ".message-itself";
const BACK_TO_ENTRIES_LIST_ICON = "#entries-sml-btn";
const FORUM_NEW_ENTRY_MODAL = "#course-details-modal";
const FORUM_NEW_ENTRY_MODAL_TITLE = "#input-post-title";
const FORUM_NEW_ENTRY_MODAL_CONTENT = "#input-post-comment";
const FORUM_NEW_ENTRY_MODAL_POST_BUTTON = "#post-modal-btn";
const FORUM_COMMENT_LIST_NEW_COMMENT_ICON = ".forum-icon";
const FORUM_NEW_COMMENT_MODAL = "#course-details-modal";
const FORUM_NEW_COMMENT_MODAL_TEXT_FIELD = "#input-post-comment";
const FORUM_NEW_COMMENT_MODAL_POST_BUTTON = "#post-modal-btn";
const FORUM_COMMENT_LIST_COMMENT_REPLY_ICON = ".replay-icon";
const FORUM_COMMENT_LIST_MODAL_NEW_REPLY = "#course-details-modal";
const FORUM_COMMENT_LIST_MODAL_NEW_REPLY_TEXT_FIELD = "#input-post-comment";
const FORUM_COMMENT_LIST_COMMENT_DIV = ".comment-div";

// Sessions
const SESSION_LIST_NEW_SESSION_MODAL = "#course-details-modal";
const SESSION_LIST_NEW_SESSION_MODAL_TITLE = "#input-post-title";
const SESSION_LIST_NEW_SESSION_MODAL_CONTENT = "#input-post-comment";
const SESSION_LIST_NEW_SESSION_MODAL_DATE = "#input-post-date";
const SESSION_LIST_NEW_SESSION_MODAL_TIME = "#input-post-time";
const SESSION_LIST_NEW_SESSION_MODAL_POST_BUTTON = "#post-modal-btn";
const SESSION_LIST_SESSION_ROW = ".session-data";
const SESSION_LIST_SESSION_NAME = ".session-title";
const SESSION_LIST_SESSION_ACCESS = ".session-ready";
const SESSION_LIST_SESSION_EDIT_ICON = ".forum-icon";
const SESSION_LIST_EDIT_MODAL = "#put-delete-modal";
const SESSION_LIST_EDIT_MODAL_DELETE_DIV = ".delete-div";

const SESSION_LEFT_MENU_BUTTON = "#side-menu-button";
const SESSION_EXIT_ICON = "#exit-icon";

// Attenders
const ATTENDERS_LIST_ROWS = ".attender-row-div";
const ATTENDERS_LIST_HIGHLIGHTED_ROW = ".attender-name-p";

// Settings
const SETTINGS_USER_EMAIL = "#stng-user-mail";

// Login/dialog helpers used by BaseLoggedTest.java's login()/openDialog()/waitForDialogClosed()
// was: //div[contains(@class, 'modal-overlay') and contains(@style, 'opacity: 0.5')]
const MODAL_OVERLAY_OPENING = ".modal-overlay[style*='opacity: 0.5']";
const MODAL_OPEN = ".modal.my-modal-class.open";
const MODAL_OVERLAY = ".modal-overlay";

// was: //div[@id='dialogId' and contains(@class, 'my-modal-class') and contains(@style, 'opacity: 0') and contains(@style, 'display: none')]
function modalClosedSelector(dialogId) {
  return `#${dialogId}.my-modal-class[style*="opacity: 0"][style*="display: none"]`;
}

module.exports = {
  WAIT_SECONDS,
  SPIDER_DEPTH,
  LOCALHOST,
  STUDENT_NAME,
  TEACHER_NAME,
  COURSES_URL,
  FORUM_TEST_COURSE_NAME,
  FOOTER,
  MAIN_MENU_ARROW,
  LOGOUT_BUTTON,
  LOGIN_MODAL,
  LOGIN_USER_FIELD,
  LOGIN_PASSWORD_FIELD,
  LOGIN_BUTTON,
  DOWNLOAD_BUTTON,
  COURSES_DASHBOARD_TITLE,
  COURSE_LIST_COURSE_TITLE,
  COURSE_LIST,
  COURSE_LIST_ID,
  COURSE_TITLE,
  TABS_DIV,
  NEW_COURSE_BUTTON,
  NEW_COURSE_MODAL,
  NEW_COURSE_MODAL_NAME_FIELD,
  NEW_COURSE_MODAL_SAVE,
  EDIT_COURSE_BUTTON,
  EDIT_DELETE_MODAL,
  EDIT_COURSE_MODAL_NAME_FIELD,
  EDIT_COURSE_MODAL_SAVE,
  EDIT_COURSE_DELETE_CHECK,
  EDIT_COURSE_DELETE_BUTTON,
  BACK_TO_DASHBOARD,
  COURSE_TABS,
  HOME_ICON,
  SESSION_ICON,
  FORUM_ICON,
  FILES_ICON,
  ATTENDERS_ICON,
  SESSION_LIST_NEW_SESSION_ICON,
  EDIT_DESCRIPTION_BUTTON,
  EDIT_DESCRIPTION_CONTENT_BOX,
  EDIT_DESCRIPTION_SAVE_BUTTON,
  USERNAME_FIELD,
  LOGIN_MENU_LINK,
  ENABLE_FORUM_BUTTON,
  DISABLE_FORUM_BUTTON,
  ENABLE_FORUM_MODAL_SAVE_BUTTON,
  ENABLE_FORUM_MODAL,
  COURSES_BUTTON,
  SETTINGS_BUTTON,
  FORUM_NEW_ENTRY_ICON,
  FORUM_EDIT_ENTRY_ICON,
  FORUM_ENTRY_LIST_ENTRY_TITLE,
  FORUM_ENTRY_ROW,
  FORUM_ENTRY_LIST_ENTRY_USER,
  FORUM_COMMENT_LIST_ENTRY_TITLE,
  FORUM_COMMENT_LIST_ENTRY_USER,
  FORUM_COMMENT_LIST,
  FORUM_COMMENT_LIST_COMMENT,
  FORUM_COMMENT_LIST_COMMENT_USER,
  FORUM_COMMENT_LIST_COMMENT_CONTENT,
  BACK_TO_ENTRIES_LIST_ICON,
  FORUM_NEW_ENTRY_MODAL,
  FORUM_NEW_ENTRY_MODAL_TITLE,
  FORUM_NEW_ENTRY_MODAL_CONTENT,
  FORUM_NEW_ENTRY_MODAL_POST_BUTTON,
  FORUM_COMMENT_LIST_NEW_COMMENT_ICON,
  FORUM_NEW_COMMENT_MODAL,
  FORUM_NEW_COMMENT_MODAL_TEXT_FIELD,
  FORUM_NEW_COMMENT_MODAL_POST_BUTTON,
  FORUM_COMMENT_LIST_COMMENT_REPLY_ICON,
  FORUM_COMMENT_LIST_MODAL_NEW_REPLY,
  FORUM_COMMENT_LIST_MODAL_NEW_REPLY_TEXT_FIELD,
  FORUM_COMMENT_LIST_COMMENT_DIV,
  SESSION_LIST_NEW_SESSION_MODAL,
  SESSION_LIST_NEW_SESSION_MODAL_TITLE,
  SESSION_LIST_NEW_SESSION_MODAL_CONTENT,
  SESSION_LIST_NEW_SESSION_MODAL_DATE,
  SESSION_LIST_NEW_SESSION_MODAL_TIME,
  SESSION_LIST_NEW_SESSION_MODAL_POST_BUTTON,
  SESSION_LIST_SESSION_ROW,
  SESSION_LIST_SESSION_NAME,
  SESSION_LIST_SESSION_ACCESS,
  SESSION_LIST_SESSION_EDIT_ICON,
  SESSION_LIST_EDIT_MODAL,
  SESSION_LIST_EDIT_MODAL_DELETE_DIV,
  SESSION_LEFT_MENU_BUTTON,
  SESSION_EXIT_ICON,
  ATTENDERS_LIST_ROWS,
  ATTENDERS_LIST_HIGHLIGHTED_ROW,
  SETTINGS_USER_EMAIL,
  MODAL_OVERLAY_OPENING,
  MODAL_OPEN,
  MODAL_OVERLAY,
  modalClosedSelector,
};
