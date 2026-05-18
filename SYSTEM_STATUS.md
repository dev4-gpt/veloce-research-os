# Veloce Research OS System Status

Date: 2026-05-18

## Summary

Veloce Research OS v1.1 is operational as a self-hosted research operating system running on the Hostinger VPS with Paperclip, Open WebUI, Hermes, direct NVIDIA model access, GitHub, Obsidian, and a runnable research project scaffold.

The system is ready for controlled use. Hermes standalone and Hermes memory persistence are verified. Paperclip-to-Hermes execution remains deferred because Paperclip's local Hermes adapter cannot find a local `hermes` command.

V1.2 core is also verified: Open WebUI can call the `Veloce Status Check` tool through the native Open WebUI tool interface when using `openai/gpt-oss-120b`.

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
- Open WebUI can call the `status_check_tool` native tool.
- `status_check_tool` verified `hermes`, `paperclip`, and `research_repo`.
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
Paperclip -> Hermes local adapter: deferred
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

Paperclip's local Hermes adapter remains deferred.

Reason:

```text
The adapter tries to run a local `hermes` command inside the Paperclip runtime. That command is not available in Paperclip's PATH.
```

Future fix:

```text
Add a Paperclip-to-Hermes HTTP adapter that calls https://hermes.srv1314350.hstgr.cloud/v1/chat/completions with API_SERVER_KEY.
```

Decision:

```text
Use direct NVIDIA models for fast Open WebUI work.
Use Hermes when agent behavior or memory is specifically needed.
Do not rely on Paperclip's local Hermes adapter yet.
```

### Ruflo / MCPO

Ruflo and MCPO are deferred.

Reason:

```text
The original Ruflo Docker image was not pullable during setup.
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

## Recommended V1.3 Task

```text
Add a Paperclip-to-Hermes HTTP adapter so Paperclip can call Hermes through https://hermes.srv1314350.hstgr.cloud instead of trying to run a local hermes command.
```

Detailed plan:

```text
docs/v1.2-integration-plan.md
docs/v1.2-design-review.md
docs/status-check-tool.md
```
