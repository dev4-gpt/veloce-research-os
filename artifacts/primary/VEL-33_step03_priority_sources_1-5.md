# VEL-33 Step 03 - Summaries for Priority Sources 1-5

Scope: factual summary of the first 5 priority sources selected in VEL-32 Step 02.

## 1) OSWorld

1. Title and link: OSWorld: Benchmarking Multimodal Agents for Open-Ended Tasks in Real Computer Environments (2024) — https://arxiv.org/abs/2404.07972
2. Category: Computer-use agent benchmark (desktop GUI automation).
3. Source type: arXiv preprint + benchmark framework.
4. Core problem addressed: Existing evaluations overfit to narrow web tasks and do not capture realistic, long-horizon desktop operations.
5. Main method/system/dataset/idea: A benchmark environment with open-ended tasks across real computer interfaces, designed to test multimodal perception, planning, and execution.
6. Key contribution: Establishes a more realistic evaluation substrate for computer-use agents, including task diversity and environment interaction complexity.
7. Why it matters for Veloce AI: Provides a credible foundation for measuring reliability claims in practical automation workflows.
8. Possible technical project inspired by it: Build a reproducible harness that runs a fixed controller (e.g., ReAct-style policy) across OSWorld with failure-taxonomy logging.
9. Possible public writing angle: “Why web-only agent benchmarks are not enough for real automation.”
10. Evidence/portfolio value: Benchmark-based results are citable, comparable, and suitable for showing measurable technical contribution.
11. One limitation or open question: Transferability from benchmark tasks to production enterprise desktops remains uncertain.

## 2) VisualWebArena

1. Title and link: VisualWebArena: Evaluating Multimodal Agents on Realistic Visual Web Tasks (2024) — https://arxiv.org/abs/2401.13649
2. Category: Web-based multimodal agent benchmark.
3. Source type: arXiv preprint + benchmark environment.
4. Core problem addressed: Text-centric web benchmarks underrepresent visual grounding and UI interpretation demands.
5. Main method/system/dataset/idea: A realistic visual web task suite requiring screenshot understanding, element grounding, and multi-step interaction.
6. Key contribution: Brings visual perception into web-agent evaluation so success is tied to true GUI understanding, not only text reasoning.
7. Why it matters for Veloce AI: Directly maps to browser-heavy automation scenarios where visual ambiguity causes real failures.
8. Possible technical project inspired by it: Compare screenshot-grounded action policies versus DOM-heavy policies under equal budget constraints.
9. Possible public writing angle: “The hidden failure modes of browser agents: visual grounding vs. DOM shortcuts.”
10. Evidence/portfolio value: Produces quantitative, repeatable results on a well-known benchmark used by agent papers.
11. One limitation or open question: Benchmark scenarios may still be cleaner than real enterprise websites with custom widgets and auth friction.

## 3) TheAgentCompany

1. Title and link: TheAgentCompany: Benchmarking LLM Agents on Consequential Real World Tasks (2024) — https://arxiv.org/abs/2412.14161
2. Category: Long-horizon workplace automation benchmark.
3. Source type: arXiv preprint + benchmark proposal.
4. Core problem addressed: Many benchmarks fail to reflect consequential, multi-step tasks with real-world-style dependencies and stakes.
5. Main method/system/dataset/idea: A benchmark centered on workplace-like tasks that require planning, tool use, and sustained execution.
6. Key contribution: Pushes evaluation toward practical task utility rather than short synthetic tasks.
7. Why it matters for Veloce AI: Aligns with business automation narratives and supports evidence of impact on realistic operational workflows.
8. Possible technical project inspired by it: Add a “recovery policy layer” and evaluate how rollback/retry strategies affect task completion and error propagation.
9. Possible public writing angle: “From toy tasks to consequential workflows: what changes in agent design?”
10. Evidence/portfolio value: Strong for demonstrating practical relevance and long-horizon system design capability.
11. One limitation or open question: Community standardization and broad adoption are still developing compared with older benchmarks.

## 4) ReAct

1. Title and link: ReAct: Synergizing Reasoning and Acting in Language Models (2022) — https://arxiv.org/abs/2210.03629
2. Category: Agent control/prompting method.
3. Source type: arXiv preprint (method paper).
4. Core problem addressed: Pure chain-of-thought or pure action approaches each fail on tasks needing iterative reasoning plus environment interaction.
5. Main method/system/dataset/idea: Interleaves reasoning traces and explicit actions so the model can update plans based on observations.
6. Key contribution: A simple but influential control pattern for tool-using agents that improved interpretability and task success in many settings.
7. Why it matters for Veloce AI: Serves as a strong baseline controller and ablation anchor when testing reliability improvements.
8. Possible technical project inspired by it: Implement ReAct plus guarded action schemas, then measure hallucination-induced action errors versus non-ReAct baselines.
9. Possible public writing angle: “Why reasoning-action interleaving remains a durable baseline for production agents.”
10. Evidence/portfolio value: Methodological grounding that reviewers and practitioners already recognize.
11. One limitation or open question: Verbose reasoning traces can increase latency/cost and do not guarantee robustness without additional safeguards.

## 5) OpenVLA

1. Title and link: OpenVLA: An Open-Source Vision-Language-Action Model (2024) — https://arxiv.org/abs/2406.09246
2. Category: Vision-language-action (VLA) model/system.
3. Source type: arXiv preprint + open-source model/system release.
4. Core problem addressed: Bridging perception, language understanding, and action in a reproducible open framework is difficult.
5. Main method/system/dataset/idea: An open VLA stack intended to connect visual inputs and language-conditioned action outputs with reproducible tooling.
6. Key contribution: Provides an accessible open-source reference for VLA experimentation and extension.
7. Why it matters for Veloce AI: Enables cross-pollination from CV/VLA advances into automation agent architectures and evaluation.
8. Possible technical project inspired by it: Adapt VLA-style perception-action interfaces to GUI automation primitives and compare against text-only planners.
9. Possible public writing angle: “What VLA research can (and cannot) transfer to enterprise automation agents.”
10. Evidence/portfolio value: Demonstrates ability to connect frontier CV+action ideas with practical agent systems.
11. One limitation or open question: Domain shift from embodied/robotic assumptions to desktop/web GUIs may limit direct transfer.

## Cross-Source Patterns (3)

1. Evaluation realism is the central bottleneck: OSWorld, VisualWebArena, and TheAgentCompany all emphasize that benchmark choice strongly determines whether claimed progress survives outside lab settings.
2. Reliability requires policy + environment co-design: ReAct-style controllers are useful, but benchmark complexity shows that control logic and environment instrumentation must evolve together.
3. Perception-action integration is becoming mandatory: Visual grounding and action execution are increasingly coupled, connecting benchmark work (OSWorld/VisualWebArena) with model/system work (OpenVLA).

## Combined Project Ideas (2)

1. Reliability-First Computer-Use Agent Stack
- Combine: OSWorld + VisualWebArena + ReAct.
- Build a unified benchmark harness with standardized prompts, action schema validation, and recovery policy ablations.
- Output: reproducible report on success rate, cost, latency, and failure taxonomy.

2. VLA-Informed GUI Automation Transfer Study
- Combine: OpenVLA + TheAgentCompany + OSWorld.
- Prototype a perception-action interface inspired by VLA design for long-horizon office-style tasks.
- Output: transfer analysis showing where VLA abstractions help or fail in real computer-use settings.

## Items Needing Human Verification

1. Confirm canonical publication metadata (final title/version/date) for all five sources before attorney-facing or external packet use.
2. Confirm official repositories/benchmark docs and licensing terms for OSWorld, VisualWebArena, TheAgentCompany, and OpenVLA.
3. Verify current benchmark maintenance status and reproducibility instructions (setup requirements can change).
4. For ReAct, confirm whether the target citation should be arXiv-only or a later venue-specific version in final materials.

## Disposition

Status recommendation: done

Rationale: Step 03 objective is completed for the first five priority sources with all required fields, cross-source synthesis, combined project ideas, and verification flags.
