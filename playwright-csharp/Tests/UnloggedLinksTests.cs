using FullTeaching.E2E.Common;
using FullTeaching.E2E.Utils;
using NUnit.Framework;

namespace FullTeaching.E2E.Tests;

/// <summary>Ported from functional/test/UnLoggedLinksTests.java.</summary>
[TestFixture]
[Category("Unlogged")]
[Category("Links")]
public class UnloggedLinksTests : BaseTest
{
    // Status SpiderNavigation records for a link that could not be followed.
    private const string BrokenLinkStatus = "KO";

    /// <summary>
    /// Crawls every same-origin link from the home page (no login) and asserts none are broken.
    /// mail/password/role are unused below, matching the Java source: it parametrizes over
    /// teachers but never logs in, just re-runs the same crawl once per teacher.
    /// Resources: loginservice(READONLY,10) openvidumock(NOACCESS,10) course(READWRITE,15)
    /// executor/webbrowser/webserver(READWRITE,1).
    /// </summary>
    [TestCaseSource(typeof(ParameterLoader), nameof(ParameterLoader.GetTestTeachers))]
    [Description("Without logging in, every same-origin link reachable from the home page can be followed.")]
    public async Task SpiderUnloggedTest(string mail, string password, string role)
    {
        var failedLinks = await CrawlAndGetBrokenLinksAsync();

        Assert.That(failedLinks, Is.Empty, $"Broken links:{Environment.NewLine}{string.Join(Environment.NewLine, failedLinks)}");
    }

    private async Task<IReadOnlyList<string>> CrawlAndGetBrokenLinksAsync()
    {
        await NavigationUtilities.GetUrlAndWaitFooterAsync(User.Page, AppUrl);
        var pageLinks = await SpiderNavigation.GetPageLinksAsync(User.Page, AppUrl);
        var explored = await SpiderNavigation.ExploreLinksAsync(
            User.Page, AppUrl, pageLinks, new Dictionary<string, string>(), Constants.SpiderDepth);

        return explored.Where(link => link.Value == BrokenLinkStatus).Select(link => link.Key).ToList();
    }
}
