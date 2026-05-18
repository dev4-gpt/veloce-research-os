# Veloce Status Check Server

This is the first v1.2 OpenAPI tool server for Open WebUI.

It exposes one safe tool:

```text
status_check
```

Allowed targets:

```text
openwebui
hermes
paperclip
research_repo
```

It does not execute arbitrary shell commands, fetch arbitrary URLs, or mutate files.

## Local Run

```bash
python3 app.py
```

Then:

```bash
curl -sS http://localhost:8080/healthz
curl -sS http://localhost:8080/openapi.json
curl -sS http://localhost:8080/status_check \
  -H "Content-Type: application/json" \
  -d '{"target":"research_repo"}'
```

## Docker

```bash
docker build -t veloce/status-check-server:0.1.0 .
docker run --rm -p 8080:8080 \
  -v /root/veloce-research-os:/repo:ro \
  veloce/status-check-server:0.1.0
```
