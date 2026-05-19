#!/usr/bin/env bash
set -euo pipefail

ENV_FILE="${HERMES_ENV_FILE:-/paperclip/adapters/hermes.env}"

if [ -f "$ENV_FILE" ]; then
  set -a
  # shellcheck disable=SC1090
  . "$ENV_FILE"
  set +a
fi

: "${HERMES_API_KEY:?HERMES_API_KEY missing}"

export HERMES_BASE_URL="${HERMES_BASE_URL:-http://hermes:8642/v1}"
export HERMES_MODEL="${HERMES_MODEL:-hermes-agent}"
export HERMES_TIMEOUT_MS="${HERMES_TIMEOUT_MS:-180000}"
export HERMES_MAX_PROMPT_CHARS="${HERMES_MAX_PROMPT_CHARS:-12000}"
export HERMES_SYSTEM_PROMPT="${HERMES_SYSTEM_PROMPT:-You are Veloce Hermes HTTP Agent. Answer briefly. Do not create recovery issues. If the bridge worked, recommend Done.}"

if [ "${HERMES_FIXED_PROMPT:-}" != "" ]; then
  printf '%s\n' "$HERMES_FIXED_PROMPT" | node /paperclip/adapters/hermes_http_agent.mjs
else
  exec node /paperclip/adapters/hermes_http_agent.mjs "$@"
fi
