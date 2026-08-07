using Microsoft.Playwright;
using FullTeaching.E2E.Common;
using FullTeaching.E2E.Utils;
using NUnit.Framework;

namespace FullTeaching.E2E.Tests;

/// <summary>Ported from functional/test/LoggedForumTest.java.</summary>
[TestFixture]
public class LoggedForumTests : BaseTest
{
    private static string NewEntryContentFor(DateTime now) =>
        $"This is the content written on the {now.Day} of {now:MMMM}, {now.Hour}:{now.Minute},{now.Second}";

    private async Task EnterForumTestCourseForumAsync()
    {
        await NavigationUtilities.ToCoursesHomeAsync(User);
        var course = await CourseNavigationUtilities.GetCourseByNameAsync(User, Constants.ForumTestCourseName);
        await course.Locator(Constants.CourseListCourseTitle).ClickAsync();
        await User.Page.Locator(Constants.TabsDiv).WaitForAsync();
        await CourseNavigationUtilities.Go2TabAsync(User, Constants.ForumIcon);
        var tabContent = await CourseNavigationUtilities.GetTabContentAsync(User, Constants.ForumIcon);
        Assert.That(await ForumNavigationUtilities.IsForumEnabledAsync(tabContent), Is.True, "Forum not activated");
    }

    private async Task<ILocator> FirstEntryOrNewAsync(string prefix)
    {
        var entries = await ForumNavigationUtilities.GetFullEntryListAsync(User);
        if (entries.Count == 0)
        {
            var now = DateTime.Now;
            var title = $"{prefix} {now.Day}{now.Month}{now.Year}{now.Hour}{now.Minute}{now.Second}";
            await ForumNavigationUtilities.NewEntryAsync(User, title, NewEntryContentFor(now));
            return await ForumNavigationUtilities.GetEntryAsync(User, title);
        }
        return await ForumNavigationUtilities.GetEntryAsync(User, entries[0]);
    }

    /// <summary>
    /// Logs in, walks every course's forum (if enabled) and its entries/comments.
    /// Resources: loginservice(READONLY,10) openvidumock(NOACCESS,10) forum(READONLY,10)
    /// executor/webbrowser/webserver(READWRITE,1).
    /// </summary>
    [TestCaseSource(typeof(ParameterLoader), nameof(ParameterLoader.GetTestUsers))]
    public async Task ForumLoadEntriesTest(string mail, string password, string role)
    {
        var userName = await LoginHelper.SlowLoginAsync(User, mail, password);
        var page = User.Page;

        var courses = await CourseNavigationUtilities.GetCoursesListAsync(User);
        Assert.That(courses, Is.Not.Empty, "No courses in the list");

        var activatedForumOnSomeTest = false;
        var hasComments = false;

        foreach (var courseName in courses)
        {
            var course = await CourseNavigationUtilities.GetCourseByNameAsync(User, courseName);
            await course.Locator(Constants.CourseListCourseTitle).ClickAsync();
            await page.Locator(Constants.TabsDiv).WaitForAsync();

            await CourseNavigationUtilities.Go2TabAsync(User, Constants.ForumIcon);
            var tabContent = await CourseNavigationUtilities.GetTabContentAsync(User, Constants.ForumIcon);
            if (!await ForumNavigationUtilities.IsForumEnabledAsync(tabContent))
            {
                await page.Locator(Constants.BackToDashboard).ClickAsync();
                continue; // forum not active on this course, go to next
            }
            activatedForumOnSomeTest = true;

            var entries = await ForumNavigationUtilities.GetFullEntryListAsync(User);
            foreach (var entryName in entries)
            {
                var entry = await ForumNavigationUtilities.GetEntryAsync(User, entryName);
                await entry.Locator(Constants.ForumEntryListEntryTitle).ClickAsync();
                await page.Locator(Constants.ForumCommentList).WaitForAsync();

                var comments = await ForumNavigationUtilities.GetCommentsAsync(User);
                if (comments.Count > 0)
                {
                    hasComments = true;
                    await ForumNavigationUtilities.GetUserCommentsAsync(User, userName);
                }

                var backIcon = page.Locator(Constants.BackToEntriesListIcon);
                await backIcon.Locator("xpath=..").ClickAsync();
            }

            await page.Locator(Constants.BackToDashboard).ClickAsync();
        }

        Assert.That(activatedForumOnSomeTest && hasComments, Is.True,
            "There isn't any forum that can be used to test this [Or not activated or no entry lists or not comments]");
    }

    /// <summary>
    /// Creates a new forum entry and checks it appears with the right author/title/content.
    /// Resources: loginservice(READONLY,10) openvidumock(NOACCESS,10) forum(READWRITE,1,exclusive)
    /// executor/webbrowser/webserver(READWRITE,1).
    /// </summary>
    [TestCaseSource(typeof(ParameterLoader), nameof(ParameterLoader.GetTestUsers))]
    public async Task ForumNewEntryTest(string mail, string password, string role)
    {
        var userName = await LoginHelper.SlowLoginAsync(User, mail, password);
        var page = User.Page;
        var now = DateTime.Now;
        var newEntryTitle = $"New Entry Test {now.Day}{now.Month}{now.Year}{now.Hour}{now.Minute}{now.Second}";
        var newEntryContent = NewEntryContentFor(now);

        await EnterForumTestCourseForumAsync();
        await ForumNavigationUtilities.NewEntryAsync(User, newEntryTitle, newEntryContent);

        var newEntry = await ForumNavigationUtilities.GetEntryAsync(User, newEntryTitle);
        var authorText = (await newEntry.Locator(Constants.ForumEntryListEntryUser).InnerTextAsync()).Trim();
        Assert.That(authorText, Is.EqualTo(userName), "Incorrect user");
        await newEntry.Locator(Constants.ForumEntryListEntryTitle).ClickAsync();

        await page.Locator(Constants.ForumCommentList).WaitForAsync();
        var entryTitleRow = page.Locator(Constants.ForumCommentListEntryTitle);
        var entryTitleText = await entryTitleRow.InnerTextAsync();
        Assert.That(entryTitleText.Split('\n')[0], Is.EqualTo(newEntryTitle), "Incorrect Entry Title");
        var entryAuthorText = (await entryTitleRow.Locator(Constants.ForumCommentListEntryUser).InnerTextAsync()).Trim();
        Assert.That(entryAuthorText, Is.EqualTo(userName), "Incorrect User for Entry");

        var comments = await ForumNavigationUtilities.GetCommentsAsync(User);
        Assert.That(comments, Is.Not.Empty, "No comments on the entry");
        var newComment = comments[0];
        var commentContent = (await newComment.Locator(Constants.ForumCommentListCommentContent).InnerTextAsync()).Trim();
        Assert.That(commentContent, Is.EqualTo(newEntryContent), "Bad content of comment");
        var commentAuthor = (await newComment.Locator(Constants.ForumCommentListCommentUser).InnerTextAsync()).Trim();
        Assert.That(commentAuthor, Is.EqualTo(userName), "Bad user in comment");

        // Navigate to the main page first to avoid a flaky logout
        await page.GotoAsync(AppUrl);
    }

    /// <summary>
    /// Adds a comment to the course forum's first entry (creating one first if none exist).
    /// Resources: loginservice(READONLY,10) openvidumock(NOACCESS,10) forum(READWRITE,1,exclusive)
    /// executor/webbrowser/webserver(READWRITE,1).
    /// </summary>
    [TestCaseSource(typeof(ParameterLoader), nameof(ParameterLoader.GetTestUsers))]
    public async Task ForumNewCommentTest(string mail, string password, string role)
    {
        var userName = await LoginHelper.SlowLoginAsync(User, mail, password);
        var page = User.Page;

        await EnterForumTestCourseForumAsync();
        var entry = await FirstEntryOrNewAsync("New Comment Test");
        await entry.Locator(Constants.ForumEntryListEntryTitle).ClickAsync();

        var commentList = page.Locator(Constants.ForumCommentList);
        await commentList.WaitForAsync();
        var numberCommentsOld = (await ForumNavigationUtilities.GetCommentsAsync(User)).Count;

        await commentList.Locator(Constants.ForumCommentListNewCommentIcon).ClickAsync();
        await page.Locator(Constants.ForumNewCommentModal).WaitForAsync();

        var now = DateTime.Now;
        var newCommentContent =
            $"COMMENT TEST{now.Day}{now.Month}{now.Year}{now.Hour}{now.Minute}{now.Second}. " +
            $"This is the comment written on the {now.Day} of {now:MMMM}, {now.Hour}:{now.Minute},{now.Second}";
        await page.Locator(Constants.ForumNewCommentModalTextField).FillAsync(newCommentContent);
        await page.Locator(Constants.ForumNewCommentModalPostButton).ClickAsync();

        await page.Locator(Constants.ForumCommentList).WaitForAsync();
        await User.WaitUntilAsync(
            () => page.Locator(Constants.ForumCommentListComment).First.WaitForAsync(), "The comment list are not visible");

        var comments = await PollHelper.PollUntilAsync(
            () => ForumNavigationUtilities.GetCommentsAsync(User),
            list => list.Count > numberCommentsOld);
        Assert.That(comments.Count, Is.GreaterThan(numberCommentsOld), "Comment list empty or only original comment");

        var commentFound = false;
        foreach (var comment in comments)
        {
            var text = await comment.Locator(Constants.ForumCommentListCommentContent).InnerTextAsync();
            if (text == newCommentContent)
            {
                commentFound = true;
                var author = (await comment.Locator(Constants.ForumCommentListCommentUser).InnerTextAsync()).Trim();
                Assert.That(author, Is.EqualTo(userName), "Bad user in comment");
            }
        }
        Assert.That(commentFound, Is.True, "Comment not found");
    }

    /// <summary>
    /// Replies to the first comment of the course forum's first entry.
    /// Resources: loginservice(READONLY,10) openvidumock(NOACCESS,10) forum(READWRITE,1,exclusive)
    /// executor/webbrowser/webserver(READWRITE,1).
    /// </summary>
    [TestCaseSource(typeof(ParameterLoader), nameof(ParameterLoader.GetTestUsers))]
    public async Task ForumNewReply2CommentTest(string mail, string password, string role)
    {
        var userName = await LoginHelper.SlowLoginAsync(User, mail, password);
        var page = User.Page;

        await EnterForumTestCourseForumAsync();
        var entry = await FirstEntryOrNewAsync("New Comment Test");
        await entry.Locator(Constants.ForumEntryListEntryTitle).ClickAsync();
        await page.Locator(Constants.ForumCommentList).WaitForAsync();

        var comments = await ForumNavigationUtilities.GetCommentsAsync(User);
        var comment = comments[0];
        await comment.Locator(Constants.ForumCommentListCommentReplyIcon).ClickAsync();

        var now = DateTime.Now;
        var newReplyContent = $"This is the reply written on the {now.Day} of {now:MMMM}, {now.Hour}:{now.Minute},{now.Second}";
        await page.Locator(Constants.ForumCommentListModalNewReply).WaitForAsync();
        await page.Locator(Constants.ForumCommentListModalNewReplyTextField).FillAsync(newReplyContent);
        await page.Locator(Constants.ForumNewCommentModalPostButton).ClickAsync();

        await page.Locator(Constants.ForumCommentListModalNewReply).WaitForAsync(new() { State = WaitForSelectorState.Hidden });
        await page.Locator(Constants.ForumCommentList).WaitForAsync();
        await page.Locator(Constants.ForumCommentListComment).First.WaitForAsync();

        comments = await ForumNavigationUtilities.GetCommentsAsync(User);
        var replies = await ForumNavigationUtilities.GetRepliesAsync(comments[0]);

        ILocator? newReply = null;
        foreach (var reply in replies)
        {
            var text = await reply.InnerTextAsync();
            if (text.Contains(newReplyContent, StringComparison.Ordinal))
            {
                newReply = reply;
            }
        }

        Assert.That(newReply, Is.Not.Null, "Reply not found");
        var replyAuthor = (await newReply!.Locator(Constants.ForumCommentListCommentUser).InnerTextAsync()).Trim();
        Assert.That(replyAuthor, Is.EqualTo(userName), "Bad user in comment");
    }
}
