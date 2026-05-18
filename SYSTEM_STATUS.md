# Veloce Research OS System Status

Date: 2026-05-18

## Summary

Veloce Research OS v1 is operational as a self-hosted research operating system running on the Hostinger VPS with Paperclip, Open WebUI, Hermes, direct NVIDIA model access, GitHub, Obsidian, and a runnable research project scaffold.

The system is ready for controlled use. Hermes is usable but should be treated as partial for v1 because memory persistence and Paperclip-to-Hermes execution are not fully validated.

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

## Partial or Deferred

### Hermes

Hermes is installed and reachable, but v1 should not depend on Hermes for every workflow.

Reasons:

- Hermes adds large agent-runtime context, making simple requests slower and token-heavy.
- Memory persistence still needs a formal two-session verification artifact.
- Paperclip's local Hermes adapter failed because the Paperclip runtime could not find a local `hermes` command.
- A proper Paperclip-to-Hermes HTTP adapter remains a v1.1 task.

Decision:

```text
Use direct NVIDIA models for fast Open WebUI work.
Use Hermes only when agent behavior or memory is specifically needed.
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

- [ ] Confirm Paperclip Step 01-21 issues are Done.
- [ ] Confirm recovery issues are Done or Cancelled.
- [ ] Export any new Paperclip markdown artifacts into Obsidian.
- [ ] Commit and push this `SYSTEM_STATUS.md`.
- [ ] Stop adding Paperclip issues until v1 status is frozen.

## Recommended V1.1 Task

```text
Add a Paperclip-to-Hermes HTTP adapter so Paperclip can call Hermes through https://hermes.srv1314350.hstgr.cloud instead of trying to run a local hermes command.
```
