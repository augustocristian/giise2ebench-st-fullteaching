using Microsoft.Playwright;
using FullTeaching.E2E.Common.Exceptions;
using NUnit.Framework;
using static Microsoft.Playwright.Assertions;

namespace FullTeaching.E2E.Common;

/// <summary>Forum navigation helpers, ported from common/ForumNavigationUtilities.java.</summary>
public static class ForumNavigationUtilities
{
    /// <summary>Whether the forum tab shows the "new entry" icon, i.e. the forum is enabled. One-shot.</summary>
    public static async Task<bool> IsForumEnabledAsync(ILocator forumTabContent)
    {
        ArgumentNullException.ThrowIfNull(forumTabContent);
        return await forumTabContent.Locator(Constants.ForumNewEntryIcon).CountAsync() > 0;
    }

    private static async Task<ILocator> EntryRowsAsync(BrowserUser user)
    {
        var tabContent = await CourseNavigationUtilities.GetTabContentAsync(user, Constants.ForumIcon);
        return tabContent.Locator(Constants.ForumEntryRow);
    }

    /// <summary>Returns the titles of every entry of the forum, in order.</summary>
    public static async Task<IReadOnlyList<string>> GetFullEntryListAsync(BrowserUser user)
    {
        ArgumentNullException.ThrowIfNull(user);
        await user.Page.Locator(Constants.ForumIcon).WaitForAsync();
        var rows = await EntryRowsAsync(user);
        return await rows.ChildTextsAsync(Constants.ForumEntryListEntryTitle);
    }

    /// <summary>Returns the titles of the forum entries whose row mentions <paramref name="userName"/>.</summary>
    public static async Task<IReadOnlyList<string>> GetUserEntriesAsync(BrowserUser user, string userName)
    {
        ArgumentNullException.ThrowIfNull(user);
        ArgumentNullException.ThrowIfNull(userName);
        var rows = await EntryRowsAsync(user);
        var entries = await rows.AllAsync();
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

    /// <summary>
    /// Yields the entry locator with the given title, mirrors ForumNavigationUtilities.getEntry;
    /// waits (auto-retrying) until it is found - an entry list newly posted-to can take a moment
    /// to re-render.
    /// </summary>
    /// <exception cref="ElementNotFoundException">No entry with that title appeared in time.</exception>
    public static async Task<ILocator> GetEntryAsync(BrowserUser user, string entryName)
    {
        ArgumentNullException.ThrowIfNull(user);
        ArgumentNullException.ThrowIfNull(entryName);
        await user.Page.Locator(Constants.ForumIcon).WaitForAsync();
        var rows = await EntryRowsAsync(user);
        var entry = rows
            .Filter(new()
            {
                Has = user.Page.Locator(Constants.ForumEntryListEntryTitle)
                    .Filter(new() { HasTextRegex = LocatorExtensions.ExactText(entryName) }),
            })
            .First;
        try
        {
            await Expect(entry).ToBeAttachedAsync();
        }
        catch (PlaywrightException ex)
        {
            throw new ElementNotFoundException(
                $"[{user.ClientData}] [GetEntry] The entry with title \"{entryName}\" doesn't exist, " +
                $"the number of entries was {await rows.CountAsync()}",
                ex);
        }
        return entry;
    }

    /// <summary>Waits for the first comment and returns every comment of the open forum entry.</summary>
    public static async Task<IReadOnlyList<ILocator>> GetCommentsAsync(BrowserUser user)
    {
        ArgumentNullException.ThrowIfNull(user);
        var comments = user.Page.Locator(Constants.ForumCommentListComment);
        await comments.First.WaitForAsync(new() { Timeout = TestConfig.ShortTimeoutMs });
        return await comments.AllAsync();
    }

    /// <summary>Returns the comments written by <paramref name="userName"/>.</summary>
    public static async Task<IReadOnlyList<ILocator>> GetUserCommentsAsync(BrowserUser user, string userName)
    {
        var allComments = await GetCommentsAsync(user);
        var userComments = new List<ILocator>();
        foreach (var comment in allComments)
        {
            var author = (await comment.Locator(Constants.ForumCommentListCommentUser).First.InnerTextAsync()).Trim();
            if (author == userName)
            {
                userComments.Add(comment);
            }
        }
        return userComments;
    }

    /// <summary>Posts a new forum entry and waits until it is listed.</summary>
    public static async Task NewEntryAsync(BrowserUser user, string title, string content)
    {
        ArgumentNullException.ThrowIfNull(user);
        var page = user.Page;
        await CourseNavigationUtilities.Go2TabAsync(user, Constants.ForumIcon);
        var tabContent = await CourseNavigationUtilities.GetTabContentAsync(user, Constants.ForumIcon);
        Assert.That(await IsForumEnabledAsync(tabContent), Is.True, "Forum not activated");

        await page.Locator(Constants.ForumNewEntryIcon).ClickAsync();
        await page.Locator(Constants.ForumNewEntryModal).WaitForAsync();

        await page.Locator(Constants.ForumNewEntryModalTitle).FillAsync(title);
        await page.Locator(Constants.ForumNewEntryModalContent).FillAsync(content);
        await page.Locator(Constants.ForumNewEntryModalPostButton).ClickAsync();

        await page.Locator(Constants.ForumEntriesSideView).WaitForAsync();
        await GetEntryAsync(user, title);
    }

    /// <summary>Ignores the first nested comment-div, which is the original comment itself.</summary>
    public static async Task<IReadOnlyList<ILocator>> GetRepliesAsync(ILocator comment)
    {
        ArgumentNullException.ThrowIfNull(comment);
        var nested = await comment.Locator(Constants.ForumCommentListCommentDiv).AllAsync();
        return nested.Skip(1).ToList();
    }

    /// <summary>Enables the forum of the open course and asserts it is active.</summary>
    public static Task EnableForumAsync(BrowserUser user) =>
        SetForumEnabledAsync(user, Constants.EnableForumButton, expectEnabled: true, "The forum is not enabled");

    /// <summary>Disables the forum of the open course and asserts it is inactive.</summary>
    public static Task DisableForumAsync(BrowserUser user) =>
        SetForumEnabledAsync(user, Constants.DisableForumButton, expectEnabled: false, "The forum is not disabled");

    private static async Task SetForumEnabledAsync(
        BrowserUser user, string toggleSelector, bool expectEnabled, string failureMessage)
    {
        ArgumentNullException.ThrowIfNull(user);
        var page = user.Page;
        await page.Locator(Constants.ForumEditEntryIcon).ClickAsync();
        var editModal = page.Locator(Constants.EnableForumModal);
        await editModal.WaitForAsync();

        await editModal.Locator(toggleSelector).ClickAsync();
        await editModal.Locator(Constants.EnableForumModalSaveButton).ClickAsync();
        await editModal.WaitForAsync(new() { State = WaitForSelectorState.Hidden });

        var tabContent = await CourseNavigationUtilities.GetTabContentAsync(user, Constants.ForumIcon);
        Assert.That(await IsForumEnabledAsync(tabContent), Is.EqualTo(expectEnabled), failureMessage);
    }
}
