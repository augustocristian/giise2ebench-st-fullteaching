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
    private static async Task<IReadOnlyList<string>> CourseTitlesInAsync(ILocator courseList)
    {
        var items = await courseList.Locator("li").AllAsync();
        var titles = new List<string>(items.Count);
        foreach (var item in items)
        {
            titles.Add((await item.Locator(Constants.CourseTitle).InnerTextAsync()).Trim());
        }
        return titles;
    }

    public static async Task<string> NewCourseAsync(BrowserUser user, string courseName)
    {
        var page = user.Page;
        await NavigationUtilities.ToCoursesHomeAsync(user);

        await page.Locator(".course-list-item").First.WaitForAsync();
        var newCourseButton = page.Locator(Constants.NewCourseButton);
        await newCourseButton.WaitForAsync();
        await newCourseButton.ClickAsync();
        await page.Locator(Constants.NewCourseModal).WaitForAsync();

        await page.Locator(Constants.NewCourseModalNameField).FillAsync(courseName);
        await page.Locator(Constants.NewCourseModalSave).ClickAsync();

        await AssertCourseExistsAsync(user, courseName);
        return courseName;
    }

    /// <summary>One-shot check, mirrors CourseNavigationUtilities.checkIfCourseExists(wd, title).</summary>
    public static async Task<bool> CourseExistsAsync(BrowserUser user, string courseTitle)
    {
        var courseList = user.Page.Locator(Constants.CourseList);
        var titles = await CourseTitlesInAsync(courseList);
        return titles.Contains(courseTitle);
    }

    /// <summary>
    /// Retrying assertion, mirrors both the two-argument and the three-argument
    /// (with manual retries) Java overloads via PollHelper (see its doc comment for why).
    /// </summary>
    public static Task AssertCourseExistsAsync(BrowserUser user, string courseTitle, int? timeoutMs = null) =>
        PollHelper.PollUntilAsync(
            () => CourseTitlesInAsync(user.Page.Locator(Constants.CourseList)),
            titles => titles.Contains(courseTitle),
            timeoutMs);

    public static Task AssertCourseNotExistsAsync(BrowserUser user, string courseTitle, int? timeoutMs = null) =>
        PollHelper.PollUntilAsync(
            () => CourseTitlesInAsync(user.Page.Locator(Constants.CourseList)),
            titles => !titles.Contains(courseTitle),
            timeoutMs);

    private static async Task OpenEditCourseModalAsync(BrowserUser user, string courseTitle)
    {
        var courseElement = await GetCourseByNameAsync(user, courseTitle);
        await courseElement.Locator(Constants.EditCourseButton).ClickAsync();
        await user.Page.Locator(Constants.EditDeleteModal).WaitForAsync();
    }

    public static async Task ChangeCourseNameAsync(BrowserUser user, string oldName, string newName)
    {
        var page = user.Page;
        await page.Locator(Constants.CourseList).WaitForAsync();
        await OpenEditCourseModalAsync(user, oldName);

        var nameField = page.Locator(Constants.EditCourseModalNameField);
        await nameField.FillAsync(newName);
        await page.Locator(Constants.EditCourseModalSave).ClickAsync();
        await page.Locator(Constants.EditDeleteModal).WaitForAsync(new() { State = WaitForSelectorState.Hidden });
    }

    public static async Task DeleteCourseAsync(BrowserUser user, string courseName)
    {
        var page = user.Page;
        await NavigationUtilities.ToCoursesHomeAsync(user);
        var courseList = page.Locator(Constants.CourseList);
        await courseList.WaitForAsync();
        var numCoursesInitial = await courseList.Locator("li").CountAsync();

        await OpenEditCourseModalAsync(user, courseName);
        await page.Locator(Constants.EditCourseDeleteCheck).ClickAsync();
        await page.Locator(Constants.EditCourseDeleteButton).ClickAsync();
        await page.Locator(Constants.EditCourseModalSave).ClickAsync();

        await Expect(courseList.Locator("li")).ToHaveCountAsync(numCoursesInitial - 1);
    }

    public static async Task<IReadOnlyList<string>> GetCoursesListAsync(BrowserUser user)
    {
        await NavigationUtilities.ToCoursesHomeAsync(user);
        return await CourseTitlesInAsync(user.Page.Locator(Constants.CourseList));
    }

    /// <summary>Yields the &lt;li&gt; locator for the course with the given title; throws if not found.</summary>
    public static async Task<ILocator> GetCourseByNameAsync(BrowserUser user, string name)
    {
        var courseList = user.Page.Locator(Constants.CourseList);
        await courseList.WaitForAsync();
        var items = await courseList.Locator("li").AllAsync();
        foreach (var item in items)
        {
            var title = (await item.Locator(Constants.CourseTitle).InnerTextAsync()).Trim();
            if (title == name)
            {
                return item;
            }
        }
        throw new ElementNotFoundException("getCourseElement - the course doesn't exist");
    }

    private static ILocator TabElementFromIcon(BrowserUser user, string iconSelector)
    {
        var iconElement = user.Page.Locator(Constants.CourseTabs).Locator(iconSelector);
        var parent1 = iconElement.Locator("xpath=..");
        var parent2 = parent1.Locator("xpath=..");
        return parent2;
    }

    public static async Task Go2TabAsync(BrowserUser user, string iconSelector)
    {
        var tab = TabElementFromIcon(user, iconSelector);
        var tabId = await tab.GetAttributeAsync("id") ?? throw new ElementNotFoundException("tab element has no id");
        await tab.ClickAsync();
        var contentId = tabId.Replace("label", "content");
        await user.Page.Locator($"#{contentId}").WaitForAsync(new() { Timeout = 4000 });
    }

    public static async Task<ILocator> GetTabContentAsync(BrowserUser user, string iconSelector)
    {
        var tab = TabElementFromIcon(user, iconSelector);
        var tabId = await tab.GetAttributeAsync("id") ?? throw new ElementNotFoundException("tab element has no id");
        return user.Page.Locator($"#{tabId.Replace("label", "content")}");
    }

    public static async Task<bool> IsUserInAttendersListAsync(BrowserUser user, string userName)
    {
        var page = user.Page;
        await page.Locator(Constants.AttendersIcon).WaitForAsync();
        await GetTabContentAsync(user, Constants.AttendersIcon);
        var rows = page.Locator(Constants.AttendersListRows);
        await rows.First.WaitForAsync();

        var rowLocators = await rows.AllAsync();
        if (rowLocators.Count == 0)
        {
            throw new ElementNotFoundException("isUserInAttendersList - attenders list is empty");
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

    public static async Task<string> GetHighlightedAttenderAsync(BrowserUser user)
    {
        var content = await GetTabContentAsync(user, Constants.AttendersIcon);
        var highlighted = content.Locator(Constants.AttendersListHighlightedRow);
        if (await highlighted.CountAsync() == 0)
        {
            throw new ElementNotFoundException("getHighlightedAttender - no highlighted user");
        }
        return (await highlighted.First.InnerTextAsync()).Trim();
    }
}
