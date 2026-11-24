"""FullTeaching selectors, timeouts and fixed test data, ported from ``common/Constants.java``.

Every selector is plain CSS, resolved by the Puppeteer bridge. They were verified against the
Angular sources of the SUT (``sut/src/main/angular/src/app``). A Puppeteer locator waits on the
FIRST element it matches, so selectors that can match several elements must be specific enough
for the first one to be the wanted one.
"""

# Default action timeout of a user, and the longer one for media/video-session flows
# (WebRTC negotiation, fake camera start-up), in seconds.
WAIT_SECONDS = 30
MEDIA_WAIT_SECONDS = 150
# Recursion depth of the spider-navigation link crawler, from BaseLoggedTest.DEPTH.
SPIDER_DEPTH = 3
# App URL used when neither SUT_URL nor app.url is set.
LOCALHOST = "https://localhost:5000"
STUDENT_NAME = "Student Imprudent"
TEACHER_NAME = "Teacher Cheater"
# Course used by the forum tests (also stored as forum.test.course in resources/inputs/test.properties).
FORUM_TEST_COURSE_NAME = "Pseudoscientific course for treating the evil eye"

COURSES_PATH = "/courses"

# Other elements
FOOTER = ".page-footer"
MAIN_MENU_ARROW = "#arrow-drop-down"
LOGOUT_BUTTON = "#logout-button"
# Collapsed ("shrunk") navbar: hamburger button and the Logout button of the side nav.
MOBILE_MENU_BUTTON = "a.button-collapse"
MOBILE_LOGOUT_BUTTON = "#nav-mobile button.nav-action-btn"
# Navbar "Log in" link, only present while logged out: the entry right after "Sign up".
LOGIN_MENU = "#navigation-bar li:has(#signUpButton) + li > a"

# Login modal
LOGIN_MODAL = "#login-modal"
LOGIN_USER_FIELD = "#email"
LOGIN_PASSWORD_FIELD = "#password"
LOGIN_BUTTON = "#log-in-btn"
DOWNLOAD_BUTTON = "#download-button"

# Native dialogs: <dialog class="modal my-modal-class"> with the `open` attribute while shown
# (shared/native-dialog.directive.ts). The old materialize ".modal-overlay"/"opacity" markup is gone.
MODAL_OPEN = "dialog.modal.my-modal-class[open]"

# Dashboard / course list. The dashboard has two ".dashboard-col" columns (MY COURSES and
# MY CALENDAR), so everything is scoped to the one holding the course list.
COURSE_LIST = ".dashboard-col:has(#course-list)"
COURSE_LIST_ID = "#course-list"
COURSES_DASHBOARD_TITLE = ".dashboard-col:has(#course-list) .dashboard-title"
COURSE_LIST_ITEM = "#course-list .course-list-item"
FIRST_COURSE = "#course-list > li.course-list-item:first-child"
COURSE_LIST_COURSE_TITLE = ".course-title"
# The course-title anchor inside a course row.
COURSE_TITLE = ".title"

TABS_DIV = "#tabs-course-details"
COURSE_TABS = "#tabs-course-details"

# New/edit course modals. The "add" anchor wraps a floated icon and has an empty box, so the
# icon is what gets clicked.
NEW_COURSE_BUTTON = "#add-new-course-btn"
NEW_COURSE_ICON = "#add-course-icon"
NEW_COURSE_MODAL = "#course-modal"
NEW_COURSE_MODAL_NAME_FIELD = "#input-post-course-name"
NEW_COURSE_MODAL_SAVE = "#submit-post-course-btn"

EDIT_COURSE_BUTTON = ".course-put-icon"
EDIT_DELETE_MODAL = "#put-delete-course-modal"
EDIT_COURSE_MODAL_NAME_FIELD = "#input-put-course-name"
EDIT_COURSE_MODAL_SAVE = "#submit-put-course-btn"
EDIT_COURSE_DELETE_CHECK = "#label-delete-checkbox"
EDIT_COURSE_DELETE_BUTTON = "#delete-course-btn"

BACK_TO_DASHBOARD = "#back-to-dashboard-btn"

# Course tabs: the tab itself is the <li class="tab"> holding the icon.
HOME_ICON = "#info-tab-icon"
SESSION_ICON = "#sessions-tab-icon"
FORUM_ICON = "#forum-tab-icon"
FILES_ICON = "#files-tab-icon"
ATTENDERS_ICON = "#attenders-tab-icon"

SESSION_LIST_NEW_SESSION_ICON = "#add-session-icon"

# Course description (Quill): the editable box also has the rendered view's ql-editor class,
# so the two are told apart by ql-editor-custom.
EDIT_DESCRIPTION_BUTTON = "#edit-course-info"
EDIT_DESCRIPTION_CONTENT_BOX = ".ql-editor:not(.ql-editor-custom)"
DESCRIPTION_VIEW = ".ql-editor-custom"
DESCRIPTION_VIEW_TEXT = ".ql-editor-custom p"
EDIT_DESCRIPTION_SAVE_BUTTON = "#send-info-btn"

# Settings page: value of the "Name" row (second row of the list), and the e-mail one.
SETTINGS_USER_NAME = "app-settings .collection > li:nth-child(2) .setting-content"
SETTINGS_USER_EMAIL = "#stng-user-mail"

# Forum enable/disable (same checkbox label, aliased by intent like the Java constants)
ENABLE_FORUM_BUTTON = "#label-forum-checkbox"
DISABLE_FORUM_BUTTON = "#label-forum-checkbox"
ENABLE_FORUM_MODAL_SAVE_BUTTON = "#put-modal-btn"
ENABLE_FORUM_MODAL = "#put-delete-modal"

COURSES_BUTTON = "#courses-button"
SETTINGS_BUTTON = "#settings-button"

# Forum
FORUM_NEW_ENTRY_ICON = "#add-entry-icon"
FORUM_EDIT_ENTRY_ICON = "#edit-forum-icon"
FORUM_ENTRY_ROW = ".entry-title"
FORUM_ENTRY_LIST_ENTRY_TITLE = ".forum-entry-title"
FORUM_ENTRY_LIST_ENTRIES_UL = ".entries-side-view"
FORUM_ENTRY_LIST_ENTRY_USER = ".forum-entry-author"
FORUM_COMMENT_LIST_ENTRY_TITLE = ".comment-section-title"
FORUM_COMMENT_LIST_ENTRY_USER = ".comment-section-title .user-name"
FORUM_COMMENT_LIST = "#row-of-comments"
FORUM_COMMENT_LIST_COMMENT = ".comment-block"
# Replies nested in a comment carry the same class: take the first match of a comment.
FORUM_COMMENT_LIST_COMMENT_USER = ".forum-comment-author"
FORUM_COMMENT_LIST_COMMENT_CONTENT = ".message-itself"
BACK_TO_ENTRIES_LIST_ICON = "#entries-sml-btn"
FORUM_NEW_ENTRY_MODAL = "#course-details-modal"
FORUM_NEW_ENTRY_MODAL_TITLE = "#input-post-title"
FORUM_NEW_ENTRY_MODAL_CONTENT = "#input-post-comment"
FORUM_NEW_ENTRY_MODAL_POST_BUTTON = "#post-modal-btn"
# The comments header and each comment have a text icon and a video icon: the text ones are targeted.
FORUM_COMMENT_LIST_NEW_COMMENT_ICON = "#row-of-comments a[title='New comment'] .forum-icon"
FORUM_NEW_COMMENT_MODAL = "#course-details-modal"
FORUM_NEW_COMMENT_MODAL_TEXT_FIELD = "#input-post-comment"
FORUM_NEW_COMMENT_MODAL_POST_BUTTON = "#post-modal-btn"
FORUM_COMMENT_LIST_COMMENT_REPLY_ICON = "a[title='Send replay'] .replay-icon"
FORUM_COMMENT_LIST_MODAL_NEW_REPLY = "#course-details-modal"
FORUM_COMMENT_LIST_MODAL_NEW_REPLY_TEXT_FIELD = "#input-post-comment"
FORUM_COMMENT_LIST_COMMENT_DIV = ".comment-div"

# Sessions. In the new-session modal <input type=date/time> only accept "yyyy-MM-dd" / "HH:mm".
SESSION_LIST_NEW_SESSION_MODAL = "#course-details-modal"
SESSION_LIST_NEW_SESSION_MODAL_TITLE = "#input-post-title"
SESSION_LIST_NEW_SESSION_MODAL_CONTENT = "#input-post-comment"
SESSION_LIST_NEW_SESSION_MODAL_DATE = "#input-post-date"
SESSION_LIST_NEW_SESSION_MODAL_TIME = "#input-post-time"
SESSION_LIST_NEW_SESSION_MODAL_POST_BUTTON = "#post-modal-btn"
SESSION_LIST_SESSION_ROW = ".session-data"
SESSION_LIST_SESSION_NAME = ".session-title"
SESSION_LIST_SESSION_ACCESS = ".session-ready"
SESSION_LIST_SESSION_EDIT_ICON = ".edit-session-icon"
SESSION_LIST_EDIT_MODAL = "#put-delete-modal"
SESSION_LIST_EDIT_MODAL_DELETE_DIV = ".delete-div"

# Video-session page
SESSION_FIXED_ICON = "#fixed-icon"
SESSION_LEFT_MENU_BUTTON = "#side-menu-button"
SESSION_EXIT_ICON = "#exit-icon"

# Attenders
ATTENDERS_LIST_ROWS = ".attender-row-div"
ATTENDERS_LIST_HIGHLIGHTED_ROW = ".attender-name-p"


def modal_open_selector(dialog_id: str) -> str:
    """Selector of the dialog with the given id while it is open.

    Waiting for it to be hidden also covers dialogs that the SUT removes from the DOM once closed.
    """
    return f"dialog#{dialog_id}[open]"
