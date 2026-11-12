# Backlog

Durable ad-hoc queue for non-milestone work (bugs, ideas). AI-owned. See `AGENTS.md` → Ownership.
**Do not duplicate milestone criteria here.** Planned milestones live strictly in `50_ROADMAP.md`.

**Columns:** Todo | Done | Icebox | Rejected  
**In-progress work lives only in** `brain/20_PROGRESS.yaml` → `working_on` — not here.

**Item format:** `- [TASK-001] Description` optional `(ref: DEC-003)`

---

## Todo

<!-- Queued work not yet started -->
- [TASK-002] Human: delete the legacy `Main/TheraQuestVR/server/theraquest.db` once the dashboard shows the migrated data (ref: DEC-010)

<!-- Post-M4 review (2026-10-25). Priority: high = fix before new features; research = before reporting results; low = housekeeping -->
- [TASK-007] (research) The exercise `LIBRARY` targets, tolerances, safety limits, holds and sets are placeholders; review them with a licensed physical therapist and record the final values. This includes the per-phase angles and reps of all nine built-in protocols (the source documents mostly give no angles; M5.7 added seven) and the M5.3 attention-flag thresholds (`ATTENTION_DAYS`, `PAIN_SPIKE`, `PAIN_RISE`, `ACCURACY_DROP`, `MISSED_DAYS`, `UNSAFE_REPS` in `server.py`).
- [TASK-008] (research) Collect the real evaluation inputs for the Section 3.9 metrics: goniometer readings, therapist rep labels, SUS and PT survey (templates in `Main/TheraQuestVR/evaluation/templates/`). Likely its own milestone when scheduled. (ref: DEC-011)
- [TASK-009] (low) `AGENTS.md` does not list the TBF status or unscheduled milestone IDs (`HW`); only [[50_ROADMAP]] explains them. `60_AGENTS.md` still lists milestone agents for M1 and M4.
- [TASK-010] (low) Check whether Unity `6000.6.5f1` is an LTS release ([[00_PROJECT]] says Unity 6 LTS); move to an LTS version if not.
- [TASK-015] (low) The tracker falls back to the DSHOW camera backend (black or slow frames) when MSMF is still busy from a previous run; retry MSMF for a few seconds before falling back. Seen in M6.5.
- [TASK-016] (low) Side-on, overlapping legs still confuse the lite pose model at moments; try `--model full` live if curls or marches miscount. Seen in M6.5.
- [TASK-018] (low) Dashboard button for the encrypted backup (today only `Backup_Database.bat` / `server/backup.py`). Skipped in M7.3 as YAGNI.
- [TASK-019] Human: create a private GitHub repository and add it as a remote for the code (the repository must stay private, DEC-020). Not a backup of the database.
- [TASK-017] (research) Informed consent: study participants must agree to their real name being stored in the clinical database (DEC-027); prepare the consent wording with the ethics review before real study data.
- [TASK-013] (research) The MGB and BWH protocol documents are copyrighted ("all rights reserved"); the built-in protocols are short paraphrases with citations. Before publishing the thesis or distributing the app, confirm this use is acceptable or ask the institutions for permission.

## Done

- [TASK-020] The therapist app builds as a Windows program, `server/dist/TheraQuest Therapist/TheraQuest Therapist.exe` (`server/build_app.py`, PyInstaller one-folder, no console, own icon); `Start_Therapist_App.bat` prefers it; `start_server.bat` no longer opens a browser; downloads allowed in the native window, which blocked the CSV exports until now (2026-11-12, ref: DEC-013). Human check left: one CSV download from inside the app.

- [TASK-001] "Download Reps (CSV)" button on the patient chart, next to the telemetry download (`export?kind=reps`) (2026-11-12, ref: DEC-011).

- [TASK-011] `Main/TheraQuestVR/run_tests.py` runs the server, tracker, evaluation and Unity EditMode suites and prints one table; exit 1 on any failure; Unity is skipped while the Editor has the project open (2026-11-12).

- [TASK-003] Only webcam sessions count for adherence, readiness, flags, XP, badges and progression; other sessions stay on record, labelled (2026-11-12, M7.1).
- [TASK-004] Patient name stays in the dashboard only; exports and VR routes use the code (2026-11-12, M7.2, DEC-027).
- [TASK-005] Password-encrypted backup and restore (2026-11-12, M7.3). The private git remote is TASK-019.
- [TASK-006] Unity companyName set to `TheraQuest` (2026-11-12, M7.4); the data-folder copy is a human check.

- [TASK-012] Ankle exercises in the webcam tracker and the exercise `LIBRARY` (2026-11-07, M6.4): ankle pump (lying), seated and standing heel raise, used by the ankle ORIF and lateral ankle sprain protocols. Targets are placeholders until TASK-007.

- [TASK-014] Room decorations and the seated-exercise chair are 3D models (2026-10-27): Low Poly Gym Pack (reodesuxz) and Kenney Furniture Kit (CC0), chosen by the human; walls, windows, posters and the exercise-spot marker stay built from primitives. (ref: DEC-019)

<!-- Completed items -->

## Icebox

<!-- Deferred, not rejected -->

## Rejected

<!-- Explicitly rejected ideas -->
