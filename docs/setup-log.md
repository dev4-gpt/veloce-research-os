# Hostinger Paperclip Hermes OpenWebUI Setup

> Tested setup notes for deploying a small AI agency stack on a Hostinger VPS using Hostinger's Paperclip template, existing Traefik, Open WebUI, Hermes Agent, NVIDIA direct models, and optional OpenRouter fallback.

## Current Working Architecture

This setup uses Hostinger's existing Docker projects instead of replacing them.

```text
Internet
  |
  v
Hostinger Traefik (:80/:443)
  |
  |-- https://paperclip-iraj.<DOMAIN>  -> Hostinger Paperclip container
  |-- https://chat.<DOMAIN>            -> Open WebUI
  |-- https://hermes.<DOMAIN>          -> Hermes Agent API

Open WebUI
  |-- Hermes endpoint: http://hermes:8642/v1
  |-- NVIDIA direct endpoint: https://integrate.api.nvidia.com/v1

Hermes Agent
  |-- Provider: NVIDIA NIM
  |-- Model tested: minimaxai/minimax-m2.7
  |-- Persistent data: Docker volume ai-agency_hermes_data
```

Use the direct NVIDIA models in Open WebUI for normal fast chat. Use `hermes-agent` only when you specifically want Hermes agent behavior, memory, or orchestration.

## What We Learned The Hard Way

1. Do not install Caddy on this Hostinger template. Hostinger already runs Traefik on ports `80` and `443`.
2. Paperclip and Traefik are already separate Hostinger Docker Compose projects. Our stack should be a third compose project named `ai-agency`.
3. The `aiagency` Docker network should be external in compose because we create/connect it manually and attach Paperclip to it.
4. Nous Portal subscription credits are not the same as API credits. A free account may show `$0.10` subscription credit but still block API key creation.
5. OpenRouter free models can return `HTTP 429` because upstream free providers are rate-limited.
6. NVIDIA direct API worked with the same key even when OpenRouter was rate-limited.
7. Hermes looks for `NVIDIA_API_KEY`, not only `NVIDIA_NIM_API_KEY`.
8. Hermes is heavy. A tiny prompt can become tens of thousands of prompt tokens because Hermes adds agent runtime context. This is expected for an agent runtime, but not ideal for casual chat.
9. Open WebUI direct provider connections avoid Hermes prompt overhead.
10. Ruflo / MCPO was deferred because `ruvnet/claude-flow:v2-alpha` was not pullable from Docker Hub during testing.

## VPS Facts From This Setup

```text
VPS hostname: srv1314350.hstgr.cloud
Public IP: 72.60.29.216
Paperclip project: paperclip-iraj
Paperclip container: paperclip-iraj-paperclip-1
Traefik container: traefik-traefik-1
Base domain: srv1314350.hstgr.cloud
Paperclip URL: https://paperclip-iraj.srv1314350.hstgr.cloud
Open WebUI URL: https://chat.srv1314350.hstgr.cloud
Hermes URL: https://hermes.srv1314350.hstgr.cloud
```

Check Hostinger values:

```bash
grep -E '^(TRAEFIK_HOST|VPS_IP|PUBLIC_PORT)=' /docker/paperclip-iraj/.env
```

Expected:

```text
TRAEFIK_HOST=srv1314350.hstgr.cloud
PUBLIC_PORT=65408
VPS_IP=72.60.29.216
```

## Step 1: Create Project Structure

Run from the VPS host shell, not inside the Paperclip container.

Correct prompt:

```text
root@srv1314350:~#
```

Not this:

```text
$ codex --version
```

That `$` prompt was inside the Paperclip container and should only be used for Paperclip/Codex checks.

Create folders:

```bash
mkdir -p /root/ai-agency/hermes /root/ai-agency/scripts
cd /root/ai-agency
```

## Step 2: Create `.env`

Create `/root/ai-agency/.env`:

```bash
nano /root/ai-agency/.env
```

Use this shape. Replace secrets with real values.

```dotenv
DOMAIN=srv1314350.hstgr.cloud
LE_EMAIL=your-email@example.com

API_SERVER_KEY=generate-with-openssl-rand-hex-32
OPENWEBUI_SECRET_KEY=generate-with-openssl-rand-hex-32
OPENWEBUI_ADMIN_EMAIL=your-email@example.com
OPENWEBUI_ADMIN_PASSWORD=your-strong-password

PROVIDER=nvidia
MEMORY_ENABLED=true
PAPERCLIP_NETWORK_ALIAS=paperclip
BACKUP_RETENTION_DAYS=14

NOUS_PORTAL_API_KEY=
OPENROUTER_API_KEY=optional-openrouter-key
NVIDIA_NIM_API_KEY=your-nvidia-key
NVIDIA_API_KEY=your-nvidia-key
ANTHROPIC_API_KEY=
OPENAI_API_KEY=
```

Generate secrets:

```bash
openssl rand -hex 32
openssl rand -hex 32
```

Important: `NVIDIA_API_KEY` and `NVIDIA_NIM_API_KEY` can be the same NVIDIA key. Hermes specifically needed `NVIDIA_API_KEY`.

## Step 3: Create Hermes Config

Create `/root/ai-agency/hermes/config.yaml`:

```bash
nano /root/ai-agency/hermes/config.yaml
```

Working minimal config:

```yaml
model:
  default: minimaxai/minimax-m2.7
  provider: nvidia
  base_url: https://integrate.api.nvidia.com/v1

memory:
  enabled: true
  user_profile_enabled: true
  trajectory_learning_enabled: true
  storage_path: /opt/data/memory

api_server:
  enabled: true
  host: 0.0.0.0
  port: 8642
  require_api_key: true
```

Avoid this older shape because it caused duplicate model handling in this Hermes build:

```yaml
model:
  name: hermes-agent
  provider: openrouter
  model: meta-llama/llama-3.3-70b-instruct:free
```

## Step 4: Create Docker Compose

Create `/root/ai-agency/docker-compose.yml`:

```bash
nano /root/ai-agency/docker-compose.yml
```

Use this tested core compose:

```yaml
services:
  openwebui:
    image: ghcr.io/open-webui/open-webui:v0.9.2
    container_name: aiagency-openwebui
    restart: unless-stopped
    environment:
      ENV: prod
      WEBUI_AUTH: "true"
      ENABLE_SIGNUP: "false"
      DEFAULT_USER_ROLE: pending
      WEBUI_SECRET_KEY: ${OPENWEBUI_SECRET_KEY}
      WEBUI_URL: https://chat.${DOMAIN}
      WEBUI_ADMIN_EMAIL: ${OPENWEBUI_ADMIN_EMAIL}
      WEBUI_ADMIN_PASSWORD: ${OPENWEBUI_ADMIN_PASSWORD}
      WEBUI_ADMIN_NAME: AI Agency Admin
      OPENAI_API_BASE_URLS: http://hermes:8642/v1;https://integrate.api.nvidia.com/v1
      OPENAI_API_KEYS: ${API_SERVER_KEY};${NVIDIA_API_KEY}
      ENABLE_OLLAMA_API: "false"
      ENABLE_OPENAI_API: "true"
    volumes:
      - openwebui_data:/app/backend/data
    networks:
      - aiagency
    expose:
      - "8080"
    labels:
      - traefik.enable=true
      - traefik.http.routers.aiagency-chat.rule=Host(`chat.${DOMAIN}`)
      - traefik.http.routers.aiagency-chat.entrypoints=websecure
      - traefik.http.routers.aiagency-chat.tls.certresolver=letsencrypt
      - traefik.http.services.aiagency-chat.loadbalancer.server.port=8080
      - traefik.http.routers.aiagency-chat-http.rule=Host(`chat.${DOMAIN}`)
      - traefik.http.routers.aiagency-chat-http.entrypoints=web
      - traefik.http.routers.aiagency-chat-http.middlewares=aiagency-chat-redirect
      - traefik.http.middlewares.aiagency-chat-redirect.redirectscheme.scheme=https
      - traefik.http.middlewares.aiagency-chat-redirect.redirectscheme.permanent=true

  hermes:
    image: nousresearch/hermes-agent:v2026.5.7
    container_name: aiagency-hermes
    restart: unless-stopped
    command: gateway run
    shm_size: 1gb
    environment:
      API_SERVER_ENABLED: "true"
      API_SERVER_HOST: 0.0.0.0
      API_SERVER_PORT: "8642"
      API_SERVER_KEY: ${API_SERVER_KEY}
      API_SERVER_CORS_ORIGINS: https://chat.${DOMAIN}
      HERMES_DASHBOARD: "0"
      PROVIDER: ${PROVIDER}
      NOUS_PORTAL_API_KEY: ${NOUS_PORTAL_API_KEY}
      OPENROUTER_API_KEY: ${OPENROUTER_API_KEY}
      NVIDIA_NIM_API_KEY: ${NVIDIA_NIM_API_KEY}
      NVIDIA_API_KEY: ${NVIDIA_API_KEY}
      ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY}
      OPENAI_API_KEY: ${OPENAI_API_KEY}
      MEMORY_ENABLED: ${MEMORY_ENABLED}
    volumes:
      - hermes_data:/opt/data
    networks:
      - aiagency
    expose:
      - "8642"
    labels:
      - traefik.enable=true
      - traefik.http.routers.aiagency-hermes.rule=Host(`hermes.${DOMAIN}`)
      - traefik.http.routers.aiagency-hermes.entrypoints=websecure
      - traefik.http.routers.aiagency-hermes.tls.certresolver=letsencrypt
      - traefik.http.services.aiagency-hermes.loadbalancer.server.port=8642
      - traefik.http.routers.aiagency-hermes-http.rule=Host(`hermes.${DOMAIN}`)
      - traefik.http.routers.aiagency-hermes-http.entrypoints=web
      - traefik.http.routers.aiagency-hermes-http.middlewares=aiagency-hermes-redirect
      - traefik.http.middlewares.aiagency-hermes-redirect.redirectscheme.scheme=https
      - traefik.http.middlewares.aiagency-hermes-redirect.redirectscheme.permanent=true

networks:
  aiagency:
    name: aiagency
    external: true

volumes:
  hermes_data:
    name: ai-agency_hermes_data
  openwebui_data:
    name: ai-agency_openwebui_data
```

Why direct NVIDIA is included in Open WebUI:

```text
OPENAI_API_BASE_URLS=http://hermes:8642/v1;https://integrate.api.nvidia.com/v1
OPENAI_API_KEYS=${API_SERVER_KEY};${NVIDIA_API_KEY}
```

This gives two lanes:

```text
Open WebUI -> Hermes Agent -> NVIDIA
Open WebUI -> NVIDIA direct
```

Use NVIDIA direct for normal chat to avoid Hermes prompt overhead.

## Step 5: Create Bootstrap Script

Create `/root/ai-agency/scripts/bootstrap.sh`:

```bash
nano /root/ai-agency/scripts/bootstrap.sh
```

Script:

```bash
#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="/root/ai-agency"
cd "$REPO_DIR"

if [[ ! -f .env ]]; then
  echo "[ERROR] /root/ai-agency/.env is missing. Create it first."
  exit 1
fi

set -a
source .env
set +a

for name in DOMAIN LE_EMAIL API_SERVER_KEY PROVIDER OPENWEBUI_SECRET_KEY OPENWEBUI_ADMIN_EMAIL OPENWEBUI_ADMIN_PASSWORD MEMORY_ENABLED PAPERCLIP_NETWORK_ALIAS BACKUP_RETENTION_DAYS; do
  if [[ -z "${!name:-}" ]]; then
    echo "[ERROR] Missing required variable: $name"
    exit 1
  fi
done

if [[ -z "${NVIDIA_API_KEY:-}" && -z "${OPENROUTER_API_KEY:-}" && -z "${NOUS_PORTAL_API_KEY:-}" ]]; then
  echo "[ERROR] Set at least one provider key. Recommended: NVIDIA_API_KEY."
  exit 1
fi

docker network inspect aiagency >/dev/null 2>&1 || docker network create aiagency >/dev/null

PAPERCLIP_CONTAINER="$(docker ps --format '{{.Names}}' | awk 'tolower($0) ~ /paperclip/ {print; exit}')"
if [[ -n "$PAPERCLIP_CONTAINER" ]]; then
  NETWORKS="$(docker inspect --format '{{range $name, $_ := .NetworkSettings.Networks}}{{println $name}}{{end}}' "$PAPERCLIP_CONTAINER")"
  if ! printf '%s\n' "$NETWORKS" | grep -qx 'aiagency'; then
    docker network connect --alias "${PAPERCLIP_NETWORK_ALIAS}" aiagency "$PAPERCLIP_CONTAINER" || true
  fi
fi

# Hermes reads config from its data volume. Copy the local config into that volume every bootstrap.
docker volume create ai-agency_hermes_data >/dev/null
docker run --rm \
  -v ai-agency_hermes_data:/data \
  -v /root/ai-agency/hermes/config.yaml:/seed/config.yaml:ro \
  busybox:1.36.1 \
  sh -c 'cp /seed/config.yaml /data/config.yaml'

docker compose pull
docker compose up -d

echo
echo "Stack started. Check:"
echo "  https://chat.${DOMAIN}"
echo "  https://hermes.${DOMAIN}/health"
echo "  https://paperclip-iraj.${DOMAIN}"
```

Make executable:

```bash
chmod +x /root/ai-agency/scripts/bootstrap.sh
```

## Step 6: Start Stack

```bash
cd /root/ai-agency
docker compose config
bash scripts/bootstrap.sh
docker compose ps
```

Expected containers:

```text
aiagency-hermes      Up
aiagency-openwebui   Up
```

Open:

```text
https://chat.srv1314350.hstgr.cloud
https://hermes.srv1314350.hstgr.cloud/health
```

Hermes root may show `404`. That is fine. Test `/health` instead.

## Step 7: Verify Hermes API

Load env:

```bash
cd /root/ai-agency
set -a
source .env
set +a
```

Models endpoint:

```bash
curl -sS https://hermes.srv1314350.hstgr.cloud/v1/models \
  -H "Authorization: Bearer $API_SERVER_KEY"
```

Expected:

```json
{"object":"list","data":[{"id":"hermes-agent"}]}
```

Chat completion:

```bash
curl -sS https://hermes.srv1314350.hstgr.cloud/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_SERVER_KEY" \
  -d '{
    "model": "hermes-agent",
    "messages": [
      {"role": "user", "content": "Reply with exactly: Veloce stack online"}
    ]
  }'
```

Expected content:

```text
Veloce stack online
```

## Step 8: Verify NVIDIA Direct API

This bypasses Hermes and proves the provider key works.

```bash
curl -iS https://integrate.api.nvidia.com/v1/chat/completions \
  -H "Authorization: Bearer $NVIDIA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "minimaxai/minimax-m2.7",
    "messages": [{"role": "user", "content": "Reply with exactly: nvidia works"}]
  }'
```

Expected:

```text
HTTP/2 200
...
nvidia works
```

## Step 9: Open WebUI Usage

Open:

```text
https://chat.srv1314350.hstgr.cloud
```

Use your configured admin email/password.

Model choices should include:

```text
hermes-agent
NVIDIA direct models such as minimaxai/minimax-m2.7
```

Recommended usage:

```text
Use direct NVIDIA models for normal chat.
Use hermes-agent for agent workflow tests and memory experiments.
```

Why: Hermes may send very large prompts. We observed a tiny memory prompt becoming around `28,000` prompt tokens because Hermes adds its agent runtime context.

## Troubleshooting

### OpenRouter returns 429

Raw response may say:

```text
Provider returned error
model is temporarily rate-limited upstream
retry-after: 21
```

Meaning: free upstream provider is saturated. Try later, use BYOK, or use NVIDIA direct.

### Hermes says NVIDIA key missing

Error:

```text
Provider 'nvidia' is set in config.yaml but no API key was found. Set the NVIDIA_API_KEY environment variable
```

Fix:

1. Add `NVIDIA_API_KEY=...` to `.env`.
2. Add `NVIDIA_API_KEY: ${NVIDIA_API_KEY}` under the `hermes` service in `docker-compose.yml`.
3. Recreate Hermes:

```bash
docker compose up -d --force-recreate hermes
```

### Hermes root URL returns 404

This is fine:

```text
https://hermes.<DOMAIN>/
```

Test this instead:

```text
https://hermes.<DOMAIN>/health
```

### Open WebUI still checks Ollama

Make sure compose has:

```yaml
ENABLE_OLLAMA_API: "false"
```

Then recreate Open WebUI:

```bash
docker compose up -d --force-recreate openwebui
```

### Docker network label warning

If compose complains that `aiagency` exists but was not created by compose, use:

```yaml
networks:
  aiagency:
    name: aiagency
    external: true
```

This is expected because Paperclip is manually attached to the shared network.

### Hermes has huge prompt tokens

This is expected agent overhead. Do not use Hermes as the default casual chat lane.

Use:

```text
Open WebUI -> NVIDIA direct
```

for fast chat.

Use:

```text
Open WebUI -> Hermes
```

for heavier agent behavior.

## Deferred Work

### Ruflo / MCPO

Original image failed:

```text
ruvnet/claude-flow:v2-alpha
pull access denied
```

Do not include Ruflo/MCPO in the core compose until a verified public image or install path is confirmed.

### Paperclip -> Hermes HTTP Adapter

Next integration target:

```text
URL: http://hermes:8642/v1/chat/completions
Method: POST
Header: Authorization: Bearer <API_SERVER_KEY>
```

Use this after confirming Paperclip can resolve `hermes` on the `aiagency` Docker network.

### Codex Local

Codex inside Paperclip container was verified:

```bash
docker exec -it paperclip-iraj-paperclip-1 sh
codex --version
```

Observed:

```text
codex-cli 0.130.0
```

For ChatGPT/Codex student credits, device auth was required because normal browser login from the remote VPS failed on localhost callback.

## Final Mental Model

```text
Paperclip = HR, tasks, companies, agent budgets
Open WebUI = chat front door
NVIDIA direct = fast everyday model lane
Hermes Agent = heavy agent runtime with memory/tools/self-improvement
Codex local = optional coding/implementation adapter inside Paperclip
Traefik = Hostinger HTTPS router
```

This is the reproducible lesson: do not force every message through Hermes. Give users both lanes from day one.

## Paperclip Research OS Workflow

After the infrastructure was working, the first real Paperclip workflow was reset around a larger research source map.

Current clean project:

```text
Project: F-1 to O-1 Research OS
Parent issue: Build v1 research source map
Initial source task: Collect 100 sources across AI systems fields
```

The source map scope changed from `20` sources to `100` sources. The 100-source target is better because the Research OS should cover multiple AI domains before narrowing into weekly summaries and build projects.

Source categories:

```text
AI agents
Computer vision
NLP
LLMs
Automation
AI systems engineering
```

Use this safe Paperclip operating pattern while adapters are still being tested:

```text
1. Create the issue assigned to Me / You.
2. Write the description and deliverables clearly.
3. Only after review, assign one issue at a time to the intended agent.
4. Watch the run.
5. If it succeeds, move to the next issue.
6. If it fails, stop and fix the model/adapter before running more tasks.
```

Do not batch-assign a whole tree to agents yet. Paperclip can start runs immediately when an issue is assigned to an agent, and the Codex local adapter previously failed when a model profile mapped to unsupported `gpt-5`.

### Source Map Parent Issue

Recommended title:

```text
Build v1 research source map
```

Recommended description:

```markdown
Build the first research source map for Veloce AI.

Goal:
Collect and organize 100 high-quality sources across:
- AI agents
- Computer vision
- NLP
- LLMs
- Automation
- AI systems engineering

Deliver:
1. 100 sources total.
2. Each source must include title, link, category, year, source type, and why it matters.
3. Source types can include papers, benchmarks, datasets, open-source repos, technical reports, or strong engineering case studies.
4. Categorize each source as one or more of:
   - Research foundation
   - Technical build inspiration
   - Public writing topic
   - Evidence/portfolio support
5. Recommend the top 20 sources to summarize next.
6. Recommend 5 research themes for the next 30 days.

Guardrails:
- Keep claims factual.
- Prefer primary sources when possible.
- Do not frame this as legal advice or immigration strategy.
- This is research, portfolio, and evidence organization only.
```

### Initial Agent Task

Recommended sub-issue title:

```text
Step 01 - Collect 100 sources across AI systems fields
```

Recommended assignee during draft:

```text
Me / You
```

After the task is reviewed and ready to run, assign it to:

```text
Research Navigator
```

Recommended description:

```markdown
Collect 100 high-quality sources across AI agents, computer vision, NLP, LLMs, automation, and AI systems engineering.

Deliver a table with:
1. Number.
2. Title.
3. Link.
4. Category.
5. Year.
6. Source type.
7. Why it matters.
8. Best use: research foundation, technical build inspiration, public writing topic, or evidence/portfolio support.
9. Suggested priority: high, medium, or low.

Selection rules:
- Prefer papers, benchmarks, datasets, open-source repos, technical reports, and strong engineering case studies.
- Include a balanced mix across the six categories.
- Avoid weak blogspam or unsourced claims.
- Mark anything uncertain as needs human review.
```

### Paperclip Operating Lessons From The First Runs

These are the lessons that made the workflow stable:

1. Create each issue assigned to `You` first. Only assign to an agent after the description is complete.
2. Run one agent task at a time until the org is stable. Parallel runs create confusing recovery chains.
3. Every issue needs an `Input artifacts` section that names the prior issue or file it depends on.
4. Every issue needs a `Disposition` section, but the human still has to set Paperclip status to `Done`.
5. Agent text that says `Final disposition: done` is evidence for the operator. It does not reliably change the Paperclip issue status.
6. If the agent creates a useful artifact and says done, manually set the source issue to `Done`.
7. If Paperclip creates a recovery issue, mark the recovery issue `Done` after the source issue is resolved.
8. Do not keep rerunning recovery issues such as `Recover missing next step ...`; they often waste runs trying Paperclip API mutations that are not authorized.
9. Paperclip-generated file links can be broken. A link like `/paperclip/instances/...` may route to a fake company prefix called `PAPERCLIP` and show `Company not found`.
10. If a file link breaks, check inside the Paperclip container and copy the artifact out manually.
11. Paper Summarizer originally failed because its adapter was set to `Hermes Agent (local)` with command `hermes`; the Paperclip runtime did not have a local `hermes` binary.
12. Some recovery runs failed because `gpt-5.3-codex-spark` was not supported by the active ChatGPT/Codex account context.
13. `rg` was not installed in the Paperclip runtime. Agents can use `grep` and `sed`; installing `ripgrep` is a later platform improvement, not a blocker.

Useful artifact recovery command:

```bash
docker exec paperclip-iraj-paperclip-1 sh -lc 'find /paperclip -maxdepth 10 -type f -name "VEL-*_*.md" -print'
```

Copy a Paperclip artifact to the VPS host:

```bash
docker cp paperclip-iraj-paperclip-1:/paperclip/instances/default/projects/<company-id>/<project-id>/_default/<file>.md /root/<file>.md
```

Example that recovered the 100-source table:

```bash
docker cp paperclip-iraj-paperclip-1:/paperclip/instances/default/projects/d365f4a2-abf3-4b77-ab22-636293bb0f0c/0144899c-5367-4e79-b451-0de62432bd1a/_default/VEL-31_step01_100_sources_table.md /root/VEL-31_step01_100_sources_table.md
```

## Research OS Issue Sequence

Paperclip issue IDs cannot be renumbered. If issues are created out of order, trust the visible step title (`Step 01`, `Step 02`, etc.), not the `VEL-*` number.

Create each issue assigned to `You` first. After review, assign it to the listed agent.

### Step 01

Title:

```text
Step 01 - Collect 100 sources across AI systems fields
```

Assignee:

```text
Research Navigator
```

Description:

```markdown
Collect 100 high-quality sources across AI agents, computer vision, NLP, LLMs, automation, and AI systems engineering.

Deliver a table with:
1. Number.
2. Title.
3. Link.
4. Category.
5. Year.
6. Source type.
7. Why it matters.
8. Best use: research foundation, technical build inspiration, public writing topic, or evidence/portfolio support.
9. Suggested priority: high, medium, or low.

Selection rules:
- Prefer papers, benchmarks, datasets, open-source repos, technical reports, and strong engineering case studies.
- Include a balanced mix across the six categories.
- Avoid weak blogspam or unsourced claims.
- Mark anything uncertain as needs human review.

Disposition:
- If complete, mark this issue done.
- If fewer than 100 sources are found, mark in_review and explain the gap.
```

### Step 02

Title:

```text
Step 02 - Validate top 20 sources and 5 research themes
```

Assignee:

```text
Research Navigator
```

Description:

```markdown
Input artifact:
- Step 01 source table.
- Host copy if needed: /root/VEL-31_step01_100_sources_table.md

Review the completed 100-source map from Step 01 and validate the recommended top 20 sources and 5 research themes.

Deliver:
1. Confirm whether the top 20 sources are the right first summarization set.
2. If any source should be replaced, explain why and name the replacement.
3. Rank the top 20 from highest to lowest priority.
4. Confirm or revise the 5 research themes.
5. Pick the first 5 sources to summarize next.
6. Note any links or sources that need human verification.

Guardrails:
- Keep this as research and portfolio planning.
- Do not provide legal advice.
- Prefer primary papers, official docs, repos, datasets, or conference pages.

Disposition:
- If complete, mark this issue done.
- If Step 01 is missing, mark blocked by Step 01.
```

### Step 03

Title:

```text
Step 03 - Summarize validated sources 1-5 from Step 02
```

Assignee:

```text
Paper Summarizer
```

Description:

```markdown
Input artifact:
- Step 02 validated top-20 ranking.
- Use only sources ranked 1-5.
- Do not re-rank the full 100-source table.
- Do not replace sources unless a link is broken or the source is clearly invalid.

For each source, deliver:
1. Title and link.
2. Category.
3. Source type.
4. Core problem addressed.
5. Main method, system, dataset, or idea.
6. Key contribution.
7. Why it matters for Veloce AI.
8. Possible technical project inspired by it.
9. Possible public writing angle.
10. Evidence/portfolio value.
11. One limitation or open question.

End with:
- 3 cross-source patterns.
- 2 project ideas that combine these sources.
- Any items needing human verification.

Guardrails:
- Keep summaries factual.
- Cite links.
- Do not overclaim impact.

Disposition:
- If complete, mark this issue done.
- If the validated top-20 list is missing from Step 02, mark this issue blocked by Step 02.
```

### Step 04

Title:

```text
Step 04 - Summarize validated sources 6-10 from Step 02
```

Assignee:

```text
Paper Summarizer
```

Description:

```markdown
Input artifact:
- Step 02 validated top-20 ranking.
- Use only sources ranked 6-10.
- Do not re-rank the full 100-source table.

Deliver the same 11-point source summary structure used in Step 03.

End with:
- 3 cross-source patterns.
- 2 project ideas that combine these sources.
- Any items needing human verification.

Disposition:
- If complete, mark this issue done.
- If the validated top-20 list is missing from Step 02, mark this issue blocked by Step 02.
```

### Step 05

Title:

```text
Step 05 - Summarize validated sources 11-15 from Step 02
```

Assignee:

```text
Paper Summarizer
```

Description:

```markdown
Input artifact:
- Step 02 validated top-20 ranking.
- Use only sources ranked 11-15.
- Do not re-rank the full 100-source table.

Deliver the same 11-point source summary structure used in Step 03.

End with:
- 3 cross-source patterns.
- 2 project ideas that combine these sources.
- Any items needing human verification.

Disposition:
- If complete, mark this issue done.
- If the validated top-20 list is missing from Step 02, mark this issue blocked by Step 02.
```

### Step 06

Title:

```text
Step 06 - Summarize validated sources 16-20 from Step 02
```

Assignee:

```text
Paper Summarizer
```

Description:

```markdown
Input artifact:
- Step 02 validated top-20 ranking.
- Use only sources ranked 16-20.
- Do not re-rank the full 100-source table.

Deliver the same 11-point source summary structure used in Step 03.

End with:
- 3 cross-source patterns.
- 2 project ideas that combine these sources.
- Any items needing human verification.

Disposition:
- If complete, mark this issue done.
- If the validated top-20 list is missing from Step 02, mark this issue blocked by Step 02.
```

### Step 07

Title:

```text
Step 07 - Synthesize top 20 sources into research directions
```

Assignee:

```text
Research Navigator
```

Description:

```markdown
Input artifacts:
- Step 03: summaries for priority sources 1-5.
- Step 04: summaries for priority sources 6-10.
- Step 05: summaries for priority sources 11-15.
- Step 06: summaries for priority sources 16-20.

Do not re-summarize individual papers. Use the existing Step 03-06 summaries.

Current task:
Synthesize the top 20 source summaries into a focused research direction map for Veloce AI.

Deliver:
1. 5 major research themes found across the top 20 sources.
2. For each theme:
   - supporting sources,
   - why the theme matters,
   - possible original research angle,
   - possible technical artifact,
   - possible public writing angle,
   - evidence/portfolio value.
3. Rank the 5 themes by:
   - feasibility in 30 days,
   - originality potential,
   - portfolio/O-1 evidence value,
   - alignment with computer vision, AI agents, automation, and applied AI systems.
4. Recommend the top 2 themes to pursue first.
5. List 5 concrete project ideas derived from the top 2 themes.
6. List human review checkpoints.

Guardrails:
- This is research and portfolio planning, not legal advice.
- Do not overclaim O-1 eligibility.
- Focus on concrete research artifacts: papers, repos, benchmarks, demos, public writing, talks, or evidence logs.

Disposition:
- If complete, mark this issue done.
- If any Step 03-06 artifact is missing, mark blocked and name the missing artifact.
```

### Step 08

Title:

```text
Step 08 - Choose first 30-day flagship project
```

Assignee:

```text
Technical Builder
```

Description:

```markdown
Input artifact:
- Step 07 research direction map.

Do not create a new research map. Use Step 07 as the source of truth.

Current task:
Choose the best first 30-day flagship project for Veloce AI.

Deliver:
1. Recommended flagship project title.
2. One-paragraph project thesis.
3. Why this project is the best first choice.
4. Research sources/themes from Step 07 that support it.
5. MVP scope for 30 days.
6. What is explicitly out of scope.
7. Dataset, benchmark, or evaluation target.
8. Technical artifact to build.
9. Public artifact to publish.
10. Evidence/portfolio value.
11. Risks and mitigation plan.
12. Definition of done for the 30-day project.

Guardrails:
- Choose one project, not many.
- Prefer a project that can produce a repo, demo, writeup, and evidence log.
- Keep immigration framing as evidence organization, not legal advice.

Disposition:
- If complete, mark this issue done.
- If Step 07 is missing or incomplete, mark blocked by Step 07.
```

### Step 09

Title:

```text
Step 09 - Create 30-day execution plan for flagship project
```

Assignee:

```text
Task Manager
```

Description:

```markdown
Input artifact:
- Step 08 selected flagship project.

Current task:
Turn the selected flagship project into a 30-day execution plan.

Deliver:
1. Week 1 goal and daily tasks.
2. Week 2 goal and daily tasks.
3. Week 3 goal and daily tasks.
4. Week 4 goal and daily tasks.
5. Milestones for:
   - research reading,
   - implementation,
   - evaluation,
   - public writing,
   - evidence logging.
6. Dependencies and blockers.
7. Human review checkpoints.
8. What should be created in Paperclip next.

Guardrails:
- Make the plan realistic for a solo F-1 student.
- Keep tasks specific and checkable.
- Do not add legal advice.

Disposition:
- If complete, mark this issue done.
- If Step 08 is missing, mark blocked by Step 08.
```

### Step 10

Title:

```text
Step 10 - Build evidence ledger structure
```

Assignee:

```text
Evidence Tracker
```

Description:

```markdown
Input artifacts:
- Step 08 selected flagship project.
- Step 09 30-day execution plan.

Current task:
Create an evidence ledger structure for tracking portfolio and O-1-relevant proof over time.

Deliver:
1. Evidence categories to track.
2. Suggested Obsidian folder/database structure.
3. Fields for each evidence record.
4. Example records for:
   - paper summary,
   - code commit,
   - experiment result,
   - public article,
   - outreach message,
   - expert feedback,
   - presentation/talk,
   - repository metric.
5. Weekly evidence review checklist.
6. Items that should be reviewed by an immigration attorney later.

Guardrails:
- This is evidence organization only.
- Do not claim eligibility for any visa.
- Do not advise legal strategy beyond preparing material for attorney review.

Disposition:
- If complete, mark this issue done.
- If Step 08 or Step 09 is missing, mark blocked and name the missing input.
```

### Step 11

Title:

```text
Step 11 - Draft first public research article
```

Assignee:

```text
Content Creator
```

Description:

```markdown
Input artifacts:
- Step 07 research direction map.
- Step 08 selected flagship project.
- Step 09 30-day execution plan.

Current task:
Draft the first public research article introducing the Veloce AI research direction and flagship project.

Deliver:
1. Article title.
2. Subtitle.
3. Target audience.
4. Full article draft.
5. 5 alternative hooks.
6. 5 LinkedIn post variants.
7. 5 X/Twitter post variants.
8. Suggested visuals or diagrams.
9. Human review checklist before publishing.

Guardrails:
- Do not overclaim research results that do not exist yet.
- Frame this as a research/build journey.
- Avoid immigration claims.
- Keep tone credible and technical.

Disposition:
- If complete, mark this issue done.
- If required input artifacts are missing, mark blocked and name them.
```

### Step 12

Title:

```text
Step 12 - Create technical repo scaffold
```

Assignee:

```text
Technical Builder
```

Description:

```markdown
Input artifacts:
- Step 08 selected flagship project.
- Step 09 30-day execution plan.

Current task:
Design the initial technical repository scaffold for the flagship project.

Deliver:
1. Proposed repository name.
2. Repository purpose.
3. Folder structure.
4. README outline.
5. Experiment plan file outline.
6. Baseline implementation plan.
7. Evaluation script plan.
8. Data handling notes.
9. Reproducibility checklist.
10. First 10 GitHub issues to create.

Guardrails:
- Keep scope realistic for 30 days.
- Prefer reproducible experiments over vague demos.
- Do not invent unavailable datasets or compute.

Disposition:
- If complete, mark this issue done.
- If Step 08 or Step 09 is missing, mark blocked and name the missing input.
```

### Step 13

Title:

```text
Step 13 - Create outreach target list
```

Assignee:

```text
Research Navigator
```

Description:

```markdown
Input artifacts:
- Step 07 research direction map.
- Step 08 selected flagship project.

Current task:
Create a human-reviewed outreach target list for the flagship project.

Deliver:
1. 20 outreach targets across:
   - researchers,
   - labs,
   - open-source maintainers,
   - benchmark authors,
   - communities,
   - conferences/workshops.
2. For each target:
   - name,
   - affiliation,
   - link,
   - why they are relevant,
   - possible outreach angle,
   - risk/appropriateness note.
3. Rank top 10 for first outreach.
4. Identify 5 low-risk community channels to join first.

Guardrails:
- Do not scrape private contact information.
- Use public professional links only.
- Do not send messages.
- Keep outreach respectful and academic/professional.

Disposition:
- If complete, mark this issue done.
- If Step 07 or Step 08 is missing, mark blocked and name the missing input.
```

### Step 14

Title:

```text
Step 14 - Draft outreach messages for human review
```

Assignee:

```text
Content Creator
```

Description:

```markdown
Input artifact:
- Step 13 outreach target list.

Current task:
Draft outreach messages for human review. Do not send anything.

Deliver:
1. Email template for researchers.
2. Email template for open-source maintainers.
3. LinkedIn message template.
4. X/Twitter DM template.
5. Community/forum intro post.
6. Follow-up message template.
7. Red flags to avoid.
8. Human approval checklist before sending.

Guardrails:
- Do not claim credentials or results that do not exist.
- Do not imply visa sponsorship or legal requests.
- Keep messages short, specific, and respectful.
- All outreach must require human review before sending.

Disposition:
- If complete, mark this issue done.
- If Step 13 is missing, mark blocked by Step 13.
```

### Step 15

Title:

```text
Step 15 - Create weekly review dashboard
```

Assignee:

```text
Task Manager
```

Description:

```markdown
Input artifacts:
- Step 09 30-day execution plan.
- Step 10 evidence ledger structure.
- Step 11 public article draft.
- Step 12 repo scaffold.
- Step 13 outreach target list.

Current task:
Create a weekly review dashboard for operating the Veloce AI research OS.

Deliver:
1. Weekly dashboard sections.
2. Metrics to track.
3. Status fields.
4. Weekly review questions.
5. Blocker tracking format.
6. Evidence generated this week section.
7. Next week planning section.
8. Paperclip issue hygiene rules.
9. Obsidian dashboard template.

Guardrails:
- Keep it simple enough to use every week.
- Do not create vanity metrics.
- Prioritize shipped artifacts, learning, feedback, and evidence.

Disposition:
- If complete, mark this issue done.
- If inputs are missing, mark in_review and list missing inputs.
```

### Practical Lesson

The Research OS should start wide, then narrow:

```text
100 sources -> validated top 20 -> top 20 summaries -> 5 themes -> 1 flagship project -> 30-day plan -> public article + repo + evidence ledger + outreach
```

This prevents the system from getting trapped summarizing low-value sources and makes every later task depend on a deliberate handoff from the previous step.
