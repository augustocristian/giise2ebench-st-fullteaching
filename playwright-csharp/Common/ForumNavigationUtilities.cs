using Microsoft.Playwright;
using FullTeaching.E2E.Common.Exceptions;
using NUnit.Framework;

namespace FullTeaching.E2E.Common;

/// <summary>Forum navigation helpers, ported from common/ForumNavigationUtilities.java.</summary>
public static class ForumNavigationUtilities
{
    public static async Task<bool> IsForumEnabledAsync(ILocator forumTabContent) =>
        await forumTabContent.Locator(Constants.ForumNewEntryIcon).CountAsync() > 0;

    public static async Task<IReadOnlyList<string>> GetFullEntryListAsync(BrowserUser user)
    {
        await user.Page.Locator(Constants.ForumIcon).WaitForAsync();
        var tabContent = await CourseNavigationUtilities.GetTabContentAsync(user, Constants.ForumIcon);
        var entries = await tabContent.Locator(Constants.ForumEntryRow).AllAsync();
        var titles = new List<string>(entries.Count);
        foreach (var entry in entries)
        {
            titles.Add((await entry.Locator(Constants.ForumEntryListEntryTitle).InnerTextAsync()).Trim());
        }
        return titles;
    }

    public static async Task<IReadOnlyList<string>> GetUserEntriesAsync(BrowserUser user, string userName)
    {
        var tabContent = await CourseNavigationUtilities.GetTabContentAsync(user, Constants.ForumIcon);
        var entries = await tabContent.Locator(Constants.ForumEntryRow).AllAsync();
        var titles = new List<string>();
        foreach (var entry in entries)
        {
            if ((await entry.InnerTextAsync()).Contains(userName, StringComparison.Ordinal))
            {
                titles.Add((await entry.Locator(Constants.ForumEntryListEntryTitle).InnerTextAsync()).Trim());
            }
        }
        return titles;
    }

    /// <summary>Yields the entry locator with the given title, mirrors ForumNavigationUtilities.getEntry;
    /// retries until found (an entry list newly posted-to can take a moment to re-render).</summary>
    public static Task<ILocator> GetEntryAsync(BrowserUser user, string entryName) =>
        PollHelper.PollUntilAsync(
            async () =>
            {
                await user.Page.Locator(Constants.ForumIcon).WaitForAsync();
                var tabContent = await CourseNavigationUtilities.GetTabContentAsync(user, Constants.ForumIcon);
                var entries = await tabContent.Locator(Constants.ForumEntryRow).AllAsync();
                foreach (var entry in entries)
                {
                    var title = (await entry.Locator(Constants.ForumEntryListEntryTitle).InnerTextAsync()).Trim();
                    if (title == entryName)
                    {
                        return entry;
                    }
                }
                throw new ElementNotFoundException(
                    $"[GetEntry] The entry with title \"{entryName}\" doesn't exist, the number of entries was {entries.Count}");
            },
            _ => true);

    public static async Task<IReadOnlyList<ILocator>> GetCommentsAsync(BrowserUser user)
    {
        var comments = user.Page.Locator(Constants.ForumCommentListComment);
        await comments.First.WaitForAsync(new() { Timeout = 20000 });
        return await comments.AllAsync();
    }

    public static async Task<IReadOnlyList<ILocator>> GetUserCommentsAsync(BrowserUser user, string userName)
    {
        var allComments = await GetCommentsAsync(user);
        var userComments = new List<ILocator>();
        foreach (var comment in allComments)
        {
            var author = (await comment.Locator(Constants.ForumCommentListCommentUser).InnerTextAsync()).Trim();
            if (author == userName)
            {
                userComments.Add(comment);
            }
        }
        return userComments;
    }

    public static async Task NewEntryAsync(BrowserUser user, string title, string content)
    {
        var page = user.Page;
        await CourseNavigationUtilities.Go2TabAsync(user, Constants.ForumIcon);
        var tabContent = await CourseNavigationUtilities.GetTabContentAsync(user, Constants.ForumIcon);
        Assert.That(await IsForumEnabledAsync(tabContent), Is.True, "Forum not activated");

        await page.Locator(Constants.ForumNewEntryIcon).ClickAsync();
        await page.Locator(Constants.ForumNewEntryModal).WaitForAsync();

        await page.Locator(Constants.ForumNewEntryModalTitle).FillAsync(title);
        await page.Locator(Constants.ForumNewEntryModalContent).FillAsync(content);
        await page.Locator(Constants.ForumNewEntryModalPostButton).ClickAsync();

        await page.Locator(".entries-side-view").WaitForAsync();
        await GetEntryAsync(user, title);
    }

    /// <summary>Ignores the first nested comment-div, which is the original comment itself.</summary>
    public static async Task<IReadOnlyList<ILocator>> GetRepliesAsync(ILocator comment)
    {
        var nested = await comment.Locator(Constants.ForumCommentListCommentDiv).AllAsync();
        return nested.Skip(1).ToList();
    }

    public static async Task EnableForumAsync(BrowserUser user)
    {
        var page = user.Page;
        await page.Locator(Constants.ForumEditEntryIcon).ClickAsync();
        var editModal = page.Locator(Constants.EnableForumModal);
        await editModal.WaitForAsync();

        await editModal.Locator(Constants.EnableForumButton).ClickAsync();
        await editModal.Locator(Constants.EnableForumModalSaveButton).ClickAsync();
        await editModal.WaitForAsync(new() { State = WaitForSelectorState.Hidden });

        var tabContent = await CourseNavigationUtilities.GetTabContentAsync(user, Constants.ForumIcon);
        Assert.That(await IsForumEnabledAsync(tabContent), Is.True, "The forum is not enabled");
    }

    public static async Task DisableForumAsync(BrowserUser user)
    {
        var page = user.Page;
        await page.Locator(Constants.ForumEditEntryIcon).ClickAsync();
        var editModal = page.Locator(Constants.EnableForumModal);
        await editModal.WaitForAsync();

        await editModal.Locator(Constants.DisableForumButton).ClickAsync();
        await editModal.Locator(Constants.EnableForumModalSaveButton).ClickAsync();
        await editModal.WaitForAsync(new() { State = WaitForSelectorState.Hidden });

        var tabContent = await CourseNavigationUtilities.GetTabContentAsync(user, Constants.ForumIcon);
        Assert.That(await IsForumEnabledAsync(tabContent), Is.False, "The forum is not disabled");
    }
}
