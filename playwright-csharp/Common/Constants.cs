namespace FullTeaching.E2E.Common;

/// <summary>
/// FullTeaching selectors and timeouts, ported from common/Constants.java.
/// Playwright's selector engine understands the "xpath=" prefix natively, so - unlike the
/// Cypress port, which has no XPath support - the Java source's XPath locators are kept as-is
/// here instead of being translated to CSS.
/// </summary>
public static class Constants
{
    public const int WaitSeconds = 150;
    // Recursion depth for the spider-navigation link crawler, from BaseLoggedTest.DEPTH.
    public const int SpiderDepth = 3;
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
    public const string CoursesDashboardTitle = ".dashboard-title";
    public const string FirstCourseXPath = "xpath=/html/body/app/div/main/app-dashboard/div/div[3]/div/div[1]/ul/li[1]";
    public const string CourseListCourseTitle = ".course-title";
    public const string CourseList = ".dashboard-col";
    // Inline `By.className("title")` literal used by CourseNavigationUtilities.java, distinct
    // from CourseListCourseTitle (".course-title") used elsewhere - kept as-is for fidelity.
    public const string CourseTitle = ".title";
    public const string CourseListId = "#course-list";

    public const string TabsDiv = "#tabs-course-details";

    // New/edit course modals
    public const string NewCourseButton = "#add-new-course-btn";
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
    public const string EditDescriptionContentBox = ".ui-editor-content";
    public const string EditDescriptionSaveButton = "#send-info-btn";

    public const string UsernameXPath = "xpath=/html/body/app/div/main/app-settings/div/div[3]/div[2]/ul/li[2]/div[2]";
    public const string LoginMenuXPath = "xpath=/html/body/app/div/header/navbar/div/nav/div/ul/li[2]/a";

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
    public const string ForumEntryListEntryUser = ".user-name";
    public const string ForumCommentListEntryTitle = ".comment-section-title";
    public const string ForumCommentListEntryUser = ".user-name";
    public const string ForumCommentList = "#row-of-comments";
    public const string ForumCommentListComment = ".comment-block";
    public const string ForumCommentListCommentUser = ".user-name";
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
    public const string ModalOverlayOpening = "xpath=//div[contains(@class, 'modal-overlay') and contains(@style, 'opacity: 0.5')]";
    public const string ModalOpen = ".modal.my-modal-class.open";
    public const string ModalOverlay = ".modal-overlay";

    public static string ModalClosedXPath(string dialogId) =>
        $"xpath=//div[@id='{dialogId}' and contains(@class, 'my-modal-class') and contains(@style, 'opacity: 0') and contains(@style, 'display: none')]";
}
