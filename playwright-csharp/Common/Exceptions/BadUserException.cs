namespace FullTeaching.E2E.Common.Exceptions;

/// <summary>Thrown when the user logged into the application is not the expected one.</summary>
public class BadUserException : Exception
{
    public BadUserException() { }

    public BadUserException(string message) : base(message) { }

    public BadUserException(string message, Exception innerException) : base(message, innerException) { }
}
