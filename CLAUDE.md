# giise2ebench-st-fullteaching

## IRON RULE

**Before doing any work in this repository, run the setup script:**

- Linux/macOS: `./setup-sut.sh`
- Windows: `.\setup-sut.ps1`

This clones [retorch-st-fullteaching](https://github.com/giis-uniovi/retorch-st-fullteaching)
and populates two gitignored folders at the repo root: `sut/` and `selenium-java/`.
**Neither folder exists after a fresh `git clone` of this repo** — they are fetched
on demand and are never committed. Any task that touches the application code, the
test suite, or the RETORCH configuration is impossible until the script has been run.
If those folders are missing, run the script first — do not try to work around their
absence, and do not assume a previous session already fetched them.

## What this repo is

A benchmark wrapper around the RETORCH FullTeaching System Test suite. This repo
itself only holds the setup/deploy scripts, `docs/` (functional requirements),
`.gitignore`, and this file; the actual application and tests live upstream at
[giis-uniovi/retorch-st-fullteaching](https://github.com/giis-uniovi/retorch-st-fullteaching)
and are pulled in locally by `setup-sut.sh` / `setup-sut.ps1`.

Upstream, that repo is a detached fork of
[FullTeaching](https://github.com/elastest/full-teaching) (an OpenVidu-based
educational video-conferencing platform, originally an ElasTest EU Project
demonstrator), instrumented with the
[RETORCH](https://github.com/giis-uniovi/retorch) scheduling framework and a
Selenium/Java end-to-end test suite.

## Layout after running the setup script

```
.
├── sut/                    # System Under Test: the FullTeaching web app
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── pom.xml
│   └── src/                # FullTeaching application source
├── selenium-java/          # Everything else from upstream: the E2E test suite
│   ├── .retorch/            # RETORCH scheduling configuration (TJOBs, envs, scripts)
│   ├── src/test/java/...    # Selenium test classes (JUnit + Selenium WebDriver)
│   ├── pom.xml               # Maven project for the test suite (Java 11)
│   ├── docker-compose.yml    # Stack used to run the SUT for local testing
│   ├── deploy-sut.sh         # Linux/Mac helper: build+start the SUT stack (as shipped upstream)
│   ├── deploy-sut.ps1        # Windows helper: build+start the SUT stack (as shipped upstream)
│   └── Jenkinsfile           # CI pipeline definition
├── setup-sut.sh             # Linux/macOS: fetch sut/ and selenium-java/ from upstream
├── setup-sut.ps1            # Windows: fetch sut/ and selenium-java/ from upstream
├── deploy.sh                 # Linux/macOS: deploy the SUT stack (wraps selenium-java/deploy-sut.sh)
├── deploy.ps1                 # Windows: deploy the SUT stack (wraps selenium-java/deploy-sut.ps1)
├── docs/
│   ├── userrequirements_en.txt  # FullTeaching functional requirements (English)
│   └── userrequirements_es.txt  # FullTeaching functional requirements (Spanish)
├── .gitignore
├── CLAUDE.md
└── README.md
```

`sut/` and `selenium-java/` are gitignored and fetched on demand (see the iron
rule above); everything else in this tree is tracked in this repo.

## Working with the test suite

- The test suite is a standard Maven project (`selenium-java/pom.xml`, Java 11).
  Run tests from inside `selenium-java/`, e.g.:
  `mvn test -Dtest=FullTeachingEndToEndEChatTests -DTJOB_NAME=local -DSUT_URL=https://localhost:5000`
- To bring up the SUT locally before running tests, use the root-level deployment
  wrapper: `./deploy.sh` (Linux/Mac) or `.\deploy.ps1` (Windows) — pass `down` /
  `-Down` to stop it. These wrap `selenium-java/deploy-sut.sh` / `.ps1` and also
  copy `selenium-java/.retorch/envfiles/local.env` into `selenium-java/local.env`
  the first time, since the upstream deploy script expects it there.
- `selenium-java/.retorch/` holds the RETORCH framework configuration
  (test job definitions, environment files, container lifecycle scripts) used to
  schedule and run the suite under RETORCH.

## Functional requirements

`docs/userrequirements_en.txt` and `docs/userrequirements_es.txt` list the 16
numbered functional requirements for the FullTeaching application (courses,
classes, forum, live video sessions with intervention turns, registration,
profiles, calendar, etc.), in English and Spanish respectively. Use these as
the reference spec when relating test cases in `selenium-java/` to the
feature they cover.

## Keeping sut/ and selenium-java/ fresh

Both folders are regenerated from upstream and are gitignored — never hand-edit
them expecting the changes to persist, and never `git add` them. Re-run
`setup-sut.sh` / `setup-sut.ps1` to pull the latest upstream state; it deletes
and replaces both folders each time.
