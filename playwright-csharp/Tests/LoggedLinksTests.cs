using FullTeaching.E2E.Common;
using FullTeaching.E2E.Utils;
using NUnit.Framework;

namespace FullTeaching.E2E.Tests;

/// <summary>Ported from functional/test/LoggedLinksTests.java.</summary>
[TestFixture]
public class LoggedLinksTests : BaseTest
{
    /// <summary>
    /// Logs in, then crawls every same-origin link and asserts none are broken.
    /// Resources: loginservice(READONLY,10) openvidumock(NOACCESS,10) course(READWRITE,15)
    /// executor/webbrowser/webserver(READWRITE,1).
    /// </summary>
    [TestCaseSource(typeof(ParameterLoader), nameof(ParameterLoader.GetTestUsers))]
    public async Task SpiderLoggedTest(string mail, string password, string role)
    {
        await LoginHelper.SlowLoginAsync(User, mail, password);
        await NavigationUtilities.GetUrlAndWaitFooterAsync(User.Page, AppUrl);
        var pageLinks = await SpiderNavigation.GetPageLinksAsync(User.Page, AppUrl);
        var explored = await SpiderNavigation.ExploreLinksAsync(
            User.Page, AppUrl, pageLinks, new Dictionary<string, string>(), Constants.SpiderDepth);

        var failedLinks = explored.Where(kv => kv.Value == "KO").Select(kv => kv.Key).ToList();
        Assert.That(failedLinks, Is.Empty, string.Join("\n", failedLinks));
    }
}
