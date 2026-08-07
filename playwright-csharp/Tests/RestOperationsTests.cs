using System.Globalization;
using System.Text.RegularExpressions;
using FullTeaching.E2E.Common;
using FullTeaching.E2E.Common.Exceptions;
using FullTeaching.E2E.Utils;
using Microsoft.Playwright;
using NUnit.Framework;
using static Microsoft.Playwright.Assertions;

namespace FullTeaching.E2E.Tests;

/// <summary>
/// Ported from functional/test/media/FullTeachingEndToEndRESTTests.java.
/// Covers course/session/forum/file/attenders CRUD through the UI. Selectors here are inline
/// strings rather than named Constants, matching how the Java source keeps them local to this
/// test class rather than in common/Constants.java (those that already exist in
/// <see cref="Constants"/> are reused). Every test creates its own course and, whatever the
/// outcome, the course is deleted again by <see cref="DeleteLeftoverCourseAsync"/>.
/// </summary>
[TestFixture]
[Category("Rest")]
[Category("Teacher")]
public class RestOperationsTests : BaseTest
{
    private const string CourseName = "TEST_COURSE";
    private const string Edited = " EDITED";
    private const string TestCourseInfo = "TEST_COURSE_INFO";

    private const string PostDialogId = "course-details-modal";
    private const string PutDeleteDialogId = "put-delete-modal";
    private const string PutDeleteCourseDialogId = "put-delete-course-modal";

    private const int UploadTimeoutMs = 20_000;
    private const int CleanupTimeoutMs = 20_000;

    // The relative-date pipe flips from "a few seconds ago" to "a minute ago" after ~45 seconds.
    private static readonly Regex JustCreatedDate = new("^\\s*(a few seconds ago|a minute ago)\\s*$");

    private static readonly string TestFilePath = Path.Combine(AppContext.BaseDirectory, "Resources", "testFile.txt");

    private bool _courseCreated;

    private ILocator Warning => User.Page.Locator(Selectors.WarningPanel).First;

    private ILocator AttenderRows => User.Page.Locator(Constants.AttendersListRows);

    /// <summary>
    /// Best-effort removal of the course a test created and did not get to delete itself
    /// (the test failed half-way, possibly after renaming it). NUnit runs this derived teardown
    /// before <see cref="BaseTest"/> logs the user out. A cleanup failure is only logged so it
    /// never hides the original test failure.
    /// </summary>
    [TearDown]
    public async Task DeleteLeftoverCourseAsync()
    {
        if (!_courseCreated || !User.IsOnSession)
        {
            return;
        }

        _courseCreated = false;
        try
        {
            User.Page.SetDefaultTimeout(CleanupTimeoutMs);
            await User.Page.GotoAsync(AppUrl); // drops any dialog the failed test left open
            await NavigationUtilities.ToCoursesHomeAsync(User);
            await Expect(User.Page.Locator(Selectors.CourseListItem).First).ToBeVisibleAsync();
            foreach (var name in new[] { CourseName, CourseName + Edited })
            {
                if (await CourseNavigationUtilities.CourseExistsAsync(User, name))
                {
                    await CourseNavigationUtilities.DeleteCourseAsync(User, name);
                }
            }
        }
        catch (Exception ex) when (ex is PlaywrightException or ElementNotFoundException or TimeoutException or AssertionException)
        {
            TestContext.Out.WriteLine($"Could not delete the leftover test course: {ex.Message}");
        }
    }

    /// <summary>
    /// Create -> edit -> delete a course through the REST-backed UI forms.
    /// Resources: loginservice(READONLY,10) openvidumock(NOACCESS,10) configuration(READWRITE,1)
    /// executor/webbrowser/webserver(READWRITE,1).
    /// </summary>
    [TestCaseSource(typeof(ParameterLoader), nameof(ParameterLoader.GetTestTeachers))]
    [Description("A teacher can create, rename and delete a course.")]
    public async Task CourseRestOperations(string mail, string password, string role)
    {
        await LoginAndCreateNewCourseAsync(mail, password);
        await EditCourseAsync();
        await DeleteCourseAsync(CourseName + Edited);
    }

    /// <summary>
    /// Edits a course's Home-tab description and checks it renders back.
    /// Resources: loginservice(READONLY,10) openvidumock(NOACCESS,10) information(READWRITE,1)
    /// executor/webbrowser/webserver(READWRITE,1).
    /// </summary>
    [TestCaseSource(typeof(ParameterLoader), nameof(ParameterLoader.GetTestTeachers))]
    [Description("A teacher can edit the course description in the Home tab and see it rendered.")]
    public async Task CourseInfoRestOperations(string mail, string password, string role)
    {
        var page = User.Page;
        await LoginAndCreateNewCourseAsync(mail, password);
        await EnterCourseAndOpenTabAsync(Constants.HomeIcon);

        await Expect(page.Locator(Selectors.ActiveTabWarning)).ToBeVisibleAsync();
        await page.Locator(Constants.EditDescriptionButton).ClickAsync();
        await page.Locator(Selectors.RichTextEditor).FillAsync(TestCourseInfo);
        await page.Locator(Constants.EditDescriptionSaveButton).ClickAsync();

        await Expect(page.Locator(Selectors.RichTextParagraph)).ToHaveTextAsync(TestCourseInfo);
        await DeleteCourseAsync(CourseName);
    }

    /// <summary>
    /// Create -> edit -> delete a video session through the REST-backed UI forms.
    /// Resources: loginservice(READONLY,10) openvidumock(NOACCESS,10) session(READWRITE,1)
    /// executor/webbrowser/webserver(READWRITE,1).
    /// </summary>
    [TestCaseSource(typeof(ParameterLoader), nameof(ParameterLoader.GetTestTeachers))]
    [Description("A teacher can create, edit and delete a session of a course.")]
    public async Task SessionRestOperations(string mail, string password, string role)
    {
        var page = User.Page;
        await LoginAndCreateNewCourseAsync(mail, password);
        await EnterCourseAndOpenTabAsync(Constants.SessionIcon);

        // Create
        const string title = "TEST LESSON NAME";
        const string comment = "TEST LESSON COMMENT";
        await LoginHelper.OpenDialogAsync(User, Selectors.AddSessionIcon);
        await FillSessionFormAsync(FormMode.Post, title, comment, new DateOnly(2018, 3, 1), new TimeOnly(15, 10));
        await LoginHelper.WaitForDialogClosedAsync(User, PostDialogId, "Addition of session failed");
        // Chrome may read the typed date as either month/day or day/month
        await ExpectSessionAsync(title, comment, "Jan 3, 2018 - 03:10", "Mar 1, 2018 - 15:10");

        // Edit
        await LoginHelper.OpenDialogAsync(User, Selectors.EditSessionIcon);
        await FillSessionFormAsync(
            FormMode.Put, title + Edited, comment + Edited, new DateOnly(2019, 4, 2), new TimeOnly(5, 10));
        await LoginHelper.WaitForDialogClosedAsync(User, PutDeleteDialogId, "Edition of session failed");
        await ExpectSessionAsync(title + Edited, comment + Edited, "Feb 4, 2019 - 05:10", "Apr 2, 2019 - 05:10");

        // Delete
        await LoginHelper.OpenDialogAsync(User, Selectors.EditSessionIcon);
        await page.Locator(Selectors.DeleteCheckbox).ClickAsync();
        await page.Locator(Selectors.DeleteSessionButton).ClickAsync();
        await LoginHelper.WaitForDialogClosedAsync(User, PutDeleteDialogId, "Deletion of session failed");
        await Expect(page.Locator(Constants.SessionListSessionRow)).ToHaveCountAsync(0);

        await DeleteCourseAsync(CourseName);
    }

    /// <summary>
    /// Add a forum entry, comment on it, reply to that comment, then deactivate the forum.
    /// Resources: loginservice(READONLY,10) openvidumock(NOACCESS,10) forum(READWRITE,1)
    /// executor/webbrowser/webserver(READWRITE,1).
    /// </summary>
    [TestCaseSource(typeof(ParameterLoader), nameof(ParameterLoader.GetTestTeachers))]
    [Description("A teacher can add a forum entry and a reply to its comment, then deactivate the forum.")]
    public async Task ForumRestOperations(string mail, string password, string role)
    {
        var page = User.Page;
        await LoginAndCreateNewCourseAsync(mail, password);
        await EnterCourseAndOpenTabAsync(Constants.ForumIcon);

        // Add entry
        const string title = "TEST FORUM ENTRY";
        const string comment = "TEST FORUM COMMENT";
        await PostAsync(page.Locator(Constants.ForumNewEntryIcon), "Addition of entry failed", title, comment);

        var entry = page.Locator(Constants.ForumEntryRow);
        await Expect(entry.Locator(Constants.ForumEntryListEntryTitle)).ToHaveTextAsync(title);
        await Expect(entry.Locator(Selectors.ForumEntryAuthor)).ToHaveTextAsync(Constants.TeacherName);
        await Expect(entry.Locator(Selectors.ForumEntryDate)).ToHaveTextAsync(JustCreatedDate);

        // The entry's original comment
        await entry.ClickAsync();
        var firstComment = page.Locator(Selectors.FirstCommentDiv);
        await Expect(firstComment.Locator(Selectors.CommentMessage).First).ToHaveTextAsync(comment);
        await Expect(firstComment.Locator(Selectors.CommentAuthor).First).ToHaveTextAsync(Constants.TeacherName);

        // Reply to it
        const string reply = "TEST FORUM REPLY";
        // Every comment has a "reply" and a "video reply" icon; the first one is the text reply
        await PostAsync(
            page.Locator(Constants.ForumCommentListCommentReplyIcon).First, "Addition of entry reply failed", comment: reply);
        var firstReply = firstComment.Locator(Selectors.NestedCommentDiv);
        await Expect(firstReply.Locator(Selectors.CommentMessage)).ToHaveTextAsync(reply);
        await Expect(firstReply.Locator(Selectors.CommentAuthor)).ToHaveTextAsync(Constants.TeacherName);

        // Deactivate the forum
        await page.Locator(Constants.BackToEntriesListIcon).ClickAsync();
        await LoginHelper.OpenDialogAsync(User, Constants.ForumEditEntryIcon);
        await page.Locator(Constants.DisableForumButton).ClickAsync();
        await page.Locator(Selectors.PutButton).ClickAsync();
        await LoginHelper.WaitForDialogClosedAsync(User, PutDeleteDialogId, "Deactivation of forum failed");
        await Expect(Warning).ToBeVisibleAsync();

        await DeleteCourseAsync(CourseName);
    }

    /// <summary>
    /// Add a file group, a sub-group and a file to it, edit their names, then delete the group.
    /// Resources: loginservice(READONLY,10) openvidumock(NOACCESS,10) files(READWRITE,1)
    /// executor/webbrowser/webserver(READWRITE,1).
    /// </summary>
    [TestCaseSource(typeof(ParameterLoader), nameof(ParameterLoader.GetTestTeachers))]
    [Description("A teacher can create, rename and delete file groups, sub-groups and uploaded files.")]
    public async Task FilesRestOperations(string mail, string password, string role)
    {
        var page = User.Page;
        await LoginAndCreateNewCourseAsync(mail, password);
        await EnterCourseAndOpenTabAsync(Constants.FilesIcon);
        await Expect(Warning).ToBeVisibleAsync(); // a new course has no files yet

        // File group
        const string fileGroup = "TEST FILE GROUP";
        await PostAsync(page.Locator(Selectors.AddFileGroupIcon), "Addition of file group failed", title: fileGroup);
        await Expect(page.Locator(Selectors.FileGroupTitle)).ToHaveTextAsync(fileGroup);

        await PutAsync(Selectors.EditFileGroupIcon, Selectors.FileTitleField, fileGroup + Edited, "Edition of file group failed");
        await Expect(page.Locator(Selectors.FileGroupTitle)).ToHaveTextAsync(fileGroup + Edited);

        // File sub-group
        const string fileSubGroup = "TEST FILE SUBGROUP";
        await PostAsync(page.Locator(Selectors.AddSubgroupButton), "Addition of file sub-group failed", title: fileSubGroup);
        await Expect(page.Locator(Selectors.SubgroupTitle)).ToHaveTextAsync(fileSubGroup);

        // File: unlike Java (which must force `display:block` on the hidden <input type=file>),
        // SetInputFilesAsync works on hidden file inputs directly.
        const string fileName = "testFile.txt";
        await LoginHelper.OpenDialogAsync(User, Selectors.AddFileButton);
        await page.Locator(Selectors.FileUploader).SetInputFilesAsync(TestFilePath);
        await page.Locator(Selectors.UploadAllButton).ClickAsync();
        await page.Locator(Selectors.UploadProgressDone).WaitForAsync(new() { Timeout = UploadTimeoutMs });
        await Expect(page.Locator(Selectors.UploadStatusIcon)).ToHaveTextAsync("done");
        await page.Locator(Selectors.CloseUploadButton).ClickAsync();
        await LoginHelper.WaitForDialogClosedAsync(User, PostDialogId, "Upload of file failed");
        await Expect(page.Locator(Selectors.SubgroupFileName)).ToHaveTextAsync(fileName);

        const string editedFileName = "testFileEDITED.txt";
        await PutAsync(Selectors.EditFileNameIcon, Selectors.FileTitleField, editedFileName, "Edition of file failed");
        await Expect(page.Locator(Selectors.SubgroupFileName)).ToHaveTextAsync(editedFileName);

        // Delete the group
        await page.Locator(Selectors.DeleteFileGroupIcon).ClickAsync();
        await Expect(Warning).ToBeVisibleAsync();

        await DeleteCourseAsync(CourseName);
    }

    /// <summary>
    /// Fails to add an unregistered attender, adds a real one, then removes them.
    /// Resources: loginservice(READONLY,10) openvidumock(NOACCESS,10) attenders(READWRITE,1)
    /// executor/webbrowser/webserver(READWRITE,1).
    /// </summary>
    [TestCaseSource(typeof(ParameterLoader), nameof(ParameterLoader.GetTestTeachers))]
    [Description("A teacher cannot add an unregistered attender, can add a registered one and can remove them.")]
    public async Task AttendersRestOperations(string mail, string password, string role)
    {
        var page = User.Page;
        await LoginAndCreateNewCourseAsync(mail, password);
        await EnterCourseAndOpenTabAsync(Constants.AttendersIcon);

        await Expect(AttenderRows).ToHaveCountAsync(1);
        await Expect(AttenderRows.Locator(Constants.AttendersListHighlightedRow)).ToHaveTextAsync(Constants.TeacherName);

        // Add an unregistered attender: rejected
        await PutAsync(Selectors.AddAttendersIcon, Selectors.AttenderField, "studentFail@gmail.com", "Addition of attender fail");
        await Expect(page.Locator(Selectors.FailPanel)).ToBeVisibleAsync();
        await Expect(AttenderRows).ToHaveCountAsync(1);
        await page.Locator(Selectors.FailPanelClose).ClickAsync();

        // Add a registered attender: accepted
        await PutAsync(Selectors.AddAttendersIcon, Selectors.AttenderField, "student1@gmail.com", "Addition of attender failed");
        await Expect(page.Locator(Selectors.CorrectPanel)).ToBeVisibleAsync();
        await Expect(AttenderRows).ToHaveCountAsync(2);
        await page.Locator(Selectors.CorrectPanelClose).ClickAsync();

        // Remove the attender
        await page.Locator(Selectors.EditAttendersIcon).ClickAsync();
        await page.Locator(Selectors.DeleteAttenderIcon).ClickAsync();
        await Expect(AttenderRows).ToHaveCountAsync(1);

        await DeleteCourseAsync(CourseName);
    }

    // pyppeteer/Cypress are Chromium-only, so - like both sibling ports - this always follows
    // the BROWSER_NAME == "chrome" branch of Java's fillSessionForm (Playwright's default
    // browser here is also Chromium; see PlaywrightGlobalSetup).
    private static string FormatDateChrome(DateOnly date) => date.ToString("yyyy-MM-dd", CultureInfo.InvariantCulture);

    // <input type="time"> only accepts HH:mm (24h), whatever the locale of the displayed value.
    private static string FormatTimeChrome(TimeOnly time) => time.ToString("HH:mm", CultureInfo.InvariantCulture);

    private static Regex ExactlyOneOf(params string[] values) =>
        new($"^\\s*(?:{string.Join('|', values.Select(Regex.Escape))})\\s*$");

    private async Task LoginAndCreateNewCourseAsync(string mail, string password)
    {
        await LoginHelper.SlowLoginAsync(User, mail, password);
        _courseCreated = true; // set first: if creation dies half-way the teardown still checks for it
        await CourseNavigationUtilities.NewCourseAsync(User, CourseName);
    }

    private async Task DeleteCourseAsync(string courseName)
    {
        await CourseNavigationUtilities.DeleteCourseAsync(User, courseName);
        _courseCreated = false;
    }

    private async Task EditCourseAsync()
    {
        var page = User.Page;
        var editedCourseName = CourseName + Edited;
        await LoginHelper.OpenDialogAsync(User, page.Locator(Constants.EditCourseButton).Last);

        await page.Locator(Constants.EditCourseModalNameField).FillAsync(editedCourseName);
        await page.Locator(Constants.EditCourseModalSave).ClickAsync();
        await LoginHelper.WaitForDialogClosedAsync(User, PutDeleteCourseDialogId, "Edition of course failed");

        await Expect(page.Locator(Selectors.LastCourseTitle)).ToHaveTextAsync(editedCourseName);
    }

    /// <summary>Opens the test course from the dashboard and switches to the tab with the given icon.</summary>
    private async Task EnterCourseAndOpenTabAsync(string tabIconSelector)
    {
        var page = User.Page;
        var courseTitle = page.Locator(Selectors.CourseTitleSpan)
            .Filter(new() { HasTextRegex = new Regex($"^\\s*{Regex.Escape(CourseName)}\\s*$") })
            .First;
        await Expect(courseTitle).ToBeVisibleAsync();
        await courseTitle.ClickAsync();

        await Expect(page.Locator(Selectors.MainCourseTitle)).ToHaveTextAsync(CourseName);
        await page.Locator(tabIconSelector).ClickAsync();
    }

    private enum FormMode
    {
        Post,
        Put,
    }

    /// <summary>
    /// Opens a "new element" dialog from <paramref name="opener"/>, fills in whichever of
    /// title/comment are given, submits it and waits for the dialog to close.
    /// </summary>
    private async Task PostAsync(ILocator opener, string errorMessage, string? title = null, string? comment = null)
    {
        var page = User.Page;
        await LoginHelper.OpenDialogAsync(User, opener);

        if (title is not null)
        {
            await page.Locator(Selectors.PostTitleField).FillAsync(title);
        }

        if (comment is not null)
        {
            await page.Locator(Selectors.PostCommentField).FillAsync(comment);
        }

        await page.Locator(Selectors.PostButton).ClickAsync();
        await LoginHelper.WaitForDialogClosedAsync(User, PostDialogId, errorMessage);
    }

    /// <summary>
    /// Opens an "edit" dialog from <paramref name="openerSelector"/>, sets one text field,
    /// submits it and waits for the dialog to close.
    /// </summary>
    private async Task PutAsync(string openerSelector, string fieldSelector, string value, string errorMessage)
    {
        var page = User.Page;
        await LoginHelper.OpenDialogAsync(User, openerSelector);
        await page.Locator(fieldSelector).FillAsync(value);
        await page.Locator(Selectors.PutButton).ClickAsync();
        await LoginHelper.WaitForDialogClosedAsync(User, PutDeleteDialogId, errorMessage);
    }

    private async Task FillSessionFormAsync(FormMode mode, string title, string comment, DateOnly date, TimeOnly time)
    {
        var page = User.Page;
        var prefix = mode == FormMode.Put ? "put" : "post";
        var titleField = page.Locator($"#input-{prefix}-title");
        var commentField = page.Locator($"#input-{prefix}-comment");
        if (mode == FormMode.Put)
        {
            await titleField.ClearAsync();
            await commentField.ClearAsync();
        }

        await titleField.FillAsync(title);
        await commentField.FillAsync(comment);
        await page.Locator($"#input-{prefix}-date").FillAsync(FormatDateChrome(date));
        await page.Locator($"#input-{prefix}-time").FillAsync(FormatTimeChrome(time));
        await page.Locator($"#{prefix}-modal-btn").ClickAsync();
    }

    private async Task ExpectSessionAsync(string expectedTitle, string expectedComment, params string[] acceptedDateTimes)
    {
        var session = User.Page.Locator(Constants.SessionListSessionRow);
        await Expect(session.Locator(Constants.SessionListSessionName)).ToHaveTextAsync(expectedTitle);
        await Expect(session.Locator(Selectors.SessionDescription)).ToHaveTextAsync(expectedComment);
        await Expect(session.Locator(Selectors.SessionDateTime)).ToHaveTextAsync(ExactlyOneOf(acceptedDateTimes));
    }

    /// <summary>Selectors used only by this fixture (the Java source keeps them inline as well).</summary>
    private static class Selectors
    {
        // Generic dialogs
        public const string PostTitleField = "#input-post-title";
        public const string PostCommentField = "#input-post-comment";
        public const string PostButton = "#post-modal-btn";
        public const string PutButton = "#put-modal-btn";
        public const string DeleteCheckbox = "#label-delete-checkbox";

        public const string WarningPanel = "app-error-message .card-panel.warning";
        public const string FailPanel = "app-error-message .card-panel.fail";
        public const string FailPanelClose = FailPanel + " .material-icons";
        public const string CorrectPanel = "app-error-message .card-panel.correct";
        public const string CorrectPanelClose = CorrectPanel + " .material-icons";

        // Courses
        public const string CourseListItem = ".course-list-item";
        public const string CourseTitleSpan = "#course-list .course-list-item div.course-title span";
        public const string LastCourseTitle = "#course-list .course-list-item:last-child div.course-title span";
        public const string MainCourseTitle = "#main-course-title";
        public const string ActiveTabWarning = ".md-tab-body.md-tab-active .card-panel.warning";
        public const string RichTextEditor = Constants.EditDescriptionContentBox;
        public const string RichTextParagraph = Constants.DescriptionViewText;

        // Sessions
        public const string AddSessionIcon = "#add-session-icon";
        public const string EditSessionIcon = ".edit-session-icon";
        public const string DeleteSessionButton = "#delete-session-btn";
        public const string SessionDescription = ".session-description";
        public const string SessionDateTime = ".session-datetime";

        // Forum
        public const string ForumEntryAuthor = ".forum-entry-author";
        public const string ForumEntryDate = ".forum-entry-date";
        public const string FirstCommentDiv = ".comment-block > app-comment:first-child > div.comment-div";
        public const string NestedCommentDiv = "div.comment-div";
        public const string CommentMessage = ".message-itself";
        public const string CommentAuthor = ".forum-comment-author";

        // Files
        public const string AddFileGroupIcon = "#add-files-icon";
        public const string EditFileGroupIcon = "#edit-filegroup-icon";
        public const string DeleteFileGroupIcon = "app-file-group .delete-filegroup-icon";
        public const string AddSubgroupButton = ".add-subgroup-btn";
        public const string AddFileButton = "app-file-group app-file-group .add-file-btn";
        public const string EditFileNameIcon = "app-file-group app-file-group .edit-file-name-icon";
        public const string FileTitleField = "#input-file-title";
        public const string FileGroupTitle = "app-file-group .file-group-title h5";
        public const string SubgroupTitle = "app-file-group app-file-group .file-group-title h5";
        public const string SubgroupFileName = "app-file-group app-file-group .chip .file-name-div";
        public const string FileUploader = ".input-file-uploader";
        public const string UploadAllButton = "#upload-all-btn";
        public const string UploadProgressDone = ".determinate[style*='width: 100']";
        public const string UploadStatusIcon = "i[class*='icon-status-upload']";
        public const string CloseUploadButton = "#close-upload-modal-btn";

        // Attenders
        public const string AddAttendersIcon = "#add-attenders-icon";
        public const string EditAttendersIcon = "#edit-attenders-icon";
        public const string DeleteAttenderIcon = ".del-attender-icon";
        public const string AttenderField = "#input-attender-simple";
    }
}
