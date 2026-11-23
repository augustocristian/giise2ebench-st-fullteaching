using System.Globalization;
using FullTeaching.E2E.Common;
using FullTeaching.E2E.Utils;
using Microsoft.Playwright;
using NUnit.Framework;
using static Microsoft.Playwright.Assertions;

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
[Category("Media")]
[Category("MultiUser")]
public class LoggedVideoSessionTests : BaseTest
{
    private const string SessionNamePrefix = "Today's Session";
    private const string SessionDescription = "Wow today session will be amazing";
    private const string CleanupUserIdentifier = "CLEANUP";
    private const int CleanupTimeoutSeconds = 30;

    private const char StudentEntrySeparator = ';';
    private const char StudentFieldSeparator = ':';

    private static readonly string StudentsFilePath =
        Path.Combine(AppContext.BaseDirectory, "Resources", "Inputs", "default_user_LoggedVideoStudents.csv");

    private static readonly LocatorAssertionsToBeVisibleOptions RealtimeVisible = new() { Timeout = LiveSessionSupport.RealtimeTimeoutMs };
    private static readonly LocatorAssertionsToBeVisibleOptions MediaVisible = new() { Timeout = LiveSessionSupport.MediaTimeoutMs };

    private readonly record struct Credentials(string UserId, string Password);

    /// <summary>
    /// Creates a video session, has the teacher and every student join it, then everyone
    /// leaves and the session is deleted.
    /// Resources: loginservice(READONLY,10) openvidu(READWRITE,10) session(READONLY,1)
    /// executor/webbrowser/webserver(READWRITE,1).
    /// </summary>
    [TestCaseSource(typeof(ParameterLoader), nameof(ParameterLoader.GetTestTeachers))]
    [Description("A teacher creates a session, the teacher and every student join and leave it, and the session is deleted.")]
    public async Task SessionTest(string mail, string password, string role)
    {
        var teacher = User;
        var sessionName = CourseTestSupport.Timestamped(SessionNamePrefix);
        await LoginHelper.SlowLoginAsync(teacher, mail, password);
        var students = await LoginStudentsAsync();
        var sessionMayBeLeftBehind = true;

        try
        {
            await CreateSessionAsync(teacher, Constants.ForumTestCourseName, sessionName);
            await JoinSessionAsync(teacher, sessionName);
            foreach (var student in students)
            {
                await OpenSessionsTabAsync(student, Constants.ForumTestCourseName);
                await JoinSessionAsync(student, sessionName);
            }

            foreach (var student in students)
            {
                await LeaveSessionAsync(student);
            }
            await LeaveSessionAsync(teacher);

            await DeleteSessionAsync(teacher, sessionName);
            sessionMayBeLeftBehind = false;
        }
        finally
        {
            if (sessionMayBeLeftBehind)
            {
                await TryDeleteSessionAsync(mail, password, sessionName);
            }
        }
    }

    private async Task<List<BrowserUser>> LoginStudentsAsync()
    {
        var students = new List<BrowserUser>();
        foreach (var credentials in ParseStudents(await File.ReadAllTextAsync(StudentsFilePath)))
        {
            var student = await CreateSecondaryUserAsync(credentials.UserId, Constants.WaitSeconds);
            await LoginHelper.SlowLoginAsync(student, credentials.UserId, credentials.Password);
            students.Add(student);
        }
        return students;
    }

    /// <summary>Parses the "user:password:browser;user:password:browser" students file.</summary>
    private static List<Credentials> ParseStudents(string raw) =>
        raw.Trim()
            .Split(StudentEntrySeparator, StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries)
            .Select(entry => entry.Split(StudentFieldSeparator))
            .Select(fields => fields.Length >= 2
                ? new Credentials(fields[0], fields[1])
                : throw new InvalidDataException($"Malformed student entry in {StudentsFilePath}: expected user:password"))
            .ToList();

    /// <summary>The session's time-of-day as <c>&lt;input type="time"&gt;</c> accepts it: HH:mm (24h).</summary>
    private static string CurrentSessionTime() => DateTime.Now.ToString("HH:mm", CultureInfo.InvariantCulture);

    private static ILocator SessionRow(BrowserUser user, string sessionName) =>
        user.Page.Locator(Constants.SessionListSessionRow).Filter(new()
        {
            Has = user.Page.Locator(Constants.SessionListSessionName).Filter(new() { HasTextRegex = CourseTestSupport.ExactText(sessionName) }),
        });

    private static async Task OpenSessionsTabAsync(BrowserUser user, string courseName)
    {
        await NavigationUtilities.ToCoursesHomeAsync(user);
        await CourseTestSupport.CourseItem(user.Page, courseName).Locator(Constants.CourseListCourseTitle).ClickAsync();
        await Expect(user.Page.Locator(Constants.TabsDiv)).ToBeVisibleAsync();
        await CourseNavigationUtilities.Go2TabAsync(user, Constants.SessionIcon);
    }

    private static async Task CreateSessionAsync(BrowserUser user, string courseName, string sessionName)
    {
        var page = user.Page;
        await OpenSessionsTabAsync(user, courseName);
        await page.Locator(Constants.SessionListNewSessionIcon).ClickAsync();

        var modal = page.Locator(Constants.SessionListNewSessionModal);
        await Expect(modal).ToBeVisibleAsync();
        await modal.Locator(Constants.SessionListNewSessionModalTitle).FillAsync(sessionName);
        await modal.Locator(Constants.SessionListNewSessionModalContent).FillAsync(SessionDescription);

        // Filling an <input type=date> takes an ISO 8601 value whatever the display locale is,
        // and Playwright fires the input/change events Angular's ngModel listens to.
        var expectedDate = DateTime.Now.ToString("yyyy-MM-dd", CultureInfo.InvariantCulture);
        var dateField = modal.Locator(Constants.SessionListNewSessionModalDate);
        await dateField.FillAsync(expectedDate);
        await Expect(dateField).ToHaveValueAsync(expectedDate);

        await modal.Locator(Constants.SessionListNewSessionModalTime).FillAsync(CurrentSessionTime());
        await modal.Locator(Constants.SessionListNewSessionModalPostButton).ClickAsync();

        await Expect(SessionRow(user, sessionName)).ToBeVisibleAsync(RealtimeVisible);
    }

    private static async Task JoinSessionAsync(BrowserUser user, string sessionName)
    {
        await SessionRow(user, sessionName).Locator(Constants.SessionListSessionAccess).ClickAsync();
        await Expect(user.Page.Locator(Constants.SessionLeftMenuButton)).ToBeVisibleAsync(MediaVisible);
    }

    private static async Task LeaveSessionAsync(BrowserUser user)
    {
        await user.Page.Locator(Constants.SessionLeftMenuButton).ClickAsync();
        await user.Page.Locator(Constants.SessionExitIcon).ClickAsync(new() { Force = true });
        await Expect(user.Page.Locator(Constants.CourseTabs)).ToBeVisibleAsync();
    }

    private static async Task DeleteSessionAsync(BrowserUser user, string sessionName)
    {
        await CourseNavigationUtilities.Go2TabAsync(user, Constants.SessionIcon);
        var session = SessionRow(user, sessionName);
        await session.Locator(Constants.SessionListSessionEditIcon).ClickAsync();

        var modal = user.Page.Locator(Constants.SessionListEditModal);
        await Expect(modal).ToBeVisibleAsync();
        var deleteDiv = modal.Locator(Constants.SessionListEditModalDeleteDiv);
        await deleteDiv.Locator("label").ClickAsync();
        await deleteDiv.Locator("a").ClickAsync();

        await Expect(session).ToHaveCountAsync(0, new() { Timeout = LiveSessionSupport.RealtimeTimeoutMs });
    }

    /// <summary>
    /// Removes a session a failed run may have left behind. Uses a fresh browser context
    /// because the failing users' pages can be stuck inside the session view.
    /// </summary>
    private Task TryDeleteSessionAsync(string teacherMail, string teacherPassword, string sessionName) =>
        CourseTestSupport.BestEffortAsync($"delete session '{sessionName}'", async () =>
        {
            var cleaner = await CreateSecondaryUserAsync(CleanupUserIdentifier, CleanupTimeoutSeconds);
            await LoginHelper.SlowLoginAsync(cleaner, teacherMail, teacherPassword);
            await OpenSessionsTabAsync(cleaner, Constants.ForumTestCourseName);

            await Expect(cleaner.Page.Locator(Constants.SessionListSessionRow).First).ToBeVisibleAsync();
            if (await SessionRow(cleaner, sessionName).CountAsync() > 0)
            {
                await DeleteSessionAsync(cleaner, sessionName);
            }
        });
}
