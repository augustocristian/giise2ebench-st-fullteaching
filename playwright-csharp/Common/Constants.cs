namespace FullTeaching.E2E.Common;

/// <summary>
/// FullTeaching selectors and timeouts, ported from common/Constants.java.
/// Playwright's selector engine understands the "xpath=" prefix natively, so - unlike the
/// Cypress port, which has no XPath support - the Java source's XPath locators are kept as-is
/// here instead of being translated to CSS.
/// </summary>
public static class Constants
{
    /// <summary>Default Playwright action/navigation timeout of the primary user, in seconds.</summary>
    public const int WaitSeconds = 30;
    /// <summary>
    /// Longer Playwright timeout, in seconds, for media/video-session flows (WebRTC negotiation,
    /// fake camera start-up). Pass it to <c>CreateSecondaryUserAsync</c> or override
    /// <c>BaseTest.TimeoutSeconds</c>.
    /// </summary>
    public const int MediaWaitSeconds = 150;
    // Recursion depth for the spider-navigation link crawler, from BaseLoggedTest.DEPTH.
    public const int SpiderDepth = 3;
    /// <summary>App URL used when neither SUT_URL nor app.url is set (see <see cref="TestConfig"/>).</summary>
    public const string Localhost = "https://localhost:5000";
    public const string StudentName = "Student Imprudent";
    public const string TeacherName = "Teacher Cheater";

    public const string CoursesUrl = "__HOST__/courses";

    // LoggedForumTest.java's hardcoded `courseName` field and CourseTeacherTest.java's
    // `properties.getProperty("forum.test.course")` (test.properties, kept under Resources/
    // for parity) resolve to the same literal - unified here into one constant.
    public const string ForumTestCourseName = "Pseudoscientific course for treating the evil eye";

    // Other elements
    public const string Footer = ".page-footer";
    public const string MainMenuArrow = "#arrow-drop-down";
    public const string LogoutButton = "#logout-button";

    // Login modal
    public const string LoginModal = "#login-modal";
    public const string LoginUserField = "#email";
    public const string LoginPasswordField = "#password";
    public const string LoginButton = "#log-in-btn";
    public const string DownloadButton = "#download-button";

    // Dashboard / course list
    // Same two-column dashboard as CourseList: ".dashboard-title" alone also matches the "MY CALENDAR" title.
    public const string CoursesDashboardTitle = ".dashboard-col:has(#course-list) .dashboard-title";
    // Was an absolute path (/html/body/app/div/main/app-dashboard/div/div[3]/...) that breaks as soon
    // as a conditional <dialog> is added or removed before the course list.
    public const string FirstCourseXPath = "xpath=//ul[@id='course-list']/li[contains(@class, 'course-list-item')][1]";
    public const string CourseListCourseTitle = ".course-title";
    // The dashboard has two ".dashboard-col" columns (MY COURSES and MY CALENDAR): scope to the one with the course list.
    public const string CourseList = ".dashboard-col:has(#course-list)";
    // Inline `By.className("title")` literal used by CourseNavigationUtilities.java, distinct
    // from CourseListCourseTitle (".course-title") used elsewhere - kept as-is for fidelity.
    public const string CourseTitle = ".title";
    public const string CourseListId = "#course-list";

    public const string TabsDiv = "#tabs-course-details";

    // New/edit course modals
    public const string NewCourseButton = "#add-new-course-btn";
    // The anchor above wraps a floated icon and has an empty box (Playwright: hidden); the icon itself is clickable.
    public const string NewCourseIcon = "#add-course-icon";
    public const string NewCourseModal = "#course-modal";
    public const string NewCourseModalNameField = "#input-post-course-name";
    public const string NewCourseModalSave = "#submit-post-course-btn";

    public const string EditCourseButton = ".course-put-icon";
    public const string EditDeleteModal = "#put-delete-course-modal";
    public const string EditCourseModalNameField = "#input-put-course-name";
    public const string EditCourseModalSave = "#submit-put-course-btn";
    public const string EditCourseDeleteCheck = "#label-delete-checkbox";
    public const string EditCourseDeleteButton = "#delete-course-btn";

    public const string BackToDashboard = ".btn-floating";
    public const string CourseTabs = "#tabs-course-details";

    // Course tabs
    public const string HomeIcon = "#info-tab-icon";
    public const string SessionIcon = "#sessions-tab-icon";
    public const string ForumIcon = "#forum-tab-icon";
    public const string FilesIcon = "#files-tab-icon";
    public const string AttendersIcon = "#attenders-tab-icon";

    public const string SessionListNewSessionIcon = ".add-element-icon";

    // Course description
    public const string EditDescriptionButton = "#edit-course-info";
    // Quill: the rendered description also carries the ql-editor class; the editable one is the other.
    public const string EditDescriptionContentBox = ".ql-editor:not(.ql-editor-custom)";
    public const string DescriptionView = ".ql-editor-custom";
    public const string DescriptionViewText = ".ql-editor-custom p";
    public const string EditDescriptionSaveButton = "#send-info-btn";

    // Settings page: value of the "Name" row (was /html/body/app/div/main/app-settings/div/div[3]/div[2]/ul/li[2]/div[2]).
    public const string UsernameXPath =
        "xpath=//app-settings//li[div[contains(@class, 'setting-title') and normalize-space() = 'Name']]/div[contains(@class, 'setting-content')]";
    // Navbar "Log in" link, only present while logged out (was /html/body/app/div/header/navbar/div/nav/div/ul/li[2]/a).
    public const string LoginMenuXPath = "xpath=//navbar//nav//ul/li/a[normalize-space() = 'Log in']";

    // Forum enable/disable (same checkbox id, aliased by intent like the Java constants)
    public const string EnableForumButton = "#label-forum-checkbox";
    public const string DisableForumButton = "#label-forum-checkbox";
    public const string EnableForumModalSaveButton = "#put-modal-btn";
    public const string EnableForumModal = "#put-delete-modal";

    public const string CoursesButton = "#courses-button";
    public const string SettingsButton = "#settings-button";

    // Forum
    public const string ForumNewEntryIcon = "#add-entry-icon";
    public const string ForumEditEntryIcon = "#edit-forum-icon";
    public const string ForumEntryListEntryTitle = ".forum-entry-title";
    public const string ForumEntryRow = ".entry-title";
    public const string ForumEntryListEntryUser = ".forum-entry-author";
    public const string ForumCommentListEntryTitle = ".comment-section-title";
    public const string ForumCommentListEntryUser = ".user-name";
    public const string ForumCommentList = "#row-of-comments";
    public const string ForumCommentListComment = ".comment-block";
    public const string ForumCommentListCommentUser = ".forum-comment-author";
    public const string ForumCommentListCommentContent = ".message-itself";
    public const string BackToEntriesListIcon = "#entries-sml-btn";
    public const string ForumNewEntryModal = "#course-details-modal";
    public const string ForumNewEntryModalTitle = "#input-post-title";
    public const string ForumNewEntryModalContent = "#input-post-comment";
    public const string ForumNewEntryModalPostButton = "#post-modal-btn";
    public const string ForumCommentListNewCommentIcon = ".forum-icon";
    public const string ForumNewCommentModal = "#course-details-modal";
    public const string ForumNewCommentModalTextField = "#input-post-comment";
    public const string ForumNewCommentModalPostButton = "#post-modal-btn";
    public const string ForumCommentListCommentReplyIcon = ".replay-icon";
    public const string ForumCommentListModalNewReply = "#course-details-modal";
    public const string ForumCommentListModalNewReplyTextField = "#input-post-comment";
    public const string ForumCommentListCommentDiv = ".comment-div";

    // Sessions
    public const string SessionListNewSessionModal = "#course-details-modal";
    public const string SessionListNewSessionModalTitle = "#input-post-title";
    public const string SessionListNewSessionModalContent = "#input-post-comment";
    public const string SessionListNewSessionModalDate = "#input-post-date";
    public const string SessionListNewSessionModalTime = "#input-post-time";
    public const string SessionListNewSessionModalPostButton = "#post-modal-btn";
    public const string SessionListSessionRow = ".session-data";
    public const string SessionListSessionName = ".session-title";
    public const string SessionListSessionAccess = ".session-ready";
    public const string SessionListSessionEditIcon = ".forum-icon";
    public const string SessionListEditModal = "#put-delete-modal";
    public const string SessionListEditModalDeleteDiv = ".delete-div";

    public const string SessionLeftMenuButton = "#side-menu-button";
    public const string SessionExitIcon = "#exit-icon";

    // Attenders
    public const string AttendersListRows = ".attender-row-div";
    public const string AttendersListHighlightedRow = ".attender-name-p";

    // Settings
    public const string SettingsUserEmail = "#stng-user-mail";

    // Login/dialog helpers used by BaseLoggedTest.java's login()/openDialog()/waitForDialogClosed()
    // The SUT's modals are native <dialog class="modal my-modal-class"> elements opened with
    // showModal() (native-dialog.directive.ts): they carry the `open` attribute while shown.
    public const string ModalOverlayOpening = "dialog.modal.my-modal-class[open]";
    public const string ModalOpen = ".modal.my-modal-class.open";
    public const string ModalOverlay = ".modal-overlay";

    // Video-session page / collapsed ("shrunk") navbar, used by LoginHelper.LogoutAsync
    public const string SessionFixedIcon = "#fixed-icon";
    public const string MobileMenuButton = "a.button-collapse";
    public const string MobileLogoutLink =
        "xpath=//ul[@id='nav-mobile']//*[self::a or self::button][normalize-space() = 'Logout']";

    // Course creation / forum containers
    public const string CourseListItem = ".course-list-item";
    public const string ForumEntriesSideView = ".entries-side-view";

    /// <summary>
    /// Selector of the modal with the given id once it is closed. A closed native dialog has no
    /// <c>open</c> attribute and is not rendered, so waiting for it needs the Attached state.
    /// (The name is historical: it used to be an XPath.)
    /// </summary>
    public static string ModalClosedXPath(string dialogId) => $"dialog#{dialogId}:not([open])";
}
