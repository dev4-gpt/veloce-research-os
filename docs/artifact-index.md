# Veloce AI Research OS v1 - Artifact Index

This index connects the Paperclip Step 01-15 workflow, VPS artifact export, and Obsidian vault.

## Status

Paperclip workflow status: complete

Artifact sync status: synced to Obsidian

Last synced: 2026-05-18

## Source System

```text
Paperclip URL: https://paperclip-iraj.srv1314350.hstgr.cloud
Project: F-1 to O-1 Research OS
Parent issue: Build v1 research source map
VPS archive: /root/veloce-research-os-artifacts.tar.gz
Local Obsidian folder: Veloce AI Research OS/Artifacts
```

## Master Note

- [[Veloce AI Research OS/Veloce AI Research OS v1|Veloce AI Research OS v1]]

## Primary Artifacts

| Step | Paperclip task | Artifact | Owner |
|---|---|---|---|
| Step 01 | Collect 100 sources across AI systems fields | [[Veloce AI Research OS/Artifacts/VEL-31_step01_100_sources_table|100-source table]] | Research Navigator |
| Step 02 | Validate top 20 sources and 5 research themes | [[Veloce AI Research OS/Artifacts/VEL-32_step02_top20_and_5_themes|Top 20 and 5 themes]] | Research Navigator |
| Step 03 | Summarize validated sources 1-5 | [[Veloce AI Research OS/Artifacts/VEL-33_step03_priority_sources_1-5|Sources 1-5 summaries]] | Paper Summarizer |
| Step 04 | Summarize validated sources 6-10 | [[Veloce AI Research OS/Artifacts/VEL-34_step04_priority_sources_6-10|Sources 6-10 summaries]] | Paper Summarizer |
| Step 05 | Summarize validated sources 11-15 | [[Veloce AI Research OS/Artifacts/VEL-35_step05_priority_sources_11-15|Sources 11-15 summaries]] | Paper Summarizer |
| Step 06 | Summarize validated sources 16-20 | [[Veloce AI Research OS/Artifacts/VEL-36_step06_priority_sources_16-20|Sources 16-20 summaries]] | Paper Summarizer |
| Step 07 | Synthesize top 20 sources into research directions | [[Veloce AI Research OS/Artifacts/VEL-56_step07_synthesis_top20_to_research_directions|Research direction synthesis]] | Research Navigator |
| Step 08 | Choose first 30-day flagship project | [[Veloce AI Research OS/Artifacts/VEL-59_step08_first_30_day_flagship_project|Flagship project selection]] | Technical Builder |
| Step 09 | Create 30-day execution plan for flagship project | [[Veloce AI Research OS/Artifacts/VEL-61_step09_30_day_execution_plan_flagship|30-day execution plan]] | Task Manager |
| Step 10 | Build evidence ledger structure | [[Veloce AI Research OS/Artifacts/VEL-63_step10_evidence_ledger_structure|Evidence ledger structure]] | Evidence Tracker |
| Step 11 | Draft first public research article | [[Veloce AI Research OS/Artifacts/VEL-64_step11_public_research_article_package|Public article package]] | Content Creator |
| Step 12 | Create technical repo scaffold | [[Veloce AI Research OS/Artifacts/VEL-68_step12_technical_repo_scaffold|Technical repo scaffold]] | Technical Builder |
| Step 13 | Create outreach target list | [[Veloce AI Research OS/Artifacts/VEL-71_step13_outreach_target_list|Outreach target list]] | Research Navigator |
| Step 14 | Draft outreach messages for human review | [[Veloce AI Research OS/Artifacts/VEL-73_step14_outreach_message_drafts|Outreach message drafts]] | Content Creator |
| Step 15 | Create weekly review dashboard | [[Veloce AI Research OS/Artifacts/VEL-75_step15_weekly_review_dashboard|Weekly review dashboard]] | Task Manager |

## Closeout and Disposition Files

These are useful for Paperclip audit/debugging, but not the main operating artifacts.

- [[Veloce AI Research OS/Artifacts/VEL-56_CLOSEOUT|Step 07 closeout]]
- [[Veloce AI Research OS/Artifacts/VEL-59_CLOSEOUT|Step 08 closeout]]
- [[Veloce AI Research OS/Artifacts/VEL-61_CLOSEOUT|Step 09 closeout]]
- [[Veloce AI Research OS/Artifacts/VEL-63_CLOSEOUT|Step 10 closeout]]
- [[Veloce AI Research OS/Artifacts/VEL-64_CLOSEOUT|Step 11 closeout]]
- [[Veloce AI Research OS/Artifacts/VEL-68_CLOSEOUT|Step 12 closeout]]
- [[Veloce AI Research OS/Artifacts/VEL-71_CLOSEOUT|Step 13 closeout]]
- [[Veloce AI Research OS/Artifacts/VEL-73_CLOSEOUT|Step 14 closeout]]
- [[Veloce AI Research OS/Artifacts/VEL-75_CLOSEOUT|Step 15 closeout]]

## Artifact Sync Commands Used

VPS export:

```bash
mkdir -p /root/veloce-research-os-artifacts
docker exec paperclip-iraj-paperclip-1 sh -lc 'find /paperclip -maxdepth 10 -type f -name "VEL-*_*.md" -print' > /root/veloce-research-os-artifact-paths.txt
while IFS= read -r file; do
  docker cp "paperclip-iraj-paperclip-1:${file}" "/root/veloce-research-os-artifacts/$(basename "$file")"
done < /root/veloce-research-os-artifact-paths.txt
tar -czf /root/veloce-research-os-artifacts.tar.gz -C /root veloce-research-os-artifacts
```

Mac import:

```bash
scp root@72.60.29.216:/root/veloce-research-os-artifacts.tar.gz ~/Downloads/
mkdir -p "$HOME/Documents/Claude/Projects/obsidian/Computer-Vision-Vault/Veloce AI Research OS/Artifacts"
tar -xzf ~/Downloads/veloce-research-os-artifacts.tar.gz -C "$HOME/Documents/Claude/Projects/obsidian/Computer-Vision-Vault/Veloce AI Research OS/Artifacts" --strip-components=1
```

## Next Action

Start execution on the selected flagship project:

```text
Reliability Policy Matrix for Computer-Use Agents
```

Use [[Veloce AI Research OS/Artifacts/VEL-68_step12_technical_repo_scaffold|Step 12]] to create the repository, then use [[Veloce AI Research OS/Artifacts/VEL-61_step09_30_day_execution_plan_flagship|Step 09]] to begin Days 1-3.
