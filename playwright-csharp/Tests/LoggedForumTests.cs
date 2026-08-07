using System.Globalization;
using System.Text.RegularExpressions;
using FullTeaching.E2E.Common;
using FullTeaching.E2E.Utils;
using Microsoft.Playwright;
using NUnit.Framework;
using static Microsoft.Playwright.Assertions;

namespace FullTeaching.E2E.Tests;

/// <summary>
/// Ported from functional/test/LoggedForumTest.java.
/// The FullTeaching UI offers no way to delete forum entries or comments, so the data created
/// by these tests (always inside <see cref="Constants.ForumTestCourseName"/>, with a unique
/// timestamped title) cannot be removed afterwards.
/// </summary>
[TestFixture]
[Category("Logged")]
[Category("Forum")]
public class LoggedForumTests : BaseTest
{
    private const string NewEntryTitlePrefix = "New Entry Test";
    private const string NewCommentTitlePrefix = "New Comment Test";
    private const string NewReplyTitlePrefix = "New Reply Test";
    private const string CommentTextPrefix = "COMMENT TEST";
    private const string ParentXPath = "xpath=..";

    private ILocator Comments => User.Page.Locator(Constants.ForumCommentListComment);

    /// <summary>
    /// Leaves the (possibly modal-covered) forum view so that the logout performed by
    /// <see cref="BaseTest"/> is not flaky. NUnit runs this derived teardown before the base one.
    /// </summary>
    [TearDown]
    public async Task ReturnToHomePageAsync()
    {
        if (!User.IsOnSession)
        {
            return;
        }

        try
        {
            await User.Page.GotoAsync(AppUrl);
        }
        catch (PlaywrightException ex)
        {
            TestContext.Out.WriteLine($"Could not return to the home page before logout: {ex.Message}");
        }
    }

    /// <summary>
    /// Logs in, walks every course's forum (if enabled) and its entries/comments.
    /// Resources: loginservice(READONLY,10) openvidumock(NOACCESS,10) forum(READONLY,10)
    /// executor/webbrowser/webserver(READWRITE,1).
    /// </summary>
    [TestCaseSource(typeof(ParameterLoader), nameof(ParameterLoader.GetTestUsers))]
    [Description("Every enabled course forum can be browsed entry by entry, and at least one entry has comments.")]
    public async Task ForumLoadEntriesTest(string mail, string password, string role)
    {
        var userName = await LoginHelper.SlowLoginAsync(User, mail, password);

        var courses = await CourseNavigationUtilities.GetCoursesListAsync(User);
        Assert.That(courses, Is.Not.Empty, "No courses in the list");

        var forumEnabledSomewhere = false;
        var someEntryHasComments = false;

        foreach (var courseName in courses)
        {
            if (!await OpenCourseForumAsync(courseName))
            {
                await BackToDashboardAsync();
                continue; // forum not active on this course, go to next
            }

            forumEnabledSomewhere = true;
            foreach (var entryTitle in await ForumNavigationUtilities.GetFullEntryListAsync(User))
            {
                someEntryHasComments |= await BrowseEntryAsync(entryTitle, userName);
            }

            await BackToDashboardAsync();
        }

        Assert.That(forumEnabledSomewhere && someEntryHasComments, Is.True,
            "There isn't any forum that can be used to test this [Or not activated or no entry lists or not comments]");
    }

    /// <summary>
    /// Creates a new forum entry and checks it appears with the right author/title/content.
    /// Resources: loginservice(READONLY,10) openvidumock(NOACCESS,10) forum(READWRITE,1,exclusive)
    /// executor/webbrowser/webserver(READWRITE,1).
    /// </summary>
    [TestCaseSource(typeof(ParameterLoader), nameof(ParameterLoader.GetTestUsers))]
    [Description("A new forum entry is listed with its author and opens with its title and first comment.")]
    public async Task ForumNewEntryTest(string mail, string password, string role)
    {
        var userName = await LoginHelper.SlowLoginAsync(User, mail, password);
        var page = User.Page;
        var stamp = NewStamp();
        var entryTitle = $"{NewEntryTitlePrefix} {stamp}";
        var entryContent = EntryContentFor(stamp);

        await OpenForumTestCourseForumAsync();
        await ForumNavigationUtilities.NewEntryAsync(User, entryTitle, entryContent);

        await Expect(EntryRow(entryTitle).Locator(Constants.ForumEntryListEntryUser).First).ToHaveTextAsync(userName);

        await OpenEntryAsync(entryTitle);
        var header = page.Locator(Constants.ForumCommentListEntryTitle);
        await Expect(header).ToHaveTextAsync(new Regex($"^\\s*{Regex.Escape(entryTitle)}"));
        await Expect(header.Locator(Constants.ForumCommentListEntryUser).First).ToHaveTextAsync(userName);

        var firstComment = Comments.First;
        await Expect(firstComment.Locator(Constants.ForumCommentListCommentContent).First).ToHaveTextAsync(entryContent);
        await Expect(firstComment.Locator(Constants.ForumCommentListCommentUser).First).ToHaveTextAsync(userName);
    }

    /// <summary>
    /// Adds a comment to the course forum's first entry (creating one first if none exist).
    /// Resources: loginservice(READONLY,10) openvidumock(NOACCESS,10) forum(READWRITE,1,exclusive)
    /// executor/webbrowser/webserver(READWRITE,1).
    /// </summary>
    [TestCaseSource(typeof(ParameterLoader), nameof(ParameterLoader.GetTestUsers))]
    [Description("A comment posted on a forum entry is appended to the entry with the right author.")]
    public async Task ForumNewCommentTest(string mail, string password, string role)
    {
        var userName = await LoginHelper.SlowLoginAsync(User, mail, password);
        var page = User.Page;

        await OpenForumTestCourseForumAsync();
        await OpenEntryAsync(await FirstEntryTitleOrCreateAsync(NewCommentTitlePrefix));

        await Expect(Comments.First).ToBeVisibleAsync();
        var commentsBefore = await Comments.CountAsync();

        var commentContent = $"{CommentTextPrefix}{NewStamp()}. This is the comment written by the test";
        await page.Locator(Constants.ForumCommentList).Locator(Constants.ForumCommentListNewCommentIcon).First.ClickAsync();
        await PostFromModalAsync(Constants.ForumNewCommentModal, Constants.ForumNewCommentModalTextField, commentContent);

        var postedComment = Comments.Filter(new() { HasText = commentContent });
        await Expect(postedComment).ToHaveCountAsync(1);
        Assert.That(await Comments.CountAsync(), Is.GreaterThan(commentsBefore), "Comment list empty or only original comment");
        await Expect(postedComment.Locator(Constants.ForumCommentListCommentContent).First).ToHaveTextAsync(commentContent);
        await Expect(postedComment.Locator(Constants.ForumCommentListCommentUser).First).ToHaveTextAsync(userName);
    }

    /// <summary>
    /// Replies to the first comment of the course forum's first entry.
    /// Resources: loginservice(READONLY,10) openvidumock(NOACCESS,10) forum(READWRITE,1,exclusive)
    /// executor/webbrowser/webserver(READWRITE,1).
    /// </summary>
    [TestCaseSource(typeof(ParameterLoader), nameof(ParameterLoader.GetTestUsers))]
    [Description("A reply posted on the first comment of an entry is nested under it with the right author.")]
    public async Task ForumNewReply2CommentTest(string mail, string password, string role)
    {
        var userName = await LoginHelper.SlowLoginAsync(User, mail, password);

        await OpenForumTestCourseForumAsync();
        await OpenEntryAsync(await FirstEntryTitleOrCreateAsync(NewReplyTitlePrefix));

        var firstComment = Comments.First;
        await Expect(firstComment).ToBeVisibleAsync();
        await firstComment.Locator(Constants.ForumCommentListCommentReplyIcon).First.ClickAsync();

        var replyContent = $"This is the reply written by the test {NewStamp()}";
        await PostFromModalAsync(
            Constants.ForumCommentListModalNewReply, Constants.ForumCommentListModalNewReplyTextField, replyContent);

        // Replies are comment-divs nested inside the comment's own (root) comment-div.
        var reply = firstComment
            .Locator($"{Constants.ForumCommentListCommentDiv} {Constants.ForumCommentListCommentDiv}")
            .Filter(new() { HasText = replyContent })
            .First;
        await Expect(reply).ToBeVisibleAsync();
        await Expect(reply.Locator(Constants.ForumCommentListCommentContent).First).ToHaveTextAsync(replyContent);
        await Expect(reply.Locator(Constants.ForumCommentListCommentUser).First).ToHaveTextAsync(userName);
    }

    private static string NewStamp() => DateTime.Now.ToString("yyyyMMdd-HHmmss-fff", CultureInfo.InvariantCulture);

    private static string EntryContentFor(string stamp) => $"This is the content written by the test {stamp}";

    private static Regex ExactText(string text) => new($"^\\s*{Regex.Escape(text)}\\s*$");

    /// <summary>The forum-list row of the (first) entry with the given title; auto-waits when used.</summary>
    private ILocator EntryRow(string title)
    {
        var page = User.Page;
        var titleLocator = page.Locator(Constants.ForumEntryListEntryTitle).Filter(new() { HasTextRegex = ExactText(title) });
        return page.Locator(Constants.ForumEntryRow).Filter(new() { Has = titleLocator }).First;
    }

    /// <summary>Opens the entry from the forum list and waits for its comment list.</summary>
    private async Task OpenEntryAsync(string entryTitle)
    {
        await EntryRow(entryTitle).Locator(Constants.ForumEntryListEntryTitle).ClickAsync();
        await Expect(User.Page.Locator(Constants.ForumCommentList)).ToBeVisibleAsync();
    }

    private async Task BackToDashboardAsync() => await User.Page.Locator(Constants.BackToDashboard).ClickAsync();

    /// <summary>Opens the course and its Forum tab; returns whether the forum is activated.</summary>
    private async Task<bool> OpenCourseForumAsync(string courseName)
    {
        var course = await CourseNavigationUtilities.GetCourseByNameAsync(User, courseName);
        await course.Locator(Constants.CourseListCourseTitle).ClickAsync();
        await User.Page.Locator(Constants.TabsDiv).WaitForAsync();

        await CourseNavigationUtilities.Go2TabAsync(User, Constants.ForumIcon);
        var tabContent = await CourseNavigationUtilities.GetTabContentAsync(User, Constants.ForumIcon);
        return await ForumNavigationUtilities.IsForumEnabledAsync(tabContent);
    }

    private async Task OpenForumTestCourseForumAsync()
    {
        await NavigationUtilities.ToCoursesHomeAsync(User);
        Assert.That(await OpenCourseForumAsync(Constants.ForumTestCourseName), Is.True, "Forum not activated");
    }

    /// <summary>Opens one entry, inspects its comments, and returns whether it has any.</summary>
    private async Task<bool> BrowseEntryAsync(string entryTitle, string userName)
    {
        await OpenEntryAsync(entryTitle);

        var comments = await ForumNavigationUtilities.GetCommentsAsync(User);
        var hasComments = comments.Count > 0;
        if (hasComments)
        {
            await ForumNavigationUtilities.GetUserCommentsAsync(User, userName);
        }

        // The icon sits inside the actual back button
        await User.Page.Locator(Constants.BackToEntriesListIcon).Locator(ParentXPath).ClickAsync();
        return hasComments;
    }

    private async Task<string> FirstEntryTitleOrCreateAsync(string titlePrefix)
    {
        var entries = await ForumNavigationUtilities.GetFullEntryListAsync(User);
        if (entries.Count > 0)
        {
            return entries[0];
        }

        var stamp = NewStamp();
        var title = $"{titlePrefix} {stamp}";
        await ForumNavigationUtilities.NewEntryAsync(User, title, EntryContentFor(stamp));
        return title;
    }

    /// <summary>Fills the (already requested) post modal, submits it and waits until it closes.</summary>
    private async Task PostFromModalAsync(string modalSelector, string textFieldSelector, string text)
    {
        var page = User.Page;
        await Expect(page.Locator(modalSelector)).ToBeVisibleAsync();
        await page.Locator(textFieldSelector).FillAsync(text);
        await page.Locator(Constants.ForumNewCommentModalPostButton).ClickAsync();
        await Expect(page.Locator(modalSelector)).ToBeHiddenAsync();
    }
}
