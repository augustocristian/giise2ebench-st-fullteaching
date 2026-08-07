using FullTeaching.E2E.Common.Exceptions;
using static Microsoft.Playwright.Assertions;

namespace FullTeaching.E2E.Common;

/// <summary>Login/logout assertions, ported from common/UserUtilities.java.</summary>
public static class UserUtilities
{
    public static async Task CheckLoginAsync(BrowserUser user, string email)
    {
        var page = user.Page;
        var settingsButton = page.Locator(Constants.SettingsButton);
        await settingsButton.WaitForAsync();
        await settingsButton.ClickAsync();

        var settingsEmail = (await page.Locator(Constants.SettingsUserEmail).InnerTextAsync()).Trim();
        if (settingsEmail != email.Trim())
        {
            throw new BadUserException();
        }
    }

    public static async Task CheckLogOutAsync(BrowserUser user)
    {
        await Expect(user.Page.Locator(Constants.LoginMenuXPath)).ToBeVisibleAsync();
    }
}
