using FullTeaching.E2E.Common;
using FullTeaching.E2E.Utils;
using NUnit.Framework;
using static Microsoft.Playwright.Assertions;

namespace FullTeaching.E2E.Tests;

/// <summary>Ported from functional/test/student/CourseStudentTest.java.</summary>
[TestFixture]
[Category("Course")]
[Category("Student")]
public class CourseStudentTests : BaseTest
{
    private const string ListItem = "li";

    /// <summary>
    /// Logs in as a student, opens the first course and checks every tab loads.
    /// Resources: course(READONLY,15) loginservice(READONLY,10) openvidumock(NOACCESS,10)
    /// executor/webbrowser/webserver(READWRITE,1).
    /// </summary>
    [TestCaseSource(typeof(ParameterLoader), nameof(ParameterLoader.GetTestStudents))]
    [Description("A student can open the first course and every one of its tabs loads.")]
    public async Task StudentCourseMainTest(string mail, string password, string role)
    {
        await LoginHelper.SlowLoginAsync(User, mail, password);
        await NavigationUtilities.ToCoursesHomeAsync(User);

        var firstCourse = User.Page.Locator(Constants.CourseList).Locator(ListItem).First;
        await Expect(firstCourse, "No courses available for test user").ToBeVisibleAsync();
        await firstCourse.Locator(Constants.CourseTitle).ClickAsync();
        await Expect(User.Page.Locator(Constants.CourseTabs)).ToBeVisibleAsync();

        await CourseTestSupport.VisitEveryTabAsync(User);
    }
}
