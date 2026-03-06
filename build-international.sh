#!/usr/bin/env bash
set -euo pipefail

export PROFILE_ID="${PROFILE_ID:-production}"
export BROWSER_VARIANT="international"

./mach build
