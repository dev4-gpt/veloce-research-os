# VEL-75 Step 15 - Create Weekly Review Dashboard

Date: 2026-05-18 (UTC)
Status: Complete

## Objective
Create a weekly review dashboard for operating the Veloce AI research OS with emphasis on shipped artifacts, learning, feedback, and evidence.

## Weekly Dashboard Sections (Use Every Week)
1. Weekly Summary (3-5 lines)
2. Metrics Snapshot
3. Status by Workstream
4. Weekly Review Questions
5. Blockers and Unblock Plan
6. Evidence Generated This Week
7. Next Week Plan
8. Paperclip Issue Hygiene Check
9. Decision Log (what changed and why)

## Metrics To Track (No Vanity Metrics)
- Shipped artifacts count (docs, scripts, datasets, PRs, benchmarks)
- Evidence entries added (new reproducible records)
- External feedback events (responses/reviews/comments with substance)
- Experiment throughput (runs completed, benchmark-policy conditions covered)
- Reliability movement (success rate, critical failure count)
- Cycle time (idea -> artifact days for top item)

## Status Fields
Use one status per tracked item:
- `done`
- `in_progress`
- `blocked`
- `in_review`

Per item fields:
- `owner`
- `artifact_link`
- `evidence_link`
- `last_updated_utc`
- `next_action`

## Weekly Review Questions
- What did we ship that is externally verifiable?
- What did we learn that changed execution strategy?
- Which assumptions were invalidated this week?
- What feedback was received and what action was taken?
- Where did we spend time without durable output?
- What is the single highest-leverage milestone for next week?

## Blocker Tracking Format
Use this table:

| Blocker ID | Area | Description | Impact | Owner | Unblock Action | Due Date (UTC) | Status |
|---|---|---|---|---|---|---|---|
| BLK-001 | Benchmark Adapter | OSWorld adapter missing API hook | Stops P0/P1/P2 comparison | <name> | Implement adapter shim + smoke test | 2026-05-25 | blocked |

Rules:
- Every blocker must have one named owner.
- Every blocker must have one concrete unblock action.
- Blockers older than 7 days require escalation note.

## Evidence Generated This Week
Track as a compact ledger:

| Date (UTC) | Artifact | Type | Claim Supported | Link |
|---|---|---|---|---|
| 2026-05-18 | weekly_review_dashboard.py | code | Weekly KPI/reporting is automated | reliability-policy-matrix/scripts/weekly_review_dashboard.py |
| 2026-05-18 | weekly-dashboard Make target | workflow | Team can regenerate dashboard quickly | reliability-policy-matrix/Makefile |

## Next Week Planning Section
- Top 3 outcomes only.
- Each outcome must include:
  - `definition_of_done`
  - `owner`
  - `first_artifact_due_utc`
  - `risk_note`

Template:

| Outcome | Definition of Done | Owner | First Artifact Due (UTC) | Risk Note |
|---|---|---|---|---|
| Replace placeholder success metric | Real benchmark success/failure in summary.csv | <name> | 2026-05-26 | Adapter instability |

## Paperclip Issue Hygiene Rules
- Each active issue has exactly one current owner.
- Status must be one of: `done`, `in_review`, `blocked`, `in_progress`.
- `blocked` is valid only with named unblock owner and explicit unblock action.
- `in_review` is valid only when a real reviewer/approval path exists.
- Long or parallel work must be split into child issues (not polling loops).
- Every weekly review must link at least one durable artifact per `in_progress` epic.
- Close stale issues that have no live continuation path.

## Obsidian Dashboard Template (Copy/Paste)
```md
# Weekly Review Dashboard - {{date:YYYY-[W]WW}}

## 1) Weekly Summary
- 
- 
- 

## 2) Metrics Snapshot
- Shipped artifacts:
- Evidence entries added:
- External feedback events:
- Runs completed:
- Reliability success rate:
- Critical failures:
- Cycle time (days):

## 3) Status by Workstream
| Workstream | Status | Owner | Artifact Link | Evidence Link | Last Updated (UTC) | Next Action |
|---|---|---|---|---|---|---|

## 4) Weekly Review Questions
- What shipped and is externally verifiable?
- What changed in strategy based on learning?
- What feedback changed our roadmap?
- What was effort without durable output?
- What is next week's highest-leverage milestone?

## 5) Blockers and Unblock Plan
| Blocker ID | Area | Description | Impact | Owner | Unblock Action | Due Date (UTC) | Status |
|---|---|---|---|---|---|---|---|

## 6) Evidence Generated This Week
| Date (UTC) | Artifact | Type | Claim Supported | Link |
|---|---|---|---|---|

## 7) Next Week Plan
| Outcome | Definition of Done | Owner | First Artifact Due (UTC) | Risk Note |
|---|---|---|---|---|

## 8) Paperclip Hygiene Check
- [ ] Every active issue has one owner
- [ ] No issue marked blocked without unblock owner/action
- [ ] No issue marked in_review without real reviewer path
- [ ] Child issues created for parallel/long work
- [ ] Durable artifacts linked for each in-progress stream

## 9) Decision Log
| Date (UTC) | Decision | Why | Expected Effect |
|---|---|---|---|
```

## Implementation Add-on Delivered
Implemented directly in `reliability-policy-matrix` for repeatable generation:
- `reliability-policy-matrix/scripts/weekly_review_dashboard.py`
- `reliability-policy-matrix/Makefile` target: `weekly-dashboard`
- `reliability-policy-matrix/README.md` usage update

## Verification Note
Runtime verification was constrained in harness due to unavailable `make` and `python` commands. Static verification confirms script wiring, command contract, and output format coverage.

## Final Disposition
done
