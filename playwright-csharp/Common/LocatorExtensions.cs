using System.Text.RegularExpressions;
using Microsoft.Playwright;

namespace FullTeaching.E2E.Common;

/// <summary>Small <see cref="ILocator"/> helpers shared by the navigation utilities.</summary>
public static class LocatorExtensions
{
    /// <summary>
    /// Pattern matching an element whose whole text equals <paramref name="text"/>, ignoring
    /// leading/trailing whitespace (the retrying equivalent of <c>InnerText.Trim() == text</c>).
    /// </summary>
    public static Regex ExactText(string text)
    {
        ArgumentNullException.ThrowIfNull(text);
        return new Regex($@"^\s*{Regex.Escape(text.Trim())}\s*$");
    }

    /// <summary>
    /// Returns the trimmed inner text of <paramref name="childSelector"/> inside each row of
    /// <paramref name="rows"/>, in DOM order.
    /// </summary>
    public static async Task<IReadOnlyList<string>> ChildTextsAsync(this ILocator rows, string childSelector)
    {
        ArgumentNullException.ThrowIfNull(rows);
        var items = await rows.AllAsync();
        var texts = new List<string>(items.Count);
        foreach (var item in items)
        {
            texts.Add((await item.Locator(childSelector).InnerTextAsync()).Trim());
        }
        return texts;
    }

    /// <summary>
    /// Returns the first row of <paramref name="rows"/> whose <paramref name="childSelector"/> text
    /// equals <paramref name="text"/> (trimmed), or <see langword="null"/> when there is none.
    /// One-shot: it does not wait for the row to appear.
    /// </summary>
    public static async Task<ILocator?> FindRowByChildTextAsync(this ILocator rows, string childSelector, string text)
    {
        ArgumentNullException.ThrowIfNull(rows);
        var items = await rows.AllAsync();
        foreach (var item in items)
        {
            var candidate = (await item.Locator(childSelector).InnerTextAsync()).Trim();
            if (candidate == text)
            {
                return item;
            }
        }
        return null;
    }
}
