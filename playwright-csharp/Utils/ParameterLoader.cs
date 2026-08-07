using NUnit.Framework;

namespace FullTeaching.E2E.Utils;

/// <summary>
/// NUnit [TestCaseSource] data providers, ported from utils/ParameterLoader.java. NUnit's
/// TestCaseSource is the closest 1:1 match of any of the sibling ports to JUnit's
/// @ParameterizedTest + @MethodSource - same "static method returning test data" shape.
/// </summary>
public static class ParameterLoader
{
    public static IEnumerable<TestCaseData> GetTestUsers() =>
        UserLoader.GetAllUsers().Select(ToTestCase);

    public static IEnumerable<TestCaseData> GetTestStudents() =>
        UserLoader.GetAllUsers().Where(u => IsStudent(u) && !IsTeacher(u)).Select(ToTestCase);

    public static IEnumerable<TestCaseData> GetTestTeachers() =>
        UserLoader.GetAllUsers().Where(u => IsTeacher(u) && !IsStudent(u)).Select(ToTestCase);

    private static bool IsStudent(User user) => user.Role.Trim().Equals("STUDENT", StringComparison.OrdinalIgnoreCase);

    private static bool IsTeacher(User user) => user.Role.Trim().Equals("TEACHER", StringComparison.OrdinalIgnoreCase);

    private static TestCaseData ToTestCase(User user) =>
        new TestCaseData(user.Name, user.Password, user.Role).SetName($"{{m}}({user.Role}_{user.Name})");
}
