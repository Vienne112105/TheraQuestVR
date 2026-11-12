# Backlog

Durable ad-hoc queue for non-milestone work (bugs, ideas). AI-owned. See `AGENTS.md` → Ownership.
**Do not duplicate milestone criteria here.** Planned milestones live strictly in `50_ROADMAP.md`.

**Columns:** Todo | Done | Icebox | Rejected  
**In-progress work lives only in** `brain/20_PROGRESS.yaml` → `working_on` — not here.

**Item format:** `- [TASK-001] Description` optional `(ref: DEC-003)`

---

## Todo

<!-- Queued work not yet started -->
- [TASK-001] Dashboard button for the per-rep export (`/api/patients/{id}/export?kind=reps`); today it is only reachable by URL (ref: DEC-011)
- [TASK-002] Human: delete the legacy `Main/TheraQuestVR/server/theraquest.db` once the dashboard shows the migrated data (ref: DEC-010)

<!-- Post-M4 review (2026-10-25). Priority: high = fix before new features; research = before reporting results; low = housekeeping -->
- [TASK-003] (high) Keyboard / simulated sessions count toward adherence, phase readiness, rep progression, XP and badges like webcam sessions; 6 of 11 sessions in the live database are simulated. Needs a human choice: exclude non-webcam sessions from clinical rules (keep them on record) or use a dedicated demo patient for tests. Also show the input source in the dashboard Session History.
- [TASK-004] (high) Patient records have a free-text name field (P-002 is stored as "Maria Santos"), which conflicts with code-only pseudonymization. Remove the field or label it as an alias with no real names. (ref: DEC-003)
- [TASK-005] (high) No off-machine backup: the git repo has no remote (OneDrive syncing `.git` is not a backup) and the clinical database in `%LOCALAPPDATA%\TheraQuest` is not backed up. Add a backup routine (encrypted copy to a drive the clinic controls) before real study data; consider a private git remote. (ref: DEC-010)
- [TASK-006] (high) Unity `companyName` is still `DefaultCompany`; the player's data folder (config.json, PIN, cached program, offline queue) is named after it, so changing it after deployment orphans those files. Set the final company name before any clinic install.
- [TASK-007] (research) The exercise `LIBRARY` targets, tolerances, safety limits, holds and sets are placeholders; review them with a licensed physical therapist and record the final values. This includes the per-phase angles and reps of all nine built-in protocols (the source documents mostly give no angles; M5.7 added seven) and the M5.3 attention-flag thresholds (`ATTENTION_DAYS`, `PAIN_SPIKE`, `PAIN_RISE`, `ACCURACY_DROP`, `MISSED_DAYS`, `UNSAFE_REPS` in `server.py`).
- [TASK-008] (research) Collect the real evaluation inputs for the Section 3.9 metrics: goniometer readings, therapist rep labels, SUS and PT survey (templates in `Main/TheraQuestVR/evaluation/templates/`). Likely its own milestone when scheduled. (ref: DEC-011)
- [TASK-009] (low) `AGENTS.md` does not list the TBF status or unscheduled milestone IDs (`HW`); only [[50_ROADMAP]] explains them. `60_AGENTS.md` still lists milestone agents for M1 and M4.
- [TASK-010] (low) Check whether Unity `6000.6.5f1` is an LTS release ([[00_PROJECT]] says Unity 6 LTS); move to an LTS version if not.
- [TASK-011] (low) One script that runs all test suites (server, tracker, evaluation, Unity EditMode in batch mode) and reports the results.
- [TASK-015] (low) The tracker falls back to the DSHOW camera backend (black or slow frames) when MSMF is still busy from a previous run; retry MSMF for a few seconds before falling back. Seen in M6.5.
- [TASK-016] (low) Side-on, overlapping legs still confuse the lite pose model at moments; try `--model full` live if curls or marches miscount. Seen in M6.5.
- [TASK-013] (research) The MGB and BWH protocol documents are copyrighted ("all rights reserved"); the built-in protocols are short paraphrases with citations. Before publishing the thesis or distributing the app, confirm this use is acceptable or ask the institutions for permission.

## Done

- [TASK-012] Ankle exercises in the webcam tracker and the exercise `LIBRARY` (2026-11-07, M6.4): ankle pump (lying), seated and standing heel raise, used by the ankle ORIF and lateral ankle sprain protocols. Targets are placeholders until TASK-007.

- [TASK-014] Room decorations and the seated-exercise chair are 3D models (2026-10-27): Low Poly Gym Pack (reodesuxz) and Kenney Furniture Kit (CC0), chosen by the human; walls, windows, posters and the exercise-spot marker stay built from primitives. (ref: DEC-019)

<!-- Completed items -->

## Icebox

<!-- Deferred, not rejected -->

## Rejected

<!-- Explicitly rejected ideas -->
