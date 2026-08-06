const js = require("@eslint/js");
const cypress = require("eslint-plugin-cypress");

module.exports = [
  js.configs.recommended,
  {
    files: ["cypress/**/*.js", "*.js"],
    languageOptions: {
      ecmaVersion: 2023,
      sourceType: "commonjs",
      globals: {
        require: "readonly",
        module: "readonly",
        process: "readonly",
        __dirname: "readonly",
      },
    },
  },
  {
    files: ["cypress/e2e/**/*.js", "cypress/support/**/*.js"],
    ...cypress.configs.recommended,
  },
  {
    ignores: ["node_modules/**", "cypress/downloads/**", "cypress/screenshots/**", "cypress/videos/**"],
  },
];
