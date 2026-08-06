#!/usr/bin/env bash
# deploy.sh - Deploy the FullTeaching SUT stack (Linux/macOS), from the repo root.
#
# Thin wrapper around selenium-java/deploy-sut.sh: it just makes sure the
# fetched folders exist and that local.env is in place, then delegates.
#
# Usage:   ./deploy.sh          (build + start the SUT, uses TJOB_NAME=local)
#          ./deploy.sh down     (stop the SUT)
# Requires: Docker with Compose plugin. Run scripts/setup-sut.sh first.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEST_DIR="$ROOT_DIR/selenium-java"
DEPLOY_SCRIPT="$TEST_DIR/deploy-sut.sh"
ENV_FILE="$TEST_DIR/local.env"
SOURCE_ENV_FILE="$TEST_DIR/.retorch/envfiles/local.env"

if [ ! -f "$DEPLOY_SCRIPT" ]; then
    echo "ERROR: $DEPLOY_SCRIPT not found." >&2
    echo "Run ./scripts/setup-sut.sh first to fetch sut/ and selenium-java/." >&2
    exit 1
fi

# deploy-sut.sh expects local.env next to itself, but it only ships under
# .retorch/envfiles/local.env - copy it into place if missing.
if [ ! -f "$ENV_FILE" ] && [ -f "$SOURCE_ENV_FILE" ]; then
    cp "$SOURCE_ENV_FILE" "$ENV_FILE"
fi

exec "$DEPLOY_SCRIPT" "$@"
