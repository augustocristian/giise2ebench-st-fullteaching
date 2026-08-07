using FullTeaching.E2E.Common;
using FullTeaching.E2E.Utils;
using NUnit.Framework;

namespace FullTeaching.E2E.Tests;

/// <summary>Ported from functional/test/UnLoggedLinksTests.java.</summary>
[TestFixture]
public class UnloggedLinksTests : BaseTest
{
    /// <summary>
    /// Crawls every same-origin link from the home page (no login) and asserts none are broken.
    /// mail/password/role are unused below, matching the Java source: it parametrizes over
    /// teachers but never logs in, just re-runs the same crawl once per teacher.
    /// Resources: loginservice(READONLY,10) openvidumock(NOACCESS,10) course(READWRITE,15)
    /// executor/webbrowser/webserver(READWRITE,1).
    /// </summary>
    [TestCaseSource(typeof(ParameterLoader), nameof(ParameterLoader.GetTestTeachers))]
    public async Task SpiderUnloggedTest(string mail, string password, string role)
    {
        await NavigationUtilities.GetUrlAndWaitFooterAsync(User.Page, AppUrl);
        var pageLinks = await SpiderNavigation.GetPageLinksAsync(User.Page, AppUrl);
        var explored = await SpiderNavigation.ExploreLinksAsync(
            User.Page, AppUrl, pageLinks, new Dictionary<string, string>(), Constants.SpiderDepth);

        var failedLinks = explored.Where(kv => kv.Value == "KO").Select(kv => kv.Key).ToList();
        Assert.That(failedLinks, Is.Empty, string.Join("\n", failedLinks));
    }
}
