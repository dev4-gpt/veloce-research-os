# Status Check Tool

The `status_check` tool is the first v1.2 OpenAPI tool for Open WebUI.

It is intentionally narrow. It can only check approved targets:

```text
openwebui
hermes
paperclip
research_repo
```

It cannot run shell commands, fetch arbitrary URLs, or mutate files.

## Files

```text
tools/status-check-server/
deploy/ai-agency/docker-compose.status-tool.yml
```

## VPS Install

Run on the VPS:

```bash
cd /root/veloce-research-os
git pull

cp deploy/ai-agency/docker-compose.status-tool.yml /root/ai-agency/docker-compose.status-tool.yml

cd /root/ai-agency
docker compose -f docker-compose.yml -f docker-compose.status-tool.yml up -d --build status-tool
docker compose -f docker-compose.yml -f docker-compose.status-tool.yml ps
```

## Internal Verification

Run on the VPS:

```bash
docker exec aiagency-openwebui python - <<'PY'
import json
import urllib.request

for target in ["openwebui", "hermes", "paperclip", "research_repo"]:
    req = urllib.request.Request(
        "http://status-tool:8080/status_check",
        data=json.dumps({"target": target, "timeout_ms": 1500}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    print(target, urllib.request.urlopen(req, timeout=5).read().decode())
PY
```

## Open WebUI Registration

In Open WebUI admin, add this OpenAPI tool server URL:

```text
http://status-tool:8080/openapi.json
```

If Open WebUI cannot register an internal Docker URL, expose the tool through Traefik later with authentication. Do not expose it publicly without auth.

## Test Prompt

After registration, ask Open WebUI:

```text
Use status_check to check hermes and research_repo. Summarize the result.
```
