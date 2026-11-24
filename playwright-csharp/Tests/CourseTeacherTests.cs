using System.Text.RegularExpressions;
using FullTeaching.E2E.Common;
using FullTeaching.E2E.Utils;
using Microsoft.Playwright;
using NUnit.Framework;
using static Microsoft.Playwright.Assertions;

namespace FullTeaching.E2E.Tests;

/// <summary>
/// Ported from functional/test/teacher/CourseTeacherTest.java.
/// Unlike the Java source, steps are not individually wrapped in try/catch + Assert.Fail(label):
/// NUnit's own failure output already pinpoints the failing line, so a manual per-step label
/// adds noise rather than clarity (same call made in the Python and Cypress ports).
/// </summary>
[TestFixture]
[Category("Course")]
[Category("Teacher")]
public class CourseTeacherTests : BaseTest
{
    private const string NewCourseNamePrefix = "Test Course";
    private const string EditedCourseNamePrefix = "EDITION TEST";

    /// <summary>Quill rich-text editor selectors and the content the description test writes.</summary>
    private static class DescriptionEditor
    {
        public const string Content = Constants.EditDescriptionContentBox;
        // Quill builds a span picker and keeps the hidden <select> it replaces, both with class ql-header.
        public const string HeaderPicker = "span.ql-header";
        public const string PickerOptions = ".ql-picker-options";
        public const string HeadingOption = ".ql-picker-item[data-label=\"Heading\"]";
        // The preview toggle is the only floated (left) control of the editor's button row.
        public const string PreviewButton = "#textEditorRowButtons .left";
        public const string Rendered = Constants.DescriptionView;

        public const string Title = "New Title";
        public const string SubHeading = "New SubHeading";
        public const string Paragraph = "This is the normal content";

        public static readonly string Html = $"<h1>{Title}</h1><h2>{SubHeading}</h2><p>{Paragraph}</p>";
    }

    /// <summary>
    /// Opens the first course and clicks through every tab.
    /// Resources: loginservice(READONLY,10) openvidumock(NOACCESS,10) course(READONLY,15)
    /// executor/webbrowser/webserver(READWRITE,1).
    /// </summary>
    [TestCaseSource(typeof(ParameterLoader), nameof(ParameterLoader.GetTestTeachers))]
    [Description("A teacher can open the first course and every one of its tabs loads.")]
    public async Task TeacherCourseMainTest(string mail, string password, string role)
    {
        await LoginHelper.SlowLoginAsync(User, mail, password);
        await NavigationUtilities.ToCoursesHomeAsync(User);

        await User.Page.Locator(Constants.FirstCourseXPath).ClickAsync();
        await Expect(User.Page.Locator(Constants.TabsDiv)).ToBeVisibleAsync();

        await CourseTestSupport.VisitEveryTabAsync(User);
    }

    /// <summary>
    /// Creates a course, confirms it exists, deletes it, confirms it's gone.
    /// Resources: loginservice(READONLY,10) openvidumock(NOACCESS,10) course(DYNAMIC,15)
    /// executor/webbrowser/webserver(READWRITE,1).
    /// </summary>
    [TestCaseSource(typeof(ParameterLoader), nameof(ParameterLoader.GetTestTeachers))]
    [Description("A teacher can create a new course and then delete it again.")]
    public async Task TeacherCreateAndDeleteCourseTest(string mail, string password, string role)
    {
        await LoginHelper.SlowLoginAsync(User, mail, password);
        var courseTitle = CourseTestSupport.Timestamped(NewCourseNamePrefix);
        var course = CourseTestSupport.CourseItem(User.Page, courseTitle);
        var courseMayBeLeftBehind = true;

        try
        {
            await CourseNavigationUtilities.NewCourseAsync(User, courseTitle);
            await Expect(course).ToBeVisibleAsync(CourseTestSupport.CourseListVisible);

            await CourseNavigationUtilities.DeleteCourseAsync(User, courseTitle);
            courseMayBeLeftBehind = false;
            await Expect(course).ToHaveCountAsync(0);

            // Reset to the landing page so the teardown logout starts from a known state.
            await User.Page.GotoAsync(AppUrl);
        }
        finally
        {
            if (courseMayBeLeftBehind)
            {
                await CourseTestSupport.TryDeleteCourseAsync(User, courseTitle);
            }
        }
    }

    /// <summary>
    /// Renames a course and back, rewrites its rich-text description, toggles its forum, and
    /// checks the current user shows up (highlighted) in its attenders list.
    /// Resources: loginservice(READONLY,10) openvidumock(NOACCESS,10) configuration(READWRITE,1,exclusive)
    /// executor/webbrowser/webserver(READWRITE,1).
    /// </summary>
    [TestCaseSource(typeof(ParameterLoader), nameof(ParameterLoader.GetTestTeachers))]
    [Description("A teacher can rename a course, edit its description, toggle its forum and see themselves in the attenders list.")]
    public async Task TeacherEditCourseValues(string mail, string password, string role)
    {
        var userName = await LoginHelper.SlowLoginAsync(User, mail, password);
        var page = User.Page;
        const string originalName = Constants.ForumTestCourseName;
        var editedName = CourseTestSupport.Timestamped(EditedCourseNamePrefix);
        var mustRestoreName = true;

        try
        {
            await NavigationUtilities.ToCoursesHomeAsync(User);
            await Expect(CourseTestSupport.CourseItem(page, originalName)).ToBeVisibleAsync(CourseTestSupport.CourseListVisible);

            await CourseNavigationUtilities.ChangeCourseNameAsync(User, originalName, editedName);
            await Expect(CourseTestSupport.CourseItem(page, editedName)).ToBeVisibleAsync(CourseTestSupport.CourseListVisible);
            await CourseNavigationUtilities.ChangeCourseNameAsync(User, editedName, originalName);
            mustRestoreName = false;
            await Expect(CourseTestSupport.CourseItem(page, originalName)).ToBeVisibleAsync(CourseTestSupport.CourseListVisible);

            await CourseTestSupport.CourseItem(page, originalName).Locator(Constants.CourseListCourseTitle).ClickAsync();
            await Expect(page.Locator(Constants.TabsDiv)).ToBeVisibleAsync();

            await EditHomeDescriptionAsync(User);

            // New/delete session are covered by RestOperationsTests's session test.
            await CourseNavigationUtilities.Go2TabAsync(User, Constants.SessionIcon);

            await ToggleForumAsync(User);

            await CourseNavigationUtilities.Go2TabAsync(User, Constants.AttendersIcon);
            var isListed = await CourseNavigationUtilities.IsUserInAttendersListAsync(User, userName);
            var highlighted = await CourseNavigationUtilities.GetHighlightedAttenderAsync(User);
            using (Assert.EnterMultipleScope())
            {
                Assert.That(isListed, Is.True, "User isn't in the attenders list");
                Assert.That(highlighted, Is.EqualTo(userName), "Main user and active user doesn't match");
            }

            // At the end of this test the header isn't reliably loaded; wait for it before finishing.
            await Expect(page.Locator(Constants.MainMenuArrow)).ToBeVisibleAsync();
        }
        finally
        {
            if (mustRestoreName)
            {
                await CourseTestSupport.TryRenameCourseAsync(User, editedName, originalName);
            }
        }
    }

    /// <summary>
    /// Creates a dummy course and deletes it, checking the course count drops by exactly one.
    /// Resources: loginservice(READONLY,10) openvidumock(NOACCESS,10) course(READWRITE,1,exclusive)
    /// executor/webbrowser/webserver(READWRITE,1).
    /// </summary>
    [TestCaseSource(typeof(ParameterLoader), nameof(ParameterLoader.GetTestTeachers))]
    [Description("Deleting a course removes exactly one entry from the course list.")]
    public async Task TeacherDeleteCourseTest(string mail, string password, string role)
    {
        await LoginHelper.SlowLoginAsync(User, mail, password);
        var courseName = CourseTestSupport.Timestamped(NewCourseNamePrefix);
        var courseMayBeLeftBehind = true;

        try
        {
            await CourseNavigationUtilities.NewCourseAsync(User, courseName);

            var courseEntries = User.Page.Locator(CourseTestSupport.CourseEntry);
            var countBefore = await courseEntries.CountAsync();
            await CourseNavigationUtilities.DeleteCourseAsync(User, courseName);
            courseMayBeLeftBehind = false;

            await Expect(courseEntries).ToHaveCountAsync(countBefore - 1);
        }
        finally
        {
            if (courseMayBeLeftBehind)
            {
                await CourseTestSupport.TryDeleteCourseAsync(User, courseName);
            }
        }
    }

    private static async Task EditHomeDescriptionAsync(BrowserUser user)
    {
        var page = user.Page;
        await CourseNavigationUtilities.Go2TabAsync(user, Constants.HomeIcon);
        await page.Locator(Constants.EditDescriptionButton).ClickAsync();
        await Expect(page.Locator(Constants.EditDescriptionContentBox)).ToBeVisibleAsync();

        var editor = page.Locator(DescriptionEditor.Content);
        await editor.ClickAsync();
        await editor.PressAsync("Control+a");
        await editor.PressAsync("Delete");

        await page.Locator(DescriptionEditor.HeaderPicker).ClickAsync();
        await Expect(page.Locator(DescriptionEditor.PickerOptions)).ToBeVisibleAsync();
        await page.Locator(DescriptionEditor.HeadingOption).ClickAsync();

        // Quill offers no UI path to type structured (h1/h2/p) content in one go, so the
        // editor's DOM is set directly; Quill's mutation observer syncs it into its model.
        await editor.EvaluateAsync("(el, html) => { el.innerHTML = html; }", DescriptionEditor.Html);
        await page.Locator(DescriptionEditor.PreviewButton).ClickAsync();
        await ExpectDescriptionRenderedAsync(page);

        await page.Locator(Constants.EditDescriptionSaveButton).ClickAsync();
        await ExpectDescriptionRenderedAsync(page);
    }

    private static async Task ExpectDescriptionRenderedAsync(IPage page)
    {
        var rendered = page.Locator(DescriptionEditor.Rendered);
        await Expect(rendered).ToBeVisibleAsync();
        await Expect(rendered.Locator("h1")).ToHaveTextAsync(DescriptionEditor.Title);
        await Expect(rendered.Locator("h2")).ToHaveTextAsync(DescriptionEditor.SubHeading);
        await Expect(rendered.Locator("p")).ToHaveTextAsync(DescriptionEditor.Paragraph);
    }

    /// <summary>Exercises the forum toggle from whichever state the course is in and leaves it as found.</summary>
    private static async Task ToggleForumAsync(BrowserUser user)
    {
        await CourseNavigationUtilities.Go2TabAsync(user, Constants.ForumIcon);
        var forumTabContent = await CourseNavigationUtilities.GetTabContentAsync(user, Constants.ForumIcon);
        var forumWasEnabled = await ForumNavigationUtilities.IsForumEnabledAsync(forumTabContent);

        if (!forumWasEnabled)
        {
            await ForumNavigationUtilities.EnableForumAsync(user);
        }

        await Expect(forumTabContent.Locator(Constants.ForumNewEntryIcon).First).ToBeVisibleAsync();
        await Expect(forumTabContent.Locator(Constants.ForumEditEntryIcon).First).ToBeVisibleAsync();

        await ForumNavigationUtilities.DisableForumAsync(user);
        if (forumWasEnabled)
        {
            await ForumNavigationUtilities.EnableForumAsync(user);
        }
    }
}

/// <summary>Course-related helpers shared by the course test fixtures of this suite.</summary>
internal static class CourseTestSupport
{
    /// <summary>Every course entry in the dashboard list.</summary>
    public const string CourseEntry = ".course-list-item";

    private const string ListItem = "li";
    private const float CourseListTimeoutMs = 20_000;

    public static readonly LocatorAssertionsToBeVisibleOptions CourseListVisible = new() { Timeout = CourseListTimeoutMs };

    public static readonly string[] AllTabIcons =
    [
        Constants.HomeIcon,
        Constants.SessionIcon,
        Constants.ForumIcon,
        Constants.FilesIcon,
        Constants.AttendersIcon,
    ];

    public static string Timestamped(string prefix) => $"{prefix}_{DateTimeOffset.UtcNow.ToUnixTimeMilliseconds()}";

    /// <summary>Matches an element whose whole text is <paramref name="text"/>, ignoring surrounding whitespace.</summary>
    public static Regex ExactText(string text) => new($"^\\s*{Regex.Escape(text)}\\s*$");

    /// <summary>The (auto-waiting) dashboard list entry whose title is exactly <paramref name="title"/>.</summary>
    public static ILocator CourseItem(IPage page, string title) =>
        page.Locator(Constants.CourseList).Locator(ListItem).Filter(new()
        {
            Has = page.Locator(Constants.CourseTitle).Filter(new() { HasTextRegex = ExactText(title) }),
        });

    /// <summary>Opens every tab of the currently open course, checking each one's content loads.</summary>
    public static async Task VisitEveryTabAsync(BrowserUser user)
    {
        foreach (var icon in AllTabIcons)
        {
            await CourseNavigationUtilities.Go2TabAsync(user, icon);
        }
    }

    /// <summary>Runs a cleanup step without letting its own failure mask the test's real outcome.</summary>
    public static async Task BestEffortAsync(string description, Func<Task> cleanup)
    {
        try
        {
            await cleanup();
        }
        catch (Exception ex)
        {
            TestContext.Progress.WriteLine($"Cleanup failed ({description}): {ex.Message}");
        }
    }

    public static Task TryDeleteCourseAsync(BrowserUser user, string courseTitle) =>
        BestEffortAsync($"delete course '{courseTitle}'", async () =>
        {
            await NavigationUtilities.ToCoursesHomeAsync(user);
            await Expect(user.Page.Locator(CourseEntry).First).ToBeVisibleAsync();
            if (await CourseItem(user.Page, courseTitle).CountAsync() > 0)
            {
                await CourseNavigationUtilities.DeleteCourseAsync(user, courseTitle);
            }
        });

    public static Task TryRenameCourseAsync(BrowserUser user, string currentName, string originalName) =>
        BestEffortAsync($"rename course '{currentName}' back to '{originalName}'", async () =>
        {
            await NavigationUtilities.ToCoursesHomeAsync(user);
            await Expect(user.Page.Locator(CourseEntry).First).ToBeVisibleAsync();
            if (await CourseItem(user.Page, currentName).CountAsync() > 0)
            {
                await CourseNavigationUtilities.ChangeCourseNameAsync(user, currentName, originalName);
            }
        });
}
