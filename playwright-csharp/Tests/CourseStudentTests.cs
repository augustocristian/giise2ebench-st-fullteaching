using FullTeaching.E2E.Common;
using FullTeaching.E2E.Utils;
using NUnit.Framework;

namespace FullTeaching.E2E.Tests;

/// <summary>Ported from functional/test/student/CourseStudentTest.java.</summary>
[TestFixture]
public class CourseStudentTests : BaseTest
{
    /// <summary>
    /// Logs in as a student, opens the first course and checks every tab loads.
    /// Resources: course(READONLY,15) loginservice(READONLY,10) openvidumock(NOACCESS,10)
    /// executor/webbrowser/webserver(READWRITE,1).
    /// </summary>
    [TestCaseSource(typeof(ParameterLoader), nameof(ParameterLoader.GetTestStudents))]
    public async Task StudentCourseMainTest(string mail, string password, string role)
    {
        await LoginHelper.SlowLoginAsync(User, mail, password);
        var page = User.Page;

        await NavigationUtilities.ToCoursesHomeAsync(User);
        var courseList = await CourseNavigationUtilities.GetCoursesListAsync(User);
        Assert.That(courseList, Is.Not.Empty, "No courses available for test user");

        var course = await CourseNavigationUtilities.GetCourseByNameAsync(User, courseList[0]);
        await course.Locator(Constants.CourseTitle).ClickAsync();
        await page.Locator(Constants.CourseTabs).WaitForAsync();

        await CourseNavigationUtilities.Go2TabAsync(User, Constants.HomeIcon);
        await CourseNavigationUtilities.Go2TabAsync(User, Constants.SessionIcon);
        await CourseNavigationUtilities.Go2TabAsync(User, Constants.ForumIcon);
        await CourseNavigationUtilities.Go2TabAsync(User, Constants.FilesIcon);
        await CourseNavigationUtilities.Go2TabAsync(User, Constants.AttendersIcon);
    }
}
