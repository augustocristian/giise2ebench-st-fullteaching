using System.Runtime.ExceptionServices;
using NUnit.Framework;

namespace FullTeaching.E2E.Common;

/// <summary>
/// Shared per-test lifecycle, ported from the @BeforeEach/@AfterEach of common/BaseLoggedTest.java.
/// <see cref="User"/> mirrors BaseLoggedTest's primary `user` field; <see cref="CreateSecondaryUserAsync"/>
/// generalizes the `student`/`studentBrowserUserList` fields into a factory so any test can spin
/// up as many extra simulated users as it needs, all auto-disposed in TearDown.
/// </summary>
public abstract class BaseTest
{
    private readonly List<BrowserUser> _secondaryUsers = [];
    private BrowserUser? _user;

    /// <summary>The primary (TEACHER) user of the test.</summary>
    protected BrowserUser User => _user
        ?? throw new InvalidOperationException("The primary user is not available: SetUpAsync has not completed.");

    /// <summary>Base URL of the application under test.</summary>
    protected static string AppUrl => TestConfig.AppUrl;

    /// <summary>RETORCH TJob name.</summary>
    protected static string TJobName => TestConfig.TJobName;

    /// <summary>
    /// Default Playwright action timeout, in seconds, of the primary user. Media/video fixtures
    /// can override it with <see cref="Constants.MediaWaitSeconds"/>.
    /// </summary>
    protected virtual int TimeoutSeconds => Constants.WaitSeconds;

    [SetUp]
    public async Task SetUpAsync()
    {
        _user = await BrowserUser.SetupBrowserAsync(
            PlaywrightGlobalSetup.Browser, AppUrl, QualifiedTestName(), "TEACHER", TimeoutSeconds);
    }

    [TearDown]
    public async Task TearDownAsync()
    {
        // Every user is closed even if a previous logout/dispose fails; failures are reported
        // together afterwards so a broken logout cannot leak the remaining browser contexts.
        var errors = new List<Exception>();
        var users = new List<BrowserUser>(_secondaryUsers.Count + 1);
        if (_user is not null)
        {
            users.Add(_user);
        }
        users.AddRange(_secondaryUsers);
        _user = null;
        _secondaryUsers.Clear();

        foreach (var user in users)
        {
            await CloseUserAsync(user, errors);
        }

        switch (errors.Count)
        {
            case 0:
                return;
            case 1:
                ExceptionDispatchInfo.Capture(errors[0]).Throw();
                return;
            default:
                throw new AggregateException("Several users could not be closed cleanly.", errors);
        }
    }

    /// <summary>Mirrors BaseLoggedTest.setupBrowser(browser, testName, userIdentifier, secondsOfWait).</summary>
    protected async Task<BrowserUser> CreateSecondaryUserAsync(string userIdentifier, int secondsOfWait = 5)
    {
        var user = await BrowserUser.SetupBrowserAsync(
            PlaywrightGlobalSetup.Browser, AppUrl, QualifiedTestName(), userIdentifier, secondsOfWait);
        _secondaryUsers.Add(user);
        return user;
    }

    private static string QualifiedTestName() => $"{TJobName}-{TestContext.CurrentContext.Test.Name}";

    private static async Task CloseUserAsync(BrowserUser user, List<Exception> errors)
    {
        try
        {
            // Capture the failing page before logging out navigates away from it.
            await user.CaptureFailureArtifactsAsync();
            if (user.IsOnSession)
            {
                await LoginHelper.LogoutAsync(user);
            }
        }
        catch (Exception ex)
        {
            errors.Add(ex);
        }

        try
        {
            await user.DisposeAsync();
        }
        catch (Exception ex)
        {
            errors.Add(ex);
        }
    }
}
