namespace FullTeaching.E2E.Common.Exceptions;

public class BadUserException : Exception
{
    public BadUserException() { }

    public BadUserException(string message) : base(message) { }
}
