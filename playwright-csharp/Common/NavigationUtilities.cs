using Microsoft.Playwright;

namespace FullTeaching.E2E.Common;

public enum FindOption
{
    Class,
    Text,
    Value,
    Attribute,
}

/// <summary>Generic page navigation helpers, ported from common/NavigationUtilities.java.</summary>
public static class NavigationUtilities
{
    /// <summary>Mirrors NavigationUtilities.amINotHere(wd, url), comparing with trailing-slash tolerance.</summary>
    public static bool AmINotHere(string currentUrl, string url)
    {
        currentUrl = currentUrl.Trim();
        var compareUrl = url.Trim();

        if (currentUrl.EndsWith('/') && !compareUrl.EndsWith('/'))
        {
            compareUrl += "/";
        }
        else if (!currentUrl.EndsWith('/') && compareUrl.EndsWith('/'))
        {
            compareUrl = compareUrl[..^1];
        }

        return currentUrl != compareUrl;
    }

    public static async Task GetUrlAndWaitFooterAsync(IPage page, string url)
    {
        await page.GotoAsync(url);
        await page.Locator(Constants.Footer).WaitForAsync();
    }

    public static async Task ToCoursesHomeAsync(BrowserUser user)
    {
        var page = user.Page;
        var coursesUrl = Constants.CoursesUrl.Replace("__HOST__", user.AppUrl);
        if (AmINotHere(page.Url, coursesUrl))
        {
            await page.Locator(Constants.CoursesButton).ClickAsync();
            await page.Locator(Constants.CoursesDashboardTitle).WaitForAsync();
        }
    }

    /// <summary>Mirrors NavigationUtilities.getOption(options, find, type, attribute).</summary>
    public static async Task<ILocator?> GetOptionAsync(IReadOnlyList<ILocator> options, string find, FindOption type, string attribute)
    {
        foreach (var option in options)
        {
            var candidate = type switch
            {
                FindOption.Class => await option.GetAttributeAsync("class"),
                FindOption.Text => await option.InnerTextAsync(),
                FindOption.Value => await option.GetAttributeAsync("value"),
                _ => await option.GetAttributeAsync(attribute),
            };
            if (find == candidate)
            {
                return option;
            }
        }
        return null;
    }
}
