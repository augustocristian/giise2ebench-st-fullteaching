using Microsoft.Playwright;

namespace FullTeaching.E2E.Common;

/// <summary>
/// One simulated end user: an isolated Playwright <see cref="IBrowserContext"/> + <see cref="IPage"/>,
/// ported from common/BrowserUser.java and common/ChromeUser.java.
///
/// Unlike Selenium (one WebDriver process per user) and pyppeteer (one Chromium process per
/// user), Playwright's browser contexts are cheap, fully isolated (separate cookies/storage/
/// permissions) sessions within a *single* shared browser process - the documented Playwright
/// pattern for exactly this "simulate several independent logged-in users" scenario, which is
/// why (unlike the Cypress port) EChatTests/VideoSessionTests/LoggedVideoSessionTests are
/// fully implemented here rather than skipped: Playwright can drive several simultaneous
/// sessions where Cypress fundamentally cannot.
/// </summary>
public class BrowserUser
{
    private const string VideoPlayingProbeJs = """
        window.MY_FUNC = function(containerQuerySelector) {
            var elem = document.createElement('div');
            elem.id = 'video-playing-div';
            elem.innerText = 'VIDEO PLAYING';
            document.body.appendChild(elem);
            console.log('Video check function successfully added to DOM by Playwright');
        };
        """;

    public string ClientData { get; }
    public int TimeoutMs { get; }
    public string TestName { get; }
    public bool IsOnSession { get; set; }
    public string AppUrl { get; private set; } = string.Empty;
    public IBrowserContext Context { get; private set; } = null!;
    public IPage Page { get; private set; } = null!;

    private BrowserUser(string clientData, int timeoutSeconds, string testName)
    {
        ClientData = clientData;
        TimeoutMs = timeoutSeconds * 1000;
        TestName = testName;
    }

    /// <summary>
    /// Creates a BrowserUser, navigates it to appUrl and injects the video-playing probe.
    /// Mirrors BaseLoggedTest.setupBrowser(browser, testName, userIdentifier, secondsOfWait).
    /// </summary>
    public static async Task<BrowserUser> SetupBrowserAsync(
        IBrowser browser, string appUrl, string testName, string userIdentifier, int secondsOfWait)
    {
        var user = new BrowserUser(userIdentifier, secondsOfWait, testName)
        {
            AppUrl = appUrl,
        };

        user.Context = await browser.NewContextAsync(new BrowserNewContextOptions
        {
            IgnoreHTTPSErrors = true,
            Permissions = ["camera", "microphone"],
        });
        user.Context.SetDefaultTimeout(user.TimeoutMs);
        user.Page = await user.Context.NewPageAsync();

        await user.Page.GotoAsync(appUrl);
        await user.Page.EvaluateAsync(VideoPlayingProbeJs);
        return user;
    }

    public Task<object?> RunJavascriptAsync(string script, object? arg = null) =>
        Page.EvaluateAsync<object?>(script, arg);

    /// <summary>
    /// Awaits <paramref name="action"/>, mirrors BrowserUser.waitUntil(condition, errorMessage):
    /// re-throws Playwright's own timeout with the caller's more specific error message prefixed.
    /// </summary>
    public async Task WaitUntilAsync(Func<Task> action, string errorMessage)
    {
        try
        {
            await action();
        }
        catch (PlaywrightException ex)
        {
            throw new PlaywrightException($"\"{errorMessage}\" (checked with condition) > {ex.Message}", ex);
        }
    }

    public async Task<T> WaitUntilAsync<T>(Func<Task<T>> action, string errorMessage)
    {
        try
        {
            return await action();
        }
        catch (PlaywrightException ex)
        {
            throw new PlaywrightException($"\"{errorMessage}\" (checked with condition) > {ex.Message}", ex);
        }
    }

    public async Task DisposeAsync()
    {
        await Context.CloseAsync();
    }
}
