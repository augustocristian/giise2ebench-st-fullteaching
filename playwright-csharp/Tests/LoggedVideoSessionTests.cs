using Microsoft.Playwright;
using FullTeaching.E2E.Common;
using FullTeaching.E2E.Utils;
using NUnit.Framework;

namespace FullTeaching.E2E.Tests;

/// <summary>
/// Ported from functional/test/media/FullTeachingLoggedVideoSessionTests.java.
/// See EChatTests's doc comment for why this - unlike its Cypress counterpart - is fully
/// implemented rather than skipped.
///
/// `studentNameList`/`studentNamesList`/`studentPassList` from the Java class are not ported:
/// they're populated in initializeStudents() but never read anywhere afterwards (write-only
/// dead fields, matching the same call made in the Python port) - only the actual list of
/// BrowserUsers matters, which BaseTest's secondary-user tracking already gives us.
/// </summary>
[TestFixture]
public class LoggedVideoSessionTests : BaseTest
{
    private static readonly string StudentsFilePath =
        Path.Combine(AppContext.BaseDirectory, "Resources", "Inputs", "default_user_LoggedVideoStudents.csv");

    private async Task<List<BrowserUser>> InitializeStudentsAsync()
    {
        var raw = (await File.ReadAllTextAsync(StudentsFilePath)).Trim();
        var students = new List<BrowserUser>();
        foreach (var entry in raw.Split(';', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries))
        {
            var parts = entry.Split(':');
            var userid = parts[0];
            var password = parts[1];
            var student = await CreateSecondaryUserAsync(userid, Constants.WaitSeconds);
            await LoginHelper.SlowLoginAsync(student, userid, password);
            students.Add(student);
        }
        return students;
    }

    private static string GetCurrentSessionHour()
    {
        var now = DateTime.Now;
        var hour12 = now.Hour % 12 == 0 ? 12 : now.Hour % 12;
        var ampm = now.Hour < 12 ? "A" : "P";
        return $"{hour12:D2}{now.Minute:D2}{ampm}";
    }

    private static async Task<bool> DateFieldValueIsAsync(ILocator dateField, string expected)
    {
        var actual = await dateField.InputValueAsync();
        return actual == expected;
    }

    private static async Task IntroduceSessionDateAsync(BrowserUser user, ILocator modal)
    {
        var expectedDate = DateTime.Now.ToString("yyyy-MM-dd");
        var dateField = modal.Locator(Constants.SessionListNewSessionModalDate);
        // <input type=date>.value is always ISO 8601 regardless of display locale, so setting
        // it directly via JS (and firing input/change so Angular's ngModel updates) is simpler
        // and more reliable than typing a locale-formatted string - which is what the Java
        // version does, to work around Selenium/ChromeDriver-specific typing quirks that don't
        // apply here (same simplification made in the Python and Cypress ports).
        await dateField.EvaluateAsync(
            "(el, value) => { el.value = value; el.dispatchEvent(new Event('input', {bubbles: true})); el.dispatchEvent(new Event('change', {bubbles: true})); }",
            expectedDate);
        await user.WaitUntilAsync(
            () => PollHelper.PollUntilAsync(() => DateFieldValueIsAsync(dateField, expectedDate), ok => ok),
            "Failed to set the session date");
    }

    private async Task CreateNewSessionAsync(BrowserUser user, string courseName, string sessionName)
    {
        var page = user.Page;
        var sessionHour = GetCurrentSessionHour();
        const string sessionDescription = "Wow today session will be amazing";

        await NavigateToCourseAsync(user, courseName);
        await page.Locator(Constants.SessionListNewSessionIcon).ClickAsync();
        var modal = page.Locator(Constants.SessionListNewSessionModal);
        await modal.WaitForAsync();

        await modal.Locator(Constants.SessionListNewSessionModalTitle).FillAsync(sessionName);
        await modal.Locator(Constants.SessionListNewSessionModalContent).FillAsync(sessionDescription);
        await IntroduceSessionDateAsync(user, modal);
        await modal.Locator(Constants.SessionListNewSessionModalTime).FillAsync(sessionHour);
        await modal.Locator(Constants.SessionListNewSessionModalPostButton).ClickAsync();

        await PollHelper.PollUntilAsync(
            () => page.Locator(Constants.SessionListSessionRow).AllAsync(),
            rows => rows.Count > 3);
        var sessionTitles = await SessionNavigationUtilities.GetFullSessionListAsync(user);
        Assert.That(sessionTitles, Does.Contain(sessionName), "Session has not been created");
    }

    private static async Task JoinSessionAsync(BrowserUser user, string sessionName)
    {
        var sessionTitles = await SessionNavigationUtilities.GetFullSessionListAsync(user);
        Assert.That(sessionTitles, Does.Contain(sessionName), "Session has not been created");
        var session = await SessionNavigationUtilities.GetSessionAsync(user, sessionName);
        await session.Locator(Constants.SessionListSessionAccess).ClickAsync();
    }

    private static async Task NavigateToCourseAsync(BrowserUser user, string courseName)
    {
        var courses = await CourseNavigationUtilities.GetCoursesListAsync(user);
        Assert.That(courses, Is.Not.Empty, "No courses in the list");
        var course = await CourseNavigationUtilities.GetCourseByNameAsync(user, courseName);
        await course.Locator(Constants.CourseListCourseTitle).ClickAsync();
        await user.Page.Locator(Constants.TabsDiv).WaitForAsync();
        await CourseNavigationUtilities.Go2TabAsync(user, Constants.SessionIcon);
    }

    private static async Task LeaveSessionAsync(BrowserUser user)
    {
        var page = user.Page;
        await page.Locator(Constants.SessionLeftMenuButton).ClickAsync();
        await page.Locator(Constants.SessionExitIcon).ClickAsync(new() { Force = true });
        await page.Locator(Constants.CourseTabs).WaitForAsync();
    }

    private static async Task DeleteSessionAsync(BrowserUser user, string sessionName)
    {
        var session = await SessionNavigationUtilities.GetSessionAsync(user, sessionName);
        await session.Locator(Constants.SessionListSessionEditIcon).ClickAsync();
        var modal = user.Page.Locator(Constants.SessionListEditModal);
        await modal.WaitForAsync();
        var deleteDiv = modal.Locator(Constants.SessionListEditModalDeleteDiv);
        await deleteDiv.Locator("label").ClickAsync();
        await deleteDiv.Locator("a").ClickAsync();

        var sessionTitles = await SessionNavigationUtilities.GetFullSessionListAsync(user);
        Assert.That(sessionTitles, Does.Not.Contain(sessionName), "Session has not been deleted");
    }

    /// <summary>
    /// Creates a video session, has the teacher and every student join it, then everyone
    /// leaves and the session is deleted.
    /// Resources: loginservice(READONLY,10) openvidu(READWRITE,10) session(READONLY,1)
    /// executor/webbrowser/webserver(READWRITE,1).
    /// </summary>
    [TestCaseSource(typeof(ParameterLoader), nameof(ParameterLoader.GetTestTeachers))]
    public async Task SessionTest(string mail, string password, string role)
    {
        const string sessionName = "Today's Session";
        await LoginHelper.SlowLoginAsync(User, mail, password);
        var students = await InitializeStudentsAsync();

        await CreateNewSessionAsync(User, Constants.ForumTestCourseName, sessionName);
        await JoinSessionAsync(User, sessionName);
        foreach (var student in students)
        {
            await NavigateToCourseAsync(student, Constants.ForumTestCourseName);
            await JoinSessionAsync(student, sessionName);
        }

        foreach (var student in students)
        {
            await LeaveSessionAsync(student);
        }
        await LeaveSessionAsync(User);

        await DeleteSessionAsync(User, sessionName);
    }
}
