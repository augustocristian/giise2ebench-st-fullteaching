using System.Collections;
using System.Diagnostics;

namespace FullTeaching.E2E.Common;

/// <summary>
/// Retries an arbitrary async computation until a predicate passes or a timeout elapses.
/// </summary>
/// <remarks>
/// Prefer Playwright's own auto-waiting (<c>locator.WaitForAsync()</c>, <c>Expect(locator).ToXxxAsync()</c>)
/// whenever the condition is about a single locator: it is retried natively and reports the
/// locator on failure. This helper only covers conditions Playwright cannot express, such as
/// "the list of chat lines contains a line matching a computed predicate", mirroring
/// wait.poll_until (Python) / wait.pollUntil (Cypress) in the sibling ports.
/// </remarks>
public static class PollHelper
{
    private const int IntervalMs = 200;

    /// <summary>
    /// Evaluates <paramref name="factory"/> repeatedly until <paramref name="predicate"/> accepts its result.
    /// Exceptions thrown by the factory (or the predicate) are treated as "not yet" and retried,
    /// except cancellation. The factory always runs at least once.
    /// </summary>
    /// <param name="factory">Produces the value to check, typically by querying the page.</param>
    /// <param name="predicate">Condition the value has to satisfy.</param>
    /// <param name="timeoutMs">Overall timeout; defaults to <see cref="TestConfig.ShortTimeoutMs"/>.</param>
    /// <param name="description">What is being awaited, included in the timeout message.</param>
    /// <param name="cancellationToken">Aborts the wait early.</param>
    /// <returns>The first value accepted by the predicate.</returns>
    /// <exception cref="TimeoutException">The condition was not met in time; carries the last error, if any, as inner exception.</exception>
    public static async Task<T> PollUntilAsync<T>(
        Func<Task<T>> factory,
        Func<T, bool> predicate,
        int? timeoutMs = null,
        string? description = null,
        CancellationToken cancellationToken = default)
    {
        ArgumentNullException.ThrowIfNull(factory);
        ArgumentNullException.ThrowIfNull(predicate);

        var timeout = timeoutMs ?? TestConfig.ShortTimeoutMs;
        var clock = Stopwatch.StartNew();
        T? last = default;
        var hasLast = false;
        Exception? lastError = null;

        do
        {
            cancellationToken.ThrowIfCancellationRequested();
            try
            {
                last = await factory();
                hasLast = true;
                if (predicate(last))
                {
                    return last;
                }
                lastError = null;
            }
            catch (Exception ex) when (ex is not OperationCanceledException)
            {
                lastError = ex;
            }

            var remaining = timeout - (int)clock.ElapsedMilliseconds;
            if (remaining > 0)
            {
                await Task.Delay(Math.Min(IntervalMs, remaining), cancellationToken);
            }
        }
        while (clock.ElapsedMilliseconds < timeout);

        var message = $"Condition{(description is null ? string.Empty : $" '{description}'")} not met within {timeout}ms";
        if (lastError is not null)
        {
            message += $": {lastError.Message}";
        }
        else if (hasLast)
        {
            message += $". Last value: {Describe(last)}";
        }
        throw new TimeoutException(message, lastError);
    }

    private static string Describe(object? value) => value switch
    {
        null => "<null>",
        string text => $"\"{text}\"",
        IEnumerable items => "[" + string.Join(", ", items.Cast<object?>().Take(20).Select(Describe)) + "]",
        _ => value.ToString() ?? "<null>",
    };
}
