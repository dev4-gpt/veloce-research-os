# MCPO Ruflo Status Tool

Date: 2026-05-19

## Purpose

`ruflo_status` is the first production-safe Ruflo integration point.

It does not start Ruflo. It does not run tasks. It does not expose shell access. It only reports whether the planning-only sandbox is present, initialized, hardened, and backed by the recorded VEL-124 validation proof.

## Endpoint

```text
POST https://tools.srv1314350.hstgr.cloud/ruflo_status
```

Internal proxy route:

```text
http://mcpo-openwebui-proxy:8080/ruflo_status
```

Auth:

```text
Authorization: Bearer $MCPO_API_KEY
```

Request:

```json
{"scope":"sandbox"}
```

## What It Checks

The endpoint reads only mounted files:

```text
/workspace/ruflo-sandbox/.claude-flow/config.yaml
/workspace/ruflo-sandbox/.claude/settings.json
/workspace/ruflo-sandbox/.agents/config.toml
/workspace/ruflo-sandbox/.mcp.json
/workspace/ruflo-sandbox/AGENTS.md
/workspace/ruflo-sandbox/CLAUDE.md
/workspace/veloce-research-os/docs/v1.6-ruflo-planning-closeout.md
```

It verifies:

```text
sandbox directory exists
Ruflo runtime config exists
Codex config exists
Claude-style settings exist
MCP config exists but autoStart=false
autoScale=false
autoExecute=false
maxAgents=1
hooks disabled
Claude Flow disabled
shell/write/edit denied in Claude settings
VEL-124 validation proof exists
```

## What It Does Not Do

```text
No daemon start.
No swarm start.
No memory start.
No hooks execution.
No autopilot.
No Claude MCP autostart.
No Codex MCP autostart.
No production repo write mount.
No secrets mount.
```

## Deploy

On the VPS:

```bash
cd /root/veloce-research-os
git pull --ff-only

cp deploy/ai-agency/docker-compose.mcpo.yml /root/ai-agency/docker-compose.mcpo.yml

cd /root/ai-agency
docker compose -f docker-compose.yml -f docker-compose.status-tool.yml -f docker-compose.mcpo.yml up -d --build --force-recreate mcpo-openwebui-proxy
```

## Verify

```bash
cd /root/ai-agency
set -a
source .env
set +a

curl -sS https://tools.srv1314350.hstgr.cloud/ruflo_status \
  -H "Authorization: Bearer $MCPO_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"scope":"sandbox"}' | python3 -m json.tool

docker logs --tail=30 aiagency-mcpo-openwebui-proxy
```

Expected:

```text
"service": "veloce_ruflo_status"
"mode": "read_only_status"
"production_enabled": false
"ok": true
POST /ruflo_status HTTP/1.1" 200
```

## Open WebUI Tool

Import:

```text
https://raw.githubusercontent.com/dev4-gpt/veloce-research-os/main/tools/openwebui/mcpo_ruflo_tool.py
```

Prompt:

```text
Use Veloce MCPO Ruflo to run ruflo_status with scope="sandbox". Return only the raw JSON.
```

## Decision

This completes the first real Ruflo integration step because the production cockpit can see Ruflo sandbox readiness without granting Ruflo production execution authority.

The next bridge is `ruflo_plan`, documented in `docs/mcpo-ruflo-plan-tool.md`.
