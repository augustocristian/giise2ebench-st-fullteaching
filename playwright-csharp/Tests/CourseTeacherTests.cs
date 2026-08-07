using Microsoft.Playwright;
using FullTeaching.E2E.Common;
using FullTeaching.E2E.Utils;
using NUnit.Framework;

namespace FullTeaching.E2E.Tests;

/// <summary>
/// Ported from functional/test/teacher/CourseTeacherTest.java.
/// Unlike the Java source, steps are not individually wrapped in try/catch + Assert.Fail(label):
/// NUnit's own failure output already pinpoints the failing line, so a manual per-step label
/// adds noise rather than clarity (same call made in the Python and Cypress ports).
/// </summary>
[TestFixture]
public class CourseTeacherTests : BaseTest
{
    private static string Timestamped(string prefix) => $"{prefix}_{DateTimeOffset.UtcNow.ToUnixTimeMilliseconds()}";

    /// <summary>
    /// Opens the first course and clicks through every tab.
    /// Resources: loginservice(READONLY,10) openvidumock(NOACCESS,10) course(READONLY,15)
    /// executor/webbrowser/webserver(READWRITE,1).
    /// </summary>
    [TestCaseSource(typeof(ParameterLoader), nameof(ParameterLoader.GetTestTeachers))]
    public async Task TeacherCourseMainTest(string mail, string password, string role)
    {
        await LoginHelper.SlowLoginAsync(User, mail, password);
        var page = User.Page;

        await NavigationUtilities.ToCoursesHomeAsync(User);
        await page.Locator(Constants.FirstCourseXPath).ClickAsync();
        await page.Locator(Constants.TabsDiv).WaitForAsync();

        foreach (var icon in new[] { Constants.HomeIcon, Constants.SessionIcon, Constants.ForumIcon, Constants.FilesIcon, Constants.AttendersIcon })
        {
            await CourseNavigationUtilities.Go2TabAsync(User, icon);
        }
    }

    /// <summary>
    /// Creates a course, confirms it exists, deletes it, confirms it's gone.
    /// Resources: loginservice(READONLY,10) openvidumock(NOACCESS,10) course(DYNAMIC,15)
    /// executor/webbrowser/webserver(READWRITE,1).
    /// </summary>
    [TestCaseSource(typeof(ParameterLoader), nameof(ParameterLoader.GetTestTeachers))]
    public async Task TeacherCreateAndDeleteCourseTest(string mail, string password, string role)
    {
        await LoginHelper.SlowLoginAsync(User, mail, password);
        var courseTitle = Timestamped("Test Course");

        await CourseNavigationUtilities.NewCourseAsync(User, courseTitle);
        Assert.That(await CourseNavigationUtilities.CourseExistsAsync(User, courseTitle), Is.True);

        await CourseNavigationUtilities.DeleteCourseAsync(User, courseTitle);
        Assert.That(await CourseNavigationUtilities.CourseExistsAsync(User, courseTitle), Is.False);

        await User.Page.GotoAsync(AppUrl);
    }

    /// <summary>
    /// Renames a course and back, rewrites its rich-text description, toggles its forum, and
    /// checks the current user shows up (highlighted) in its attenders list.
    /// Resources: loginservice(READONLY,10) openvidumock(NOACCESS,10) configuration(READWRITE,1,exclusive)
    /// executor/webbrowser/webserver(READWRITE,1).
    /// </summary>
    [TestCaseSource(typeof(ParameterLoader), nameof(ParameterLoader.GetTestTeachers))]
    public async Task TeacherEditCourseValues(string mail, string password, string role)
    {
        var userName = await LoginHelper.SlowLoginAsync(User, mail, password);
        var page = User.Page;

        await NavigationUtilities.ToCoursesHomeAsync(User);

        var course = await CourseNavigationUtilities.GetCourseByNameAsync(User, Constants.ForumTestCourseName);
        var oldName = (await course.Locator(Constants.CourseTitle).InnerTextAsync()).Trim();
        var editionName = Timestamped("EDITION TEST");

        await CourseNavigationUtilities.ChangeCourseNameAsync(User, oldName, editionName);
        await CourseNavigationUtilities.AssertCourseExistsAsync(
            User, editionName, timeoutMs: 20000);
        await CourseNavigationUtilities.ChangeCourseNameAsync(User, editionName, oldName);
        await CourseNavigationUtilities.AssertCourseExistsAsync(User, oldName, timeoutMs: 20000);

        course = await CourseNavigationUtilities.GetCourseByNameAsync(User, Constants.ForumTestCourseName);
        await course.Locator(Constants.CourseListCourseTitle).ClickAsync();
        await page.Locator(Constants.TabsDiv).WaitForAsync();

        await EditHomeDescriptionAsync(User);

        await CourseNavigationUtilities.Go2TabAsync(User, Constants.SessionIcon);
        // new/delete session are covered by RestOperationsTests's session test

        await ToggleForumAsync(User);

        await page.Locator(Constants.AttendersIcon).WaitForAsync();
        await CourseNavigationUtilities.Go2TabAsync(User, Constants.AttendersIcon);
        await CourseNavigationUtilities.GetTabContentAsync(User, Constants.AttendersIcon);
        Assert.That(await CourseNavigationUtilities.IsUserInAttendersListAsync(User, userName), Is.True, "User isn't in the attenders list");
        var mainUser = await CourseNavigationUtilities.GetHighlightedAttenderAsync(User);
        Assert.That(mainUser, Is.EqualTo(userName), "Main user and active user doesn't match");

        // At the end of this test the header isn't reliably loaded; wait for it before finishing.
        await page.Locator(Constants.MainMenuArrow).WaitForAsync();
    }

    private static async Task EditHomeDescriptionAsync(BrowserUser user)
    {
        var page = user.Page;
        await CourseNavigationUtilities.Go2TabAsync(user, Constants.HomeIcon);
        await page.Locator(Constants.EditDescriptionButton).ClickAsync();
        await page.Locator(Constants.EditDescriptionContentBox).WaitForAsync();

        var editor = page.Locator(".ql-editor");
        await editor.ClickAsync();
        await editor.PressAsync("Control+a");
        await editor.PressAsync("Delete");

        await page.Locator(".ql-header").ClickAsync();
        await page.Locator(".ql-picker-options").WaitForAsync();
        await page.Locator(".ql-picker-item[data-label=\"Heading\"]").ClickAsync();

        await editor.EvaluateAsync(
            "(el) => { el.innerHTML = '<h1>New Title</h1><h2>New SubHeading</h2><p>This is the normal content</p>'; }");
        await page.Locator("#textEditorRowButtons a").Nth(1).ClickAsync();

        await page.Locator(".ql-editor-custom").WaitForAsync();
        await AssertDescriptionRenderedAsync(page, "preview");

        await page.Locator(Constants.EditDescriptionSaveButton).ClickAsync();
        await page.Locator(".ql-editor-custom").WaitForAsync();
        await AssertDescriptionRenderedAsync(page, "saved");
    }

    private static async Task AssertDescriptionRenderedAsync(IPage page, string phase)
    {
        var heading = await page.Locator(".ql-editor-custom h1").InnerTextAsync();
        Assert.That(heading, Is.EqualTo("New Title"), $"Heading {phase} not properly rendered");
        var subheading = await page.Locator(".ql-editor-custom h2").InnerTextAsync();
        Assert.That(subheading, Is.EqualTo("New SubHeading"), $"Subheading {phase} not properly rendered");
        var content = await page.Locator(".ql-editor-custom p").InnerTextAsync();
        Assert.That(content, Is.EqualTo("This is the normal content"), $"Normal {phase} content not properly rendered");
    }

    private static async Task ToggleForumAsync(BrowserUser user)
    {
        await CourseNavigationUtilities.Go2TabAsync(user, Constants.ForumIcon);
        var forumTabContent = await CourseNavigationUtilities.GetTabContentAsync(user, Constants.ForumIcon);

        if (await ForumNavigationUtilities.IsForumEnabledAsync(forumTabContent))
        {
            Assert.That(await forumTabContent.Locator(Constants.ForumNewEntryIcon).CountAsync(), Is.GreaterThan(0), "Add Entry not found");
            Assert.That(await forumTabContent.Locator(Constants.ForumEditEntryIcon).CountAsync(), Is.GreaterThan(0), "Add Entry not found");
            await ForumNavigationUtilities.DisableForumAsync(user);
            await ForumNavigationUtilities.EnableForumAsync(user);
        }
        else
        {
            await ForumNavigationUtilities.EnableForumAsync(user);
            Assert.That(await forumTabContent.Locator(Constants.ForumNewEntryIcon).CountAsync(), Is.GreaterThan(0), "Add Entry not found");
            Assert.That(await forumTabContent.Locator(Constants.ForumEditEntryIcon).CountAsync(), Is.GreaterThan(0), "Add Entry not found");
            await ForumNavigationUtilities.DisableForumAsync(user);
        }
    }

    /// <summary>
    /// Creates a dummy course and deletes it, checking the course count drops by exactly one.
    /// Resources: loginservice(READONLY,10) openvidumock(NOACCESS,10) course(READWRITE,1,exclusive)
    /// executor/webbrowser/webserver(READWRITE,1).
    /// </summary>
    [TestCaseSource(typeof(ParameterLoader), nameof(ParameterLoader.GetTestTeachers))]
    public async Task TeacherDeleteCourseTest(string mail, string password, string role)
    {
        await LoginHelper.SlowLoginAsync(User, mail, password);
        var page = User.Page;
        var courseName = Timestamped("Test Course");

        await NavigationUtilities.ToCoursesHomeAsync(User);
        await CourseNavigationUtilities.NewCourseAsync(User, courseName);

        var countBefore = await page.Locator(".course-list-item").CountAsync();
        await CourseNavigationUtilities.DeleteCourseAsync(User, courseName);
        await Microsoft.Playwright.Assertions.Expect(page.Locator(".course-list-item")).ToHaveCountAsync(countBefore - 1);
    }
}
