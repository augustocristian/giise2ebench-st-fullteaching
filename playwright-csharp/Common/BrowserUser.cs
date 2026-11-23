using System.Text.RegularExpressions;
using Microsoft.Playwright;
using NUnit.Framework;
using NUnit.Framework.Interfaces;

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
public sealed partial class BrowserUser : IAsyncDisposable
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

    private const int ScreenshotTimeoutMs = 10_000;
    private const int MaxArtifactNameLength = 120;

    private bool _disposed;
    private bool _failureArtifactsCaptured;

    private BrowserUser(
        IBrowserContext context, IPage page, string appUrl, string clientData, int timeoutSeconds, string testName)
    {
        Context = context;
        Page = page;
        AppUrl = appUrl;
        ClientData = clientData;
        TimeoutMs = timeoutSeconds * 1000;
        TestName = testName;
    }

    /// <summary>Identifier of the simulated user (e.g. TEACHER, STUDENT), as passed to <see cref="SetupBrowserAsync"/>.</summary>
    public string ClientData { get; }

    /// <summary>Default Playwright action/navigation timeout of this user, in milliseconds.</summary>
    public int TimeoutMs { get; }

    /// <summary>Name of the test this user belongs to.</summary>
    public string TestName { get; }

    /// <summary>Whether the user is (or may be) logged in and so needs a logout during teardown.</summary>
    public bool IsOnSession { get; set; }

    /// <summary>Base URL of the application under test.</summary>
    public string AppUrl { get; }

    /// <summary>The isolated browser context of this user.</summary>
    public IBrowserContext Context { get; }

    /// <summary>The page this user drives.</summary>
    public IPage Page { get; }

    /// <summary>
    /// Creates a BrowserUser, navigates it to appUrl and injects the video-playing probe.
    /// Mirrors BaseLoggedTest.setupBrowser(browser, testName, userIdentifier, secondsOfWait).
    /// </summary>
    public static async Task<BrowserUser> SetupBrowserAsync(
        IBrowser browser, string appUrl, string testName, string userIdentifier, int secondsOfWait)
    {
        ArgumentNullException.ThrowIfNull(browser);

        var context = await browser.NewContextAsync(new BrowserNewContextOptions
        {
            IgnoreHTTPSErrors = true,
            Permissions = ["camera", "microphone"],
        });
        try
        {
            context.SetDefaultTimeout(secondsOfWait * 1000);
            if (TestConfig.TraceEnabled)
            {
                await context.Tracing.StartAsync(new TracingStartOptions { Screenshots = true, Snapshots = true });
            }

            var page = await context.NewPageAsync();
            var user = new BrowserUser(context, page, appUrl, userIdentifier, secondsOfWait, testName);

            await page.GotoAsync(appUrl);
            await page.EvaluateAsync(VideoPlayingProbeJs);
            return user;
        }
        catch
        {
            // Do not leak the context (and its page) when the app is unreachable.
            await context.CloseAsync();
            throw;
        }
    }

    /// <summary>Evaluates a JavaScript expression in the page of this user.</summary>
    public Task<object?> RunJavascriptAsync(string script, object? arg = null) =>
        Page.EvaluateAsync<object?>(script, arg);

    /// <summary>
    /// Awaits <paramref name="action"/>, mirrors BrowserUser.waitUntil(condition, errorMessage):
    /// re-throws Playwright's own timeout with the caller's more specific error message prefixed.
    /// </summary>
    public Task WaitUntilAsync(Func<Task> action, string errorMessage)
    {
        ArgumentNullException.ThrowIfNull(action);
        return WaitUntilAsync<object?>(
            async () =>
            {
                await action();
                return null;
            },
            errorMessage);
    }

    /// <inheritdoc cref="WaitUntilAsync(Func{Task}, string)"/>
    public async Task<T> WaitUntilAsync<T>(Func<Task<T>> action, string errorMessage)
    {
        ArgumentNullException.ThrowIfNull(action);
        try
        {
            return await action();
        }
        catch (PlaywrightException ex)
        {
            throw new PlaywrightException(
                $"[{ClientData}] \"{errorMessage}\" (checked with condition) > {ex.Message}", ex);
        }
    }

    /// <summary>
    /// Saves a full-page screenshot of this user when the current NUnit test has failed and
    /// <c>PW_SCREENSHOT_ON_FAILURE</c> (or <c>PW_TRACE</c>) is enabled. Safe to call repeatedly;
    /// never throws, so it cannot mask the original failure.
    /// </summary>
    public async Task CaptureFailureArtifactsAsync()
    {
        if (_failureArtifactsCaptured || !TestConfig.ScreenshotOnFailure || !TestFailed())
        {
            return;
        }
        _failureArtifactsCaptured = true;
        try
        {
            Directory.CreateDirectory(TestConfig.ArtifactsDir);
            var path = Path.Combine(TestConfig.ArtifactsDir, ArtifactBaseName() + ".png");
            await Page.ScreenshotAsync(new PageScreenshotOptions
            {
                Path = path,
                FullPage = true,
                Timeout = ScreenshotTimeoutMs,
            });
            TestContext.AddTestAttachment(path, $"Screenshot of {ClientData}");
        }
        catch (Exception ex) when (ex is PlaywrightException or IOException or UnauthorizedAccessException)
        {
            TestContext.Progress.WriteLine($"[{ClientData}] could not save failure screenshot: {ex.Message}");
        }
    }

    /// <summary>
    /// Stops tracing (keeping the zip only for failed tests) and closes the browser context.
    /// Idempotent.
    /// </summary>
    public async Task DisposeAsync()
    {
        if (_disposed)
        {
            return;
        }
        _disposed = true;

        try
        {
            await CaptureFailureArtifactsAsync();
            if (TestConfig.TraceEnabled)
            {
                await StopTracingAsync();
            }
        }
        finally
        {
            await Context.CloseAsync();
        }
    }

    /// <inheritdoc/>
    ValueTask IAsyncDisposable.DisposeAsync() => new(DisposeAsync());

    private async Task StopTracingAsync()
    {
        try
        {
            if (TestFailed())
            {
                Directory.CreateDirectory(TestConfig.ArtifactsDir);
                var path = Path.Combine(TestConfig.ArtifactsDir, ArtifactBaseName() + ".trace.zip");
                await Context.Tracing.StopAsync(new TracingStopOptions { Path = path });
                TestContext.AddTestAttachment(path, $"Playwright trace of {ClientData}");
            }
            else
            {
                await Context.Tracing.StopAsync();
            }
        }
        catch (Exception ex) when (ex is PlaywrightException or IOException or UnauthorizedAccessException)
        {
            TestContext.Progress.WriteLine($"[{ClientData}] could not save trace: {ex.Message}");
        }
    }

    private static bool TestFailed() =>
        TestContext.CurrentContext.Result.Outcome.Status == TestStatus.Failed;

    private string ArtifactBaseName()
    {
        var name = UnsafeFileNameChars().Replace($"{TestName}-{ClientData}", "_");
        return name.Length > MaxArtifactNameLength ? name[..MaxArtifactNameLength] : name;
    }

    [GeneratedRegex(@"[^A-Za-z0-9._-]+")]
    private static partial Regex UnsafeFileNameChars();
}
