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

    private static readonly Lazy<IReadOnlyList<User>> Users = new(() => Load(DefaultUserFile));

    /// <summary>Parses a <c>name,password,role[,...]</c> CSV line.</summary>
    /// <exception cref="FormatException">The line has fewer than three fields.</exception>
    public static User ParseUser(string csvLine)
    {
        ArgumentNullException.ThrowIfNull(csvLine);
        var fields = csvLine.Trim().Split(',');
        if (fields.Length < 3)
        {
            throw new FormatException($"Invalid user line '{csvLine}': expected 'name,password,role[,...]'.");
        }
        return new User(fields[0], fields[1], fields[2]);
    }

    /// <summary>All users of the default catalog (<c>Resources/Inputs/default_user_file.csv</c>), loaded once.</summary>
    public static IReadOnlyList<User> GetAllUsers() => Users.Value;

    private static List<User> Load(string path) =>
        File.ReadLines(path)
            .Where(line => !string.IsNullOrWhiteSpace(line))
            .Select(ParseUser)
            .ToList();
}
