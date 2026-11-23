// Registers every custom command (Cypress auto-loads support/e2e.js, which requires this).
// One file per feature area under ./commands; see SUPPORT_API.md for the preferred API.
require("./commands/auth");
require("./commands/dialogs");
require("./commands/user");
require("./commands/courses");
require("./commands/forum");
require("./commands/sessions");
require("./commands/spider");
