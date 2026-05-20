# MCPO Ruflo Execution Packet Tool

Date: 2026-05-20

## Purpose

`ruflo_execution_packet` completes the Paperclip-facing Ruflo loop without granting Ruflo production execution authority.

It accepts an approved Paperclip-shaped plan and returns a structured execution handoff packet plus a Paperclip-ready comment. The packet tells the operator what to do next through Codex/GitHub/VPS verification. It does not start Ruflo, run shell commands, mutate Paperclip, write to GitHub, touch Docker, or mount secrets.

## Endpoint

```text
POST https://tools.srv1314350.hstgr.cloud/ruflo_execution_packet
```

Internal proxy route:

```text
http://mcpo-openwebui-proxy:8080/ruflo_execution_packet
```

Auth:

```text
Authorization: Bearer $MCPO_API_KEY
```

## Request

```json
{
  "issue_id": "VEL-128",
  "title": "Test Ruflo planning bridge",
  "description": "Complete the approved Paperclip execution loop for the Ruflo bridge.",
  "plan_trace_id": "d63c0864-b5d4-49d6-bdf8-eb2377ff51cf",
  "approved_by": "Aryaman",
  "approval": "human_approved",
  "execution_owner": "Codex/GitHub",
  "labels": ["v1.6", "ruflo"],
  "requested_mode": "execution_packet"
}
```

Allowed modes:

```text
execution_packet
packet
handoff
approval_gated_execution
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

The bridge also blocks explicit runtime flags:

```text
allow_runtime_execution=true
execute_now=true
start_services=true
write_changes=true
```

## Response Shape

```json
{
  "ok": true,
  "service": "veloce_ruflo_execution_packet",
  "decision": "approval_gated_execution_packet_ready",
  "execution_authority": "manual_or_codex_only: ...",
  "approved_by": "Aryaman",
  "execution_owner": "Codex/GitHub",
  "execution_packet": {
    "mode": "approval_gated_manual_execution",
    "steps": ["..."],
    "verification_commands": ["..."],
    "rollback_note": "..."
  },
  "paperclip_comment_markdown": "...",
  "ruflo_runtime_invoked": false,
  "production_enabled": false
}
```

## Paperclip Flow

1. Use `ruflo_plan` to create a planning-only result from the issue title and description.
2. Human reviews the plan.
3. Use `ruflo_execution_packet` with `approved_by` and `approval=human_approved`.
4. Paste `paperclip_comment_markdown` into the Paperclip issue.
5. Execute the approved work through Codex/GitHub or the VPS operator, not through Ruflo runtime.
6. Run the verification commands and paste the output into Paperclip.
7. Mark the issue done only after the verification evidence exists.

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

curl -sS https://tools.srv1314350.hstgr.cloud/ruflo_execution_packet \
  -H "Authorization: Bearer $MCPO_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "issue_id":"VEL-128",
    "title":"Test Ruflo planning bridge",
    "description":"Complete the approved Paperclip execution loop for the Ruflo bridge.",
    "approved_by":"Aryaman",
    "approval":"human_approved",
    "execution_owner":"Codex/GitHub",
    "labels":["v1.6","ruflo"],
    "requested_mode":"execution_packet"
  }' | python3 -m json.tool
```

Expected:

```text
"service": "veloce_ruflo_execution_packet"
"decision": "approval_gated_execution_packet_ready"
"ruflo_runtime_invoked": false
"production_enabled": false
"paperclip_comment_markdown": ...
```

## Verify Block

```bash
curl -sS https://tools.srv1314350.hstgr.cloud/ruflo_execution_packet \
  -H "Authorization: Bearer $MCPO_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "title":"Start Ruflo runtime",
    "description":"Start autopilot now.",
    "approved_by":"Aryaman",
    "approval":"human_approved",
    "requested_mode":"execute"
  }' | python3 -m json.tool
```

Expected:

```text
"ok": false
"decision": "blocked_runtime_execution_request"
"ruflo_runtime_invoked": false
```

## Open WebUI Tool

Import:

```text
https://raw.githubusercontent.com/dev4-gpt/veloce-research-os/main/tools/openwebui/mcpo_ruflo_tool.py
```

Prompt:

```text
Use Veloce MCPO Ruflo to run ruflo_execution_packet for issue_id="VEL-128", title="Test Ruflo planning bridge", description="Complete the approved Paperclip execution loop for the Ruflo bridge.", approved_by="Aryaman", approval="human_approved", execution_owner="Codex/GitHub", labels="v1.6,ruflo", requested_mode="execution_packet". Return only the raw JSON.
```

## Decision

This completes the safe Paperclip execution handoff for Ruflo. Ruflo is integrated as a planner and packet generator, while real production execution remains with human-approved Codex/GitHub/VPS operations.
