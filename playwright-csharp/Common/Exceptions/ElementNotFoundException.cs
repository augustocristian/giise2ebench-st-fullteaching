namespace FullTeaching.E2E.Common.Exceptions;

/// <summary>Thrown when a page element a helper was asked to find does not exist.</summary>
public class ElementNotFoundException : Exception
{
    public ElementNotFoundException() { }

    public ElementNotFoundException(string message) : base(message) { }

    public ElementNotFoundException(string message, Exception innerException) : base(message, innerException) { }
}
