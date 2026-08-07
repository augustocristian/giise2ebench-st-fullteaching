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

    public static async Task<IReadOnlyList<string>> GetPageLinksAsync(IPage page, string host)
    {
        var anchors = await page.Locator("a").AllAsync();
        var links = new List<string>();
        foreach (var a in anchors)
        {
            var href = await a.GetAttributeAsync("href");
            if (IsFollowable(href, host))
            {
                links.Add(href!);
            }
        }
        return links;
    }

    public static async Task<IReadOnlyList<string>> GetUnexploredPageLinksAsync(
        IPage page, string host, IDictionary<string, string> explored)
    {
        var links = new List<string>();
        foreach (var href in await GetPageLinksAsync(page, host))
        {
            if (!explored.ContainsKey(href))
            {
                links.Add(href);
            }
        }
        return links;
    }

    public static async Task<IDictionary<string, string>> ExploreLinksAsync(
        IPage page, string host, IReadOnlyList<string> pageLinks, IDictionary<string, string> explored, int depth)
    {
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
                await page.Locator($"a[href='{href}']").First.ClickAsync();
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
}
