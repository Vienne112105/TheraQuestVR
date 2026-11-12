# M7 — Pre-Study Data Readiness (plan, 2026-11-12)

Status: **approved by the human on 2026-11-12** ("Approve, real name"). M7 and its children are in
`genOS-main/brain/50_ROADMAP.md` (the authority for criteria and status); M7 and M7.4 are `active` and
`20_PROGRESS.yaml → current_milestone` is `M7.4`. DEC-027 is recorded.

**Objective:** make the clinical data trustworthy and safe before real study data is collected: only real webcam
sessions drive clinical rules, patient identity is handled under one clear decision, the database has an encrypted
off-machine backup that can be restored, and the Unity data folder name is final.

**Source:** backlog TASK-003, TASK-004, TASK-005, TASK-006 (high priority). The choices below are the human's
answers given at kickoff on 2026-11-12.

**Governing agent rules (persona gate):**
- `engineering-data-engineer`: reruns must be idempotent and never duplicate; null handling must be deliberate
  (a session with an unknown source is not treated as webcam data); keep data on record (soft rules, no deletes).
- `unity-architect`: each component solves one problem; no `FindObjectOfType`/singletons for new cross-system
  wiring; keep changes small and data-driven.
- `ponytail`: reuse the single choke points that already exist (`day_statuses`, upload handler), stdlib first;
  exactly one new dependency (`cryptography`, for TASK-005 only); never skimp on validation or tests.

**Test suites (all must stay green):** `server/test_backend.py`, `server/test_authorization.py`, tracker tests,
Unity EditMode tests. Baseline at M6.5: tracker 96, server 68, Unity EditMode 86.

---

## M7.1 — Only webcam sessions count (TASK-003)

**Human choice:** exclude keyboard, simulated and unknown-source sessions from **all** rules, including XP and
badges. Keep them on record and label them.

Write the failing tests first (`server/test_backend.py`):
1. A simulated session on a prescribed day does not make that day `complete` in `day_statuses`, so it does not
   raise adherence or the streak; a webcam session the same day does.
2. `readiness()` ignores non-webcam sessions (accuracy, pain, session count).
3. `attention_flags()` ignores non-webcam sessions (accuracy drop, unsafe reps, missed days); the per-flag
   `sources` breakdown goes away or only ever shows webcam.
4. Upload of a `keyboard`/`simulated` session: stored with its source, but XP is not added, badges in
   `badges_earned` are not stored, the Progression Controller does not run; the response says it was a practice
   session (e.g. `"counted": false`). Re-upload of the same `session_uuid` stays idempotent.
5. Upload with no `input_source` (old clients → `unknown`) is treated like practice.
6. Session History rows (`/api/patients/{id}` history) carry `input_source`, and the per-rep and telemetry
   exports keep their `input_source` column (already there; add a regression test).

Then implement:
- One helper, e.g. `COUNTED_SOURCES = ("webcam",)`, used by `day_statuses`, `readiness`, `attention_flags`, the
  upload handler (XP, badges, progression) and `vr_progress` totals.
- Dashboard Session History: an input-source tag per row ("Webcam", "Keyboard (not counted)", ...).
- Unity session summary: one short line for a non-webcam session ("Practice: not counted"); per the
  patient-screens-minimal rule, nothing more. EditMode test for the line.
- XP and badges already earned from past simulated sessions stay as they are (not retroactive); say so in the
  roadmap entry.

**Done when:** tests above pass; the live database's 6 simulated sessions no longer change P-001/P-002 adherence,
readiness or flags; Session History shows the source.

## M7.2 — Patient name and code (TASK-004)

**Human choice (2026-11-12):** keep both the patient's name and their code.

This changes DEC-003 and `00_PROJECT.md` Out of Scope item 4 ("strict patient pseudonymization"): with real names
the database holds personal information under RA 10173. The human confirmed at approval that "name" means the
patient's real name.

**DEC-027 "Patient Records Hold Name and Code; Only the Code Leaves the Dashboard"** is recorded (supersedes the
pseudonymization part of DEC-003) and `00_PROJECT.md` Out of Scope item 4 is updated (done at approval):
- The name is stored and shown only in the therapist dashboard.
- Everything that leaves the dashboard uses the code only: research exports (CSV/JSON), evaluation reports, VR
  client routes, logs, tracker recordings.
- Backups are encrypted (M7.3); study participants give informed consent (a human/ethics task, recorded in the
  backlog, not code).

Tests first:
1. Exports (`export_rep_events`, `export_telemetry`, session export) contain no `name` column and no name value.
2. VR routes (`vr_progress`, prescription fetch) do not return `name` (today `vr_progress` does); Unity
   `DataModels` drops the unused field.
3. Name length and type are validated (already `maxlength=200` in the form; check the server enforces it).

Implement: remove `name` from VR payloads; update the `schema.sql` comment; dashboard label "Patient full name
(dashboard only)". No migration: existing names stay.

## M7.3 — Encrypted backup and restore (TASK-005)

**Human choice:** a password-encrypted backup file.

Design (smallest that is safe):
- New dependency `cryptography` (pinned in `server/requirements.txt`; the server itself stays stdlib, only the
  backup tool imports it).
- `server/backup.py` with two commands:
  - `backup <folder>`: consistent snapshot through `sqlite3.Connection.backup` (safe while the server runs, WAL
    included), encrypt with a key from the password via Scrypt plus AES-GCM (or Fernet), write
    `theraquest-YYYYMMDD-HHMMSS.tqbak` with a small header (magic, version, salt, KDF parameters). Password asked
    twice with `getpass`, minimum 12 characters, never stored or logged.
  - `restore <file> <out.db>`: decrypt to a new file only and run `PRAGMA integrity_check`; never overwrite the
    live database. Swapping it in is a documented manual step with the server stopped.
- `Backup_Database.bat` next to `Start_Therapist_App.bat` (asks for the folder, e.g. a USB drive).
- README section: where to keep backups, that **a lost password means the backup can't be recovered**, how to restore.
- No dashboard button in this milestone (YAGNI; add a backlog item if wanted).

Tests first (`server/test_backup.py`): round trip gives identical table contents; wrong password fails cleanly;
a tampered file fails; header version checked; restore refuses an existing output path; backup during an open
write transaction still gives a consistent copy.

The private git remote stays a human action (create a private repository and add it as a remote), kept in TASK-005's
note; DEC-020 still applies.

## M7.4 — Unity company name (TASK-006)

**Human choice:** `TheraQuest`.

- Set `companyName: TheraQuest` in `unity/ProjectSettings/ProjectSettings.asset` (through the Editor/MCP so
  Unity stays consistent).
- On this PC, the data folder moves from `%USERPROFILE%\AppData\LocalLow\DefaultCompany\TheraQuestVR` to
  `...\LocalLow\TheraQuest\TheraQuestVR`: config.json, PIN, cached program and offline queue. Either copy them
  once by hand (dev machine only, no clinic installs exist) or add a one-time copy on startup. Recommend: manual
  copy plus a README note, since no clinic install exists yet (YAGNI). Check the offline queue is empty first.
- EditMode test (or a check) that `Application.companyName` is not `DefaultCompany`.

## Order and sessions

M7.4 (smallest) → M7.1 → M7.2 → M7.3. M7.1 and M7.2 both edit `server.py` and `dashboard.html`, so run them one
after another, not in parallel. Commit per child on a new branch from the current one (`m7-pre-study-data`);
TheraQuest.unity holds the human's uncommitted scene changes: never commit or discard them.

**Brain updates during execution:** ROADMAP (M7 entries, statuses), DEC-027, `00_PROJECT.md` item 4 (approved),
backlog (TASK-003..006 to Done; new TASK for consent forms and the optional dashboard backup button),
system files ClinicalBackend, TherapistDashboard, SessionOrchestration, Gamification.
