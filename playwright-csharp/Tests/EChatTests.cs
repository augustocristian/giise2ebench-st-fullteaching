using FullTeaching.E2E.Common;
using FullTeaching.E2E.Utils;
using Microsoft.Playwright;
using NUnit.Framework;
using static Microsoft.Playwright.Assertions;

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
[Category("Media")]
[Category("MultiUser")]
public class EChatTests : BaseTest
{
    private const string SideMenuToggle = "#fixed-icon";
    private const string ChatLine = "app-chat-line";
    private const string SystemMessage = ".system-msg";
    private const string OwnMessage = ".own-msg";
    private const string StrangerMessage = ".stranger-msg";
    private const string MessageSender = ".message-header .user-name";
    private const string MessageText = ".message-content .user-message";
    private const string MessageInput = "#message";
    private const string SendButton = "#send-btn";

    private const string ConnectedNotice = "Connected";
    private const string TeacherMessage = "TEACHER CHAT MESSAGE";
    private const string StudentMessage = "STUDENT CHAT MESSAGE";

    /// <summary>
    /// Teacher and student join the same video session and exchange chat messages.
    /// Resources: loginservice(READONLY,10) openvidu(READWRITE,10) configuration(READONLY,1)
    /// executor/webbrowser/webserver(READWRITE,1).
    /// </summary>
    [TestCaseSource(typeof(ParameterLoader), nameof(ParameterLoader.GetTestTeachers))]
    [Description("A teacher and a student in the same session see each other's join notices and exchange chat messages.")]
    public async Task OneToOneChatInSessionChrome(string mail, string password, string role)
    {
        var teacher = User;
        await LoginHelper.SlowLoginAsync(teacher, mail, password);
        await EnterSessionChatAsync(teacher);
        await ExpectSystemMessageAsync(ChatLines(teacher).Last, ConnectedNotice);

        var student = await CreateSecondaryUserAsync(LiveSessionSupport.StudentIdentifier, Constants.WaitSeconds);
        await LoginHelper.SlowLoginAsync(student, LiveSessionSupport.StudentMail, LiveSessionSupport.StudentPassword);
        await EnterSessionChatAsync(student);
        await ExpectSystemMessageAsync(ChatLines(student).First, ConnectedNotice);

        await ExpectSystemMessageAsync(ChatLines(teacher).Last, $"{Constants.StudentName} has connected");
        await ExpectSystemMessageAsync(ChatLines(student).Last, $"{Constants.TeacherName} has connected");

        await SendMessageAsync(teacher, TeacherMessage);
        await ExpectMessageAsync(teacher, OwnMessage, Constants.TeacherName, TeacherMessage);
        await ExpectMessageAsync(student, StrangerMessage, Constants.TeacherName, TeacherMessage);

        await SendMessageAsync(student, StudentMessage);
        await ExpectMessageAsync(teacher, StrangerMessage, Constants.StudentName, StudentMessage);
        await ExpectMessageAsync(student, OwnMessage, Constants.StudentName, StudentMessage);
    }

    private static ILocator ChatLines(BrowserUser user) => user.Page.Locator(ChatLine);

    private static async Task EnterSessionChatAsync(BrowserUser user)
    {
        await LiveSessionSupport.OpenFirstSessionAsync(user);
        await user.Page.Locator(SideMenuToggle).ClickAsync();
    }

    private static async Task SendMessageAsync(BrowserUser user, string message)
    {
        await user.Page.Locator(MessageInput).FillAsync(message);
        await user.Page.Locator(SendButton).ClickAsync();
    }

    private static Task ExpectSystemMessageAsync(ILocator chatLine, string text) =>
        Expect(chatLine.Locator(SystemMessage)).ToContainTextAsync(text, new() { Timeout = LiveSessionSupport.RealtimeTimeoutMs });

    /// <summary>Waits for the newest chat line to be a message of the given kind (own or from the other user).</summary>
    private static async Task ExpectMessageAsync(BrowserUser user, string kindSelector, string sender, string text)
    {
        var message = ChatLines(user).Last.Locator(kindSelector);
        var options = new LocatorAssertionsToContainTextOptions { Timeout = LiveSessionSupport.RealtimeTimeoutMs };
        await Expect(message.Locator(MessageSender)).ToContainTextAsync(sender, options);
        await Expect(message.Locator(MessageText)).ToContainTextAsync(text, options);
    }
}
