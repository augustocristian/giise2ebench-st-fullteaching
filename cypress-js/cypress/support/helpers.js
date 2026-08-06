// Pure DOM helpers shared by the command files (jQuery in, plain values out).

/** Trimmed text of every `rowSelector` match in `$container`, found via `titleSelector`. */
function rowTitles($container, rowSelector, titleSelector) {
  return $container
    .find(rowSelector)
    .toArray()
    .map((row) => Cypress.$(row).find(titleSelector).text().trim());
}

/** The row element of `$container` whose title text equals `title` (undefined if none). */
function findRowByTitle($container, rowSelector, titleSelector, title) {
  return $container
    .find(rowSelector)
    .toArray()
    .find((row) => Cypress.$(row).find(titleSelector).text().trim() === title);
}

/**
 * Yields the row titled `title`, retrying until it appears (default command timeout).
 * `getContainer` is a function returning the Cypress chain for the container.
 */
function getRowByTitle(getContainer, rowSelector, titleSelector, title, label) {
  return getContainer()
    .should(($c) => {
      expect(rowTitles($c, rowSelector, titleSelector), `${label} "${title}" to be found`).to.include(title);
    })
    .then(($c) => cy.wrap(findRowByTitle($c, rowSelector, titleSelector, title)));
}

module.exports = { rowTitles, findRowByTitle, getRowByTitle };
