using Microsoft.Playwright;
using FullTeaching.E2E.Common;
using FullTeaching.E2E.Utils;
using NUnit.Framework;

namespace FullTeaching.E2E.Tests;

/// <summary>
/// Ported from functional/test/media/FullTeachingEndToEndEChatTests.java.
///
/// Unlike the Cypress port (where this scenario has no equivalent and is skipped - see
/// cypress-js/cypress/e2e/echat.cy.js), Playwright's browser contexts are explicitly designed
/// to isolate several simultaneous logged-in sessions within one browser process, which is the
/// documented Playwright pattern for exactly this "two users interacting live" scenario. See
/// BrowserUser's doc comment and BaseTest.CreateSecondaryUserAsync.
/// </summary>
[TestFixture]
public class EChatTests : BaseTest
{
    private const string StudentMail = "student1@gmail.com";
    private const string StudentPass = "pass";
    private const string FirstCourseTitle = "ul.collection li.collection-item:first-child div.course-title";
    private const string SessionsTab = "#md-tab-label-0-1";
    private const string FirstSessionReady = "ul div:first-child li.session-data div.session-ready";

    private static async Task EnterFirstSessionAsync(BrowserUser user)
    {
        var page = user.Page;
        await page.Locator(FirstCourseTitle).ClickAsync();
        await page.Locator(SessionsTab).ClickAsync();
        await page.Locator(FirstSessionReady).ClickAsync();
        await page.Locator("#fixed-icon").WaitForAsync();
        await page.Locator("#fixed-icon").ClickAsync();
    }

    private static async Task<int> GetNumberMessagesAsync(BrowserUser user) =>
        await user.Page.Locator("app-chat-line").CountAsync();

    private static async Task CheckSystemMessageAsync(BrowserUser user, string message, int messageNumber)
    {
        var messages = await PollHelper.PollUntilAsync(
            () => user.Page.Locator("app-chat-line").AllAsync(),
            list => list.Count > 0);
        var lastMessage = messageNumber >= 0 && messageNumber < messages.Count ? messages[messageNumber] : messages[^1];
        var content = lastMessage.Locator(".system-msg");
        await Microsoft.Playwright.Assertions.Expect(content).ToContainTextAsync(message);
    }

    private static async Task CheckOwnMessageAsync(BrowserUser user, string message, string sender, int numberPriorMessages)
    {
        var messages = await PollHelper.PollUntilAsync(
            () => user.Page.Locator("app-chat-line").AllAsync(),
            list => list.Count > numberPriorMessages);
        var lastMessage = messages[^1];
        await Microsoft.Playwright.Assertions.Expect(lastMessage.Locator(".own-msg .message-header .user-name")).ToContainTextAsync(sender);
        await Microsoft.Playwright.Assertions.Expect(lastMessage.Locator(".own-msg .message-content .user-message")).ToContainTextAsync(message);
    }

    private static async Task CheckStrangerMessageAsync(BrowserUser user, string message, string sender, int numberPriorMessages)
    {
        var messages = await PollHelper.PollUntilAsync(
            () => user.Page.Locator("app-chat-line").AllAsync(),
            list => list.Count > numberPriorMessages);
        var lastMessage = messages[^1];
        await Microsoft.Playwright.Assertions.Expect(lastMessage.Locator(".stranger-msg .message-header .user-name")).ToContainTextAsync(sender);
        await Microsoft.Playwright.Assertions.Expect(lastMessage.Locator(".stranger-msg .message-content .user-message")).ToContainTextAsync(message);
    }

    /// <summary>
    /// Teacher and student join the same video session and exchange chat messages.
    /// Resources: loginservice(READONLY,10) openvidu(READWRITE,10) configuration(READONLY,1)
    /// executor/webbrowser/webserver(READWRITE,1).
    /// </summary>
    [TestCaseSource(typeof(ParameterLoader), nameof(ParameterLoader.GetTestTeachers))]
    public async Task OneToOneChatInSessionChrome(string mail, string password, string role)
    {
        // TEACHER
        await LoginHelper.SlowLoginAsync(User, mail, password);
        await EnterFirstSessionAsync(User);
        await CheckSystemMessageAsync(User, "Connected", 100);

        // STUDENT
        var student = await CreateSecondaryUserAsync("STUDENT", 5);
        await LoginHelper.SlowLoginAsync(student, StudentMail, StudentPass);
        await EnterFirstSessionAsync(student);
        await CheckSystemMessageAsync(student, "Connected", 0);

        await CheckSystemMessageAsync(User, $"{Constants.StudentName} has connected", 100);
        await CheckSystemMessageAsync(student, $"{Constants.TeacherName} has connected", 100);

        // Chat exchange
        const string teacherMessage = "TEACHER CHAT MESSAGE";
        const string studentMessage = "STUDENT CHAT MESSAGE";

        var numberPriorMessages = await GetNumberMessagesAsync(User);
        await User.Page.Locator("#message").FillAsync(teacherMessage);
        await User.Page.Locator("#send-btn").ClickAsync();

        await CheckOwnMessageAsync(User, teacherMessage, Constants.TeacherName, numberPriorMessages);
        await CheckStrangerMessageAsync(student, teacherMessage, Constants.TeacherName, numberPriorMessages);

        numberPriorMessages = await GetNumberMessagesAsync(student);
        await student.Page.Locator("#message").FillAsync(studentMessage);
        await student.Page.Locator("#send-btn").ClickAsync();

        await CheckStrangerMessageAsync(User, studentMessage, Constants.StudentName, numberPriorMessages);
        await CheckOwnMessageAsync(student, studentMessage, Constants.StudentName, numberPriorMessages);
    }
}
