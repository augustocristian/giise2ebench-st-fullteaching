// FullTeaching CSS selectors grouped by feature.
//
// Cypress has no built-in XPath support, so the XPath locators of the Java source are
// translated to CSS: `/div[3]` -> `div:nth-child(3)`, `contains(@class, x)` -> `[class*="x"]`,
// `text() = 'x'` -> jQuery `:contains('x')`.
//
// Most FullTeaching modals reuse the same ids (#course-details-modal, #input-post-title, ...),
// so the shared "details modal" is declared once and referenced by forum and sessions.

const detailsModal = {
  root: "#course-details-modal",
  title: "#input-post-title",
  content: "#input-post-comment",
  date: "#input-post-date",
  time: "#input-post-time",
  postButton: "#post-modal-btn",
};

const common = {
  footer: ".page-footer",
  mainMenuArrow: "#arrow-drop-down",
  logoutButton: "#logout-button",
  coursesButton: "#courses-button",
  settingsButton: "#settings-button",
  // was: /html/body/app/div/header/navbar/div/nav/div/ul/li[2]/a
  loginMenuLink: "navbar nav ul li:nth-child(2) a",
};

const modal = {
  // was: //div[contains(@class, 'modal-overlay') and contains(@style, 'opacity: 0.5')]
  overlayOpening: ".modal-overlay[style*='opacity: 0.5']",
  open: ".modal.my-modal-class.open",
  overlay: ".modal-overlay",
  /** Selector of the dialog `dialogId` once its close animation has finished. */
  closed: (dialogId) => `#${dialogId}.my-modal-class[style*="opacity: 0"][style*="display: none"]`,
};

const login = {
  modal: "#login-modal",
  userField: "#email",
  passwordField: "#password",
  button: "#log-in-btn",
  downloadButton: "#download-button",
};

const settings = {
  userEmail: "#stng-user-mail",
  // was: /html/body/app/div/main/app-settings/div/div[3]/div[2]/ul/li[2]/div[2]
  userName: "app-settings div div:nth-child(3) div:nth-child(2) ul li:nth-child(2) div:nth-child(2)",
};

const course = {
  dashboardTitle: ".dashboard-title",
  list: ".dashboard-col",
  listId: "#course-list",
  listItem: ".course-list-item",
  /** Title inside a course <li> (distinct from `listCourseTitle`, kept as in the Java source). */
  title: ".title",
  listCourseTitle: ".course-title",
  backToDashboard: ".btn-floating",
  newButton: "#add-new-course-btn",
  newModal: "#course-modal",
  newNameField: "#input-post-course-name",
  newSave: "#submit-post-course-btn",
  editButton: ".course-put-icon",
  editModal: "#put-delete-course-modal",
  editNameField: "#input-put-course-name",
  editSave: "#submit-put-course-btn",
  deleteCheck: "#label-delete-checkbox",
  deleteButton: "#delete-course-btn",
  editDescriptionButton: "#edit-course-info",
  editDescriptionContent: ".ui-editor-content",
  editDescriptionSave: "#send-info-btn",
};

const tabs = {
  container: "#tabs-course-details",
  homeIcon: "#info-tab-icon",
  sessionIcon: "#sessions-tab-icon",
  forumIcon: "#forum-tab-icon",
  filesIcon: "#files-tab-icon",
  attendersIcon: "#attenders-tab-icon",
};

const forum = {
  // The enable and disable actions share the same checkbox.
  toggleCheckbox: "#label-forum-checkbox",
  toggleSave: "#put-modal-btn",
  toggleModal: "#put-delete-modal",
  newEntryIcon: "#add-entry-icon",
  editIcon: "#edit-forum-icon",
  entriesSideView: ".entries-side-view",
  entryRow: ".entry-title",
  entryTitle: ".forum-entry-title",
  entryUser: ".forum-entry-author",
  backToEntriesIcon: "#entries-sml-btn",
  commentSectionTitle: ".comment-section-title",
  commentList: "#row-of-comments",
  comment: ".comment-block",
  commentUser: ".forum-comment-author",
  /** Author of the selected entry, shown in the comment-list header (first of its two .user-name cells). */
  sectionAuthor: ".user-name",
  commentContent: ".message-itself",
  commentDiv: ".comment-div",
  newCommentIcon: ".forum-icon",
  replyIcon: ".replay-icon",
  newEntryModal: detailsModal,
  newCommentModal: { root: detailsModal.root, text: detailsModal.content, postButton: detailsModal.postButton },
  replyModal: { root: detailsModal.root, text: detailsModal.content },
};

const session = {
  newIcon: ".add-element-icon",
  newModal: detailsModal,
  row: ".session-data",
  name: ".session-title",
  access: ".session-ready",
  editIcon: ".forum-icon",
  editModal: "#put-delete-modal",
  editModalDeleteDiv: ".delete-div",
  leftMenuButton: "#side-menu-button",
  exitIcon: "#exit-icon",
  /** Collapsed side-menu toggle shown while inside a video session. */
  fixedIcon: "#fixed-icon",
};

const attenders = {
  rows: ".attender-row-div",
  highlightedRow: ".attender-name-p",
};

module.exports = { common, modal, login, settings, course, tabs, forum, session, attenders };
