namespace FullTeaching.E2E.Common.Exceptions;

public class NotLoggedException : Exception
{
    public NotLoggedException() { }

    public NotLoggedException(string message) : base(message) { }
}
