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

## Open WebUI Native Tool Fallback

If Open WebUI shows an error like:

```text
true is not defined
```

then Open WebUI is interpreting the OpenAPI JSON as Python code. Do not paste `/openapi.json` into the Python Tool editor.

Use the native Open WebUI Tool instead:

```text
tools/openwebui/status_check_tool.py
```

Steps:

1. Go to Open WebUI `Workspace`.
2. Open `Tools`.
3. Create or import a new Python tool.
4. Paste the full contents of `tools/openwebui/status_check_tool.py`.
5. Save it as `Veloce Status Check`.
6. Enable it in the chat tool selector.

Then ask:

```text
Use status_check with target="hermes" and timeout_ms=1500. Return the JSON result.
```

And:

```text
Use status_check with target="research_repo" and timeout_ms=1500. Return the JSON result.
```

## Test Prompt

After registration, ask Open WebUI:

```text
Use status_check to check hermes and research_repo. Summarize the result.
```

## Verified Result

Verified on 2026-05-18 using Open WebUI model:

```text
openai/gpt-oss-120b
```

Working prompts:

```text
Use status_check_tool with target="hermes" and timeout_ms=1500. Return the JSON result.
Use status_check_tool with target="research_repo" and timeout_ms=1500. Return the JSON result.
Use status_check_tool with target="paperclip" and timeout_ms=1500. Return the JSON result.
```

Observed results:

```text
hermes: online
research_repo: online
paperclip: online
```

Model caveat:

```text
Mistral and Qwen variants did not reliably invoke the tool.
Use GPT OSS for tool-calling flows until other models are verified.
```
