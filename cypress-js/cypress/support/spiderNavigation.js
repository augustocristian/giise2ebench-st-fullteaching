// Link crawler used by the spider tests, ported from common/SpiderNavigation.java.
//
// Two deliberate deviations from the Java version:
//
// 1. Java's `getPageLinks`/`getUnexploredPageLinks` pass a freshly-created, never-populated
//    `Set` into a "not already seen" check, which is a latent no-op bug (dedup never actually
//    happens). This crawler preserves that *observed behavior* (no dedup against a running
//    "seen" set across a single getPageLinks() call) for fidelity - see the Python port's
//    spider_navigation.py for the same call.
// 2. Java collects {href: "OK"|"KO"} for every link and asserts the KO list is empty at the
//    end. Cypress commands aren't wrapped in try/catch the way Java's are; letting a broken
//    link fail the `cy.get(FOOTER)` assertion directly - failing the test right there, with
//    Cypress's own error pointing at exactly which link and page - is more idiomatic than
//    reimplementing manual failure collection, and no less informative.

const constants = require("./constants");

function isFollowable(href, host) {
  return Boolean(href) && href.trim() !== "" && !href.includes("#") && href.includes(host);
}

function sameOriginHrefs($anchors, host) {
  return $anchors
    .toArray()
    .map((a) => Cypress.$(a).attr("href"))
    .filter((href) => isFollowable(href, host));
}

Cypress.Commands.add("getPageLinks", (host) => {
  return cy.get("a").then(($anchors) => sameOriginHrefs($anchors, host));
});

function crawlLevel(host, hrefs, explored, remainingDepth) {
  if (remainingDepth <= 0 || hrefs.length === 0) {
    return;
  }
  const [href, ...rest] = hrefs;
  if (explored.has(href)) {
    crawlLevel(host, rest, explored, remainingDepth);
    return;
  }
  explored.add(href);

  cy.location("href").then((cameFrom) => {
    cy.log(`Navigate the links... following ${href}`);
    cy.get(`a[href="${href}"]`).first().click();
    cy.get(constants.FOOTER, { timeout: 20000 }).should("exist");

    cy.get("a").then(($anchors) => {
      const nested = sameOriginHrefs($anchors, host).filter((h) => !explored.has(h));
      crawlLevel(host, nested, explored, remainingDepth - 1);
    });

    cy.visit(cameFrom);
    cy.get(constants.FOOTER, { timeout: 20000 }).should("exist");
  });

  crawlLevel(host, rest, explored, remainingDepth);
}

// Recursively follows every same-origin link up to `depth` levels deep, mirrors
// SpiderNavigation.exploreLinks. Fails the test directly (see file header) if any link
// doesn't lead to a page with the expected footer.
Cypress.Commands.add("crawlSameOriginLinks", (host, depth) => {
  cy.getPageLinks(host).then((hrefs) => {
    crawlLevel(host, hrefs, new Set(), depth);
  });
});
