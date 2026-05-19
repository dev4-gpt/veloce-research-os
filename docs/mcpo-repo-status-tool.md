# MCPO Repo Status Tool

Date: 2026-05-19

## Purpose

`repo_status` is a read-only Open WebUI tool for checking what Veloce Research OS commit is live on the VPS.

It answers the common operator question:

```text
What exact repo state am I running against right now?
```

## Tool Path

```text
Open WebUI chat
-> Veloce MCPO Repo native tool
-> http://mcpo-openwebui-proxy:8080/repo_status
-> read-only /workspace/veloce-research-os mount
```

External OpenAPI proxy:

```text
https://tools.srv1314350.hstgr.cloud/openapi.json
```

Internal Open WebUI native tool endpoint:

```text
http://mcpo-openwebui-proxy:8080/repo_status
```

## Security Boundary

The tool is intentionally narrow.

Allowed:

```text
git rev-parse --abbrev-ref HEAD
git rev-parse HEAD
git rev-parse --short HEAD
git status --porcelain=v1 --untracked-files=normal
git log -1 --pretty=format:%h%x09%s%x09%cI
```

Not allowed:

```text
git pull
git push
git commit
git checkout
git reset
arbitrary shell commands
arbitrary filesystem reads
```

The repository is mounted into the proxy container as read-only:

```text
/root/veloce-research-os:/workspace/veloce-research-os:ro
```

## Open WebUI Native Tool

Import this file in Open WebUI:

```text
https://raw.githubusercontent.com/dev4-gpt/veloce-research-os/main/tools/openwebui/mcpo_repo_tool.py
```

Tool name:

```text
Veloce MCPO Repo
```

Use with `openai/gpt-oss-120b` until other models are verified for tool calling.

Prompt:

```text
Use Veloce MCPO Repo to run repo_status with scope="current". Return only the raw JSON.
```

Expected fields:

```text
ok
service
checked_at
trace_id
path
branch
commit
short_commit
dirty
dirty_count
dirty_paths
last_commit
verification_hints
```

## VPS Deployment

```bash
cd /root/veloce-research-os
git pull

cp deploy/ai-agency/docker-compose.mcpo.yml /root/ai-agency/docker-compose.mcpo.yml

cd /root/ai-agency
docker compose -f docker-compose.yml -f docker-compose.status-tool.yml -f docker-compose.mcpo.yml up -d --build --force-recreate mcpo-openwebui-proxy
```

## VPS Verification

```bash
cd /root/ai-agency
set -a
source .env
set +a

curl -sS https://tools.srv1314350.hstgr.cloud/repo_status \
  -H "Authorization: Bearer $MCPO_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{}' | python3 -m json.tool

docker logs --tail=30 aiagency-mcpo-openwebui-proxy
```

Acceptance proof:

```text
HTTP result has service = veloce_repo_status.
Result includes current branch, commit, dirty state, and last commit.
Proxy logs show POST /repo_status HTTP/1.1 200.
No write operation is exposed.
```
