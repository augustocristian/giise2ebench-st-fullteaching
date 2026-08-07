namespace FullTeaching.E2E.Utils;

/// <summary>
/// CSV-backed user catalog, ported from utils/UserLoader.java.
/// `getSessionParameters()` (session_test_file.csv) is not ported: it's never called from
/// any test, in Java or here - the CSV is kept under Resources/ for parity only.
/// </summary>
public static class UserLoader
{
    // Resources/ is copied next to the test assembly by the .csproj, unlike Java's fragile
    // cwd-relative "src/test/resources/...".
    private static readonly string DefaultUserFile =
        Path.Combine(AppContext.BaseDirectory, "Resources", "Inputs", "default_user_file.csv");

    private static IReadOnlyList<User>? _users;

    public static User ParseUser(string csvLine)
    {
        var fields = csvLine.Trim().Split(',');
        return new User(fields[0], fields[1], fields[2]);
    }

    public static IReadOnlyList<User> GetAllUsers()
    {
        if (_users is not null)
        {
            return _users;
        }

        var users = new List<User>();
        foreach (var line in File.ReadLines(DefaultUserFile))
        {
            if (!string.IsNullOrWhiteSpace(line))
            {
                users.Add(ParseUser(line));
            }
        }
        _users = users;
        return _users;
    }
}
