using FullTeaching.E2E.Common;
using FullTeaching.E2E.Utils;
using NUnit.Framework;
using static Microsoft.Playwright.Assertions;

namespace FullTeaching.E2E.Tests;

/// <summary>
/// Ported from functional/test/media/FullTeachingTestEndToEndVideoSessionTests.java.
/// See EChatTests's doc comment for why this - unlike its Cypress counterpart - is fully
/// implemented rather than skipped.
/// </summary>
[TestFixture]
public class VideoSessionTests : BaseTest
{
    private const string StudentMail = "student1@gmail.com";
    private const string StudentPass = "pass";
    private const string FirstCourseTitle = "ul.collection li.collection-item:first-child div.course-title";
    private const string SessionsTab = "#md-tab-label-0-1";
    private const string FirstSessionReady = "ul div:first-child li.session-data div.session-ready";
    private const string RecordVoiceOverIcon = "xpath=//div[@id='div-header-buttons']//i[text() = 'record_voice_over']";
    private const string InterventionButton = "xpath=//a[contains(@class, 'usr-btn')]";

    private static async Task EnterFirstSessionAndCheckVideoAsync(BrowserUser user)
    {
        var page = user.Page;
        await page.Locator(FirstCourseTitle).ClickAsync();
        await page.Locator(SessionsTab).ClickAsync();
        await page.Locator(FirstSessionReady).ClickAsync();
        await page.Locator("div.participant video").WaitForAsync();
        await CheckVideoPlayingAsync(user, "div.participant");
    }

    /// <summary>
    /// Confirms the &lt;video&gt; element has an active srcObject, mirrors checkVideoPlaying().
    /// Full readyState=4 is not checked because the CI media server cannot always relay media
    /// over DTLS to headless Chromium, so data never actually flows even though the session
    /// and stream objects are correctly initialized - same caveat the Java version documents.
    /// </summary>
    private static async Task CheckVideoPlayingAsync(BrowserUser user, string containerQuerySelector)
    {
        var probe =
            $"var v = document.querySelector('{containerQuerySelector}').getElementsByTagName('video')[0];" +
            "return v && v.srcObject != null && v.srcObject.active;";

        await PollHelper.PollUntilAsync(
            async () =>
            {
                var active = await user.Page.EvaluateAsync<bool>($"() => {{ {probe} }}");
                if (!active)
                {
                    throw new TimeoutException($"video in '{containerQuerySelector}' not playing yet");
                }
                return active;
            },
            active => active);
    }

    /// <summary>
    /// Teacher and student join a session; the student requests to intervene, the teacher
    /// grants and then revokes it, and both sides' videos are checked at each step.
    /// Resources: loginservice(READONLY,10) openvidu(READWRITE,10) session(READWRITE,1)
    /// executor/webbrowser/webserver(READWRITE,1).
    /// </summary>
    [TestCaseSource(typeof(ParameterLoader), nameof(ParameterLoader.GetTestTeachers))]
    public async Task OneToOneVideoAudioSessionChrome(string mail, string password, string role)
    {
        // TEACHER
        await LoginHelper.SlowLoginAsync(User, mail, password);
        await EnterFirstSessionAndCheckVideoAsync(User);

        // STUDENT
        var student = await CreateSecondaryUserAsync("STUDENT", 5);
        await LoginHelper.SlowLoginAsync(student, StudentMail, StudentPass);
        await EnterFirstSessionAndCheckVideoAsync(student);

        // Student asks for intervention
        await student.Page.Locator(RecordVoiceOverIcon).ClickAsync();

        // Teacher accepts intervention
        await User.Page.Locator(InterventionButton).ClickAsync();

        // Check both videos for both users
        await student.Page.Locator("div.participant-small video").WaitForAsync();
        await CheckVideoPlayingAsync(student, "div.participant-small");
        await CheckVideoPlayingAsync(student, "div.participant");

        await User.Page.Locator("div.participant-small video").WaitForAsync();
        await CheckVideoPlayingAsync(User, "div.participant-small");
        await CheckVideoPlayingAsync(User, "div.participant");

        // Teacher stops student intervention
        await User.Page.Locator(InterventionButton).ClickAsync();

        // Wait until only one video is left on each side
        await Expect(User.Page.Locator("div.participant-small video")).ToHaveCountAsync(0);
        await Expect(student.Page.Locator("div.participant-small video")).ToHaveCountAsync(0);
    }
}
