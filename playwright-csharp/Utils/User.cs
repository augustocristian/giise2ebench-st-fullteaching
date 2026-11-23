namespace FullTeaching.E2E.Utils;

/// <summary>Test-data user record, ported from utils/User.java.</summary>
public record User(string Name, string Password, string Role)
{
    /// <summary>Whether the user's role equals <paramref name="role"/>, ignoring case and surrounding whitespace.</summary>
    public bool HasRole(string role) => Role.Trim().Equals(role, StringComparison.OrdinalIgnoreCase);
}
