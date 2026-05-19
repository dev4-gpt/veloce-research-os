# Ruflo Sandbox Evaluation

Date: 2026-05-19

## Purpose

This is the v1.5C sandbox gate for Ruflo.

Ruflo is not part of the production Veloce flow yet. The goal is to evaluate it as a planning-only orchestration layer without giving it production secrets, write access, Paperclip mutation rights, or GitHub write rights.

Official upstream:

```text
https://github.com/ruvnet/ruflo
```

## Current Upstream Install Paths

From the upstream README, the current CLI paths are:

```bash
npx ruflo@latest init wizard
npx ruflo@latest init
npm install -g ruflo@latest
```

The upstream README also lists a POSIX installer:

```bash
curl -fsSL https://cdn.jsdelivr.net/gh/ruvnet/ruflo@main/scripts/install.sh | bash
```

Ruflo MCP registration for Claude Code is listed as:

```bash
claude mcp add ruflo -- npx ruflo@latest mcp start
```

## Veloce Decision

Use `npx ruflo@latest init wizard` only inside an isolated sandbox, after human approval.

Do not run the one-line `curl | bash` installer on the production VPS for the first evaluation.

Reason:

```text
Ruflo is powerful and can install hooks, MCP servers, agents, memory, and background orchestration.
Veloce already had blocked-agent loops, so the first Ruflo test must be planning-only.
```

## Sandbox Directory

Use:

```text
/opt/veloce-ruflo-sandbox
```

This directory must not be inside:

```text
/root/ai-agency
/root/veloce-research-os
/docker/paperclip-iraj
```

## Environment Rules

No production secrets:

```text
Do not source /root/ai-agency/.env.
Do not pass API_SERVER_KEY.
Do not pass NVIDIA_API_KEY.
Do not pass MCPO_API_KEY.
Do not pass Paperclip API keys.
Do not mount Obsidian.
```

No production writes:

```text
Do not mount /root/ai-agency as writable.
Do not mount /root/veloce-research-os as writable.
Do not allow Ruflo to edit Paperclip issues.
Do not allow Ruflo to push to GitHub.
```

## Planning-Only Test Goal

Initial prompt:

```text
Given this goal: "Add a read-only artifact_index tool to Veloce Open WebUI."
Produce a plan with owner, next action, verification command, and rollback note.
Do not execute commands.
Do not modify files.
Do not call external services.
```

Acceptance:

```text
Ruflo produces a structured plan.
No files outside /opt/veloce-ruflo-sandbox are modified.
No Paperclip issue is modified.
No GitHub write happens.
No VPS infrastructure config is changed.
Rollback command is documented.
```

## Human-Approved Test Commands

Run only after explicit human approval:

```bash
mkdir -p /opt/veloce-ruflo-sandbox
cd /opt/veloce-ruflo-sandbox

npx ruflo@latest init wizard
```

If Ruflo asks for hooks, production workspace paths, or secrets during the wizard:

```text
Decline them for the first evaluation.
```

If a non-interactive dry run is available in the installed version, prefer it. Otherwise, keep the wizard manual and stop before production integration.

## Rollback

```bash
rm -rf /opt/veloce-ruflo-sandbox
npm uninstall -g ruflo || true
```

If the wizard created home-directory config, inspect before deleting:

```bash
find "$HOME" -maxdepth 3 \
  \( -iname '*ruflo*' -o -iname '*claude-flow*' \) \
  -print
```

Do not delete files blindly.

## Decision

Current decision:

```text
Prepared, not production-enabled.
Adopt only after a planning-only sandbox run is verified.
```

Recommended next state after sandbox pass:

```text
Adopt Ruflo as a planning assistant only.
Do not allow Ruflo to mutate Paperclip, GitHub, Docker, or production files until v1.6+.
```
