# VEL-32 Step 02 - Validated Top 20 Sources + 5 Research Themes

Scope: computer vision, AI agents, automation, and F-1 long-term O-1 evidence-building.

Method:
- Started from Step 01 longlist and refreshed with recent benchmark/agent literature.
- Prioritized sources with strong reproducibility value, active community adoption, and clear publication paths.
- Weighted for O-1-aligned evidence potential: peer-reviewed outputs, open-source impact, benchmarking leadership, invited visibility.

Priority key:
- P0: highest near-term leverage for publishable results and O-1 evidence accumulation.
- P1: high value support sources for methods depth and framing.

## A) Top 20 Validated Sources (ranked)

1. (P0) OSWorld: Benchmarking Multimodal Agents for Open-Ended Tasks in Real Computer Environments (2024)  
https://arxiv.org/abs/2404.07972  
Rationale: Core benchmark for desktop computer-use agents; direct fit to automation and agent reliability research.

2. (P0) VisualWebArena: Evaluating Multimodal Agents on Realistic Visual Web Tasks (2024)  
https://arxiv.org/abs/2401.13649  
Rationale: Strong complementary benchmark to OSWorld for web-based GUI workflows.

3. (P0) WebArena: A Realistic Web Environment for Building Autonomous Agents (2023)  
https://arxiv.org/abs/2307.13854  
Rationale: Foundational web-agent benchmark with active use in agent evaluation papers.

4. (P0) TheAgentCompany: Benchmarking LLM Agents on Consequential Real World Tasks (2024)  
https://arxiv.org/abs/2412.14161  
Rationale: Long-horizon workplace-style automation tasks; strong relevance to practical AI automation.

5. (P0) CRAB: Cross-environment Agent Benchmark for Multimodal Language Model Agents (2024)  
https://arxiv.org/abs/2407.01511  
Rationale: Cross-platform benchmark design supports generalization claims across environments.

6. (P0) ITBench: Evaluating AI Agents across Diverse Real-World IT Automation Tasks (2025)  
https://arxiv.org/abs/2502.05352  
Rationale: Directly aligned with enterprise automation; useful for measurable business-impact narratives.

7. (P0) AgentBench: Evaluating LLMs as Agents (2023)  
https://arxiv.org/abs/2308.03688  
Rationale: Broad reference benchmark for cross-task agent capabilities; useful baseline anchor.

8. (P0) GAIA: A Benchmark for General AI Assistants (2023)  
https://arxiv.org/abs/2311.12983  
Rationale: Strong high-difficulty assistant benchmark to stress reasoning + tool use.

9. (P0) ReAct: Synergizing Reasoning and Acting in Language Models (2022)  
https://arxiv.org/abs/2210.03629  
Rationale: Fundamental prompting/control pattern used in many modern agent pipelines.

10. (P0) Reflexion: Language Agents with Verbal Reinforcement Learning (2023)  
https://arxiv.org/abs/2303.11366  
Rationale: Self-improvement loop approach; high utility for reliability and recovery experiments.

11. (P0) Toolformer: Language Models Can Teach Themselves to Use Tools (2023)  
https://arxiv.org/abs/2302.04761  
Rationale: Important conceptual basis for external tool integration and automation workflows.

12. (P0) Voyager: An Open-Ended Embodied Agent with Large Language Models (2023)  
https://arxiv.org/abs/2305.16291  
Rationale: Demonstrates iterative skill libraries and long-horizon planning in embodied settings.

13. (P0) OpenVLA: An Open-Source Vision-Language-Action Model (2024)  
https://arxiv.org/abs/2406.09246  
Rationale: Strong bridge from CV+VLM to action, with open reproducibility and extension potential.

14. (P0) RT-2: Vision-Language-Action Models Transfer Web Knowledge to Robotic Control (2023)  
https://arxiv.org/abs/2307.15818  
Rationale: High-impact VLA reference for grounding perception in action.

15. (P0) Segment Anything (SAM) (2023)  
https://arxiv.org/abs/2304.02643  
Rationale: Widely adopted CV component; useful for perception modules in agent pipelines.

16. (P0) DINOv2: Learning Robust Visual Features without Supervision (2023)  
https://arxiv.org/abs/2304.07193  
Rationale: High-quality visual representations that improve robustness for downstream agent tasks.

17. (P1) CLIP: Learning Transferable Visual Models From Natural Language Supervision (2021)  
https://arxiv.org/abs/2103.00020  
Rationale: Essential vision-language grounding reference.

18. (P1) SWE-bench: Can Language Models Resolve Real-World GitHub Issues? (2023)  
https://arxiv.org/abs/2310.06770  
Rationale: Useful automation benchmark analog for measurable agent productivity.

19. (P1) CORE-Bench: Computational Reproducibility Agent Benchmark (2024)  
https://arxiv.org/abs/2409.11363  
Rationale: Strong fit for reproducibility-first contribution strategy (high credibility signal).

20. (P1) PaperBench: Evaluating AI's Ability to Replicate AI Research (2025)  
https://arxiv.org/abs/2504.01848  
Rationale: Directly tied to replication quality, which supports strong evidence of original contribution.

## B) Five Prioritized Research Themes

### Theme 1 (P0): Reliable Computer-Use Agents for Real GUI Work
Core question: How can multimodal agents reliably complete long-horizon desktop and web tasks with low failure rates?
- Primary sources: OSWorld, VisualWebArena, WebArena, TheAgentCompany, ITBench.
- O-1 evidence angle: benchmark publications, reproducible harnesses, leaderboard visibility, open-source eval tooling.
- Immediate next actions (2 weeks):
  1. Stand up unified eval harness on OSWorld + VisualWebArena.
  2. Reproduce 2-3 baseline agents with fixed prompts/tools.
  3. Publish initial failure taxonomy and recovery-loop ablations.

### Theme 2 (P0): Agent Reliability Through Reflection, Tooling, and Recovery Policies
Core question: Which control policies (ReAct/Reflexion/tool-use gating) most reduce compounding errors?
- Primary sources: ReAct, Reflexion, Toolformer, AgentBench, GAIA.
- O-1 evidence angle: method paper with ablations + practical reliability framework used by others.
- Immediate next actions:
  1. Build a modular controller with swap-in policies.
  2. Run cross-benchmark ablations (success, cost, latency, recovery rate).
  3. Release code + standardized eval config.

### Theme 3 (P0): Vision-Language-Action Transfer from CV Foundations to Automation
Core question: How do strong CV/VLM representations improve downstream agent action quality?
- Primary sources: OpenVLA, RT-2, CLIP, DINOv2, SAM.
- O-1 evidence angle: cross-domain method contribution linking vision quality to automation outcomes.
- Immediate next actions:
  1. Compare perception backbones in the same agent stack.
  2. Quantify grounding errors vs task failures.
  3. Submit findings to a CV/agents workshop.

### Theme 4 (P1): Reproducibility as a First-Class Research Product
Core question: Can reproducibility benchmarks become a differentiating research identity?
- Primary sources: CORE-Bench, PaperBench, SWE-bench.
- O-1 evidence angle: credible third-party uptake of reproducible pipelines, independent replications, citable artifacts.
- Immediate next actions:
  1. Release one-click replication scripts and data cards.
  2. Produce an audit report for 3 selected papers/tasks.
  3. Propose a reproducibility challenge track/workshop submission.

### Theme 5 (P1): Domain-Specific Automation Benchmarks (IT/SRE First)
Core question: How should general agent methods be adapted for high-stakes operational workflows?
- Primary sources: ITBench, AgentBench, TheAgentCompany.
- O-1 evidence angle: real-world impact narrative via domain benchmarks and industry collaboration.
- Immediate next actions:
  1. Select one operational domain (incident triage or change management).
  2. Extend existing benchmark tasks with domain constraints.
  3. Publish benchmark extension + baseline results.

## C) Ranked Conferences and Venues For These Themes

1. CVPR / ICCV / ECCV (computer vision + multimodal perception)
2. NeurIPS / ICLR (general ML + agent methods + benchmarks)
3. CoRL / RSS (VLA and embodied transfer)
4. AAAI / ICAPS / AAMAS (automation, planning, multi-agent structure)
5. Domain workshops (reproducibility, benchmarks, AI for operations)

## D) Ranked Labs and Author Clusters To Track

1. Stanford (vision + embodied + agents)
2. Berkeley BAIR (robotics/embodied + agentic systems)
3. CMU RI (automation + robotics + HCI intersections)
4. Princeton Vision / MIT CSAIL Vision / ETH Vision (core CV and representation strength)
5. Microsoft Research / Google DeepMind / OpenAI / AI2 (agent benchmarks and system-level evaluations)

## E) O-1 Evidence-Building Roadmap (12-18 months)

1. Publish 1 strong first-author paper in a top-tier venue or top workshop with clear benchmark gains.
2. Maintain 1 open-source benchmark/eval repo with reproducibility standards and external adoption.
3. Produce 2-3 citable technical reports/preprints with thorough ablations and failure analysis.
4. Build scholarly service: reviews, workshop participation, public talks/posters.
5. Establish independent recognition signals: citations, invited collaborations, external references to your benchmark tooling.

## F) What To Execute Next (Immediate)

1. Pick Theme 1 or Theme 2 as the main lane (highest near-term ROI).
2. Freeze a benchmark triad: OSWorld + VisualWebArena + one of ITBench/GAIA.
3. Start a reproducible baseline repo with experiment registry and failure taxonomy template.
4. Draft one workshop-positioning abstract focused on reliability + reproducibility.

## G) Replacements From Step 01 Top-20 Candidate Set

Confirmed: the Step 01 core was strong, but the Step 02 top-20 replaces several foundational CV-heavy entries with benchmark/reproducibility sources that better match this phase's automation-agent objective.

Replacements made:
1. Replaced DETR with TheAgentCompany.
Why: DETR is foundational CV, but TheAgentCompany is higher immediate value for long-horizon real-world automation benchmarking.

2. Replaced BLIP-2 with CRAB.
Why: BLIP-2 is useful model architecture context, while CRAB better supports cross-environment agent generalization claims.

3. Replaced LLaVA with ITBench.
Why: LLaVA is strong for multimodal instruction-following, but ITBench directly targets practical IT automation tasks.

4. Replaced SAM 2 with CORE-Bench.
Why: SAM 2 is high-value perception progress, but CORE-Bench contributes directly to reproducibility evidence and research credibility.

5. Replaced Grounding DINO with PaperBench.
Why: Grounding DINO is valuable for open-vocabulary detection, but PaperBench aligns better with replication-centered evaluation strategy.

## H) First 5 Sources To Summarize Next

Priority order for immediate deep summaries:
1. OSWorld (https://arxiv.org/abs/2404.07972)
2. VisualWebArena (https://arxiv.org/abs/2401.13649)
3. TheAgentCompany (https://arxiv.org/abs/2412.14161)
4. ReAct (https://arxiv.org/abs/2210.03629)
5. OpenVLA (https://arxiv.org/abs/2406.09246)

Reason for this sequence:
- 1-3 establish the main evaluation substrate for computer-use and automation claims.
- 4 defines control-policy baseline logic for agent behavior.
- 5 links perception-to-action architecture for cross-domain novelty.

## I) Links Requiring Human Verification Before External/Attorney-Facing Use

The following are likely valid but should be manually checked at final package time for canonical venue pages, final versions, and metadata consistency:

1. TheAgentCompany arXiv entry and any corresponding code/benchmark site.
2. CRAB arXiv entry and official benchmark repository.
3. ITBench arXiv entry and supporting task/environment documentation.
4. CORE-Bench arXiv entry and associated reproducibility artifacts.
5. PaperBench arXiv entry and final publication status.
6. Conference year-specific submission deadlines and workshop pages (CVPR/ICCV/ECCV/NeurIPS/ICLR/CoRL/RSS).

Verification checklist:
- Confirm paper title/version/date matches the final citable version.
- Confirm official code repo exists and is maintained.
- Confirm benchmark license/data-access constraints.
- Confirm conference/workshop deadlines from official conference sites.

## J) Issue Disposition and Handoff

Disposition: done

Completion statement:
- Step 02 objectives are fully satisfied: validated/ranked top 20, confirmed/revised 5 themes, explicit replacements, first 5 summaries selected, and human-verification flags captured.

Next owner/action:
- Owner: assignee for Step 03 summarization work.
- Action: start deep summaries for the five selected sources in Section H using the verification checklist in Section I.

## K) Objective-to-Deliverable Checklist

1. Confirm top 20 first summarization set: completed (Sections A, G).
2. Replacements with reasons: completed (Section G).
3. Ranked top 20 highest to lowest: completed (Section A).
4. Confirm/revise 5 research themes: completed (Section B).
5. First 5 sources to summarize next: completed (Section H).
6. Links/sources requiring human verification: completed (Section I).
