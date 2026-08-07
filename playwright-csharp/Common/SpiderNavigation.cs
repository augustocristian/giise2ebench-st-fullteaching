using Microsoft.Playwright;

namespace FullTeaching.E2E.Common;

/// <summary>
/// Link crawler used by the spider tests, ported from common/SpiderNavigation.java.
///
/// Note: traditional spider navigation retrieving all links and then confirming them doesn't
/// work properly for this kind of SPA. This is a specialized spider for FullTeaching.
///
/// `addNonExistentLink`/`discardExplored` from the Java class are not ported: neither is
/// called from any test, in Java or here.
///
/// Unlike the Cypress port (whose command-queue model makes try/catch awkward), C# has normal
/// exception handling, so - like the Python port - this collects {href: "OK"|"KO"} exactly
/// like SpiderNavigation.java rather than letting a broken link fail the crawl immediately.
/// </summary>
public static class SpiderNavigation
{
    private static bool IsFollowable(string? href, string host) =>
        !string.IsNullOrWhiteSpace(href) && !href.Contains('#') && href.Contains(host, StringComparison.Ordinal);

    /// <summary>Returns the href of every followable anchor of the page (same host, no fragment).</summary>
    public static async Task<IReadOnlyList<string>> GetPageLinksAsync(IPage page, string host)
    {
        ArgumentNullException.ThrowIfNull(page);
        // One round trip for all anchors instead of one auto-waiting GetAttribute per anchor.
        var hrefs = await page.Locator("a").EvaluateAllAsync<string?[]>("anchors => anchors.map(a => a.getAttribute('href'))");
        return hrefs.Where(href => IsFollowable(href, host)).Select(href => href!).ToList();
    }

    /// <summary>Returns the followable links of the page that are not yet in <paramref name="explored"/>.</summary>
    public static async Task<IReadOnlyList<string>> GetUnexploredPageLinksAsync(
        IPage page, string host, IDictionary<string, string> explored)
    {
        ArgumentNullException.ThrowIfNull(explored);
        var links = await GetPageLinksAsync(page, host);
        return links.Where(href => !explored.ContainsKey(href)).ToList();
    }

    /// <summary>
    /// Depth-first exploration: clicks every link in <paramref name="pageLinks"/>, records "OK"
    /// when the target renders the footer and "KO" otherwise, then recurses into the new links.
    /// </summary>
    public static async Task<IDictionary<string, string>> ExploreLinksAsync(
        IPage page, string host, IReadOnlyList<string> pageLinks, IDictionary<string, string> explored, int depth)
    {
        ArgumentNullException.ThrowIfNull(page);
        ArgumentNullException.ThrowIfNull(pageLinks);
        ArgumentNullException.ThrowIfNull(explored);
        if (depth <= 0)
        {
            return explored;
        }

        var remaining = new List<string>(pageLinks);
        while (remaining.Count > 0)
        {
            var href = remaining[0];
            var currentUrl = page.Url;
            var explore = true;
            try
            {
                await page.Locator(AnchorSelector(href)).First.ClickAsync();
                await page.Locator(Constants.Footer).WaitForAsync();
                explored[href] = "OK";
            }
            catch (PlaywrightException)
            {
                explored[href] = "KO";
                explore = false;
            }

            if (explore)
            {
                var newLinks = await GetUnexploredPageLinksAsync(page, host, explored);
                explored = await ExploreLinksAsync(page, host, newLinks, explored, depth - 1);
            }

            await NavigationUtilities.GetUrlAndWaitFooterAsync(page, currentUrl);
            remaining = (await GetUnexploredPageLinksAsync(page, host, explored)).ToList();
        }

        return explored;
    }

    /// <summary>CSS selector of the anchor with exactly the given href, escaping quotes and backslashes.</summary>
    private static string AnchorSelector(string href) =>
        $"a[href=\"{href.Replace("\\", "\\\\", StringComparison.Ordinal).Replace("\"", "\\\"", StringComparison.Ordinal)}\"]";
}
