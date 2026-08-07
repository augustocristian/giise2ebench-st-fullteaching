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

    protected BrowserUser User { get; private set; } = null!;
    protected static string AppUrl => PlaywrightGlobalSetup.AppUrl;
    protected static string TJobName => PlaywrightGlobalSetup.TJobName;

    [SetUp]
    public async Task SetUpAsync()
    {
        var testName = $"{TJobName}-{TestContext.CurrentContext.Test.Name}";
        User = await BrowserUser.SetupBrowserAsync(
            PlaywrightGlobalSetup.Browser, AppUrl, testName, "TEACHER", Constants.WaitSeconds);
    }

    [TearDown]
    public async Task TearDownAsync()
    {
        if (User.IsOnSession)
        {
            await LoginHelper.LogoutAsync(User);
        }
        await User.DisposeAsync();

        foreach (var secondary in _secondaryUsers)
        {
            if (secondary.IsOnSession)
            {
                await LoginHelper.LogoutAsync(secondary);
            }
            await secondary.DisposeAsync();
        }
        _secondaryUsers.Clear();
    }

    /// <summary>Mirrors BaseLoggedTest.setupBrowser(browser, testName, userIdentifier, secondsOfWait).</summary>
    protected async Task<BrowserUser> CreateSecondaryUserAsync(string userIdentifier, int secondsOfWait = 5)
    {
        var testName = $"{TJobName}-{TestContext.CurrentContext.Test.Name}";
        var user = await BrowserUser.SetupBrowserAsync(
            PlaywrightGlobalSetup.Browser, AppUrl, testName, userIdentifier, secondsOfWait);
        _secondaryUsers.Add(user);
        return user;
    }
}
