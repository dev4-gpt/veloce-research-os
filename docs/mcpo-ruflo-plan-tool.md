# MCPO Ruflo Plan Tool

Date: 2026-05-20

## Purpose

`ruflo_plan` is the first Paperclip-to-Ruflo planning bridge.

It accepts a Paperclip-shaped issue payload and returns a structured, approval-gated plan plus a Paperclip-ready comment. It does not start Ruflo, execute tasks, mutate Paperclip, write to GitHub, touch Docker, or mount secrets.

## Endpoint

```text
POST https://tools.srv1314350.hstgr.cloud/ruflo_plan
```

Internal proxy route:

```text
http://mcpo-openwebui-proxy:8080/ruflo_plan
```

Auth:

```text
Authorization: Bearer $MCPO_API_KEY
```

## Request

```json
{
  "issue_id": "VEL-128",
  "title": "Integrate Ruflo planning bridge",
  "description": "Create a planning-only bridge from Paperclip issue text to a structured plan.",
  "priority": "medium",
  "assignee": "Technical Builder",
  "labels": ["v1.6", "ruflo"],
  "requested_mode": "plan"
}
```

Allowed mode:

```text
plan
```

Blocked modes:

```text
run
exec
execute
apply
deploy
mutate
write
autopilot
start
```

The bridge also blocks explicit boolean execution flags:

```text
allow_execution=true
execute_now=true
start_services=true
write_changes=true
```

## Response Shape

```json
{
  "ok": true,
  "service": "veloce_ruflo_plan",
  "decision": "plan_only_ready",
  "owner": "Technical Builder",
  "risk_level": "medium",
  "next_action": "...",
  "verification_command": "...",
  "rollback_note": "...",
  "approval_gates": ["..."],
  "paperclip_comment_markdown": "...",
  "ruflo_runtime_invoked": false,
  "production_enabled": false
}
```

## Guardrails

Before planning, the endpoint calls the local `ruflo_status` guard.

If the sandbox is missing or not hardened, planning is refused with:

```text
decision = blocked_sandbox_not_ready
```

If the payload requests execution, planning is refused with:

```text
decision = blocked_execution_request
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

## Verify Directly

```bash
cd /root/ai-agency
set -a
source .env
set +a

curl -sS https://tools.srv1314350.hstgr.cloud/ruflo_plan \
  -H "Authorization: Bearer $MCPO_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "issue_id":"VEL-128",
    "title":"Test Ruflo planning bridge",
    "description":"Create a planning-only response for a Paperclip issue.",
    "priority":"medium",
    "assignee":"Technical Builder",
    "labels":["v1.6","ruflo"],
    "requested_mode":"plan"
  }' | python3 -m json.tool
```

Expected:

```text
"service": "veloce_ruflo_plan"
"decision": "plan_only_ready"
"ruflo_runtime_invoked": false
"production_enabled": false
"paperclip_comment_markdown": ...
```

## Verify Block

```bash
curl -sS https://tools.srv1314350.hstgr.cloud/ruflo_plan \
  -H "Authorization: Bearer $MCPO_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "title":"Start Ruflo services",
    "description":"Start daemon and swarm now.",
    "requested_mode":"execute"
  }' | python3 -m json.tool
```

Expected:

```text
"ok": false
"decision": "blocked_execution_request"
"ruflo_runtime_invoked": false
```

## Open WebUI Tool

Import:

```text
https://raw.githubusercontent.com/dev4-gpt/veloce-research-os/main/tools/openwebui/mcpo_ruflo_tool.py
```

Prompt:

```text
Use Veloce MCPO Ruflo to run ruflo_plan for issue_id="VEL-128", title="Test Ruflo planning bridge", description="Create a planning-only response for a Paperclip issue.", priority="medium", assignee="Technical Builder", labels="v1.6,ruflo", requested_mode="plan". Return only the raw JSON.
```

## Paperclip Operating Pattern

1. Copy a Paperclip issue title and description into `ruflo_plan`.
2. Review the returned `paperclip_comment_markdown`.
3. Paste the comment into the Paperclip issue.
4. Create implementation work only after human approval.
5. Keep Ruflo execution disabled.

## Decision

This completes the first practical Paperclip-to-Ruflo bridge without granting Ruflo production authority.

The next safe bridge is `ruflo_execution_packet`, documented in `docs/mcpo-ruflo-execution-packet-tool.md`. It creates a human-approved Paperclip execution handoff without starting Ruflo runtime services.
