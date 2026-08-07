namespace FullTeaching.E2E.Common;

/// <summary>
/// Retries an arbitrary async computation until a predicate passes or a timeout elapses.
/// Playwright's <c>Expect(ILocator)</c> assertions auto-retry natively for simple
/// visibility/count/text conditions on a single locator, but (unlike Cypress's
/// <c>cy.get().should(callback)</c>) there is no built-in way to retry an arbitrary
/// multi-element computation (e.g. "does this list of course titles contain X") in
/// Playwright .NET - this fills that one gap, mirroring wait.poll_until (Python) /
/// wait.pollUntil (Cypress) in the sibling ports.
/// </summary>
public static class PollHelper
{
    private const int DefaultTimeoutMs = 20000;
    private const int IntervalMs = 200;

    public static async Task<T> PollUntilAsync<T>(
        Func<Task<T>> factory, Func<T, bool> predicate, int? timeoutMs = null)
    {
        var deadline = DateTime.UtcNow.AddMilliseconds(timeoutMs ?? DefaultTimeoutMs);
        T last = default!;
        Exception? lastError = null;
        while (DateTime.UtcNow < deadline)
        {
            try
            {
                last = await factory();
                if (predicate(last))
                {
                    return last;
                }
            }
            catch (Exception ex)
            {
                lastError = ex;
            }
            await Task.Delay(IntervalMs);
        }
        throw new TimeoutException(
            $"Condition not met within {timeoutMs ?? DefaultTimeoutMs}ms" +
            (lastError != null ? $": {lastError.Message}" : string.Empty));
    }
}
