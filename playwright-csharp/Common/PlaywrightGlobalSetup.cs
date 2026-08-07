using Microsoft.Playwright;
using NUnit.Framework;

namespace FullTeaching.E2E.Common;

/// <summary>
/// Once-per-run browser launch, ported from BaseLoggedTest.java's static SeleManager field +
/// its @BeforeAll setupAll(). A single IBrowser process is shared across every test class in
/// the run (launching a browser is expensive); each test then gets its own isolated
/// IBrowserContext (cheap) via BrowserUser.SetupBrowserAsync - see BrowserUser's doc comment.
/// </summary>
[SetUpFixture]
public class PlaywrightGlobalSetup
{
    public static IPlaywright Playwright { get; private set; } = null!;
    public static IBrowser Browser { get; private set; } = null!;
    public static string AppUrl { get; private set; } = Constants.Localhost;
    public static string TJobName { get; private set; } = "TJobDef";

    [OneTimeSetUp]
    public async Task GlobalSetupAsync()
    {
        // Mirrors BaseLoggedTest.setupAll()'s SUT_URL/tjob_name env var resolution.
        var envUrl = Environment.GetEnvironmentVariable("SUT_URL");
        var envTjobName = Environment.GetEnvironmentVariable("tjob_name");
        if (!string.IsNullOrEmpty(envUrl))
        {
            AppUrl = envUrl;
            TJobName = envTjobName ?? "TJobDef";
        }
        else
        {
            AppUrl = Environment.GetEnvironmentVariable("app.url") ?? Constants.Localhost;
        }

        TestContext.Progress.WriteLine($"Using URL {AppUrl} TJOB: {TJobName}");

        Playwright = await Microsoft.Playwright.Playwright.CreateAsync();
        Browser = await Playwright.Chromium.LaunchAsync(new BrowserTypeLaunchOptions
        {
            Headless = Environment.GetEnvironmentVariable("HEADED") != "true",
            Args = ["--use-fake-ui-for-media-stream", "--use-fake-device-for-media-stream"],
        });
    }

    [OneTimeTearDown]
    public async Task GlobalTearDownAsync()
    {
        await Browser.CloseAsync();
        Playwright.Dispose();
    }
}
