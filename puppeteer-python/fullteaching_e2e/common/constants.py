# -*- coding: utf-8 -*-
"""FullTeaching selectors and timeouts, ported from common/Constants.java.

Locators are plain strings consumed by fullteaching_e2e.utils.wait/click: a CSS
selector by default, or an XPath expression when prefixed with "xpath=" (the
same convention Playwright uses), since pyppeteer needs to know which of
page.waitForSelector/page.J or page.waitForXPath/page.Jx to call.
"""

WAIT_SECONDS = 150
# Recursion depth for the spider-navigation link crawler, from BaseLoggedTest.DEPTH.
SPIDER_DEPTH = 3
LOCALHOST = "https://localhost:5000"
PORT = "11811"
STUDENT_NAME = "Student Imprudent"
TEACHER_NAME = "Teacher Cheater"

COURSES_URL = "__HOST__/courses"

# Other elements
FOOTER = ".page-footer"
MAIN_MENU_ARROW = "#arrow-drop-down"
LOGOUT_BUTTON = "#logout-button"

# Login modal
LOGIN_MODAL = "#login-modal"
LOGIN_USER_FIELD = "#email"
LOGIN_PASSWORD_FIELD = "#password"
LOGIN_BUTTON = "#log-in-btn"

# Dashboard / course list
COURSES_DASHBOARD_TITLE = ".dashboard-title"
FIRST_COURSE = "xpath=/html/body/app/div/main/app-dashboard/div/div[3]/div/div[1]/ul/li[1]"
GO_TO_COURSE_XPATH = "/div[2]"  # concatenated onto a course xpath by callers
COURSE_LIST_COURSE_TITLE = ".course-title"
COURSE_LIST = ".dashboard-col"
# Inline `By.className("title")` literal used by CourseNavigationUtilities.java, distinct
# from COURSE_LIST_COURSE_TITLE (".course-title") used elsewhere - kept as-is for fidelity.
COURSE_TITLE = ".title"

TABS_DIV = "#tabs-course-details"

# New/edit course modals
NEW_COURSE_BUTTON = "#add-new-course-btn"
NEW_COURSE_MODAL = "#course-modal"
NEW_COURSE_MODAL_NAME_FIELD = "#input-post-course-name"
NEW_COURSE_MODAL_SAVE = "#submit-post-course-btn"

EDIT_COURSE_BUTTON = ".course-put-icon"
EDIT_DELETE_MODAL = "#put-delete-course-modal"
EDIT_COURSE_MODAL_NAME_FIELD = "#input-put-course-name"
EDIT_COURSE_MODAL_SAVE = "#submit-put-course-btn"
EDIT_COURSE_DELETE_CHECK = "#label-delete-checkbox"
EDIT_COURSE_DELETE_BUTTON = "#delete-course-btn"

BACK_TO_DASHBOARD = ".btn-floating"
COURSE_TABS = "#tabs-course-details"

# Course tabs
FORUM_TAB_XPATH = "./div[1]/div[3]"
HOME_ICON = "#info-tab-icon"
SESSION_ICON = "#sessions-tab-icon"
FORUM_ICON = "#forum-tab-icon"
FILES_ICON = "#files-tab-icon"
ATTENDERS_ICON = "#attenders-tab-icon"

SESSION_LIST_NEW_SESSION_ICON = ".add-element-icon"

# Course description
EDIT_DESCRIPTION_BUTTON = "#edit-course-info"
EDIT_DESCRIPTION_CONTENT_BOX = ".ui-editor-content"
EDIT_DESCRIPTION_SAVE_BUTTON = "#send-info-btn"

USERNAME_XPATH = "xpath=/html/body/app/div/main/app-settings/div/div[3]/div[2]/ul/li[2]/div[2]"
LOGIN_MENU = "xpath=/html/body/app/div/header/navbar/div/nav/div/ul/li[2]/a"

# Forum enable/disable (same checkbox id, aliased by intent like the Java constants)
ENABLE_FORUM_BUTTON = "#label-forum-checkbox"
DISABLE_FORUM_BUTTON = "#label-forum-checkbox"
ENABLE_FORUM_MODAL_SAVE_BUTTON = "#put-modal-btn"
ENABLE_FORUM_MODAL = "#put-delete-modal"

ENABLE_COURSE_DELETION_BUTTON_XPATH = (
    "/html/body/app/div/com.fullteaching.e2e.no_elastest.main/app-dashboard/div/div[2]/div/div/form/div[2]/div/div/label"
)
DELETE_COURSE_BUTTON_XPATH = (
    "/html/body/app/div/com.fullteaching.e2e.no_elastest.main/app-dashboard/div/div[2]/div/div/form/div[2]/div/a"
)

COURSES_BUTTON = "#courses-button"
SETTINGS_BUTTON = "#settings-button"

# Forum
FORUM_NEW_ENTRY_ICON = "#add-entry-icon"
FORUM_EDIT_ENTRY_ICON = "#edit-forum-icon"
FORUM_ENTRY_LIST_ENTRY_TITLE = ".forum-entry-title"
FORUM_ENTRY_LIST_ENTRIES_UL = ".entries-side-view"
FORUM_ENTRY_LIST_ENTRY_USER = ".user-name"
FORUM_COMMENT_LIST_ENTRY_TITLE = ".comment-section-title"
FORUM_COMMENT_LIST_ENTRY_USER = ".user-name"
FORUM_COMMENT_LIST = "#row-of-comments"
FORUM_COMMENT_LIST_COMMENT = ".comment-block"
FORUM_COMMENT_LIST_COMMENT_USER = ".user-name"
FORUM_COMMENT_LIST_COMMENT_CONTENT = ".message-itself"
BACK_TO_ENTRIES_LIST_ICON = "#entries-sml-btn"
FORUM_NEW_ENTRY_MODAL = "#course-details-modal"
FORUM_NEW_ENTRY_MODAL_TITLE = "#input-post-title"
FORUM_NEW_ENTRY_MODAL_CONTENT = "#input-post-comment"
FORUM_NEW_ENTRY_MODAL_POST_BUTTON = "#post-modal-btn"
FORUM_COMMENT_LIST_NEW_COMMENT_ICON = ".forum-icon"
FORUM_NEW_COMMENT_MODAL = "#course-details-modal"
FORUM_NEW_COMMENT_MODAL_TEXT_FIELD = "#input-post-comment"
FORUM_NEW_COMMENT_MODAL_POST_BUTTON = "#post-modal-btn"
FORUM_COMMENT_LIST_COMMENT_REPLY_ICON = ".replay-icon"
FORUM_COMMENT_LIST_MODAL_NEW_REPLY = "#course-details-modal"
FORUM_COMMENT_LIST_MODAL_NEW_REPLY_TEXT_FIELD = "#input-post-comment"
FORUM_COMMENT_LIST_COMMENT_DIV = ".comment-div"

# Sessions
SESSION_LIST_NEW_SESSION_MODAL = "#course-details-modal"
SESSION_LIST_NEW_SESSION_MODAL_TITLE = "#input-post-title"
SESSION_LIST_NEW_SESSION_MODAL_CONTENT = "#input-post-comment"
SESSION_LIST_NEW_SESSION_MODAL_DATE = "#input-post-date"
SESSION_LIST_NEW_SESSION_MODAL_TIME = "#input-post-time"
SESSION_LIST_NEW_SESSION_MODAL_POST_BUTTON = "#post-modal-btn"
SESSION_LIST_SESSION_ROW = ".session-data"
SESSION_LIST_SESSION_NAME = ".session-title"
SESSION_LIST_SESSION_ACCESS = ".session-ready"
SESSION_LIST_SESSION_EDIT_ICON = ".forum-icon"
SESSION_LIST_EDIT_MODAL = "#put-delete-modal"
SESSION_LIST_EDIT_MODAL_DELETE_DIV = ".delete-div"

SESSION_LEFT_MENU_BUTTON = "#side-menu-button"
SESSION_EXIT_ICON = "#exit-icon"

# Attenders
ATTENDERS_LIST_ROWS = ".attender-row-div"
ATTENDERS_LIST_HIGHLIGHTED_ROW = ".attender-name-p"

# Settings
SETTINGS_USER_EMAIL = "#stng-user-mail"

# Login/dialog helpers used by BaseLoggedTest.java's login()/openDialog()/waitForDialogClosed()
DOWNLOAD_BUTTON = "#download-button"
COURSE_LIST_ID = "#course-list"
MODAL_OVERLAY_OPENING = "xpath=//div[contains(@class, 'modal-overlay') and contains(@style, 'opacity: 0.5')]"
MODAL_OPEN = ".modal.my-modal-class.open"
MODAL_OVERLAY = ".modal-overlay"


def modal_closed_xpath(dialog_id: str) -> str:
    return (
        f"xpath=//div[@id='{dialog_id}' and contains(@class, 'my-modal-class') "
        "and contains(@style, 'opacity: 0') and contains(@style, 'display: none')]"
    )
