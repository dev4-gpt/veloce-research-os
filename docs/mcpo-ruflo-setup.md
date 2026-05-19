# MCPO and Ruflo Setup

## Sources Used

- Open WebUI MCP/MCPO docs: https://docs.openwebui.com/features/extensibility/plugin/tools/openapi-servers/mcp/
- MCPO repo: https://github.com/open-webui/mcpo
- Ruflo repo: https://github.com/ruvnet/ruflo

## MCPO

Open WebUI documents MCPO as the bridge for exposing stdio/SSE MCP servers through OpenAPI-compatible HTTP endpoints. This matters because Open WebUI already worked with the native `Veloce Status Check` tool, so MCPO is the next safe expansion layer.

Status as of 2026-05-19:

```text
Verified on VPS.
Container: aiagency-mcpo-time
Internal URL: http://mcpo-time:8000/openapi.json
Open WebUI proxy: https://tools.srv1314350.hstgr.cloud/openapi.json
OpenAPI paths: /get_current_time, /convert_time
```

### First Tool

Start with:

```text
mcp-server-time
```

Do not begin with filesystem, shell, browser, GitHub, or Docker control tools.

### VPS Install

Add a secret to `/root/ai-agency/.env`:

```bash
MCPO_API_KEY=choose-a-long-random-token
```

Then run:

```bash
cd /root/veloce-research-os
git pull

cp deploy/ai-agency/docker-compose.mcpo.yml /root/ai-agency/docker-compose.mcpo.yml

cd /root/ai-agency
docker compose -f docker-compose.yml -f docker-compose.status-tool.yml -f docker-compose.mcpo.yml up -d --build mcpo-time mcpo-openwebui-proxy
docker compose -f docker-compose.yml -f docker-compose.status-tool.yml -f docker-compose.mcpo.yml ps
```

### Internal Verification

Run:

```bash
cd /root/ai-agency
set -a
source .env
set +a

docker run --rm --network aiagency curlimages/curl:8.10.1 \
  -i -sS http://mcpo-time:8000/openapi.json \
  -H "Authorization: Bearer $MCPO_API_KEY"
```

If `/openapi.json` is protected or not available, try:

```bash
docker run --rm --network aiagency curlimages/curl:8.10.1 \
  -i -sS http://mcpo-time:8000/docs \
  -H "Authorization: Bearer $MCPO_API_KEY"
```

Verified VPS result:

```text
GET /docs -> HTTP/1.1 200 OK
GET /openapi.json -> title mcpo-time, paths /get_current_time and /convert_time
POST /get_current_time with {"timezone":"America/New_York"} returned valid JSON time data
```

### Open WebUI Proxy Verification

Open WebUI may fail to import raw MCPO directly, especially when the schema is protected or when the UI cannot reach Docker-only service names. For that reason, v1.4 uses a tiny proxy in front of MCPO:

```text
Container: aiagency-mcpo-openwebui-proxy
Public OpenAPI URL: https://tools.srv1314350.hstgr.cloud/openapi.json
Upstream MCPO URL: http://mcpo-time:8000
```

Verify from any machine:

```bash
curl -i https://tools.srv1314350.hstgr.cloud/openapi.json
```

Expected result:

```text
HTTP 200
OpenAPI version 3.0.3
Paths: /get_current_time, /convert_time
```

Verified direct call:

```bash
docker run --rm --network aiagency curlimages/curl:8.10.1 \
  -sS -X POST http://mcpo-time:8000/get_current_time \
  -H "Authorization: Bearer $MCPO_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"timezone":"America/New_York"}'
```

Observed response shape:

```json
{
  "timezone": "America/New_York",
  "datetime": "2026-05-19T00:06:22-04:00",
  "day_of_week": "Tuesday",
  "is_dst": true
}
```

### Open WebUI Registration

In Open WebUI:

```text
Admin / Workspace -> Tools -> Add OpenAPI Server
Name: Veloce MCPO Time
URL: https://tools.srv1314350.hstgr.cloud/openapi.json
Auth: Bearer <MCPO_API_KEY>
```

If Open WebUI imports the server but the model only prints a fake tool-shaped JSON response, use the native Open WebUI tool instead:

```text
https://raw.githubusercontent.com/dev4-gpt/veloce-research-os/main/tools/openwebui/mcpo_time_tool.py
```

The native tool calls:

```text
http://mcpo-openwebui-proxy:8080/get_current_time
```

It requires `MCPO_API_KEY` to be available inside the Open WebUI container.

Use a model already proven to call tools:

```text
openai/gpt-oss-120b
```

Test prompt:

```text
Use the MCPO time tool to get the current time for America/New_York. Return only the JSON result.
```

## Ruflo

Ruflo is a multi-agent orchestration platform with MCP/tooling support. It should be treated as an experiment after MCPO works, not as a replacement for the stable Veloce flow.

Current decision:

```text
Do not attach Ruflo to production Paperclip or Open WebUI flows yet.
Evaluate Ruflo in isolation only after Open WebUI successfully invokes the MCPO time tool from chat.
```

### Ruflo Gate

Do not connect Ruflo to Paperclip production issues until:

```text
1. MCPO time bridge works.
2. Ruflo container/build path is verified from the current Ruflo repo.
3. Ruflo is isolated from `/root/ai-agency` secrets unless a specific secret is needed.
4. Only one low-risk tool/capability is enabled.
5. A rollback command is tested.
```

### Ruflo Research Task

Create a Paperclip or manual task:

```text
Title: v1.4C - Evaluate Ruflo as isolated orchestration layer
Assignee: Technical Builder
Description:
Evaluate Ruflo in isolation after MCPO is working. Do not connect it to production Paperclip issues. Confirm current Docker/build path from the Ruflo repo, start it in an isolated network or local-only mode, document one low-risk capability, and provide rollback commands. Final disposition should be in_review before any production integration.
```

### Recommended Decision

Use Ruflo only if it provides a concrete capability that the current stack lacks. The current Veloce stack already has:

```text
Paperclip for task control
Open WebUI for operator cockpit
Hermes for memory/agent behavior
Direct NVIDIA models for speed
MCPO for MCP-to-OpenAPI tools
```

Ruflo should earn its place by improving orchestration without increasing token cost or recovery-loop risk.
