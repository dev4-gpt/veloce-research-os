# VEL-63 Step 10 - Build Evidence Ledger Structure

Scope: create an evidence-organization structure for tracking portfolio progress and O-1-relevant proof over time.

Guardrails:
- This structure organizes evidence only.
- It does not claim visa eligibility.
- It does not provide legal strategy; items flagged for attorney review are preparation notes only.

## 1) Evidence Categories to Track

- Research evidence:
  - paper summaries, annotated bibliographies, benchmark notes.
- Engineering evidence:
  - code commits, pull requests, release notes, reproducible experiment runs.
- Impact evidence:
  - repository metrics, citations, downloads, usage/adoption signals.
- Public recognition evidence:
  - published articles, interviews, invited talks, conference/session listings.
- Community/professional evidence:
  - outreach messages, collaborator replies, expert feedback/testimonials.
- Reviewability evidence:
  - claim-to-proof links, source files, timestamps, verifier notes.

## 2) Suggested Obsidian Folder + Database Structure

```text
/obsidian-vault/
  00_Inbox/
  01_Projects/
    Reliable-CU-Agent-Matrix/
      Notes/
      Drafts/
      Weekly-Reviews/
  02_Evidence/
    Research/
    Engineering/
    Impact/
    Public-Recognition/
    Community/
    Attorney-Review/
  03_Databases/
    evidence_records.csv
    evidence_links.csv
    weekly_review_log.csv
  04_Attachments/
    pdfs/
    screenshots/
    logs/
    slides/
  05_Templates/
    evidence_record_template.md
    weekly_review_template.md
```

## 3) Fields for Each Evidence Record

Use one row per evidence item in `03_Databases/evidence_records.csv`.

Required fields:
- `evidence_id` (unique)
- `category` (`research|engineering|impact|public_recognition|community`)
- `record_type` (paper_summary, code_commit, experiment_result, etc.)
- `title`
- `date_utc`
- `project`
- `summary`
- `source_url_or_path`
- `artifact_path`
- `people_involved`
- `outcome_or_signal`
- `verification_status` (`draft|verified|needs_review`)
- `verified_by`
- `notes`

Recommended extra fields:
- `tags`
- `related_evidence_ids`
- `public_visibility` (`private|shareable|public`)
- `attorney_review_flag` (`yes|no`)
- `attorney_review_note`

## 4) Example Records

### 4.1 Paper Summary

- `evidence_id`: `EV-PS-001`
- `category`: `research`
- `record_type`: `paper_summary`
- `title`: `ReAct: Synergizing Reasoning and Acting`
- `date_utc`: `2026-05-17T18:10:00Z`
- `project`: `Reliable-CU-Agent-Matrix`
- `summary`: `Extracted reliability-relevant prompting pattern and failure modes.`
- `source_url_or_path`: `VEL-31_step01_100_sources.md`
- `artifact_path`: `02_Evidence/Research/EV-PS-001.md`
- `verification_status`: `verified`

### 4.2 Code Commit

- `evidence_id`: `EV-CC-004`
- `category`: `engineering`
- `record_type`: `code_commit`
- `title`: `Add deterministic run metadata schema`
- `date_utc`: `2026-05-18T01:40:00Z`
- `source_url_or_path`: `git commit <sha>`
- `artifact_path`: `02_Evidence/Engineering/EV-CC-004_commit_note.md`
- `outcome_or_signal`: `Enables run-level reproducibility checks`
- `verification_status`: `needs_review`

### 4.3 Experiment Result

- `evidence_id`: `EV-EX-009`
- `category`: `engineering`
- `record_type`: `experiment_result`
- `title`: `P2 vs P0 on VWA subset seed2`
- `date_utc`: `2026-05-18T02:00:00Z`
- `artifact_path`: `runs/2026-05-18_p2_vwa_seed2/metrics.json`
- `outcome_or_signal`: `completion_rate delta +0.09`
- `verification_status`: `verified`

### 4.4 Public Article

- `evidence_id`: `EV-PA-002`
- `category`: `public_recognition`
- `record_type`: `public_article`
- `title`: `Engineering note on reliability policy matrix`
- `date_utc`: `2026-06-02T15:00:00Z`
- `source_url_or_path`: `https://example.com/article`
- `outcome_or_signal`: `Published public technical write-up`
- `verification_status`: `draft`

### 4.5 Outreach Message

- `evidence_id`: `EV-OM-003`
- `category`: `community`
- `record_type`: `outreach_message`
- `title`: `Reachout to benchmark maintainer`
- `date_utc`: `2026-05-25T09:30:00Z`
- `artifact_path`: `02_Evidence/Community/EV-OM-003_email.txt`
- `outcome_or_signal`: `Requested technical feedback`
- `verification_status`: `verified`

### 4.6 Expert Feedback

- `evidence_id`: `EV-EF-001`
- `category`: `community`
- `record_type`: `expert_feedback`
- `title`: `Advisor review on failure taxonomy`
- `date_utc`: `2026-05-28T20:00:00Z`
- `artifact_path`: `02_Evidence/Community/EV-EF-001_feedback.md`
- `outcome_or_signal`: `Received written critique with action items`
- `verification_status`: `verified`

### 4.7 Presentation/Talk

- `evidence_id`: `EV-PT-001`
- `category`: `public_recognition`
- `record_type`: `presentation_talk`
- `title`: `Lab talk: Reliability policy benchmarking`
- `date_utc`: `2026-06-10T17:00:00Z`
- `artifact_path`: `04_Attachments/slides/2026-06-10_lab_talk.pdf`
- `outcome_or_signal`: `Invited internal/external presentation`
- `verification_status`: `draft`

### 4.8 Repository Metric

- `evidence_id`: `EV-RM-005`
- `category`: `impact`
- `record_type`: `repository_metric`
- `title`: `Repo stars and forks monthly snapshot`
- `date_utc`: `2026-06-30T23:59:00Z`
- `artifact_path`: `02_Evidence/Impact/EV-RM-005_metrics.csv`
- `outcome_or_signal`: `Stars=120, Forks=18, Contributors=6`
- `verification_status`: `verified`

## 5) Weekly Evidence Review Checklist

- Confirm all new evidence items from the week are logged with `evidence_id` and timestamp.
- Verify every item has a source path/URL and stored artifact.
- Promote `draft` items to `verified` only after a second-pass check.
- Check that major project claims have linked evidence records.
- Tag sensitive/private items and confirm visibility level.
- Flag missing documentation or ambiguous provenance.
- Add attorney-review flags where legal interpretation may be needed.
- Record weekly review outcome in `03_Databases/weekly_review_log.csv`.

## 6) Items to Prepare for Immigration Attorney Review Later

Mark these with `attorney_review_flag=yes` for later counsel review:

- Evidence that may indicate original contributions of major significance.
- External expert testimonials/reference letters and their provenance.
- Media coverage, invited talks, or judging/review activities.
- Authorship/publication records and venue quality indicators.
- Role/criticality documentation (leadership or essential responsibilities).
- Metrics used to represent impact (adoption, citations, benchmark leadership).
- Any claim that could be interpreted as legal eligibility language.

Note:
- Keep factual records only; defer legal interpretation to an immigration attorney.

## 7) Definition of Done for Step 10

- Evidence categories, structure, and fields are defined.
- All requested example record types are provided.
- Weekly checklist is documented.
- Attorney-review preparation list is documented with legal guardrails.

Disposition:
- `done` for VEL-63 Step 10.
