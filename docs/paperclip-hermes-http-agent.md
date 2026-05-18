# Paperclip Hermes HTTP Agent

This is the v1.3 bridge for calling Hermes from Paperclip without using the broken local `hermes` command.

The bridge is intentionally small:

```text
Paperclip process adapter -> Node shim -> Hermes /v1/chat/completions
```

It does not modify Paperclip internals. It does not create broad shell access. It only forwards an assigned prompt to the verified Hermes chat completion endpoint and prints the assistant result for Paperclip to capture.

## Files

```text
tools/paperclip/hermes_http_agent.mjs
```

## Required Environment

```text
HERMES_BASE_URL=http://hermes:8642/v1
HERMES_API_KEY=<same value as API_SERVER_KEY>
HERMES_MODEL=hermes-agent
HERMES_TIMEOUT_MS=180000
```

`HERMES_BASE_URL` defaults to `http://hermes:8642/v1`.

`HERMES_MODEL` defaults to `hermes-agent`.

The script also accepts `API_SERVER_KEY` if `HERMES_API_KEY` is not set.

## VPS Install

Run from the VPS host:

```bash
cd /root/veloce-research-os
git pull

mkdir -p /docker/paperclip-iraj/data/adapters
cp tools/paperclip/hermes_http_agent.mjs /docker/paperclip-iraj/data/adapters/hermes_http_agent.mjs
chmod +x /docker/paperclip-iraj/data/adapters/hermes_http_agent.mjs
```

Verify Paperclip can see the adapter file:

```bash
docker exec paperclip-iraj-paperclip-1 sh -lc 'node -v && ls -l /paperclip/adapters/hermes_http_agent.mjs'
```

If `node -v` fails inside Paperclip, do not continue. Use the external adapter service path instead.

## Network Check

Paperclip must be on the shared `aiagency` Docker network so it can resolve `hermes`.

Check:

```bash
docker inspect paperclip-iraj-paperclip-1 --format '{{json .NetworkSettings.Networks}}'
```

If the container is not attached to `aiagency`, attach it:

```bash
docker network connect --alias paperclip aiagency paperclip-iraj-paperclip-1
```

## Manual Adapter Test

Run from the VPS host:

```bash
cd /root/ai-agency
set -a
source .env
set +a

docker exec -i \
  -e HERMES_BASE_URL=http://hermes:8642/v1 \
  -e HERMES_API_KEY="$API_SERVER_KEY" \
  -e HERMES_MODEL=hermes-agent \
  -e HERMES_TIMEOUT_MS=180000 \
  paperclip-iraj-paperclip-1 \
  node /paperclip/adapters/hermes_http_agent.mjs <<'EOF'
Reply with exactly: Paperclip Hermes HTTP shim works
EOF
```

Expected result:

```text
Status: success
Paperclip Hermes HTTP shim works
```

## Paperclip Agent Configuration

After the manual adapter test passes, create or update a Paperclip agent:

```text
Adapter type: process/local command
Command: node
Extra args: /paperclip/adapters/hermes_http_agent.mjs
Timeout: 300
```

Environment variables:

```text
HERMES_BASE_URL=http://hermes:8642/v1
HERMES_API_KEY=<stored secret resolving to API_SERVER_KEY>
HERMES_MODEL=hermes-agent
HERMES_TIMEOUT_MS=180000
```

Use this agent for Hermes-memory or agent-behavior tasks only. Keep fast drafting and simple planning on direct NVIDIA models through Open WebUI.

## Safety Rules

- Do not expose this script as a general shell tool.
- Do not print secrets into Paperclip comments.
- Do not use it for every Paperclip task.
- Do not retry failed Paperclip runs in a loop.
- If the process adapter does not pass the issue prompt to stdin, test whether Paperclip passes prompt text as command arguments. The script supports both stdin and arguments.

## Done Criteria

v1.3 is complete when:

```text
Paperclip can run the shim from /paperclip/adapters/hermes_http_agent.mjs.
The shim can call Hermes through http://hermes:8642/v1/chat/completions.
A Paperclip test issue receives a Hermes-generated answer.
SYSTEM_STATUS.md is updated with the verified state.
```
