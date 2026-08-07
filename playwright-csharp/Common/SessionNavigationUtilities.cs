using Microsoft.Playwright;
using FullTeaching.E2E.Common.Exceptions;

namespace FullTeaching.E2E.Common;

/// <summary>Session navigation helpers, ported from common/SessionNavigationUtilities.java.</summary>
public static class SessionNavigationUtilities
{
    public static async Task<IReadOnlyList<string>> GetFullSessionListAsync(BrowserUser user)
    {
        var tabContent = await CourseNavigationUtilities.GetTabContentAsync(user, Constants.SessionIcon);
        var rows = await tabContent.Locator(Constants.SessionListSessionRow).AllAsync();
        var titles = new List<string>(rows.Count);
        foreach (var row in rows)
        {
            titles.Add((await row.Locator(Constants.SessionListSessionName).InnerTextAsync()).Trim());
        }
        return titles;
    }

    /// <summary>Yields the session row locator with the given title; throws if not found.</summary>
    public static async Task<ILocator> GetSessionAsync(BrowserUser user, string sessionName)
    {
        var tabContent = await CourseNavigationUtilities.GetTabContentAsync(user, Constants.SessionIcon);
        var rows = await tabContent.Locator(Constants.SessionListSessionRow).AllAsync();
        foreach (var row in rows)
        {
            var title = (await row.Locator(Constants.SessionListSessionName).InnerTextAsync()).Trim();
            if (title == sessionName)
            {
                return row;
            }
        }
        throw new ElementNotFoundException("getSession-the session doesn't exist");
    }
}
