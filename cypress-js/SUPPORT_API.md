# Support API (cypress/support)

All previously exported names keep working. Preferred additions below.

## Layout
- `support/selectors.js` - CSS selectors grouped by feature: `common, modal, login, settings, course, tabs, forum, session, attenders`
  (e.g. `const { course, forum } = require("../support/selectors")`; `course.newButton`, `forum.newEntryModal.title`, `modal.closed(id)`).
- `support/constants.js` - data constants (names, depth, URLs) plus the old flat selector names (kept for compatibility; prefer `selectors.js`).
- `support/testData.js` - `getTestUsers()`, `getTestStudents()`, `getTestTeachers()` (unchanged).
- `support/helpers.js` - internal DOM helpers (`rowTitles`, `findRowByTitle`, `getRowByTitle`).
- `support/commands/{auth,dialogs,user,courses,forum,sessions,spider}.js` - custom commands, one file per feature.

## New command
- `cy.login(email, password)` - log in via the login modal, yields the user's display name. Waits for the login button to be enabled.

## Unchanged commands (same signatures)
`logout()`, `openDialog(selectorOrElement)`, `waitForDialogClosed(dialogId, msg)`, `getUserName({goBack})`, `checkLogin(email)`, `checkLogOut()`,
`toCoursesHome()`, `newCourse(name)`, `courseExists(t)`, `assertCourseExists(t, opts)`, `assertCourseNotExists(t, opts)`, `getCourseByName(n)`,
`changeCourseName(old, new)`, `deleteCourse(n)`, `getCoursesList()`, `go2Tab(iconSel)`, `getTabContent(iconSel)`, `isUserInAttendersList(name)`,
`getHighlightedAttender()`, `isForumEnabled($content)`, `getFullEntryList()`, `getUserEntries(user)`, `getEntry(title)`, `getComments()`,
`getUserComments(user)`, `getReplies(comment)`, `newEntry(title, content)`, `enableForum()`, `disableForum()`, `getFullSessionList()`, `getSession(title)`,
`getPageLinks(host)`, `crawlSameOriginLinks(host, depth)`.

## Notes
- Prefer `.should()`/retrying queries over `cy.wait`; commands here never use fixed waits.
- The `{ timeout: 20000 }` options on these commands were dropped: it equals `defaultCommandTimeout` in `cypress.config.js`.
- `cy.session` was not adopted for login: specs exercise the login UI itself and `afterEach` logs out.
