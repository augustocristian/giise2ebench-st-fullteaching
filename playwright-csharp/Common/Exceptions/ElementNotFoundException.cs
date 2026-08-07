namespace FullTeaching.E2E.Common.Exceptions;

public class ElementNotFoundException : Exception
{
    public ElementNotFoundException() { }

    public ElementNotFoundException(string message) : base(message) { }
}
