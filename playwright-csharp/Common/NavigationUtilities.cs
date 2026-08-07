using Microsoft.Playwright;

namespace FullTeaching.E2E.Common;

/// <summary>Which property of an element <see cref="NavigationUtilities.GetOptionAsync"/> compares against.</summary>
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
        ArgumentNullException.ThrowIfNull(currentUrl);
        ArgumentNullException.ThrowIfNull(url);
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

    /// <summary>Navigates to <paramref name="url"/> and waits for the page footer to be visible.</summary>
    public static async Task GetUrlAndWaitFooterAsync(IPage page, string url)
    {
        ArgumentNullException.ThrowIfNull(page);
        await page.GotoAsync(url);
        await page.Locator(Constants.Footer).WaitForAsync();
    }

    /// <summary>Goes to the courses dashboard unless the user is already there.</summary>
    public static async Task ToCoursesHomeAsync(BrowserUser user)
    {
        ArgumentNullException.ThrowIfNull(user);
        var page = user.Page;
        var coursesUrl = Constants.CoursesUrl.Replace("__HOST__", user.AppUrl, StringComparison.Ordinal);
        if (AmINotHere(page.Url, coursesUrl))
        {
            await page.Locator(Constants.CoursesButton).ClickAsync();
            await page.Locator(Constants.CoursesDashboardTitle).WaitForAsync();
        }
    }

    /// <summary>
    /// Mirrors NavigationUtilities.getOption(options, find, type, attribute): returns the first
    /// option whose class/text/value/<paramref name="attribute"/> equals <paramref name="find"/>,
    /// or <see langword="null"/>.
    /// </summary>
    public static async Task<ILocator?> GetOptionAsync(IReadOnlyList<ILocator> options, string find, FindOption type, string attribute)
    {
        ArgumentNullException.ThrowIfNull(options);
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
