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
/// their timeout (defaulted to Wait.notTooMuch's 20s via BrowserContext.SetDefaultTimeout).
/// </summary>
public static class LoginHelper
{
    private const int ALittleMs = 4000;

    public static Task<string> SlowLoginAsync(BrowserUser user, string email, string password) =>
        LoginAsync(user, email, password, slow: true);

    public static Task<string> QuickLoginAsync(BrowserUser user, string email, string password) =>
        LoginAsync(user, email, password, slow: false);

    private static async Task<string> LoginAsync(BrowserUser user, string email, string password, bool slow)
    {
        var page = user.Page;
        user.IsOnSession = true;

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

        return await GetUserNameAsync(user);
    }

    public static async Task LogoutAsync(BrowserUser user)
    {
        var page = user.Page;

        if (await page.Locator("#fixed-icon").CountAsync() > 0)
        {
            // Get out of video session page - ensure side menu is open so exit-icon is visible
            if (await page.Locator(Constants.SessionExitIcon).CountAsync() == 0)
            {
                await page.Locator("#fixed-icon").ClickAsync();
            }
            await page.Locator(Constants.SessionExitIcon).WaitForAsync();
            // Force-click bypasses any overlay that would intercept a native click
            await page.Locator(Constants.SessionExitIcon).ClickAsync(new() { Force = true });
        }

        try
        {
            // Up bar menu - scroll to top so the navbar is in viewport, then force-click to
            // bypass any overlay that would intercept a native click.
            await page.EvaluateAsync("window.scrollTo(0, 0)");
            await page.Locator(Constants.MainMenuArrow).WaitForAsync(new() { Timeout = 20000 });
            await page.Locator(Constants.MainMenuArrow).ClickAsync(new() { Force = true });

            await page.Locator(Constants.LogoutButton).WaitForAsync();
            await page.Locator(Constants.LogoutButton).ClickAsync();
        }
        catch (PlaywrightException)
        {
            // Shrunk menu
            await page.Locator("a.button-collapse").WaitForAsync();
            await page.Locator("a.button-collapse").ClickAsync();

            var mobileLogout = page.Locator("xpath=//ul[@id='nav-mobile']//a[text() = 'Logout']");
            await mobileLogout.WaitForAsync();
            await mobileLogout.ClickAsync();
        }

        user.IsOnSession = false;
    }

    public static async Task OpenDialogAsync(BrowserUser user, string selector)
    {
        var page = user.Page;
        await user.WaitUntilAsync(() => page.Locator(selector).WaitForAsync(), "Button for opening the dialog not clickable");
        await page.Locator(selector).ClickAsync();
        await user.WaitUntilAsync(() => page.Locator(Constants.ModalOverlayOpening).WaitForAsync(), "Dialog not opened");
    }

    public static async Task OpenDialogAsync(BrowserUser user, ILocator element)
    {
        await user.WaitUntilAsync(() => element.WaitForAsync(), "Button for opening the dialog not clickable");
        await element.ClickAsync();
        await user.WaitUntilAsync(
            () => user.Page.Locator(Constants.ModalOverlayOpening).WaitForAsync(), "Dialog not opened");
    }

    public static async Task WaitForDialogClosedAsync(BrowserUser user, string dialogId, string errorMessage)
    {
        var page = user.Page;
        await user.WaitUntilAsync(
            () => page.Locator(Constants.ModalClosedXPath(dialogId)).WaitForAsync(),
            $"Dialog not closed. Reason: {errorMessage}");
        await user.WaitUntilAsync(
            () => page.Locator(Constants.ModalOpen).WaitForAsync(new() { State = WaitForSelectorState.Hidden }),
            $"Dialog not closed. Reason: {errorMessage}");
        await user.WaitUntilAsync(
            () => Expect(page.Locator(Constants.ModalOverlay)).ToHaveCountAsync(0),
            $"Dialog not closed. Reason: {errorMessage}");
    }

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
            throw new NotLoggedException(ex.Message);
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
