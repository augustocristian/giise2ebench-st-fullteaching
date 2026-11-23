using FullTeaching.E2E.Common;
using Microsoft.Playwright;
using NUnit.Framework;

// NOTE: deliberately declared in the parent namespace (FullTeaching.E2E), not in
// FullTeaching.E2E.Common. NUnit applies a [SetUpFixture] only to the tests of its own
// namespace and nested ones, and the test classes live in FullTeaching.E2E.Tests - a fixture in
// ...Common would silently never run for them.
namespace FullTeaching.E2E;

/// <summary>
/// Once-per-run browser launch, ported from BaseLoggedTest.java's static SeleManager field +
/// its @BeforeAll setupAll(). A single IBrowser process is shared across every test class in
/// the run (launching a browser is expensive); each test then gets its own isolated
/// IBrowserContext (cheap) via BrowserUser.SetupBrowserAsync - see BrowserUser's doc comment.
/// Configuration comes from <see cref="TestConfig"/>.
/// </summary>
[SetUpFixture]
public class PlaywrightGlobalSetup
{
    private static IPlaywright? _playwright;
    private static IBrowser? _browser;

    /// <summary>The Playwright driver shared by the whole run.</summary>
    public static IPlaywright Playwright => _playwright
        ?? throw new InvalidOperationException("PlaywrightGlobalSetup has not run: Playwright is not initialised.");

    /// <summary>The Chromium instance shared by the whole run.</summary>
    public static IBrowser Browser => _browser
        ?? throw new InvalidOperationException("PlaywrightGlobalSetup has not run: the browser is not launched.");

    /// <summary>Base URL of the application under test.</summary>
    public static string AppUrl => TestConfig.AppUrl;

    /// <summary>RETORCH TJob name.</summary>
    public static string TJobName => TestConfig.TJobName;

    [OneTimeSetUp]
    public async Task GlobalSetupAsync()
    {
        TestContext.Progress.WriteLine($"Using URL {AppUrl} TJOB: {TJobName}");

        // Web-first assertions default to 5s, independently of the context's action timeout.
        Assertions.SetDefaultExpectTimeout(TestConfig.ShortTimeoutMs);

        _playwright = await Microsoft.Playwright.Playwright.CreateAsync();
        try
        {
            _browser = await _playwright.Chromium.LaunchAsync(new BrowserTypeLaunchOptions
            {
                Headless = !TestConfig.Headed,
                Args = ["--use-fake-ui-for-media-stream", "--use-fake-device-for-media-stream"],
            });
        }
        catch
        {
            _playwright.Dispose();
            _playwright = null;
            throw;
        }
    }

    [OneTimeTearDown]
    public async Task GlobalTearDownAsync()
    {
        try
        {
            if (_browser is not null)
            {
                await _browser.CloseAsync();
            }
        }
        finally
        {
            _browser = null;
            _playwright?.Dispose();
            _playwright = null;
        }
    }
}
