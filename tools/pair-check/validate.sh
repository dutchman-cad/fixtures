#!/bin/bash
# Validates the workflow inputs (from the environment) and sets NATIVE_EXT, HAS_STEP, WORK and OUT.
set -euo pipefail
fail() { echo "::error::$1"; exit 1; }
[[ $PAIR_ID =~ ^[0-9]{1,9}$ ]] || fail "pair_id must be digits"
[[ $CADMPEG_REV =~ ^[0-9a-fA-F]{7,40}$ ]] || fail "cadmpeg_rev must be 7 to 40 hex digits"
[[ $SOLIDCRAFT_VERSION =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]] || fail "solidcraft_version must look like v0.28.0"
[[ $TIMEOUT_SECS =~ ^[0-9]{1,4}$ ]] && ((TIMEOUT_SECS >= 10 && TIMEOUT_SECS <= 6000)) \
  || fail "timeout_secs must be 10 to 6000"
[[ -z $REQUEST_ID || $REQUEST_ID =~ ^[A-Za-z0-9-]{1,64}$ ]] || fail "request_id has characters that are not allowed"
[[ $RELEASE_TAG =~ ^[A-Za-z0-9._-]{1,200}$ ]] || fail "release_tag has characters that are not allowed"
[[ $NATIVE_ASSET =~ ^[A-Za-z0-9._-]{1,200}$ ]] || fail "native_asset has characters that are not allowed"
[[ -z $STEP_ASSET || $STEP_ASSET =~ ^[A-Za-z0-9._-]{1,200}$ ]] || fail "step_asset has characters that are not allowed"
# The file type, as the portal stores it: ".prt.3" (a numbered save) is "prt".
if [[ $NATIVE_ASSET =~ \.[Pp][Rr][Tt]\.[0-9]+$ ]]; then ext=prt
elif [[ $NATIVE_ASSET =~ \.([A-Za-z0-9_]{1,16})$ ]]; then ext=${BASH_REMATCH[1]}
else fail "native_asset needs a file type"; fi
echo "NATIVE_EXT=$ext" >>"$GITHUB_ENV"
echo "HAS_STEP=$([[ -n $STEP_ASSET ]] && echo 1 || echo 0)" >>"$GITHUB_ENV"
echo "WORK=$RUNNER_TEMP/pair-work" >>"$GITHUB_ENV"
echo "OUT=$RUNNER_TEMP/pair-out" >>"$GITHUB_ENV"
