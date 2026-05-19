# MCPO Stack Status Tool

Date: 2026-05-19

## Purpose

`stack_status` is the first v1.5 read-only MCPO expansion tool.

It lets Open WebUI answer:

```text
Is the Veloce stack healthy right now?
```

It does not expose shell execution, Docker control, Git write operations, or arbitrary URL fetching.

## Files

```text
tools/mcpo-openwebui-proxy/app.py
tools/openwebui/mcpo_stack_tool.py
deploy/ai-agency/docker-compose.mcpo.yml
```

## What It Checks

Fixed allowlist only:

```text
openwebui -> TCP probe for http://openwebui:8080
hermes -> http://hermes:8642/health
paperclip -> http://paperclip-iraj-paperclip-1:3100
mcpo -> http://mcpo-time:8000/docs
research_repo -> read-only /workspace/veloce-research-os/.git metadata
```

The Open WebUI check intentionally uses a TCP probe instead of calling
`/api/version`. When Open WebUI invokes this tool, an HTTP self-check can time
out because Open WebUI is waiting for the tool response.

## VPS Install

Run on the VPS:

```bash
cd /root/veloce-research-os
git pull

cp deploy/ai-agency/docker-compose.mcpo.yml /root/ai-agency/docker-compose.mcpo.yml

cd /root/ai-agency
docker compose -f docker-compose.yml -f docker-compose.status-tool.yml -f docker-compose.mcpo.yml up -d --build --force-recreate mcpo-openwebui-proxy
```

## VPS Verification

Run:

```bash
cd /root/ai-agency
set -a
source .env
set +a

curl -sS https://tools.srv1314350.hstgr.cloud/openapi.json | grep -E 'stack_status|get_current_time|convert_time'

curl -sS https://tools.srv1314350.hstgr.cloud/stack_status \
  -H "Authorization: Bearer $MCPO_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{}' | python3 -m json.tool

docker logs --tail=30 aiagency-mcpo-openwebui-proxy
```

Expected:

```text
OpenAPI includes /stack_status.
stack_status returns ok, checked_at, trace_id, checks, and verification_hints.
Proxy logs include POST /stack_status HTTP/1.1 200.
```

## Open WebUI Native Tool

Import this Python tool:

```text
https://raw.githubusercontent.com/dev4-gpt/veloce-research-os/main/tools/openwebui/mcpo_stack_tool.py
```

Then in a chat:

```text
1. Use model openai/gpt-oss-120b.
2. Open the tools picker.
3. Enable Veloce MCPO Stack.
4. Ask:
```

```text
Use Veloce MCPO Stack to run stack_status with scope="all". Return only the raw JSON.
```

Proof of real execution is not the model response alone. Confirm with:

```bash
docker logs --tail=20 aiagency-mcpo-openwebui-proxy
```

Look for:

```text
POST /stack_status HTTP/1.1" 200
```
