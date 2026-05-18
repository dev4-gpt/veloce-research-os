# Draft Article: A Practical Reliability Matrix for Computer-Use Agents

Author: VEL research pipeline (draft)
Date: 2026-05-17 (UTC)
Status: First public draft

## Abstract
Computer-use agents are improving quickly, but reliability remains inconsistent under realistic task and budget constraints. This article proposes a practical Reliability Policy Matrix: a reproducible framework that compares three policy stacks on benchmark subsets and reports completion, budget adherence, and failure behavior with multi-seed reruns. The goal is not to declare a universally best policy, but to provide a transparent method for measuring tradeoffs and producing comparable evidence.

## Why This Work Matters
Most public demos optimize for one successful trajectory. Real-world deployment requires stable performance across many tasks, repeated runs, and constrained budgets.

The key problem:
- Success in one run does not establish reliability.
- Reliability claims are often not reproducible due to hidden settings.
- Failure modes are rarely logged in a way others can audit.

The practical need is a repeatable, engineering-first workflow for reliability benchmarking.

## Research Question
Which reliability policy stack produces the best completion/reliability tradeoff for computer-use tasks under fixed action and token budgets?

## Scope (First 30-Day Slice)
Benchmarks (subset only):
- OSWorld
- VisualWebArena
- ITBench

Policy variants:
- `P0`: ReAct baseline
- `P1`: ReAct + reflection checkpoint
- `P2`: ReAct + recovery playbook

Primary outcomes:
- task completion rate
- success-under-budget rate
- critical failure rate
- mean steps-to-completion
- rerun variance across 3 seeds

## Method Overview
The Reliability Policy Matrix uses one experiment config that spans policy x benchmark conditions. Each condition is rerun across fixed seeds with pinned dependencies and logged metadata.

Minimum reproducibility contract:
- pinned dependency lockfile
- explicit random seed capture
- run IDs linked to git SHA
- immutable raw logs
- generated aggregate tables/figures in separate outputs

This structure keeps claims traceable and repeatable.

## What We Expect to Learn
Hypothesis set:
- Reflection (`P1`) may improve completion on tasks where local correction is enough.
- Recovery playbooks (`P2`) may reduce critical failures on long-horizon tasks.
- Gains will likely vary by benchmark type; no single policy should be assumed dominant everywhere.

Expected decision value:
- Identify which policy provides the most reliable improvement per compute/action budget.
- Quantify where each policy fails so future work can target those failure classes directly.

## Example Failure Taxonomy (Initial)
Planned taxonomy labels for error analysis:
- state-tracking drift
- premature termination
- budget exhaustion
- recovery-loop instability
- environment/action mismatch

This taxonomy is intended for engineering diagnosis, not model ranking theater.

## Credible Evidence Standards
To avoid overclaiming, public reporting should include:
- exact subset definitions for each benchmark
- full config references for all runs
- seed-level result summaries (not only averages)
- known limitations and threats to validity
- at least one externally reproducible rerun path

## Initial Limitations
This first cycle is intentionally narrow:
- subset coverage, not full benchmark coverage
- three policy variants only
- budget settings fixed for comparability
- no legal or product claims inferred from benchmark outputs

## 30-Day Deliverables
Planned outputs for this research cycle:
1. Public code repository with runnable matrix pipeline.
2. Benchmark subset manifests and policy configs.
3. Raw logs plus aggregate metrics tables and figures.
4. Technical report with methods, results, limitations.
5. Replayable demo script or notebook.

## Early Publication Positioning
Proposed publication framing for the first public release:
- "We built a reproducible reliability benchmarking workflow for computer-use agents."
- "We compare baseline, reflection, and recovery policies under fixed budgets."
- "We release configs, logs, and analysis artifacts so results can be audited and extended."

Avoid framing as:
- final ranking of all agent methods,
- universal policy recommendation,
- evidence of generalized autonomy progress.

## Next Steps
Near-term execution priorities:
- finalize benchmark subset manifests
- complete baseline deterministic run path
- implement reflection and recovery policy wrappers
- execute 3-seed matrix runs and publish initial tables

## Suggested Public Metadata
If published as a blog or technical note, include:
- canonical title
- publication date/time (UTC)
- commit SHA / release tag
- reproduction quickstart command
- contact path for replication issues

## Conclusion
Reliability progress depends less on isolated demos and more on transparent, repeatable evaluation loops. A policy matrix with strict reproducibility rules makes it possible to compare reliability strategies credibly, understand failure modes, and iterate on methods that hold up under repeated use.
