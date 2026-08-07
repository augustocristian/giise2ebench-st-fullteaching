using NUnit.Framework;

namespace FullTeaching.E2E.Utils;

/// <summary>
/// NUnit [TestCaseSource] data providers, ported from utils/ParameterLoader.java. NUnit's
/// TestCaseSource is the closest 1:1 match of any of the sibling ports to JUnit's
/// @ParameterizedTest + @MethodSource - same "static method returning test data" shape.
/// Every case carries (name, password, role).
/// </summary>
public static class ParameterLoader
{
    /// <summary>All users of the catalog.</summary>
    public static IEnumerable<TestCaseData> GetTestUsers() =>
        UserLoader.GetAllUsers().Select(ToTestCase);

    /// <summary>Users that are students and not teachers.</summary>
    public static IEnumerable<TestCaseData> GetTestStudents() =>
        UserLoader.GetAllUsers().Where(u => u.HasRole("STUDENT") && !u.HasRole("TEACHER")).Select(ToTestCase);

    /// <summary>Users that are teachers and not students.</summary>
    public static IEnumerable<TestCaseData> GetTestTeachers() =>
        UserLoader.GetAllUsers().Where(u => u.HasRole("TEACHER") && !u.HasRole("STUDENT")).Select(ToTestCase);

    private static TestCaseData ToTestCase(User user) =>
        new TestCaseData(user.Name, user.Password, user.Role).SetName($"{{m}}({user.Role}_{user.Name})");
}
