#!/usr/bin/env bash
# setup-sut.sh - Fetch the SUT and the Selenium test suite for this benchmark.
#
# Clones https://github.com/giis-uniovi/retorch-st-fullteaching and splits it into:
#   ./sut            - the FullTeaching application (System Under Test)
#   ./selenium-java   - everything else (Selenium/Java E2E test suite, RETORCH
#                        config, pom.xml, docker-compose files, etc.)
#
# Both folders are gitignored: they are fetched on demand, never committed.
# Re-run this script any time to refresh them to the latest upstream state.
#
# Usage: ./setup-sut.sh

set -euo pipefail

REPO_URL="https://github.com/giis-uniovi/retorch-st-fullteaching.git"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SUT_DIR="$ROOT_DIR/sut"
TEST_DIR="$ROOT_DIR/selenium-java"

TMP_DIR="$(mktemp -d)"
cleanup() { rm -rf "$TMP_DIR"; }
trap cleanup EXIT

echo "==> Cloning $REPO_URL"
git -c core.longpaths=true clone --depth 1 --single-branch "$REPO_URL" "$TMP_DIR/repo"

if [ ! -d "$TMP_DIR/repo/sut" ]; then
    echo "ERROR: expected 'sut' folder not found in cloned repo." >&2
    exit 1
fi

echo "==> Refreshing $SUT_DIR"
rm -rf "$SUT_DIR"
mv "$TMP_DIR/repo/sut" "$SUT_DIR"

echo "==> Refreshing $TEST_DIR"
rm -rf "$TEST_DIR"
rm -rf "$TMP_DIR/repo/.git"
mkdir -p "$TEST_DIR"
# shopt -s dotglob so hidden files (.retorch, .gitignore, .github, ...) move too
shopt -s dotglob
mv "$TMP_DIR/repo"/* "$TEST_DIR"/
shopt -u dotglob

echo "==> Done"
echo "    sut/           -> $SUT_DIR"
echo "    selenium-java/ -> $TEST_DIR"
