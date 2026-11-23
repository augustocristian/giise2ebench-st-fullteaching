// Test-data providers
// Specs iterate these arrays at load time (`getTestUsers().forEach((u) => it(...))`),
// the Mocha equivalent of JUnit's @MethodSource.

const users = require("../fixtures/users.json");

const hasRole = (user, role) => user.role.trim().toUpperCase() === role;

/** All users from fixtures/users.json. */
const getTestUsers = () => users;

/** Users whose role is exactly STUDENT. */
const getTestStudents = () => users.filter((u) => hasRole(u, "STUDENT") && !hasRole(u, "TEACHER"));

/** Users whose role is exactly TEACHER. */
const getTestTeachers = () => users.filter((u) => hasRole(u, "TEACHER") && !hasRole(u, "STUDENT"));

module.exports = { getTestUsers, getTestStudents, getTestTeachers };
