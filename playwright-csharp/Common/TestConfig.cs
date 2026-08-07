using NUnit.Framework;

namespace FullTeaching.E2E.Common;

/// <summary>
/// Single place where the run configuration is read from environment variables.
/// Everything is resolved once, on first access, so every helper sees the same values.
/// </summary>
/// <remarks>
/// <list type="table">
/// <item><term>SUT_URL</term><description>Base URL of the FullTeaching app (default <see cref="Constants.Localhost"/>).</description></item>
/// <item><term>tjob_name</term><description>RETORCH TJob name; only honoured together with SUT_URL, like <c>BaseLoggedTest.setupAll()</c>.</description></item>
/// <item><term>app.url</term><description>Fallback app URL when SUT_URL is not set (parity with the Java suite).</description></item>
/// <item><term>HEADED</term><description><c>true</c>/<c>1</c> launches Chromium with a visible window.</description></item>
/// <item><term>EXPECT_TIMEOUT_MS</term><description>Timeout of web-first assertions, list waits and <see cref="PollHelper"/> (default 20000, Java's <c>Wait.notTooMuch</c>).</description></item>
/// <item><term>PW_TRACE</term><description><c>true</c>/<c>1</c> records a Playwright trace per user; the zip is kept only for failed tests.</description></item>
/// <item><term>PW_SCREENSHOT_ON_FAILURE</term><description><c>true</c>/<c>1</c> saves a full-page PNG of every user when a test fails (implied by PW_TRACE).</description></item>
/// <item><term>PW_ARTIFACTS_DIR</term><description>Where traces/screenshots are written (default <c>playwright-artifacts</c> next to the test assembly).</description></item>
/// </list>
/// </remarks>
public static class TestConfig
{
    /// <summary>Default timeout, in milliseconds, for assertions and bounded waits (Java's <c>Wait.notTooMuch</c>).</summary>
    public const int DefaultShortTimeoutMs = 20_000;

    private const string DefaultTJobName = "TJobDef";

    static TestConfig()
    {
        var envUrl = Environment.GetEnvironmentVariable("SUT_URL");
        if (!string.IsNullOrEmpty(envUrl))
        {
            AppUrl = envUrl;
            TJobName = Environment.GetEnvironmentVariable("tjob_name") ?? DefaultTJobName;
        }
        else
        {
            AppUrl = Environment.GetEnvironmentVariable("app.url") ?? Constants.Localhost;
            TJobName = DefaultTJobName;
        }

        Headed = IsEnabled("HEADED");
        TraceEnabled = IsEnabled("PW_TRACE");
        ScreenshotOnFailure = TraceEnabled || IsEnabled("PW_SCREENSHOT_ON_FAILURE");
        ShortTimeoutMs = int.TryParse(Environment.GetEnvironmentVariable("EXPECT_TIMEOUT_MS"), out var ms) && ms > 0
            ? ms
            : DefaultShortTimeoutMs;
    }

    /// <summary>Base URL of the application under test.</summary>
    public static string AppUrl { get; }

    /// <summary>RETORCH TJob name, used to namespace test and user identifiers.</summary>
    public static string TJobName { get; }

    /// <summary>Whether Chromium should be launched with a visible window.</summary>
    public static bool Headed { get; }

    /// <summary>Whether a Playwright trace is recorded for every simulated user.</summary>
    public static bool TraceEnabled { get; }

    /// <summary>Whether a screenshot is saved when a test fails.</summary>
    public static bool ScreenshotOnFailure { get; }

    /// <summary>Timeout, in milliseconds, for web-first assertions, list waits and polling.</summary>
    public static int ShortTimeoutMs { get; }

    /// <summary>Directory receiving failure traces and screenshots.</summary>
    public static string ArtifactsDir =>
        Environment.GetEnvironmentVariable("PW_ARTIFACTS_DIR") is { Length: > 0 } dir
            ? dir
            : Path.Combine(TestContext.CurrentContext.WorkDirectory, "playwright-artifacts");

    private static bool IsEnabled(string name)
    {
        var value = Environment.GetEnvironmentVariable(name);
        return string.Equals(value, "true", StringComparison.OrdinalIgnoreCase) || value == "1";
    }
}
