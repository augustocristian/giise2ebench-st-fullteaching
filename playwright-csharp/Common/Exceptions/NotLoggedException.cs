namespace FullTeaching.E2E.Common.Exceptions;

/// <summary>Thrown when an operation requires a logged-in user but the session is not authenticated.</summary>
public class NotLoggedException : Exception
{
    public NotLoggedException() { }

    public NotLoggedException(string message) : base(message) { }

    public NotLoggedException(string message, Exception innerException) : base(message, innerException) { }
}
