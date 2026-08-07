using FullTeaching.E2E.Common;
using FullTeaching.E2E.Utils;
using Microsoft.Playwright;
using NUnit.Framework;
using static Microsoft.Playwright.Assertions;

namespace FullTeaching.E2E.Tests;

/// <summary>
/// Ported from functional/test/media/FullTeachingTestEndToEndVideoSessionTests.java.
/// See EChatTests's doc comment for why this - unlike its Cypress counterpart - is fully
/// implemented rather than skipped.
/// </summary>
[TestFixture]
[Category("Media")]
[Category("MultiUser")]
public class VideoSessionTests : BaseTest
{
    private const string MainVideoContainer = "div.participant";
    private const string SmallVideoContainer = "div.participant-small";
    private const string RaiseHandIcon = "xpath=//div[@id='div-header-buttons']//i[text() = 'record_voice_over']";
    private const string InterventionButton = "xpath=//a[contains(@class, 'usr-btn')]";

    /// <summary>
    /// Evaluates to true once the first &lt;video&gt; inside the given container has an active
    /// srcObject, mirrors checkVideoPlaying(). Full readyState=4 is deliberately not checked
    /// because the CI media server cannot always relay media over DTLS to headless Chromium,
    /// so data never actually flows even though the session and stream objects are correctly
    /// initialized - same caveat the Java version documents.
    /// </summary>
    private const string VideoHasActiveStreamScript = """
        containerSelector => {
            const video = document.querySelector(containerSelector)?.getElementsByTagName('video')[0];
            return !!video && video.srcObject != null && video.srcObject.active === true;
        }
        """;

    private static readonly LocatorAssertionsToBeVisibleOptions MediaVisible = new() { Timeout = LiveSessionSupport.MediaTimeoutMs };
    private static readonly LocatorAssertionsToHaveCountOptions RealtimeCount = new() { Timeout = LiveSessionSupport.RealtimeTimeoutMs };

    /// <summary>
    /// Teacher and student join a session; the student requests to intervene, the teacher
    /// grants and then revokes it, and both sides' videos are checked at each step.
    /// Resources: loginservice(READONLY,10) openvidu(READWRITE,10) session(READWRITE,1)
    /// executor/webbrowser/webserver(READWRITE,1).
    /// </summary>
    [TestCaseSource(typeof(ParameterLoader), nameof(ParameterLoader.GetTestTeachers))]
    [Description("A student's intervention request can be granted and revoked by the teacher, with video flowing at each step on both sides.")]
    public async Task OneToOneVideoAudioSessionChrome(string mail, string password, string role)
    {
        var teacher = User;
        await LoginHelper.SlowLoginAsync(teacher, mail, password);
        await JoinFirstSessionAndCheckVideoAsync(teacher);

        var student = await CreateSecondaryUserAsync(LiveSessionSupport.StudentIdentifier, Constants.WaitSeconds);
        await LoginHelper.SlowLoginAsync(student, LiveSessionSupport.StudentMail, LiveSessionSupport.StudentPassword);
        await JoinFirstSessionAndCheckVideoAsync(student);

        // Student asks for the floor, teacher grants it: both users now see both streams.
        await student.Page.Locator(RaiseHandIcon).ClickAsync();
        await teacher.Page.Locator(InterventionButton).ClickAsync();

        await ExpectSmallAndMainVideosPlayingAsync(student);
        await ExpectSmallAndMainVideosPlayingAsync(teacher);

        // Teacher takes the floor back: only the main video is left on each side.
        await teacher.Page.Locator(InterventionButton).ClickAsync();

        await Expect(SmallVideo(teacher)).ToHaveCountAsync(0, RealtimeCount);
        await Expect(SmallVideo(student)).ToHaveCountAsync(0, RealtimeCount);
    }

    private static ILocator SmallVideo(BrowserUser user) => user.Page.Locator($"{SmallVideoContainer} video");

    private static async Task JoinFirstSessionAndCheckVideoAsync(BrowserUser user)
    {
        await LiveSessionSupport.OpenFirstSessionAsync(user);
        await ExpectVideoPlayingAsync(user, MainVideoContainer);
    }

    private static async Task ExpectSmallAndMainVideosPlayingAsync(BrowserUser user)
    {
        await ExpectVideoPlayingAsync(user, SmallVideoContainer);
        await ExpectVideoPlayingAsync(user, MainVideoContainer);
    }

    private static async Task ExpectVideoPlayingAsync(BrowserUser user, string containerSelector)
    {
        await Expect(user.Page.Locator($"{containerSelector} video")).ToBeVisibleAsync(MediaVisible);
        await using var streamActive = await user.Page.WaitForFunctionAsync(
            VideoHasActiveStreamScript,
            containerSelector,
            new() { Timeout = LiveSessionSupport.MediaTimeoutMs });
    }
}

/// <summary>Selectors, credentials, timeouts and navigation shared by the live-session (e-chat and video) fixtures.</summary>
internal static class LiveSessionSupport
{
    public const string StudentIdentifier = "STUDENT";
    public const string StudentMail = "student1@gmail.com";
    public const string StudentPassword = "pass";

    /// <summary>Upper bound for something another browser user has to do (chat message, grant) to show up.</summary>
    public const float RealtimeTimeoutMs = 30_000;

    /// <summary>Upper bound for the media server to connect and start relaying streams.</summary>
    public const float MediaTimeoutMs = Constants.WaitSeconds * 1000;

    private const string FirstCourseTitle = "ul.collection li.collection-item:first-child div.course-title";
    private const string FirstReadySession = "ul div:first-child li.session-data div.session-ready";

    /// <summary>From the dashboard: opens the first course, its sessions tab, and enters the first ready session.</summary>
    public static async Task OpenFirstSessionAsync(BrowserUser user)
    {
        await user.Page.Locator(FirstCourseTitle).ClickAsync();
        await CourseNavigationUtilities.Go2TabAsync(user, Constants.SessionIcon);
        await user.Page.Locator(FirstReadySession).ClickAsync();
    }
}
