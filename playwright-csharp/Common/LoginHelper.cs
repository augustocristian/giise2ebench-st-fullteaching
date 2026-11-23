using Microsoft.Playwright;
using FullTeaching.E2E.Common.Exceptions;
using static Microsoft.Playwright.Assertions;

namespace FullTeaching.E2E.Common;

/// <summary>
/// Login/logout/dialog helpers, ported from the protected methods of common/BaseLoggedTest.java.
/// Java models these as instance methods inherited by every test class; here they're static
/// helpers operating on a <see cref="BrowserUser"/>, called from BaseTest and the test classes
/// themselves. Most of Wait.java's explicit ExpectedConditions collapse away: Playwright's
/// locator actions and <c>Expect()</c> assertions already auto-retry against the DOM until
/// their timeout (<see cref="BrowserUser.TimeoutMs"/> for actions, <see cref="TestConfig.ShortTimeoutMs"/>
/// for assertions).
/// </summary>
public static class LoginHelper
{
    private const int ALittleMs = 4000;

    /// <summary>Logs in, waiting for the login button to be enabled first. Returns the user's display name.</summary>
    public static Task<string> SlowLoginAsync(BrowserUser user, string email, string password) =>
        LoginAsync(user, email, password, slow: true);

    /// <summary>Logs in without waiting for the login button to be enabled. Returns the user's display name.</summary>
    public static Task<string> QuickLoginAsync(BrowserUser user, string email, string password) =>
        LoginAsync(user, email, password, slow: false);

    private static async Task<string> LoginAsync(BrowserUser user, string email, string password, bool slow)
    {
        var page = user.Page;

        await user.WaitUntilAsync(
            () => page.Locator(Constants.DownloadButton).WaitForAsync(new() { Timeout = ALittleMs }),
            "The button searched by CSS #download-button is not clickable");
        await OpenDialogAsync(user, Constants.DownloadButton);

        var emailField = page.Locator(Constants.LoginUserField);
        var passwordField = page.Locator(Constants.LoginPasswordField);
        await emailField.WaitForAsync();
        await passwordField.WaitForAsync();

        await emailField.FillAsync(email);
        await passwordField.FillAsync(password);

        if (slow)
        {
            // Wait for the login button to be enabled (Angular validates the form) rather than sleeping
            await user.WaitUntilAsync(
                () => Expect(page.Locator(Constants.LoginButton)).ToBeEnabledAsync(),
                "Login button not enabled after filling credentials");
        }

        // Ensure fields contain what has been entered
        await Expect(emailField).ToHaveValueAsync(email);
        await Expect(passwordField).ToHaveValueAsync(password);
        await page.Locator(Constants.LoginButton).ClickAsync();

        await user.WaitUntilAsync(() => page.Locator(Constants.CourseList).WaitForAsync(), "The Course list is not present");
        await user.WaitUntilAsync(() => page.Locator(Constants.CourseListId).WaitForAsync(), "Course list is not clickable");

        // Only now is there a session to log out of; a failed login must not cost a logout timeout in TearDown.
        user.IsOnSession = true;
        return await GetUserNameAsync(user);
    }

    /// <summary>
    /// Logs the user out, leaving a video-session page first if needed and falling back to the
    /// collapsed (mobile) navbar when the desktop menu is not available.
    /// </summary>
    public static async Task LogoutAsync(BrowserUser user)
    {
        var page = user.Page;

        if (await page.Locator(Constants.SessionFixedIcon).CountAsync() > 0)
        {
            // Get out of video session page - ensure side menu is open so exit-icon is visible
            var exitIcon = page.Locator(Constants.SessionExitIcon);
            if (await exitIcon.CountAsync() == 0)
            {
                await page.Locator(Constants.SessionFixedIcon).ClickAsync();
            }
            await exitIcon.WaitForAsync();
            // Force-click bypasses any overlay that would intercept a native click
            await exitIcon.ClickAsync(new() { Force = true });
        }

        try
        {
            // Up bar menu - scroll to top so the navbar is in viewport, then force-click to
            // bypass any overlay that would intercept a native click.
            await page.EvaluateAsync("window.scrollTo(0, 0)");
            var menuArrow = page.Locator(Constants.MainMenuArrow);
            await menuArrow.WaitForAsync(new() { Timeout = TestConfig.ShortTimeoutMs });
            await menuArrow.ClickAsync(new() { Force = true });

            var logoutButton = page.Locator(Constants.LogoutButton);
            await logoutButton.WaitForAsync();
            await logoutButton.ClickAsync();
        }
        catch (PlaywrightException)
        {
            // Shrunk menu
            var menuButton = page.Locator(Constants.MobileMenuButton);
            await menuButton.WaitForAsync();
            await menuButton.ClickAsync();

            var mobileLogout = page.Locator(Constants.MobileLogoutLink);
            await mobileLogout.WaitForAsync();
            await mobileLogout.ClickAsync();
        }

        user.IsOnSession = false;
    }

    /// <summary>Clicks <paramref name="selector"/> and waits for the modal overlay to open.</summary>
    public static Task OpenDialogAsync(BrowserUser user, string selector)
    {
        ArgumentNullException.ThrowIfNull(user);
        return OpenDialogAsync(user, user.Page.Locator(selector));
    }

    /// <summary>Clicks <paramref name="element"/> and waits for the modal overlay to open.</summary>
    public static async Task OpenDialogAsync(BrowserUser user, ILocator element)
    {
        ArgumentNullException.ThrowIfNull(user);
        ArgumentNullException.ThrowIfNull(element);
        await user.WaitUntilAsync(() => element.WaitForAsync(), "Button for opening the dialog not clickable");
        await element.ClickAsync();
        await user.WaitUntilAsync(
            () => user.Page.Locator(Constants.ModalOverlayOpening).WaitForAsync(), "Dialog not opened");
    }

    /// <summary>Waits until the dialog with id <paramref name="dialogId"/> and its overlay are fully closed.</summary>
    public static async Task WaitForDialogClosedAsync(BrowserUser user, string dialogId, string errorMessage)
    {
        var page = user.Page;
        var reason = $"Dialog not closed. Reason: {errorMessage}";
        await user.WaitUntilAsync(
            () => page.Locator(Constants.ModalClosedXPath(dialogId)).WaitForAsync(new() { State = WaitForSelectorState.Attached }),
            reason);
        await user.WaitUntilAsync(
            () => page.Locator(Constants.ModalOpen).WaitForAsync(new() { State = WaitForSelectorState.Hidden }), reason);
        await user.WaitUntilAsync(() => Expect(page.Locator(Constants.ModalOverlay)).ToHaveCountAsync(0), reason);
    }

    /// <summary>
    /// Reads the display name shown in the settings page. Navigates there if needed and, when
    /// <paramref name="goBack"/> is set, returns to the previous page afterwards.
    /// </summary>
    /// <exception cref="NotLoggedException">The settings button is not available, i.e. nobody is logged in.</exception>
    public static async Task<string> GetUserNameAsync(BrowserUser user, bool goBack = true)
    {
        var page = user.Page;
        try
        {
            var settingsButton = page.Locator(Constants.SettingsButton);
            await settingsButton.WaitForAsync();

            var notOnSettings = !page.Url.TrimEnd('/').EndsWith("/settings", StringComparison.Ordinal);
            if (notOnSettings)
            {
                await settingsButton.ClickAsync();
            }
            else
            {
                goBack = false;
            }
        }
        catch (PlaywrightException ex)
        {
            throw new NotLoggedException($"[{user.ClientData}] the settings button is not available: {ex.Message}", ex);
        }

        var namePlaceholder = page.Locator(Constants.UsernameXPath);
        await namePlaceholder.WaitForAsync();
        var userName = (await namePlaceholder.InnerTextAsync()).Trim();

        if (goBack)
        {
            await page.GoBackAsync();
        }

        return userName;
    }
}
