using Microsoft.Playwright;
using FullTeaching.E2E.Common;
using FullTeaching.E2E.Utils;
using NUnit.Framework;
using static Microsoft.Playwright.Assertions;

namespace FullTeaching.E2E.Tests;

/// <summary>
/// Ported from functional/test/media/FullTeachingEndToEndRESTTests.java.
/// Covers course/session/forum/file/attenders CRUD through the UI. Selectors here are inline
/// strings rather than named Constants, matching how the Java source keeps them local to this
/// test class rather than in common/Constants.java.
/// </summary>
[TestFixture]
public class RestOperationsTests : BaseTest
{
    private const string CourseName = "TEST_COURSE";
    private const string Edited = " EDITED";
    private const string TestCourseInfo = "TEST_COURSE_INFO";
    private static readonly string TestFilePath = Path.Combine(AppContext.BaseDirectory, "Resources", "testFile.txt");

    private async Task LoginAndCreateNewCourseAsync(string mail, string password)
    {
        await LoginHelper.SlowLoginAsync(User, mail, password);
        await CourseNavigationUtilities.NewCourseAsync(User, CourseName);
    }

    private async Task EditCourseAsync()
    {
        var page = User.Page;
        var editedCourseName = CourseName + Edited;
        var editIcon = page.Locator(".course-put-icon").Last;
        await LoginHelper.OpenDialogAsync(User, editIcon);

        await page.Locator("#input-put-course-name").FillAsync(editedCourseName);
        await page.Locator("#submit-put-course-btn").ClickAsync();
        await LoginHelper.WaitForDialogClosedAsync(User, "put-delete-course-modal", "Edition of course failed");

        var lastCourseName = page.Locator("#course-list .course-list-item:last-child div.course-title span");
        await Expect(lastCourseName).ToHaveTextAsync(editedCourseName);
    }

    private async Task EnterCourseAndNavigateTabAsync(string courseName, string tabId)
    {
        var page = User.Page;
        // These tests always create a new course, so wait for 3 courses in the main page (more than 2)
        var titleSpans = page.Locator("#course-list .course-list-item div.course-title span");
        await Expect(titleSpans).Not.ToHaveCountAsync(0);
        var spans = await titleSpans.AllAsync();
        ILocator? courseSpan = null;
        foreach (var span in spans)
        {
            if ((await span.InnerTextAsync()).Trim() == courseName)
            {
                courseSpan = span;
                break;
            }
        }
        Assert.That(courseSpan, Is.Not.Null, $"The course with the name '{courseName}' could not be found. Total courses available: {spans.Count}");
        await courseSpan!.ClickAsync();

        await Expect(page.Locator("#main-course-title")).ToHaveTextAsync(courseName);
        await page.Locator($"#{tabId}").ClickAsync();
    }

    /// <summary>
    /// Create -> edit -> delete a course through the REST-backed UI forms.
    /// Resources: loginservice(READONLY,10) openvidumock(NOACCESS,10) configuration(READWRITE,1)
    /// executor/webbrowser/webserver(READWRITE,1).
    /// </summary>
    [TestCaseSource(typeof(ParameterLoader), nameof(ParameterLoader.GetTestTeachers))]
    public async Task CourseRestOperations(string mail, string password, string role)
    {
        await LoginAndCreateNewCourseAsync(mail, password);
        await EditCourseAsync();
        await CourseNavigationUtilities.DeleteCourseAsync(User, CourseName + Edited);
    }

    /// <summary>
    /// Edits a course's Home-tab description and checks it renders back.
    /// Resources: loginservice(READONLY,10) openvidumock(NOACCESS,10) information(READWRITE,1)
    /// executor/webbrowser/webserver(READWRITE,1).
    /// </summary>
    [TestCaseSource(typeof(ParameterLoader), nameof(ParameterLoader.GetTestTeachers))]
    public async Task CourseInfoRestOperations(string mail, string password, string role)
    {
        var page = User.Page;
        await LoginAndCreateNewCourseAsync(mail, password);
        await EnterCourseAndNavigateTabAsync(CourseName, "info-tab-icon");

        await page.Locator(".md-tab-body.md-tab-active .card-panel.warning").WaitForAsync();
        await page.Locator("#edit-course-info").ClickAsync();
        await page.Locator(".ql-editor").FillAsync(TestCourseInfo);
        await page.Locator("#send-info-btn").ClickAsync();

        await Expect(page.Locator(".ql-editor p")).ToHaveTextAsync(TestCourseInfo);
        await CourseNavigationUtilities.DeleteCourseAsync(User, CourseName);
    }

    // pyppeteer/Cypress are Chromium-only, so - like both sibling ports - this always follows
    // the BROWSER_NAME == "chrome" branch of Java's fillSessionForm (Playwright's default
    // browser here is also Chromium; see PlaywrightGlobalSetup).
    private static string FormatDateChrome(DateOnly date) => date.ToString("MM/dd/yyyy");

    private static string FormatTimeChrome(TimeOnly time)
    {
        var hour12 = time.Hour % 12 == 0 ? 12 : time.Hour % 12;
        var ampm = time.Hour < 12 ? "AM" : "PM";
        return $"{hour12:D2}:{time.Minute:D2}{ampm}";
    }

    private async Task FillSessionFormAsync(string title, string comment, DateOnly date, TimeOnly time, bool edit)
    {
        var page = User.Page;
        var titleField = page.Locator(edit ? "#input-put-title" : "#input-post-title");
        var commentField = page.Locator(edit ? "#input-put-comment" : "#input-post-comment");
        var dateField = page.Locator(edit ? "#input-put-date" : "#input-post-date");
        var timeField = page.Locator(edit ? "#input-put-time" : "#input-post-time");
        if (edit)
        {
            await titleField.ClearAsync();
            await commentField.ClearAsync();
        }
        await titleField.FillAsync(title);
        await commentField.FillAsync(comment);
        await dateField.FillAsync(FormatDateChrome(date));
        await timeField.FillAsync(FormatTimeChrome(time));
        await page.Locator(edit ? "#put-modal-btn" : "#post-modal-btn").ClickAsync();
    }

    private async Task VerifySessionDetailsAsync(string expectedTitle, string expectedComment, params string[] expectedDateTimes)
    {
        var page = User.Page;
        await Expect(page.Locator("li.session-data .session-title")).ToHaveTextAsync(expectedTitle);
        await Expect(page.Locator("li.session-data .session-description")).ToHaveTextAsync(expectedComment);

        var actual = await page.Locator("li.session-data .session-datetime").InnerTextAsync();
        Assert.That(expectedDateTimes, Does.Contain(actual));
    }

    /// <summary>
    /// Create -> edit -> delete a video session through the REST-backed UI forms.
    /// Resources: loginservice(READONLY,10) openvidumock(NOACCESS,10) session(READWRITE,1)
    /// executor/webbrowser/webserver(READWRITE,1).
    /// </summary>
    [TestCaseSource(typeof(ParameterLoader), nameof(ParameterLoader.GetTestTeachers))]
    public async Task SessionRestOperations(string mail, string password, string role)
    {
        var page = User.Page;
        await LoginAndCreateNewCourseAsync(mail, password);
        await EnterCourseAndNavigateTabAsync(CourseName, "sessions-tab-icon");

        await LoginHelper.OpenDialogAsync(User, "#add-session-icon");
        await FillSessionFormAsync("TEST LESSON NAME", "TEST LESSON COMMENT", new DateOnly(2018, 3, 1), new TimeOnly(15, 10), edit: false);
        await LoginHelper.WaitForDialogClosedAsync(User, "course-details-modal", "Addition of session failed");
        await VerifySessionDetailsAsync("TEST LESSON NAME", "TEST LESSON COMMENT", "Jan 3, 2018 - 03:10", "Mar 1, 2018 - 15:10");

        await LoginHelper.OpenDialogAsync(User, ".edit-session-icon");
        await FillSessionFormAsync("TEST LESSON NAME EDITED", "TEST LESSON COMMENT EDITED", new DateOnly(2019, 4, 2), new TimeOnly(5, 10), edit: true);
        await LoginHelper.WaitForDialogClosedAsync(User, "put-delete-modal", "Edition of session failed");
        await VerifySessionDetailsAsync("TEST LESSON NAME EDITED", "TEST LESSON COMMENT EDITED", "Feb 4, 2019 - 05:10", "Apr 2, 2019 - 05:10");

        await LoginHelper.OpenDialogAsync(User, ".edit-session-icon");
        await page.Locator("#label-delete-checkbox").ClickAsync();
        await page.Locator("#delete-session-btn").ClickAsync();
        await LoginHelper.WaitForDialogClosedAsync(User, "put-delete-modal", "Deletion of session failed");
        await Expect(page.Locator("li.session-data")).ToHaveCountAsync(0);

        await CourseNavigationUtilities.DeleteCourseAsync(User, CourseName);
    }

    /// <summary>
    /// Add a forum entry, comment on it, reply to that comment, then deactivate the forum.
    /// Resources: loginservice(READONLY,10) openvidumock(NOACCESS,10) forum(READWRITE,1)
    /// executor/webbrowser/webserver(READWRITE,1).
    /// </summary>
    [TestCaseSource(typeof(ParameterLoader), nameof(ParameterLoader.GetTestTeachers))]
    public async Task ForumRestOperations(string mail, string password, string role)
    {
        var page = User.Page;
        await LoginAndCreateNewCourseAsync(mail, password);
        await EnterCourseAndNavigateTabAsync(CourseName, "forum-tab-icon");

        const string title = "TEST FORUM ENTRY";
        const string comment = "TEST FORUM COMMENT";
        const string entryDate = "a few seconds ago";
        await LoginHelper.OpenDialogAsync(User, "#add-entry-icon");
        await page.Locator("#input-post-title").FillAsync(title);
        await page.Locator("#input-post-comment").FillAsync(comment);
        await page.Locator("#post-modal-btn").ClickAsync();
        await LoginHelper.WaitForDialogClosedAsync(User, "course-details-modal", "Addition of entry failed");

        var entryEl = page.Locator("li.entry-title");
        await Expect(page.Locator("li.entry-title .forum-entry-title")).ToHaveTextAsync(title);
        await Expect(page.Locator("li.entry-title .forum-entry-author")).ToHaveTextAsync(Constants.TeacherName);
        await Expect(page.Locator("li.entry-title .forum-entry-date")).ToHaveTextAsync(entryDate);

        await entryEl.ClickAsync();
        await Expect(page.Locator(".comment-block > app-comment:first-child > div.comment-div .message-itself")).ToHaveTextAsync(comment);
        await Expect(page.Locator(".comment-block > app-comment:first-child > div.comment-div .forum-comment-author")).ToHaveTextAsync(Constants.TeacherName);

        const string reply = "TEST FORUM REPLY";
        await LoginHelper.OpenDialogAsync(User, ".replay-icon");
        await page.Locator("#input-post-comment").FillAsync(reply);
        await page.Locator("#post-modal-btn").ClickAsync();
        await LoginHelper.WaitForDialogClosedAsync(User, "course-details-modal", "Addition of entry reply failed");
        await Expect(page.Locator(".comment-block > app-comment:first-child > div.comment-div div.comment-div .message-itself")).ToHaveTextAsync(reply);
        await Expect(page.Locator(".comment-block > app-comment:first-child > div.comment-div div.comment-div .forum-comment-author")).ToHaveTextAsync(Constants.TeacherName);

        await page.Locator("#entries-sml-btn").ClickAsync();
        await LoginHelper.OpenDialogAsync(User, "#edit-forum-icon");
        await page.Locator("#label-forum-checkbox").ClickAsync();
        await page.Locator("#put-modal-btn").ClickAsync();
        await LoginHelper.WaitForDialogClosedAsync(User, "put-delete-modal", "Deactivation of forum failed");
        await page.Locator("app-error-message .card-panel.warning").WaitForAsync();

        await CourseNavigationUtilities.DeleteCourseAsync(User, CourseName);
    }

    /// <summary>
    /// Add a file group, a sub-group and a file to it, edit their names, then delete the group.
    /// Resources: loginservice(READONLY,10) openvidumock(NOACCESS,10) files(READWRITE,1)
    /// executor/webbrowser/webserver(READWRITE,1).
    /// </summary>
    [TestCaseSource(typeof(ParameterLoader), nameof(ParameterLoader.GetTestTeachers))]
    public async Task FilesRestOperations(string mail, string password, string role)
    {
        var page = User.Page;
        await LoginAndCreateNewCourseAsync(mail, password);
        await EnterCourseAndNavigateTabAsync(CourseName, "files-tab-icon");

        await page.Locator("app-error-message .card-panel.warning").WaitForAsync();

        const string fileGroup = "TEST FILE GROUP";
        await LoginHelper.OpenDialogAsync(User, "#add-files-icon");
        await page.Locator("#input-post-title").FillAsync(fileGroup);
        await page.Locator("#post-modal-btn").ClickAsync();
        await LoginHelper.WaitForDialogClosedAsync(User, "course-details-modal", "Addition of file group failed");
        await Expect(page.Locator(".file-group-title h5")).ToHaveTextAsync(fileGroup);

        await LoginHelper.OpenDialogAsync(User, "#edit-filegroup-icon");
        await page.Locator("#input-file-title").FillAsync(fileGroup + Edited);
        await page.Locator("#put-modal-btn").ClickAsync();
        await LoginHelper.WaitForDialogClosedAsync(User, "put-delete-modal", "Edition of file group failed");
        await Expect(page.Locator("app-file-group .file-group-title h5")).ToHaveTextAsync(fileGroup + Edited);

        const string fileSubGroup = "TEST FILE SUBGROUP";
        await LoginHelper.OpenDialogAsync(User, ".add-subgroup-btn");
        await page.Locator("#input-post-title").FillAsync(fileSubGroup);
        await page.Locator("#post-modal-btn").ClickAsync();
        await LoginHelper.WaitForDialogClosedAsync(User, "course-details-modal", "Addition of file sub-group failed");
        await Expect(page.Locator("app-file-group app-file-group .file-group-title h5")).ToHaveTextAsync(fileSubGroup);

        await LoginHelper.OpenDialogAsync(User, "app-file-group app-file-group .add-file-btn");
        const string fileName = "testFile.txt";
        // Unlike Java (which needs to force `display:block` on the hidden <input type=file>
        // before sendKeys can target it), Playwright's SetInputFilesAsync works on hidden
        // file inputs directly - it doesn't simulate a real click, so visibility isn't required.
        await page.Locator(".input-file-uploader").SetInputFilesAsync(TestFilePath);
        await page.Locator("#upload-all-btn").ClickAsync();
        await page.Locator(".determinate[style*='width: 100']").WaitForAsync(new() { Timeout = 20000 });
        await Expect(page.Locator("i[class*='icon-status-upload']")).ToHaveTextAsync("done");

        await page.Locator("#close-upload-modal-btn").ClickAsync();
        await LoginHelper.WaitForDialogClosedAsync(User, "course-details-modal", "Upload of file failed");
        await Expect(page.Locator("app-file-group app-file-group .chip .file-name-div")).ToHaveTextAsync(fileName);

        await LoginHelper.OpenDialogAsync(User, "app-file-group app-file-group .edit-file-name-icon");
        const string editedFileName = "testFileEDITED.txt";
        await page.Locator("#input-file-title").FillAsync(editedFileName);
        await page.Locator("#put-modal-btn").ClickAsync();
        await LoginHelper.WaitForDialogClosedAsync(User, "put-delete-modal", "Edition of file failed");
        await Expect(page.Locator("app-file-group app-file-group .chip .file-name-div")).ToHaveTextAsync(editedFileName);

        await page.Locator("app-file-group .delete-filegroup-icon").ClickAsync();
        await page.Locator("app-error-message .card-panel.warning").WaitForAsync();

        await CourseNavigationUtilities.DeleteCourseAsync(User, CourseName);
    }

    /// <summary>
    /// Fails to add an unregistered attender, adds a real one, then removes them.
    /// Resources: loginservice(READONLY,10) openvidumock(NOACCESS,10) attenders(READWRITE,1)
    /// executor/webbrowser/webserver(READWRITE,1).
    /// </summary>
    [TestCaseSource(typeof(ParameterLoader), nameof(ParameterLoader.GetTestTeachers))]
    public async Task AttendersRestOperations(string mail, string password, string role)
    {
        var page = User.Page;
        await LoginAndCreateNewCourseAsync(mail, password);
        await EnterCourseAndNavigateTabAsync(CourseName, "attenders-tab-icon");

        await Expect(page.Locator(".attender-row-div")).ToHaveCountAsync(1);
        await Expect(page.Locator(".attender-row-div .attender-name-p")).ToHaveTextAsync(Constants.TeacherName);

        // Add attender fail
        await LoginHelper.OpenDialogAsync(User, "#add-attenders-icon");
        await page.Locator("#input-attender-simple").FillAsync("studentFail@gmail.com");
        await page.Locator("#put-modal-btn").ClickAsync();
        await LoginHelper.WaitForDialogClosedAsync(User, "put-delete-modal", "Addition of attender fail");
        await page.Locator("app-error-message .card-panel.fail").WaitForAsync();
        await Expect(page.Locator(".attender-row-div")).ToHaveCountAsync(1);
        await page.Locator("app-error-message .card-panel.fail .material-icons").ClickAsync();

        // Add attender success
        await LoginHelper.OpenDialogAsync(User, "#add-attenders-icon");
        await page.Locator("#input-attender-simple").FillAsync("student1@gmail.com");
        await page.Locator("#put-modal-btn").ClickAsync();
        await LoginHelper.WaitForDialogClosedAsync(User, "put-delete-modal", "Addition of attender failed");
        await page.Locator("app-error-message .card-panel.correct").WaitForAsync();
        await Expect(page.Locator(".attender-row-div")).ToHaveCountAsync(2);
        await page.Locator("app-error-message .card-panel.correct .material-icons").ClickAsync();

        // Remove attender
        await page.Locator("#edit-attenders-icon").ClickAsync();
        await page.Locator(".del-attender-icon").ClickAsync();
        await Expect(page.Locator(".attender-row-div")).ToHaveCountAsync(1);

        await CourseNavigationUtilities.DeleteCourseAsync(User, CourseName);
    }
}
