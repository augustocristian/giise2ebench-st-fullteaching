// Test-data providers, ported from utils/UserLoader.java + utils/ParameterLoader.java.
//
// Java exposes these as JUnit `@MethodSource` streams; the Mocha/Cypress idiom is a plain
// array that spec files iterate directly with `.forEach(user => it(...))` to generate cases -
// there is no parametrize decorator, so this is called at module-load time, not per-test.
//
// `getSessionParameters()` (UserLoader.java) is not ported: it reads session_test_file.csv
// (kept in fixtures/ for parity) but is never called from any test, in Java or here.

const users = require("../fixtures/users.json");

function isStudent(user) {
  return user.role.trim().toUpperCase() === "STUDENT";
}

function isTeacher(user) {
  return user.role.trim().toUpperCase() === "TEACHER";
}

function getTestUsers() {
  return users;
}

function getTestStudents() {
  return users.filter((u) => isStudent(u) && !isTeacher(u));
}

function getTestTeachers() {
  return users.filter((u) => isTeacher(u) && !isStudent(u));
}

module.exports = { getTestUsers, getTestStudents, getTestTeachers };
