// Course/tab navigation commands, ported from common/CourseNavigationUtilities.java.
//
// Where the Java source has both a one-shot `checkIfCourseExists(wd, title)` and a manually
// retried `checkIfCourseExists(wd, title, retries)` overload, this splits into a one-shot
// query (`cy.courseExists`) plus retrying assertions (`cy.assertCourseExists` /
// `cy.assertCourseNotExists`) built on `cy.get().should(callback)`, which Cypress retries
// natively until the default command timeout - no manual sleep/retry loop needed.

const constants = require("./constants");

function courseTitlesIn($list) {
  return $list
    .find("li")
    .toArray()
    .map((li) => Cypress.$(li).find(constants.COURSE_TITLE).text().trim());
}

Cypress.Commands.add("toCoursesHome", () => {
  cy.location("pathname").then((pathname) => {
    if (!pathname.endsWith("/courses")) {
      cy.log("Click into the CoursesButton");
      cy.get(constants.COURSES_BUTTON).should("exist").click();
      cy.get(constants.COURSES_DASHBOARD_TITLE).should("exist");
    } else {
      cy.log("The user was already in the Course Tab");
    }
  });
});

Cypress.Commands.add("newCourse", (courseName) => {
  cy.toCoursesHome();
  cy.log("Checking existing courses...");
  cy.get(".course-list-item").should("be.visible");
  cy.get(constants.NEW_COURSE_BUTTON).should("exist").click({ force: true });
  cy.get(constants.NEW_COURSE_MODAL).should("be.visible");

  cy.log(`Introducing Course Name: ${courseName}`);
  cy.get(constants.NEW_COURSE_MODAL_NAME_FIELD).should("be.visible").type(courseName);
  cy.get(constants.NEW_COURSE_MODAL_SAVE).click();

  cy.assertCourseExists(courseName);
  return cy.wrap(courseName);
});

// One-shot check, mirrors CourseNavigationUtilities.checkIfCourseExists(wd, title).
Cypress.Commands.add("courseExists", (courseTitle) => {
  return cy.get(constants.COURSE_LIST).then(($list) => courseTitlesIn($list).includes(courseTitle));
});

// Retrying assertions, mirror the two-argument and three-argument (with retries) Java overloads.
Cypress.Commands.add("assertCourseExists", (courseTitle, options = {}) => {
  cy.get(constants.COURSE_LIST, options).should(($list) => {
    expect(courseTitlesIn($list), `course "${courseTitle}" to exist`).to.include(courseTitle);
  });
});

Cypress.Commands.add("assertCourseNotExists", (courseTitle, options = {}) => {
  cy.get(constants.COURSE_LIST, options).should(($list) => {
    expect(courseTitlesIn($list), `course "${courseTitle}" not to exist`).to.not.include(courseTitle);
  });
});

function openEditCourseModal(courseTitle) {
  cy.getCourseByName(courseTitle).find(constants.EDIT_COURSE_BUTTON).click();
  cy.get(constants.EDIT_DELETE_MODAL).should("be.visible");
}

Cypress.Commands.add("changeCourseName", (oldName, newName) => {
  cy.log(`[INI] changeCourseName(${oldName}=>${newName})`);
  cy.get(constants.COURSE_LIST).should("be.visible");
  openEditCourseModal(oldName);

  cy.log("Changing the course Name");
  cy.get(constants.EDIT_COURSE_MODAL_NAME_FIELD).should("be.visible").clear();
  cy.get(constants.EDIT_COURSE_MODAL_NAME_FIELD).type(newName);
  cy.log("Click save button, saving changes...");
  cy.get(constants.EDIT_COURSE_MODAL_SAVE).click();
  cy.get(constants.EDIT_DELETE_MODAL).should("not.exist");
  cy.log("[END] changeCourseName OK");
});

Cypress.Commands.add("deleteCourse", (courseName) => {
  cy.log(`[INI] deleteCourse(${courseName})`);
  cy.toCoursesHome();
  cy.get(constants.COURSE_LIST)
    .find("li")
    .its("length")
    .then((numCoursesInitial) => {
      openEditCourseModal(courseName);

      cy.log("Enabling delete course");
      cy.get(constants.EDIT_COURSE_DELETE_CHECK).should("be.visible").click();
      cy.log("Click delete Course");
      cy.get(constants.EDIT_COURSE_DELETE_BUTTON).should("be.visible").click();
      cy.get(constants.EDIT_COURSE_MODAL_SAVE).click();

      cy.log(`Checking that after removing the course, the number of courses is ${numCoursesInitial} minus one`);
      cy.get(constants.COURSE_LIST)
        .find("li")
        .should("have.length", numCoursesInitial - 1);
    });
  cy.log(`[END] deleteCourse OK: Course "${courseName}"`);
});

Cypress.Commands.add("getCoursesList", () => {
  cy.toCoursesHome();
  return cy.get(constants.COURSE_LIST).then(($list) => courseTitlesIn($list));
});

// Yields the <li> element for the course with the given title, mirrors
// CourseNavigationUtilities.getCourseByName; retries (like Wait.notTooMuch) until found.
Cypress.Commands.add("getCourseByName", (name) => {
  cy.log("Finding the newly created course");
  return cy
    .get(constants.COURSE_LIST, { timeout: 20000 })
    .should(($list) => {
      const match = courseTitlesIn($list).includes(name);
      expect(match, `course "${name}" to be found`).to.be.true;
    })
    .then(($list) => {
      const li = $list.find("li").toArray().find((el) => Cypress.$(el).find(constants.COURSE_TITLE).text().trim() === name);
      return cy.wrap(li);
    });
});

function tabElementFromIcon(iconSelector) {
  return cy.get(constants.COURSE_TABS).find(iconSelector).parent().parent();
}

Cypress.Commands.add("go2Tab", (iconSelector) => {
  tabElementFromIcon(iconSelector).then(($tab) => {
    const tabId = $tab.attr("id");
    cy.log(`Navigating to tab with id: ${tabId}`);
    cy.wrap($tab).click();
    const contentId = tabId.replace("label", "content");
    cy.get(`#${contentId}`, { timeout: 4000 }).should("be.visible");
  });
});

Cypress.Commands.add("getTabContent", (iconSelector) => {
  cy.log("Get Tab content");
  return tabElementFromIcon(iconSelector)
    .invoke("attr", "id")
    .then((tabId) => cy.get(`#${tabId.replace("label", "content")}`));
});

Cypress.Commands.add("isUserInAttendersList", (userName) => {
  cy.get(constants.ATTENDERS_ICON).should("be.visible");
  cy.getTabContent(constants.ATTENDERS_ICON);
  return cy.get(constants.ATTENDERS_LIST_ROWS).then(($rows) => {
    if ($rows.length === 0) {
      throw new Error("isUserInAttendersList - attenders list is empty");
    }
    return $rows
      .toArray()
      .some((row) => userName.trim().toLowerCase() === Cypress.$(row).text().trim().toLowerCase());
  });
});

Cypress.Commands.add("getHighlightedAttender", () => {
  cy.log("[INI] getHighlightedAttender");
  return cy.getTabContent(constants.ATTENDERS_ICON).then(($content) => {
    const $highlighted = $content.find(constants.ATTENDERS_LIST_HIGHLIGHTED_ROW);
    if ($highlighted.length === 0) {
      throw new Error("getHighlightedAttender - no highlighted user");
    }
    return $highlighted.first().text().trim();
  });
});
