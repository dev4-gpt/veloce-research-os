# Veloce Research OS System Status

Date: 2026-05-19

## Summary

Veloce Research OS v1.6 is operational as a self-hosted research operating system running on the Hostinger VPS with Paperclip, Open WebUI, Hermes, direct NVIDIA model access, GitHub, Obsidian, a runnable research project scaffold, native Open WebUI tools, verified MCPO time/stack/repo bridges, and a gated Ruflo planning-only sandbox. The first read-only Ruflo cockpit integration, `ruflo_status`, is verified end to end. The first Paperclip-shaped planning bridge, `ruflo_plan`, is verified end to end. The approval-gated Paperclip execution handoff, `ruflo_execution_packet`, is implemented in the repository and ready for VPS deploy/verification.

The system is ready for controlled use. Hermes standalone and Hermes memory persistence are verified. Paperclip-to-Hermes execution is verified through the HTTP wrapper path, but Hermes should not be used for exact tiny replies because its runtime context is token-heavy.

V1.2 core is verified: Open WebUI can call the `Veloce Status Check` tool through the native Open WebUI tool interface when using `openai/gpt-oss-120b`.

V1.4 MCPO core is verified: `mcpo-time` runs on the internal `aiagency` Docker network, exposes an OpenAPI schema, and successfully calls the MCP time tool through HTTP. Open WebUI chat also invoked the MCPO time bridge through the native `Veloce MCPO Time` tool, with proxy logs showing `POST /get_current_time HTTP/1.1 200`.

V1.5A is verified: Open WebUI invoked `Veloce MCPO Stack`, the proxy returned live stack JSON, and the response showed current service health.

V1.5B is verified: Open WebUI invoked `Veloce MCPO Repo`, returned current repository metadata, and confirmed commit `98ace0c` was clean at the time of validation.

V1.6D is verified externally: the planning-only Ruflo sandbox bridge tests passed from the Paperclip workspace using a Python 3.12 container with `PYTHONPATH=.`.

## Service URLs

```text
Paperclip: https://paperclip-iraj.srv1314350.hstgr.cloud
Open WebUI: https://chat.srv1314350.hstgr.cloud
Hermes API: https://hermes.srv1314350.hstgr.cloud
GitHub: https://github.com/dev4-gpt/veloce-research-os
```

## VPS Paths

```text
/root/ai-agency
/root/veloce-research-os
/root/veloce-research-os/projects/reliability-policy-matrix
```

`/root/ai-agency` is the infrastructure stack.

`/root/veloce-research-os` is the research/product repository.

## What Works

- Hostinger Traefik routes HTTPS traffic to Paperclip, Open WebUI, and Hermes.
- Paperclip is usable as the task board and artifact generator.
- Open WebUI is reachable and usable as the chat interface.
- Direct NVIDIA models work in Open WebUI for fast model calls.
- Hermes container runs and can respond through its API.
- Hermes memory persists across separate API requests.
- Paperclip can call Hermes through the repository-backed HTTP wrapper.
- Open WebUI can call the `status_check_tool` native tool.
- `status_check_tool` verified `hermes`, `paperclip`, and `research_repo`.
- MCPO is running as `aiagency-mcpo-time`.
- MCPO exposes `/docs`, `/openapi.json`, `/get_current_time`, and `/convert_time` internally.
- Open WebUI should import MCPO through the proxy at `https://tools.srv1314350.hstgr.cloud/openapi.json`.
- MCPO `get_current_time` returned valid `America/New_York` time JSON.
- Open WebUI native tool `Veloce MCPO Time` is installed and verified from chat.
- V1.5 repo support exists for read-only `stack_status`.
- V1.5 repo support exists for read-only `repo_status`.
- V1.6 planning-only Ruflo bridge validation passed in the Paperclip workspace.
- V1.6 read-only `ruflo_status` support exists in the MCPO proxy and Open WebUI wrapper.
- V1.6 planning-only `ruflo_plan` support exists in the MCPO proxy and Open WebUI wrapper.
- V1.6 approval-gated `ruflo_execution_packet` support exists in the MCPO proxy and Open WebUI wrapper.
- GitHub repository is populated and is the source of truth for code.
- VPS can pull and run the GitHub repository.
- Obsidian contains the exported research artifacts and operating notes.
- `reliability-policy-matrix` runs its Week 1 scaffold and tests on the VPS.

## Verified Commands

Run on the VPS:

```bash
cd /root/veloce-research-os
git pull

cd projects/reliability-policy-matrix
bash scripts/week1_day1_3.sh
python3 -m unittest discover -s tests
find artifacts -maxdepth 3 -type f | sort
```

Latest observed result:

```text
GitHub already up to date.
Week 1 Day 1-3 script completed.
3 unit tests passed.
Raw run JSON artifacts were generated.
Derived summary CSV was generated.
```

## Hermes Verification

Verified on 2026-05-18:

```bash
cd /root/ai-agency
set -a
source .env
set +a

curl -sS https://hermes.srv1314350.hstgr.cloud/health

curl -sS https://hermes.srv1314350.hstgr.cloud/v1/models \
  -H "Authorization: Bearer $API_SERVER_KEY"

curl -sS https://hermes.srv1314350.hstgr.cloud/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_SERVER_KEY" \
  -d '{"model":"hermes-agent","messages":[{"role":"user","content":"Reply with exactly: Hermes standalone verified"}]}'
```

Result:

```text
Health endpoint returned ok.
Models endpoint returned hermes-agent.
Chat completion returned: Hermes standalone verified.
```

Memory verification:

```text
Stored fact: Veloce Hermes memory code is Silver Atlas.
Separate request returned: Silver Atlas.
```

Hermes status:

```text
Hermes standalone: complete
Hermes memory persistence: complete
Hermes token overhead: known limitation
Paperclip -> Hermes HTTP wrapper: complete for connectivity
Paperclip -> Hermes exact-output testing: not recommended
```

## Partial or Deferred

### Open WebUI Tool Calling

Verified:

```text
Tool: Veloce Status Check
Imported from: https://raw.githubusercontent.com/dev4-gpt/veloce-research-os/main/tools/openwebui/status_check_tool.py
Working model: openai/gpt-oss-120b
Verified targets: hermes, paperclip, research_repo
```

Observed limitation:

```text
Mistral and Qwen variants did not reliably invoke the tool.
Use GPT OSS for tool-calling flows until other models are proven.
```

VPS health proof:

```text
aiagency-status-tool: healthy
aiagency-openwebui: healthy
aiagency-hermes: running
paperclip-iraj-paperclip-1: running
traefik-traefik-1: running
```

### Paperclip to Hermes

Paperclip's local Hermes adapter remains deferred, but v1.3 has a repository-backed HTTP wrapper that works through Hermes' verified OpenAI-compatible endpoint.

Reason:

```text
The adapter tries to run a local `hermes` command inside the Paperclip runtime. That command is not available in Paperclip's PATH.
```

Verified path:

```text
Paperclip -> /paperclip/adapters/hermes_http_agent_env.sh -> /paperclip/adapters/hermes_http_agent.mjs -> http://hermes:8642/v1/chat/completions
```

V1.3 shim docs:

```text
docs/paperclip-hermes-http-agent.md
```

Decision:

```text
Use direct NVIDIA models for fast Open WebUI work.
Use Hermes when agent behavior or memory is specifically needed.
Do not use Hermes for exact one-line acceptance tests.
Do not rely on Paperclip's local `hermes` command adapter.
```

### Ruflo / MCPO

MCPO is verified for v1.4 as the next Open WebUI tool expansion layer.

Verified service:

```text
aiagency-mcpo-time: healthy
Internal URL: http://mcpo-time:8000/openapi.json
Auth: Authorization: Bearer <MCPO_API_KEY>
Paths: /get_current_time, /convert_time
```

Verified direct tool call:

```json
{"timezone":"America/New_York","datetime":"2026-05-19T00:06:22-04:00","day_of_week":"Tuesday","is_dst":true}
```

Ruflo remains gated as an orchestration sandbox.

```text
Do not enable Ruflo in the default flow until it passes the isolation gate.
Ruflo should be evaluated as an isolated planning/orchestration experiment, not connected to production Paperclip issues, GitHub writes, or VPS infrastructure mutation.
```

Current Ruflo sandbox docs:

```text
docs/ruflo-sandbox-evaluation.md
docs/mcpo-ruflo-status-tool.md
docs/mcpo-ruflo-plan-tool.md
docs/v1.6-ruflo-planning-closeout.md
docs/pipeline-setup.md
```

Current Ruflo sandbox path:

```text
/opt/veloce-ruflo-sandbox
```

Ruflo sandbox validation:

```bash
docker run --rm \
  --volumes-from paperclip-iraj-paperclip-1 \
  -w /paperclip/instances/default/workspaces/8c81e4b2-d988-46f5-8cf8-4db07300db8a \
  python:3.12-slim \
  sh -lc 'pip install pytest >/tmp/pip.log && PYTHONPATH=. pytest -q'
```

Observed result:

```text
3 passed in 0.01s
```

## Restart Checks

Infrastructure stack:

```bash
cd /root/ai-agency
docker compose ps
docker compose up -d
```

Research repo:

```bash
cd /root/veloce-research-os
git pull
cd projects/reliability-policy-matrix
bash scripts/week1_day1_3.sh
python3 -m unittest discover -s tests
```

Hostinger Paperclip stack:

```bash
docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
```

## Paperclip Operating Rule

Paperclip is the task board and artifact generator.

GitHub and VPS are the source of truth for code.

If a Paperclip agent says it cannot access `/root/veloce-research-os`, complete the code change directly in GitHub, pull it on the VPS, verify it there, and then mark the Paperclip issue done with the commit hash.

## V1 Closeout Checklist

- [x] Confirm Paperclip Step 01-21 issues are Done.
- [x] Confirm recovery issues are Done or Cancelled.
- [x] Export main Paperclip markdown artifacts into Obsidian.
- [x] Commit and push this `SYSTEM_STATUS.md`.
- [x] Verify Hermes standalone response.
- [x] Verify Hermes memory persistence.
- [x] Verify Open WebUI and Hermes containers are running.
- [x] Verify `reliability-policy-matrix` tests pass on the VPS.
- [x] Verify MCPO time bridge container is healthy.
- [x] Verify MCPO `/docs` returns HTTP 200.
- [x] Verify MCPO `/openapi.json` exposes time tool paths.
- [x] Verify MCPO `/get_current_time` returns New York time JSON.
- [x] Verify Open WebUI chat can invoke the MCPO time bridge and produce proxy log proof.
- [x] Deploy and verify MCPO read-only `stack_status` tool.
- [x] Deploy and verify MCPO read-only `repo_status` tool.
- [x] Evaluate Ruflo in isolated planning-only sandbox after human approval.
- [x] Validate VEL-124 planning-only Ruflo sandbox bridge tests externally.
- [x] Implement read-only Open WebUI/MCPO `ruflo_status` endpoint.
- [x] Deploy and verify read-only Open WebUI/MCPO `ruflo_status` endpoint on the VPS.
- [x] Implement Paperclip-shaped planning-only Open WebUI/MCPO `ruflo_plan` endpoint.
- [x] Deploy and verify Paperclip-shaped planning-only Open WebUI/MCPO `ruflo_plan` endpoint on the VPS.
- [x] Implement approval-gated Open WebUI/MCPO `ruflo_execution_packet` endpoint for Paperclip handoff.
- [ ] Deploy and verify approval-gated Open WebUI/MCPO `ruflo_execution_packet` endpoint on the VPS.

## Recommended V1.3 Task

```text
Install and verify the Paperclip-to-Hermes HTTP shim so Paperclip can call Hermes through http://hermes:8642/v1 instead of trying to run a local hermes command.
```

Detailed plan:

```text
docs/v1.2-integration-plan.md
docs/v1.2-design-review.md
docs/status-check-tool.md
docs/paperclip-hermes-http-agent.md
docs/v1.4-hermes-mcpo-ruflo-plan.md
docs/mcpo-ruflo-setup.md
docs/mcpo-stack-status-tool.md
docs/mcpo-repo-status-tool.md
docs/mcpo-ruflo-status-tool.md
docs/mcpo-ruflo-plan-tool.md
docs/ruflo-sandbox-evaluation.md
docs/v1.6-ruflo-planning-closeout.md
docs/pipeline-setup.md
```
