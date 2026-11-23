// Course dashboard and course-tab commands.
//
// Existence checks come in two flavours: a one-shot query (cy.courseExists) and retrying
// assertions (cy.assertCourseExists / cy.assertCourseNotExists) built on
// cy.get().should(callback), which Cypress retries natively - no manual sleep/retry loop.

const { common, course, tabs, attenders } = require("../selectors");
const { rowTitles, getRowByTitle } = require("../helpers");

const courseTitlesIn = ($list) => rowTitles($list, "li", course.title);
const courseListChain = () => cy.get(course.list);

// Tab labels and contents have paired ids: "...label..." <-> "...content...".
const tabLabel = (iconSelector) => cy.get(tabs.container).find(iconSelector).parent().parent();

/** Navigates to the courses dashboard unless already there. */
Cypress.Commands.add("toCoursesHome", () => {
  cy.location("pathname").then((pathname) => {
    if (!pathname.endsWith("/courses")) {
      cy.get(common.coursesButton).should("exist").click();
      cy.get(course.dashboardTitle).should("exist");
    }
  });
});

/** Creates a course named `courseName`; yields the name. */
Cypress.Commands.add("newCourse", (courseName) => {
  cy.toCoursesHome();
  cy.get(course.listItem).should("be.visible");
  cy.get(course.newButton).should("exist").click({ force: true });
  cy.get(course.newModal).should("be.visible");
  cy.get(course.newNameField).should("be.visible").type(courseName, { force: true });
  cy.get(course.newSave).click();

  cy.assertCourseExists(courseName);
  return cy.wrap(courseName);
});

/** Yields true/false: is a course titled `courseTitle` currently listed (one-shot, no retry). */
Cypress.Commands.add("courseExists", (courseTitle) => {
  return courseListChain().then(($list) => courseTitlesIn($list).includes(courseTitle));
});

/** Retrying assertion: the course is listed. `options` go to cy.get (e.g. timeout). */
Cypress.Commands.add("assertCourseExists", (courseTitle, options = {}) => {
  cy.get(course.list, options).should(($list) => {
    expect(courseTitlesIn($list), `course "${courseTitle}" to exist`).to.include(courseTitle);
  });
});

/** Retrying assertion: the course is not listed. */
Cypress.Commands.add("assertCourseNotExists", (courseTitle, options = {}) => {
  cy.get(course.list, options).should(($list) => {
    expect(courseTitlesIn($list), `course "${courseTitle}" not to exist`).to.not.include(courseTitle);
  });
});

/** Yields the <li> of the course titled `name`; retries until found. */
Cypress.Commands.add("getCourseByName", (name) => {
  return getRowByTitle(courseListChain, "li", course.title, name, "course");
});

function openEditCourseModal(courseTitle) {
  cy.getCourseByName(courseTitle).find(course.editButton).click();
  cy.get(course.editModal).should("be.visible");
}

/** Renames a course through the edit modal. */
Cypress.Commands.add("changeCourseName", (oldName, newName) => {
  courseListChain().should("be.visible");
  openEditCourseModal(oldName);
  cy.get(course.editNameField).should("be.visible").clear({ force: true });
  cy.get(course.editNameField).type(newName, { force: true });
  cy.get(course.editSave).click();
  cy.get(course.editModal).should("not.be.visible");
});

/** Deletes a course and asserts the course count dropped by one. */
Cypress.Commands.add("deleteCourse", (courseName) => {
  cy.toCoursesHome();
  courseListChain()
    .find("li")
    .its("length")
    .then((initialCount) => {
      openEditCourseModal(courseName);
      cy.get(course.deleteCheck).should("be.visible").click();
      cy.get(course.deleteButton).should("be.visible").click();
      cy.get(course.editSave).click();
      courseListChain().find("li").should("have.length", initialCount - 1);
    });
});

/** Yields the titles of all listed courses. */
Cypress.Commands.add("getCoursesList", () => {
  cy.toCoursesHome();
  return courseListChain().then(($list) => courseTitlesIn($list));
});

/** Clicks the course tab identified by its icon selector and waits for its content. */
Cypress.Commands.add("go2Tab", (iconSelector) => {
  tabLabel(iconSelector).then(($tab) => {
    const contentId = $tab.attr("id").replace("label", "content");
    cy.wrap($tab).click();
    cy.get(`#${contentId}`).should("be.visible");
  });
});

/** Yields the content element of the course tab identified by its icon selector. */
Cypress.Commands.add("getTabContent", (iconSelector) => {
  return tabLabel(iconSelector)
    .invoke("attr", "id")
    .then((tabId) => cy.get(`#${tabId.replace("label", "content")}`));
});

/** Yields true/false: is `userName` (case-insensitive) in the Attenders tab. Fails if the list is empty. */
Cypress.Commands.add("isUserInAttendersList", (userName) => {
  cy.get(tabs.attendersIcon).should("be.visible");
  cy.getTabContent(tabs.attendersIcon);
  return cy.get(attenders.rows).then(($rows) => {
    expect($rows.length, "attenders list is not empty").to.be.greaterThan(0);
    const wanted = userName.trim().toLowerCase();
    return $rows.toArray().some((row) => Cypress.$(row).text().trim().toLowerCase() === wanted);
  });
});

/** Yields the name of the highlighted attender (the one currently holding the turn). */
Cypress.Commands.add("getHighlightedAttender", () => {
  return cy.getTabContent(tabs.attendersIcon).then(($content) => {
    const $highlighted = $content.find(attenders.highlightedRow);
    expect($highlighted.length, "a highlighted attender").to.be.greaterThan(0);
    return $highlighted.first().text().trim();
  });
});
