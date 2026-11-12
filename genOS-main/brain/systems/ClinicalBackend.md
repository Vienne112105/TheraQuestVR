# ClinicalBackend

## Purpose
Provides a lightweight, local-first Python REST API and SQLite persistence layer to manage patient prescriptions, log rehabilitation sessions, track clinical protocol phases, and evaluate adherence and progression criteria.

## Status
`stable`

## Responsibilities
- Serve HTTP endpoints on port 8000 for clinician authentication, patients, prescriptions, session logs, performance records, telemetry exports, and clinical protocols.
- Maintain relational database schema (`theraquest.db`) with 11 custom performance indexes and SQLite Write-Ahead Logging (WAL) mode for concurrent VR data writing.
- Enforce secure credential hashing (PBKDF2-HMAC-SHA256 with unique 16-byte cryptographic salts) and manage bearer session tokens via `therapist_session` with 24-hour expiration; tokens are stored as SHA-256 digests and expired ones are purged at sign-in.
- No default password: the first clinician login is created through a loopback-only first-run setup; sign-ins with the old demo password must change it; failed sign-ins are throttled per username.
- Enforce authorization per [[30_DECISIONS]] DEC-009: every therapist route requires a valid bearer token (401 otherwise); the VR client uses separate patient-scoped `/api/vr/*` routes authorized by the `X-Patient-Code` header and accepted from loopback only.
- Provide full clinical protocol lifecycle operations (`POST /api/protocols`, `DELETE /api/protocols/{id}`, and `DELETE /api/patients/{id}/protocol`) using parameterized cascading updates.
- Pre-seed evidence-based clinical protocols (OHSU Knee and MGB Rotator Cuff) and load protocol hierarchies via an optimized 3-query bulk dictionary builder.
- Validate target angles and safety maximums against normal physiological ROM benchmarks (AAOS / Norkin & White standards).
- Evaluate patient stage progression: assess recent qualifying sessions for ≥85% accuracy, pain stability, and safety threshold compliance before suggesting phase advancement.
- Automatically advance prescribed repetition targets (+2 reps/set up to cap) following qualifying adherence sessions.
- Provide one-click telemetry data export in CSV and JSON formats (`/api/export`); `?kind=reps` exports one row per rep attempt.
- Store the per-rep log Unity uploads with each session (`rep_event`: attempt, set, peak angle, error, counted or not, posture fault, unsafe) as the evaluation pipeline's real input (M4.5, [[30_DECISIONS]] DEC-011).
- Own the exercise `LIBRARY`: each entry carries its prescription defaults and its rules (posture, pose, movement direction, posture checks), which the VR program sends to Unity (M4.6, DEC-012).

## Dependencies
- Standard Python standard libraries (`http.server`, `sqlite3`, `json`, `datetime`, `hashlib`, `secrets`, `csv`, `urllib`).
- Inter-system: Serves `SessionOrchestration` and powers `TherapistDashboard`.

## Runtime References
- `Main/TheraQuestVR/server/server.py`: HTTP request handler, routing, authentication, protocol lifecycle, progression evaluation logic, and seed data.
- `Main/TheraQuestVR/server/schema.sql`: Relational SQLite schema definition with 11 performance indexes.
- `Main/TheraQuestVR/server/start_server.bat`: Windows execution batch launcher.
- `Main/TheraQuestVR/server/test_authorization.py`: M3.2 authorization regression suite (therapist 401s, patient-code isolation, loopback-only VR routes).

## Invariants
- Session completion and progression are judged against the server's prescription (effective reps × sets of every active exercise), never the client's own targets; an empty program is never complete.
- A session upload with a `session_uuid` already stored is answered with the stored session (idempotent retry), never saved twice.
- Re-seeding built-in protocols (`protocol.builtin = 1`) must never delete therapist-authored protocols, and keeps built-in protocols whose content is unchanged (patients on them keep their phase); only changed or withdrawn ones are replaced.
- Built-in protocols are read-only through the API; only therapist-authored protocols can have phases edited or added (DEC-014).
- Attention flags (M5.3) are computed by the server only (`attention_flags`), suggest and never act, look back `ATTENTION_DAYS`, look only at counted sessions (see below), and are never shown for archived patients. Thresholds are placeholders until a PT confirms them (TASK-007).
- Patients are archived (`archived_at`), never deleted. An archived patient gets no new VR program, but sessions already recorded still upload (DEC-014).
- A patient code never changes after registration (the VR app is configured with it).
- Every prescription write path applies the same bounds (`RX_FIELDS`).
- The server sends no CORS headers; static files are served only from inside `static/`; the server listens on 127.0.0.1 unless started with `--host`.
- The patient record holds a real name and a code (DEC-027). The name is stored and shown only in the therapist dashboard; exports, VR routes (`get_program(for_vr=True)`), logs and recordings carry the code only.
- Only sessions whose `input_source` is in `COUNTED_SOURCES` (`webcam`) drive adherence, streak, readiness, flags, dashboard KPIs, XP, badges, progression and the VR progress page. Keyboard, simulated and unknown-source sessions are stored and labelled, and the upload response says `counted: false` (M7.1).
- A phase progression cannot be applied automatically without explicit therapist confirmation logged in `phase_history`.
- Protocol deletions and patient detachments must preserve exercise histories and use parameterized SQL queries.
- A patient code can only read or write its own record; a VR session whose `patient_id` differs from the code's patient is refused (403), and `patient_id` 0 means "recorded offline, attribute by code".
- Patient codes are pseudonyms, not secrets, so VR routes must stay loopback-only while the server binds `0.0.0.0` for the dashboard.
- The `LIBRARY` entry is the single source of an exercise's rules; adding an exercise that uses an existing pose needs no Unity change (DEC-012).
- Rep events are stored with their session in the same transaction, only for exercises in the patient's program; a repeated `session_uuid` never adds rows.
- A session without an input source is stored as `unknown`, never counted as webcam data.

## Notes
- `server/backup.py` makes and restores AES-GCM encrypted, scrypt-keyed database backups (`.tqbak`); restore writes a new file only, and a lost password cannot be recovered (M7.3).
- Running `python server.py --reset` completely resets the SQLite database and re-seeds patient `P-001` and protocol records; the first clinician login is created at first run (no default password since M4.2).
- Database operates in WAL mode (`PRAGMA journal_mode = WAL;`) with normal synchronous I/O, memory temp store, and 32MB cache.

## Future Changes
- A per-device patient secret if the VR client ever runs on a different host than the server (would replace loopback-only trust).
