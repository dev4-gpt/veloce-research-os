# Veloce AI Research OS v1

This is the consolidated operating pack created from the completed Paperclip Step 01-15 workflow.

## Current Status

Paperclip planning phase: complete

Obsidian artifact sync: complete

Selected flagship project: **Reliability Policy Matrix for Computer-Use Agents**

Repository name: `reliability-policy-matrix`

## What We Built

We used Paperclip as the task/orchestration layer to create a research operating system for Veloce AI. The workflow started broad with 100 sources across AI agents, computer vision, NLP, LLMs, automation, and AI systems engineering, then narrowed into a top-20 summary pass, research direction synthesis, flagship project selection, 30-day execution plan, evidence ledger, public content, repo scaffold, outreach plan, and weekly dashboard.

This is not legal advice. The immigration-related parts are framed as evidence organization and attorney-review preparation only.

## Core System

```text
Paperclip = issue/task control plane
Open WebUI = chat front door
Hermes = heavy agent runtime with memory, useful but not default for fast summarization
NVIDIA direct = fast model lane for everyday chat/model work
Obsidian = durable knowledge base and operating manual
```

## Artifact Index

Start here:

- [[Veloce AI Research OS/Indexes/Veloce AI Research OS v1 - Artifact Index|Artifact Index]]

## Primary Artifacts

### Source Map and Summaries

- [[Veloce AI Research OS/Artifacts/VEL-31_step01_100_sources_table|Step 01 - 100-source table]]
- [[Veloce AI Research OS/Artifacts/VEL-32_step02_top20_and_5_themes|Step 02 - validated top 20 and 5 themes]]
- [[Veloce AI Research OS/Artifacts/VEL-33_step03_priority_sources_1-5|Step 03 - sources 1-5]]
- [[Veloce AI Research OS/Artifacts/VEL-34_step04_priority_sources_6-10|Step 04 - sources 6-10]]
- [[Veloce AI Research OS/Artifacts/VEL-35_step05_priority_sources_11-15|Step 05 - sources 11-15]]
- [[Veloce AI Research OS/Artifacts/VEL-36_step06_priority_sources_16-20|Step 06 - sources 16-20]]

### Strategy and Project

- [[Veloce AI Research OS/Artifacts/VEL-56_step07_synthesis_top20_to_research_directions|Step 07 - research direction synthesis]]
- [[Veloce AI Research OS/Artifacts/VEL-59_step08_first_30_day_flagship_project|Step 08 - flagship project selection]]
- [[Veloce AI Research OS/Artifacts/VEL-61_step09_30_day_execution_plan_flagship|Step 09 - 30-day execution plan]]

### Execution Assets

- [[Veloce AI Research OS/Artifacts/VEL-63_step10_evidence_ledger_structure|Step 10 - evidence ledger structure]]
- [[Veloce AI Research OS/Artifacts/VEL-64_step11_public_research_article_package|Step 11 - public research article package]]
- [[Veloce AI Research OS/Artifacts/VEL-68_step12_technical_repo_scaffold|Step 12 - technical repo scaffold]]
- [[Veloce AI Research OS/Artifacts/VEL-71_step13_outreach_target_list|Step 13 - outreach target list]]
- [[Veloce AI Research OS/Artifacts/VEL-73_step14_outreach_message_drafts|Step 14 - outreach message drafts]]
- [[Veloce AI Research OS/Artifacts/VEL-75_step15_weekly_review_dashboard|Step 15 - weekly review dashboard]]

## Flagship Project

Working title:

```text
Reliability Policy Matrix for Computer-Use Agents
```

Repository name:

```text
reliability-policy-matrix
```

Core question:

```text
Which reliability policy stack produces the best completion/reliability tradeoff on realistic computer-use tasks under fixed action and token budgets?
```

Initial benchmark slice:

```text
OSWorld subset
VisualWebArena subset
ITBench subset
```

Initial policy variants:

```text
P0 = ReAct baseline
P1 = ReAct + reflection checkpoint
P2 = ReAct + recovery playbook
```

Primary metrics:

```text
Task completion rate
Success-under-budget rate
Critical failure rate
Mean steps-to-completion
Re-run variance across 3 seeded reruns
```

## 30-Day Execution Plan

The full plan lives here:

- [[Veloce AI Research OS/Artifacts/VEL-61_step09_30_day_execution_plan_flagship|Step 09 - 30-day execution plan]]

Milestones:

```text
Day 7: deterministic baseline pipeline complete
Day 14: P0/P1/P2 runnable from one matrix config
Day 21: full matrix executed with 3-seed reruns and aggregate tables
Day 30: reproducibility pass, report, and demo package published
```

Immediate Days 1-3:

1. Initialize repository scaffold with `src`, `configs`, `scripts`, `reports`, and `docs`.
2. Set up dependency management and lockfile.
3. Add CI for lint and unit smoke checks.
4. Implement run logging schema with `run_id`, `seed`, `git_sha`, policy, benchmark, budget, and outcome.
5. Draft benchmark subset manifests for OSWorld, VisualWebArena, and ITBench.

## Repo Scaffold

Use this as the build source:

- [[Veloce AI Research OS/Artifacts/VEL-68_step12_technical_repo_scaffold|Step 12 - technical repo scaffold]]

Expected structure:

```text
reliability-policy-matrix/
  pyproject.toml
  README.md
  .gitignore
  .env.example
  configs/
  manifests/
  src/rpmatrix/
  scripts/
  tests/
  artifacts/
```

First 10 GitHub issues are listed in Step 12.

## Evidence System

Use this as the evidence source:

- [[Veloce AI Research OS/Artifacts/VEL-63_step10_evidence_ledger_structure|Step 10 - evidence ledger structure]]

Track:

```text
paper summaries
code commits
experiment results
public articles
outreach messages
expert feedback
presentations/talks
repository metrics
```

Every claim should eventually link to concrete evidence, not memory.

## Public Writing

Use this as the first article package:

- [[Veloce AI Research OS/Artifacts/VEL-64_step11_public_research_article_package|Step 11 - public research article package]]

Rule:

```text
Publish only after human review.
Do not overclaim results before experiments exist.
Frame the work as a research/build journey.
```

## Outreach

Targets:

- [[Veloce AI Research OS/Artifacts/VEL-71_step13_outreach_target_list|Step 13 - outreach target list]]

Message drafts:

- [[Veloce AI Research OS/Artifacts/VEL-73_step14_outreach_message_drafts|Step 14 - outreach message drafts]]

Rule:

```text
Do not send automated outreach. Use drafts for human-reviewed messages only.
```

## Weekly Review

Use:

- [[Veloce AI Research OS/Artifacts/VEL-75_step15_weekly_review_dashboard|Step 15 - weekly review dashboard]]

Weekly review sections:

1. Weekly summary.
2. Metrics snapshot.
3. Status by workstream.
4. Weekly review questions.
5. Blockers and unblock plan.
6. Evidence generated this week.
7. Next week plan.
8. Paperclip issue hygiene check.
9. Decision log.

## Paperclip Lessons To Preserve

1. A comment saying `Final disposition: done` does not reliably mark an issue Done. The human must still set status to Done.
2. Recovery issues are usually administrative. If the source issue has a valid artifact and is manually resolved, mark the recovery issue Done or Cancelled.
3. Broken Paperclip artifact links can be recovered from the container and copied into Obsidian.
4. `Hermes Agent (local)` failed in Paperclip because it tried to run a local `hermes` command that was not in PATH.
5. Direct NVIDIA/OpenRouter/Open WebUI lanes are better for fast summarization; Hermes is better reserved for heavier agent/memory behavior.
6. Do not create more planning issues until the first build week starts.

## Next Action

Create the actual `reliability-policy-matrix` repository from Step 12 and begin Days 1-3 from Step 09.

Do not create Step 16 in Paperclip yet.

First execution task:

```text
Create repository scaffold for reliability-policy-matrix and commit the initial runnable skeleton.
```

Use this issue title when ready:

```text
Build Week 1 Day 1-3 scaffold for reliability-policy-matrix
```

Recommended assignee:

```text
Technical Builder
```
