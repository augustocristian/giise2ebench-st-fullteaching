// Link crawler used by the spider tests.
//
// Deviation from the Java version: instead of collecting {href: OK|KO} and asserting no KO at
// the end, a link that does not lead to a page with the footer fails the cy.get(footer)
// assertion right there, and Cypress's error already names the link and page.

const { common } = require("../selectors");

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
    cy.get(common.footer).should("exist");

    cy.get("a").then(($anchors) => {
      const nested = sameOriginHrefs($anchors, host).filter((h) => !explored.has(h));
      crawlLevel(host, nested, explored, remainingDepth - 1);
    });

    cy.visit(cameFrom);
    cy.get(common.footer).should("exist");
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
