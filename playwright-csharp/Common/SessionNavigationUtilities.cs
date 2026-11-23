using Microsoft.Playwright;
using FullTeaching.E2E.Common.Exceptions;

namespace FullTeaching.E2E.Common;

/// <summary>Session navigation helpers, ported from common/SessionNavigationUtilities.java.</summary>
public static class SessionNavigationUtilities
{
    private static async Task<ILocator> SessionRowsAsync(BrowserUser user)
    {
        var tabContent = await CourseNavigationUtilities.GetTabContentAsync(user, Constants.SessionIcon);
        return tabContent.Locator(Constants.SessionListSessionRow);
    }

    /// <summary>Returns the titles of every session of the open course, in order.</summary>
    public static async Task<IReadOnlyList<string>> GetFullSessionListAsync(BrowserUser user)
    {
        ArgumentNullException.ThrowIfNull(user);
        var rows = await SessionRowsAsync(user);
        return await rows.ChildTextsAsync(Constants.SessionListSessionName);
    }

    /// <summary>Yields the session row locator with the given title; throws if not found.</summary>
    /// <exception cref="ElementNotFoundException">No session has that title.</exception>
    public static async Task<ILocator> GetSessionAsync(BrowserUser user, string sessionName)
    {
        ArgumentNullException.ThrowIfNull(user);
        var rows = await SessionRowsAsync(user);
        var session = await rows.FindRowByChildTextAsync(Constants.SessionListSessionName, sessionName);
        return session ?? throw new ElementNotFoundException(
            $"[{user.ClientData}] GetSession - the session \"{sessionName}\" doesn't exist; " +
            $"listed sessions: [{string.Join(", ", await rows.ChildTextsAsync(Constants.SessionListSessionName))}]");
    }
}
