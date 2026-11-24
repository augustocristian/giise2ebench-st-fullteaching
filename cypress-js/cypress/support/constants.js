// FullTeaching test constants.
//
// Data values (names, depths) live here. CSS selectors live in ./selectors.js, grouped by
// feature; the flat SELECTOR_NAMES exported below are kept for backwards compatibility with
// existing specs. New code should prefer `const { course, forum } = require("./selectors")`.

const s = require("./selectors");

// --- Data ---------------------------------------------------------------------------------
const WAIT_SECONDS = 150;
/** Recursion depth of the spider-navigation link crawler (BaseLoggedTest.DEPTH). */
const SPIDER_DEPTH = 3;
const LOCALHOST = "https://localhost:5000";
const STUDENT_NAME = "Student Imprudent";
const TEACHER_NAME = "Teacher Cheater";
const COURSES_URL = "__HOST__/courses";
// Same literal as the Java `courseName` field and test.properties `forum.test.course`.
const FORUM_TEST_COURSE_NAME = "Pseudoscientific course for treating the evil eye";

// --- Flat selector aliases (backwards compatible; prefer ./selectors.js) --------------------
module.exports = {
  WAIT_SECONDS,
  SPIDER_DEPTH,
  LOCALHOST,
  STUDENT_NAME,
  TEACHER_NAME,
  COURSES_URL,
  FORUM_TEST_COURSE_NAME,

  FOOTER: s.common.footer,
  MAIN_MENU_ARROW: s.common.mainMenuArrow,
  LOGOUT_BUTTON: s.common.logoutButton,
  COURSES_BUTTON: s.common.coursesButton,
  SETTINGS_BUTTON: s.common.settingsButton,
  LOGIN_MENU_LINK: s.common.loginMenuLink,

  LOGIN_MODAL: s.login.modal,
  LOGIN_USER_FIELD: s.login.userField,
  LOGIN_PASSWORD_FIELD: s.login.passwordField,
  LOGIN_BUTTON: s.login.button,
  DOWNLOAD_BUTTON: s.login.downloadButton,

  USERNAME_FIELD: s.settings.userName,
  SETTINGS_USER_EMAIL: s.settings.userEmail,

  MODAL_OPEN: s.modal.open,
  modalOpenSelector: s.modal.openById,

  COURSES_DASHBOARD_TITLE: s.course.dashboardTitle,
  COURSE_LIST_COURSE_TITLE: s.course.listCourseTitle,
  COURSE_LIST: s.course.list,
  COURSE_LIST_ID: s.course.listId,
  COURSE_TITLE: s.course.title,
  BACK_TO_DASHBOARD: s.course.backToDashboard,
  NEW_COURSE_BUTTON: s.course.newButton,
  NEW_COURSE_MODAL: s.course.newModal,
  NEW_COURSE_MODAL_NAME_FIELD: s.course.newNameField,
  NEW_COURSE_MODAL_SAVE: s.course.newSave,
  EDIT_COURSE_BUTTON: s.course.editButton,
  EDIT_DELETE_MODAL: s.course.editModal,
  EDIT_COURSE_MODAL_NAME_FIELD: s.course.editNameField,
  EDIT_COURSE_MODAL_SAVE: s.course.editSave,
  EDIT_COURSE_DELETE_CHECK: s.course.deleteCheck,
  EDIT_COURSE_DELETE_BUTTON: s.course.deleteButton,
  EDIT_DESCRIPTION_BUTTON: s.course.editDescriptionButton,
  EDIT_DESCRIPTION_CONTENT_BOX: s.course.editDescriptionContent,
  EDIT_DESCRIPTION_SAVE_BUTTON: s.course.editDescriptionSave,

  TABS_DIV: s.tabs.container,
  COURSE_TABS: s.tabs.container,
  HOME_ICON: s.tabs.homeIcon,
  SESSION_ICON: s.tabs.sessionIcon,
  FORUM_ICON: s.tabs.forumIcon,
  FILES_ICON: s.tabs.filesIcon,
  ATTENDERS_ICON: s.tabs.attendersIcon,

  ENABLE_FORUM_BUTTON: s.forum.toggleCheckbox,
  DISABLE_FORUM_BUTTON: s.forum.toggleCheckbox,
  ENABLE_FORUM_MODAL_SAVE_BUTTON: s.forum.toggleSave,
  ENABLE_FORUM_MODAL: s.forum.toggleModal,
  FORUM_NEW_ENTRY_ICON: s.forum.newEntryIcon,
  FORUM_EDIT_ENTRY_ICON: s.forum.editIcon,
  FORUM_ENTRY_LIST_ENTRY_TITLE: s.forum.entryTitle,
  FORUM_ENTRY_ROW: s.forum.entryRow,
  FORUM_ENTRY_LIST_ENTRY_USER: s.forum.entryUser,
  FORUM_COMMENT_LIST_ENTRY_TITLE: s.forum.commentSectionTitle,
  FORUM_COMMENT_LIST_ENTRY_USER: s.forum.sectionAuthor,
  FORUM_COMMENT_LIST: s.forum.commentList,
  FORUM_COMMENT_LIST_COMMENT: s.forum.comment,
  FORUM_COMMENT_LIST_COMMENT_USER: s.forum.commentUser,
  FORUM_COMMENT_LIST_COMMENT_CONTENT: s.forum.commentContent,
  BACK_TO_ENTRIES_LIST_ICON: s.forum.backToEntriesIcon,
  FORUM_NEW_ENTRY_MODAL: s.forum.newEntryModal.root,
  FORUM_NEW_ENTRY_MODAL_TITLE: s.forum.newEntryModal.title,
  FORUM_NEW_ENTRY_MODAL_CONTENT: s.forum.newEntryModal.content,
  FORUM_NEW_ENTRY_MODAL_POST_BUTTON: s.forum.newEntryModal.postButton,
  FORUM_COMMENT_LIST_NEW_COMMENT_ICON: s.forum.newCommentIcon,
  FORUM_NEW_COMMENT_MODAL: s.forum.newCommentModal.root,
  FORUM_NEW_COMMENT_MODAL_TEXT_FIELD: s.forum.newCommentModal.text,
  FORUM_NEW_COMMENT_MODAL_POST_BUTTON: s.forum.newCommentModal.postButton,
  FORUM_COMMENT_LIST_COMMENT_REPLY_ICON: s.forum.replyIcon,
  FORUM_COMMENT_LIST_MODAL_NEW_REPLY: s.forum.replyModal.root,
  FORUM_COMMENT_LIST_MODAL_NEW_REPLY_TEXT_FIELD: s.forum.replyModal.text,
  FORUM_COMMENT_LIST_COMMENT_DIV: s.forum.commentDiv,

  SESSION_LIST_NEW_SESSION_ICON: s.session.newIcon,
  SESSION_LIST_NEW_SESSION_MODAL: s.session.newModal.root,
  SESSION_LIST_NEW_SESSION_MODAL_TITLE: s.session.newModal.title,
  SESSION_LIST_NEW_SESSION_MODAL_CONTENT: s.session.newModal.content,
  SESSION_LIST_NEW_SESSION_MODAL_DATE: s.session.newModal.date,
  SESSION_LIST_NEW_SESSION_MODAL_TIME: s.session.newModal.time,
  SESSION_LIST_NEW_SESSION_MODAL_POST_BUTTON: s.session.newModal.postButton,
  SESSION_LIST_SESSION_ROW: s.session.row,
  SESSION_LIST_SESSION_NAME: s.session.name,
  SESSION_LIST_SESSION_ACCESS: s.session.access,
  SESSION_LIST_SESSION_EDIT_ICON: s.session.editIcon,
  SESSION_LIST_EDIT_MODAL: s.session.editModal,
  SESSION_LIST_EDIT_MODAL_DELETE_DIV: s.session.editModalDeleteDiv,
  SESSION_LEFT_MENU_BUTTON: s.session.leftMenuButton,
  SESSION_EXIT_ICON: s.session.exitIcon,

  ATTENDERS_LIST_ROWS: s.attenders.rows,
  ATTENDERS_LIST_HIGHLIGHTED_ROW: s.attenders.highlightedRow,
};
