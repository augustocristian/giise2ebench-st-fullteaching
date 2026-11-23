using FullTeaching.E2E.Common.Exceptions;
using static Microsoft.Playwright.Assertions;

namespace FullTeaching.E2E.Common;

/// <summary>Login/logout assertions, ported from common/UserUtilities.java.</summary>
public static class UserUtilities
{
    /// <summary>Opens the settings page and checks the logged-in user's e-mail equals <paramref name="email"/>.</summary>
    /// <exception cref="BadUserException">A different user is logged in.</exception>
    public static async Task CheckLoginAsync(BrowserUser user, string email)
    {
        ArgumentNullException.ThrowIfNull(user);
        ArgumentNullException.ThrowIfNull(email);
        var page = user.Page;
        var settingsButton = page.Locator(Constants.SettingsButton);
        await settingsButton.WaitForAsync();
        await settingsButton.ClickAsync();

        var settingsEmail = (await page.Locator(Constants.SettingsUserEmail).InnerTextAsync()).Trim();
        if (settingsEmail != email.Trim())
        {
            throw new BadUserException($"Expected user '{email.Trim()}' to be logged in but the settings page shows '{settingsEmail}'.");
        }
    }

    /// <summary>Asserts the logged-out navbar (login link) is visible.</summary>
    public static async Task CheckLogOutAsync(BrowserUser user)
    {
        ArgumentNullException.ThrowIfNull(user);
        await Expect(user.Page.Locator(Constants.LoginMenuXPath)).ToBeVisibleAsync();
    }
}
