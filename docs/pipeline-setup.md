# Veloce Pipeline Setup

Date: 2026-05-19

## Purpose

This document is the reproducible map of the current Veloce Research OS pipeline: what exists, how the pieces connect, what is verified, and what should remain gated.

## Components

```text
GitHub repository
  git@github.com:dev4-gpt/veloce-research-os.git

VPS runtime
  /root/ai-agency
  /root/veloce-research-os

Paperclip
  durable issue ledger
  artifact generation
  agent run history

Open WebUI
  operator cockpit
  native tool interface
  GPT OSS model path for reliable tool calling

Hermes
  local agent/memory experiment
  OpenAI-compatible HTTP endpoint
  Paperclip HTTP shim target

MCPO
  MCP-to-OpenAPI bridge
  allowlisted tool paths
  exposed through mcpo-openwebui-proxy

Ruflo
  isolated planning-only sandbox
  not production enabled
```

## Runtime URLs

```text
Paperclip: https://paperclip-iraj.srv1314350.hstgr.cloud
Open WebUI: https://chat.srv1314350.hstgr.cloud
Hermes API: https://hermes.srv1314350.hstgr.cloud
MCPO tools proxy: https://tools.srv1314350.hstgr.cloud
GitHub: https://github.com/dev4-gpt/veloce-research-os
```

## Production Flow

```text
Open WebUI chat
  -> native Open WebUI tool wrapper
  -> https://tools.srv1314350.hstgr.cloud/<tool>
  -> mcpo-openwebui-proxy
  -> internal MCPO service or read-only proxy logic
  -> JSON result returned to chat
```

Verified Open WebUI tools:

```text
Veloce MCPO Time
Veloce MCPO Stack
Veloce MCPO Repo
Veloce Status Check
```

Verified from Open WebUI:

```text
Veloce MCPO Ruflo ruflo_status
Veloce MCPO Ruflo ruflo_plan
Veloce MCPO Ruflo ruflo_execution_packet
```

## Paperclip Flow

```text
Paperclip issue
  -> assignee agent
  -> run output, comments, dispositions
  -> GitHub/VPS validation when the Paperclip runtime cannot execute a command
  -> final status: Done, In Review, Blocked, or Cancelled
```

Operating rule:

```text
If Paperclip cannot access a runtime dependency, validate externally on the VPS or local machine, post the exact command/result back into the issue, and update the disposition.
```

## Hermes Flow

Verified Hermes endpoint:

```text
http://hermes:8642/v1/chat/completions
```

Paperclip shim path:

```text
/paperclip/adapters/hermes_http_agent_env.sh
/paperclip/adapters/hermes_http_agent.mjs
```

Use Hermes when memory or Hermes-specific agent behavior matters. Do not use Hermes for exact one-line acceptance tests because the wrapper/runtime context is token-heavy.

## MCPO Flow

Verified MCPO proxy paths:

```text
/openapi.json
/get_current_time
/convert_time
/stack_status
/repo_status
```

Authentication:

```text
Authorization: Bearer $MCPO_API_KEY
```

Direct verification pattern:

```bash
cd /root/ai-agency
set -a
source .env
set +a

curl -sS https://tools.srv1314350.hstgr.cloud/repo_status \
  -H "Authorization: Bearer $MCPO_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"scope":"current"}' | python3 -m json.tool
```

## Ruflo Sandbox Flow

Ruflo is not production-enabled. It is gated as a planning-only sandbox.

Sandbox path:

```text
/opt/veloce-ruflo-sandbox
```

Node 20 container path:

```bash
docker run --rm -it \
  -v /opt/veloce-ruflo-sandbox:/sandbox \
  -w /sandbox \
  -e HOME=/tmp/ruflo-home \
  node:20-bookworm \
  sh -lc 'npx ruflo@latest --help'
```

Installed Ruflo version observed:

```text
ruflo v3.7.0-alpha.70
```

Host Node.js was not sufficient:

```text
host node: v18.19.1
ruflo requirement: >=20.0.0
```

The sandbox was initialized for Codex and Claude-style config discovery, then hardened.

Safety requirements:

```text
daemon disabled
swarm disabled
memory disabled
hooks disabled
autopilot disabled
Claude MCP not connected to production
Codex MCP not connected to production
no production repo mount by default
no secrets mount by default
max agents constrained to 1 for sandbox testing
```

## VEL-124 Validation

Paperclip generated a planning-only Ruflo sandbox bridge in its workspace:

```text
/paperclip/instances/default/workspaces/8c81e4b2-d988-46f5-8cf8-4db07300db8a
```

Paperclip container did not include `python3`, so validation used a temporary Python container mounted over the Paperclip volume.

Passing validation command:

```bash
docker run --rm \
  --volumes-from paperclip-iraj-paperclip-1 \
  -w /paperclip/instances/default/workspaces/8c81e4b2-d988-46f5-8cf8-4db07300db8a \
  python:3.12-slim \
  sh -lc 'pip install pytest >/tmp/pip.log && PYTHONPATH=. pytest -q'
```

Observed result:

```text
3 passed in 0.01s
```

Root cause of the first failure:

```text
ModuleNotFoundError: No module named 'src'
```

Fix:

```text
Run pytest with PYTHONPATH=. from the workspace root.
```

## Issue State

```text
VEL-119: blocked, Paperclip-side Ruflo runtime unavailable
VEL-120: done, Paperclip-to-Ruflo planning bridge design
VEL-122: in review, OpenWebUI Ruflo status tool design
VEL-124: done, planning-only Ruflo sandbox bridge validated
VEL-125: cancelled, recovery issue no longer needed
VEL-126: done, valid disposition for VEL-124
VEL-127: done, recovery loop resolved
```

## Next Safe Step

Paste the `ruflo_execution_packet` `paperclip_comment_markdown` into the relevant Paperclip issue and attach proxy log proof.

Do not start Ruflo daemon, swarm, memory, hooks, or autopilot until a separate review approves production isolation.
