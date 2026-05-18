# VEL-64 Step 11 - Public Research Article Package

Date: 2026-05-18 (UTC)
Status: Complete draft package

## 1) Article Title
A Practical Reliability Matrix for Computer-Use Agents

## 2) Subtitle
How we are building a reproducible benchmark workflow to compare baseline, reflection, and recovery policies under fixed budgets

## 3) Target Audience
- Applied AI engineers building agent systems.
- Research engineers running evaluation pipelines.
- Technical product and infra leads who need reproducible reliability signals.

## 4) Full Article Draft
### A Practical Reliability Matrix for Computer-Use Agents

Computer-use agents are moving fast, but reliability is still inconsistent when tasks are repeated under budget constraints. Most public demonstrations show a single successful trajectory. Deployment decisions require evidence across many tasks, seeded reruns, and explicit failure analysis.

We are starting a research and build cycle around a Reliability Policy Matrix: a reproducible framework to compare reliability policies on scoped benchmark subsets. The objective is not to publish a universal winner. The objective is to create a transparent, auditable method for measuring tradeoffs and improving agent behavior over time.

#### Problem framing
Three problems make current reliability claims difficult to trust:
- One-off success is often mistaken for stable capability.
- Configuration details are frequently incomplete, which blocks replication.
- Failure modes are not consistently labeled, so teams cannot compare regressions over time.

Our approach is engineering-first: fixed scopes, explicit configs, repeatable runs, and traceable evidence artifacts.

#### Research question
Which policy stack gives the strongest completion and reliability tradeoff for computer-use tasks under fixed action and token budgets?

#### Scope for the first 30-day cycle
Benchmarks (subset only):
- OSWorld
- VisualWebArena
- ITBench

Policy variants:
- `P0`: ReAct baseline
- `P1`: ReAct plus reflection checkpoint
- `P2`: ReAct plus recovery playbook

Primary outcomes:
- completion rate
- success-under-budget rate
- critical failure rate
- mean steps to completion
- variance across 3 seeded reruns

This first cycle is intentionally narrow so the pipeline is reproducible before it is broad.

#### Method and reproducibility contract
All conditions are run through a unified matrix config over policy x benchmark combinations.

Minimum reproducibility contract:
- pinned dependencies via lockfile
- explicit random seeds captured in run metadata
- run IDs linked to git SHA
- immutable raw logs
- separate derived tables and figures

This contract is mandatory for any claim we publish.

#### What we expect to learn
Current hypotheses:
- Reflection may improve completion where local correction is enough.
- Recovery playbooks may reduce critical failures in long-horizon tasks.
- Effects will vary by benchmark type; no policy should be assumed dominant everywhere.

The near-term decision value is practical: identify where reliability gains are real, where they are noisy, and where additional policy work is justified.

#### Initial failure taxonomy
To support analysis and iteration, we will label failures into categories such as:
- state-tracking drift
- premature termination
- budget exhaustion
- recovery-loop instability
- environment/action mismatch

A useful benchmark report must explain both successes and failures.

#### Evidence standards for public reporting
We will only publish claims with:
- exact benchmark subset definitions
- full config references
- seed-level summaries, not only aggregate means
- explicit limitations and threats to validity
- at least one reproducible rerun path from clean setup

#### Known limitations
This cycle does not cover full benchmark distributions, all policy families, or production deployment behavior. It is a scoped foundation for reliable comparison.

#### 30-day outputs
Planned outputs:
1. Public repository with runnable matrix pipeline.
2. Subset manifests and policy configs.
3. Raw logs plus aggregate metrics tables and figures.
4. Technical report with methods, results, and limitations.
5. Replayable demo script or notebook.

#### Closing position
Reliability progress for computer-use agents should be measured through repeatable evaluation loops, not isolated demos. A strict policy matrix and evidence contract gives teams a defensible way to compare policies, understand failure patterns, and improve with less ambiguity.

## 5) Five Alternative Hooks
1. Most agent demos prove possibility; this project focuses on reproducibility.
2. Reliability is not a screenshot, it is a distribution across reruns.
3. We are treating agent evaluation like engineering infrastructure, not marketing output.
4. Before scaling capability, we need policy comparisons that survive fixed budgets and fixed seeds.
5. The fastest path to better agents is measurable failure analysis, not anecdotal wins.

## 6) Five LinkedIn Post Variants
1. We are launching a Reliability Policy Matrix for computer-use agents. The goal is a reproducible evaluation workflow that compares baseline, reflection, and recovery policies across scoped benchmark subsets under fixed budgets. This is a build journey, not a claim of final results. We will publish configs, logs, and limitations.

2. New research direction: reliability benchmarking for computer-use agents with explicit seeds, pinned dependencies, and policy-by-benchmark comparisons. We are prioritizing auditable methods over one-off demos. First cycle scope: OSWorld, VisualWebArena, and ITBench subsets.

3. We are sharing the first draft of our public research article on agent reliability. Core principle: no overclaims, only reproducible evidence. Our matrix evaluates `P0` ReAct, `P1` reflection, and `P2` recovery policies under fixed action/token budgets.

4. Agent reliability needs better measurement discipline. Our 30-day plan builds a unified matrix runner, multi-seed reruns, and a failure taxonomy so teams can reason about tradeoffs with real evidence. Public draft now prepared.

5. This cycle is about infrastructure for trustworthy agent evaluation: scoped benchmarks, traceable run metadata, and publishable methods. We are sharing our first public article draft and will follow with runnable artifacts.

## 7) Five X/Twitter Post Variants
1. We drafted our first public note on computer-use agent reliability. Focus: reproducible policy benchmarking, not one-off demos. `P0` ReAct vs `P1` reflection vs `P2` recovery on scoped benchmarks.

2. Reliability for agents should be measured across reruns, not screenshots. We are building a policy matrix with fixed seeds, fixed budgets, and explicit configs.

3. New draft: "A Practical Reliability Matrix for Computer-Use Agents." Goal is transparent tradeoff measurement with auditable artifacts.

4. We are treating agent eval as engineering infrastructure: reproducibility contract, failure taxonomy, and seed-level reporting.

5. First 30-day scope: OSWorld/VisualWebArena/ITBench subsets + 3 policy variants + multi-seed runs. Build journey, no overclaims.

## 8) Suggested Visuals or Diagrams
1. Policy Matrix Diagram:
- Rows: benchmark subsets.
- Columns: policy variants (`P0`, `P1`, `P2`).
- Cells: completion and critical-failure metrics.

2. Reproducibility Pipeline Flow:
- Config -> runner -> raw logs -> aggregation -> figures -> report.
- Annotate each stage with required metadata.

3. Failure Taxonomy Breakdown Chart:
- Stacked bars per policy variant showing failure category distribution.

4. Seed Variance Plot:
- Per-condition point/range plot across three seeds to show stability.

5. Budget vs Outcome Tradeoff Plot:
- X-axis budget usage, Y-axis completion/success-under-budget rate.

## 9) Human Review Checklist Before Publishing
- Title and subtitle accurately reflect scope and avoid claiming final results.
- Tone is technical and credible; no hype language.
- All statements about outcomes are framed as hypotheses or planned measurements unless data exists.
- Benchmark scope is explicitly labeled as subset-based.
- Policy labels (`P0`, `P1`, `P2`) are used consistently.
- Reproducibility contract items are present and concrete.
- Limitations and threats to validity are included.
- No immigration, legal, or eligibility claims appear.
- Social post variants match the same claim boundaries as the article.
- Visual suggestions are implementable from available artifacts.
