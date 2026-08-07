using Microsoft.Playwright;
using FullTeaching.E2E.Common.Exceptions;
using static Microsoft.Playwright.Assertions;

namespace FullTeaching.E2E.Common;

/// <summary>
/// Course/tab navigation helpers, ported from common/CourseNavigationUtilities.java. Most of
/// Click.java's manual scroll+click+JS-fallback-retry logic is unnecessary here: Playwright's
/// <c>ClickAsync()</c> already waits for the element to be attached, visible, stable and
/// enabled (auto-scrolling it into view) before acting, retrying until its timeout.
/// </summary>
public static class CourseNavigationUtilities
{
    private const int TabContentTimeoutMs = 4000;

    private static ILocator CourseItems(BrowserUser user) =>
        user.Page.Locator(Constants.CourseList).Locator("li");

    private static Task<IReadOnlyList<string>> CourseTitlesAsync(BrowserUser user) =>
        CourseItems(user).ChildTextsAsync(Constants.CourseTitle);

    /// <summary>The (retrying) locator of the course titles in the dashboard equal to <paramref name="courseTitle"/>.</summary>
    private static ILocator CourseTitleLocator(BrowserUser user, string courseTitle) =>
        CourseItems(user).Locator(Constants.CourseTitle).Filter(new() { HasTextRegex = LocatorExtensions.ExactText(courseTitle) });

    /// <summary>Creates a course through the "new course" modal and waits for it to show up in the dashboard.</summary>
    public static async Task<string> NewCourseAsync(BrowserUser user, string courseName)
    {
        ArgumentNullException.ThrowIfNull(user);
        var page = user.Page;
        await NavigationUtilities.ToCoursesHomeAsync(user);

        await page.Locator(Constants.CourseListItem).First.WaitForAsync();
        await page.Locator(Constants.NewCourseIcon).ClickAsync();
        await page.Locator(Constants.NewCourseModal).WaitForAsync();

        await page.Locator(Constants.NewCourseModalNameField).FillAsync(courseName);
        await page.Locator(Constants.NewCourseModalSave).ClickAsync();

        await AssertCourseExistsAsync(user, courseName);
        return courseName;
    }

    /// <summary>One-shot check, mirrors CourseNavigationUtilities.checkIfCourseExists(wd, title).</summary>
    public static async Task<bool> CourseExistsAsync(BrowserUser user, string courseTitle)
    {
        ArgumentNullException.ThrowIfNull(user);
        var titles = await CourseTitlesAsync(user);
        return titles.Contains(courseTitle);
    }

    /// <summary>
    /// Retrying assertion, mirrors both the two-argument and the three-argument
    /// (with manual retries) Java overloads. Uses Playwright's auto-retrying <c>Expect</c>.
    /// </summary>
    /// <param name="user">User whose dashboard is inspected.</param>
    /// <param name="courseTitle">Exact (trimmed) course title expected in the list.</param>
    /// <param name="timeoutMs">Timeout; defaults to <see cref="TestConfig.ShortTimeoutMs"/>.</param>
    public static Task AssertCourseExistsAsync(BrowserUser user, string courseTitle, int? timeoutMs = null)
    {
        ArgumentNullException.ThrowIfNull(user);
        return Expect(CourseTitleLocator(user, courseTitle).First)
            .ToBeAttachedAsync(new() { Timeout = timeoutMs ?? TestConfig.ShortTimeoutMs });
    }

    /// <summary>Retrying assertion that no course with exactly <paramref name="courseTitle"/> is listed.</summary>
    public static Task AssertCourseNotExistsAsync(BrowserUser user, string courseTitle, int? timeoutMs = null)
    {
        ArgumentNullException.ThrowIfNull(user);
        return Expect(CourseTitleLocator(user, courseTitle))
            .ToHaveCountAsync(0, new() { Timeout = timeoutMs ?? TestConfig.ShortTimeoutMs });
    }

    private static async Task OpenEditCourseModalAsync(BrowserUser user, string courseTitle)
    {
        var courseElement = await GetCourseByNameAsync(user, courseTitle);
        await courseElement.Locator(Constants.EditCourseButton).ClickAsync();
        await user.Page.Locator(Constants.EditDeleteModal).WaitForAsync();
    }

    /// <summary>Renames a course through its edit modal.</summary>
    public static async Task ChangeCourseNameAsync(BrowserUser user, string oldName, string newName)
    {
        ArgumentNullException.ThrowIfNull(user);
        var page = user.Page;
        await page.Locator(Constants.CourseList).WaitForAsync();
        await OpenEditCourseModalAsync(user, oldName);

        await page.Locator(Constants.EditCourseModalNameField).FillAsync(newName);
        await page.Locator(Constants.EditCourseModalSave).ClickAsync();
        await page.Locator(Constants.EditDeleteModal).WaitForAsync(new() { State = WaitForSelectorState.Hidden });
    }

    /// <summary>Deletes a course through its edit modal and waits for the dashboard to shrink by one.</summary>
    public static async Task DeleteCourseAsync(BrowserUser user, string courseName)
    {
        ArgumentNullException.ThrowIfNull(user);
        var page = user.Page;
        await NavigationUtilities.ToCoursesHomeAsync(user);
        await page.Locator(Constants.CourseList).WaitForAsync();
        var items = CourseItems(user);
        var numCoursesInitial = await items.CountAsync();

        await OpenEditCourseModalAsync(user, courseName);
        await page.Locator(Constants.EditCourseDeleteCheck).ClickAsync();
        await page.Locator(Constants.EditCourseDeleteButton).ClickAsync();
        await page.Locator(Constants.EditCourseModalSave).ClickAsync();

        await Expect(items).ToHaveCountAsync(numCoursesInitial - 1);
    }

    /// <summary>Returns the titles of the courses in the dashboard, in order.</summary>
    public static async Task<IReadOnlyList<string>> GetCoursesListAsync(BrowserUser user)
    {
        ArgumentNullException.ThrowIfNull(user);
        await NavigationUtilities.ToCoursesHomeAsync(user);
        return await CourseTitlesAsync(user);
    }

    /// <summary>Yields the &lt;li&gt; locator for the course with the given title; throws if not found.</summary>
    /// <exception cref="ElementNotFoundException">No course has that title.</exception>
    public static async Task<ILocator> GetCourseByNameAsync(BrowserUser user, string name)
    {
        ArgumentNullException.ThrowIfNull(user);
        await user.Page.Locator(Constants.CourseList).WaitForAsync();
        var items = CourseItems(user);
        var course = await items.FindRowByChildTextAsync(Constants.CourseTitle, name);
        return course ?? throw new ElementNotFoundException(
            $"[{user.ClientData}] GetCourseByName - the course \"{name}\" doesn't exist; " +
            $"listed courses: [{string.Join(", ", await items.ChildTextsAsync(Constants.CourseTitle))}]");
    }

    /// <summary>The tab element of a course tab: the grandparent of its icon.</summary>
    private static ILocator TabElementFromIcon(BrowserUser user, string iconSelector) =>
        user.Page.Locator(Constants.CourseTabs).Locator(iconSelector).Locator("xpath=../..");

    /// <summary>The id of the content container paired with a tab element id ("...label..." becomes "...content...").</summary>
    private static async Task<string> TabContentIdAsync(BrowserUser user, ILocator tab, string iconSelector)
    {
        var tabId = await tab.GetAttributeAsync("id")
            ?? throw new ElementNotFoundException($"[{user.ClientData}] the tab of icon '{iconSelector}' has no id");
        return tabId.Replace("label", "content", StringComparison.Ordinal);
    }

    /// <summary>Clicks the course tab identified by its icon selector and waits for its content to render.</summary>
    public static async Task Go2TabAsync(BrowserUser user, string iconSelector)
    {
        ArgumentNullException.ThrowIfNull(user);
        var tab = TabElementFromIcon(user, iconSelector);
        var contentId = await TabContentIdAsync(user, tab, iconSelector);
        await tab.ClickAsync();
        await user.Page.Locator($"#{contentId}").WaitForAsync(new() { Timeout = TabContentTimeoutMs });
    }

    /// <summary>Returns the content container of the course tab identified by its icon selector.</summary>
    public static async Task<ILocator> GetTabContentAsync(BrowserUser user, string iconSelector)
    {
        ArgumentNullException.ThrowIfNull(user);
        var contentId = await TabContentIdAsync(user, TabElementFromIcon(user, iconSelector), iconSelector);
        return user.Page.Locator($"#{contentId}");
    }

    /// <summary>Whether <paramref name="userName"/> (case-insensitive, trimmed) appears in the attenders tab.</summary>
    /// <exception cref="ElementNotFoundException">The attenders list is empty.</exception>
    public static async Task<bool> IsUserInAttendersListAsync(BrowserUser user, string userName)
    {
        ArgumentNullException.ThrowIfNull(user);
        ArgumentNullException.ThrowIfNull(userName);
        var page = user.Page;
        await page.Locator(Constants.AttendersIcon).WaitForAsync();
        await GetTabContentAsync(user, Constants.AttendersIcon);
        var rows = page.Locator(Constants.AttendersListRows);
        await rows.First.WaitForAsync();

        var rowLocators = await rows.AllAsync();
        if (rowLocators.Count == 0)
        {
            throw new ElementNotFoundException($"[{user.ClientData}] IsUserInAttendersList - attenders list is empty");
        }
        foreach (var row in rowLocators)
        {
            var rowText = (await row.InnerTextAsync()).Trim();
            if (string.Equals(userName.Trim(), rowText, StringComparison.OrdinalIgnoreCase))
            {
                return true;
            }
        }
        return false;
    }

    /// <summary>Returns the name highlighted in the attenders tab (the user currently speaking).</summary>
    /// <exception cref="ElementNotFoundException">No attender is highlighted.</exception>
    public static async Task<string> GetHighlightedAttenderAsync(BrowserUser user)
    {
        ArgumentNullException.ThrowIfNull(user);
        var content = await GetTabContentAsync(user, Constants.AttendersIcon);
        var highlighted = content.Locator(Constants.AttendersListHighlightedRow);
        if (await highlighted.CountAsync() == 0)
        {
            throw new ElementNotFoundException($"[{user.ClientData}] GetHighlightedAttender - no highlighted user");
        }
        return (await highlighted.First.InnerTextAsync()).Trim();
    }
}
