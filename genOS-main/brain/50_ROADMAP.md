# Roadmap

Authoritative long-term development roadmap and **sole source of truth for milestone definitions**.
AI-owned. See `AGENTS.md` → Ownership.

**This file owns:** milestone IDs, objectives, deliverables, completion criteria, dependencies, and lifecycle status.  
**This file does not own:** live session execution state (that is `20_PROGRESS.yaml` only).

Do not copy milestone criteria into Progress or Backlog. Progress stores only `current_milestone` (ID) plus execution RAM.

**Status values:** `planned` | `active` | `TBF` | `done` | `cancelled`
- `TBF` (To-Be-Finished): implementation and automated tests are complete; only human verification is left, listed in [[20_PROGRESS.yaml]] → `pending_human_tests`. Set it to `done` once those checks pass. A parent milestone stays `active` while a child is `TBF`.

**ID conventions:**
- Program milestones: `M0`, `M1`, `M2`, …
- Child milestones: `M0.1`, `M0.2`, `M1.1`, … under a parent
- Unscheduled future milestones: a temporary ID (e.g. `HW`, children `HW.1`) and no number until the human decides where they go in the sequence; they get the next `M` number then.

---

## Index

| ID | Parent | Status | Title |
|----|--------|--------|-------|
| M0 | — | done | Core Working Prototype & Clinical Baseline |
| M0.1 | M0 | done | MediaPipe 2D Pose Tracker & UDP Streaming |
| M0.2 | M0 | done | Unity VR & Desktop Clinic Environment with OpenXR |
| M0.3 | M0 | done | Real-Time Kinematics, Posture Checks & Safety Limits |
| M0.4 | M0 | done | Dual-Mode HUD, Gamification & Multimodal Feedback |
| M0.5 | M0 | done | Clinical REST API, SQLite Persistence & Therapist Dashboard |
| M1 | — | done | Feature Expansion: Exercise Library & Avatar Guidance |
| M1.1 | M1 | done | Extended Clinical Exercises & Pose Visualizers |
| M1.2 | M1 | done | Multi-Avatar Coach Selection & Visual Pacing / Hold Timers |
| M2 | — | done | Clinical Evaluation & Analytics Export Pipeline |
| M2.1 | M2 | done | Performance Metric Export (CSV / JSON) |
| M2.2 | M2 | done | Confusion Matrix & Angle Error Analysis Scripts |
| M3 | — | done | Security, Therapist Authentication & Production Hardening |
| M3.1 | M3 | done | Dashboard Authentication & Session Security |
| M3.2 | M3 | done | Clinical Endpoint Authorization & Patient Code Isolation |
| M4 | — | done | Foundation Hardening (pre-feature stabilization) |
| M4.1 | M4 | done | Repository & Environment Safety |
| M4.2 | M4 | done | Backend Security & Data Integrity |
| M4.3 | M4 | done | Unity Client Robustness & Deployability |
| M4.4 | M4 | done | Tracker Measurement Correctness |
| M4.5 | M4 | done | Evaluation Pipeline Integrity |
| M4.6 | M4 | done | Single Source of Exercise Definitions |
| M5 | — | done | Dashboard & Game Experience |
| M5.1 | M5 | done | Dashboard UX & Accessibility Polish |
| M5.2 | M5 | done | Patient & Protocol Management |
| M5.3 | M5 | done | Clinical Insights & Attention Flags |
| M5.4 | M5 | done | Session Flow Polish |
| M5.5 | M5 | done | Session Summary & Progress Screens |
| M5.6 | M5 | done | Audio & Visual Assets |
| M5.7 | M5 | done | Additional Built-in Clinical Protocols |
| M5.8 | M5 | done | First-Person Exercise View & Default Height |
| M5.9 | M5 | done | Tracking Reliability & Loss Safeguards |
| M6 | — | done | Camera Tracking Mechanics |
| M6.1 | M6 | done | Landmark Record & Replay Harness |
| M6.2 | M6 | done | Facing Direction & Extension Readings |
| M6.3 | M6 | done | Camera Setup Assistant |
| M6.4 | M6 | done | Out-of-Plane Live Limb & Ankle Exercises |
| M6.5 | M6 | done | Webcam Field Test & Tuning |
| M7 | — | done | Pre-Study Data Readiness |
| M7.1 | M7 | done | Only Webcam Sessions Count |
| M7.2 | M7 | done | Patient Name and Code |
| M7.3 | M7 | done | Encrypted Backup and Restore |
| M7.4 | M7 | done | Unity Company Name |
| M8 | — | active | Visual & UX Polish |
| M8.1 | M8 | done | URP Migration |
| M8.2 | M8 | done | Clinic Room Look |
| M8.3 | M8 | active | Feedback Motion |
| M8.4 | M8 | planned | Hologram & Coach Window |
| M8.5 | M8 | planned | Menus & Summary Polish |
| M8.6 | M8 | done | Dashboard Visual Refresh |
| M8.7 | M8 | planned | Dashboard Hidden Data |
| M9 | — | active | Manuscript Finalization & Polish |
| M9.1 | M9 | done | Manuscript Audit |
| M9.2 | M9 | done | Language and Flow Edit |
| M9.3 | M9 | active | Sync with the Built System |
| M9.4 | M9 | planned | Figures and Screenshots |
| M10 | — | active | XR Environment & VR Integration |
| M10.1 | M10 | done | XR Origin Rig & Quest Link Lifecycle |
| M10.2 | M10 | done | Controller Input & Ray Menus |
| M10.3 | M10 | active | Comfort Locomotion in the Rig |
| M10.4 | M10 | planned | Headset Panels & Rendering |
| HW | — | planned | Hardware Integration & Field Validation |
| HW.1 | HW | planned | Hardware Setup & Compatibility Baseline |
| HW.2 | HW | planned | Headset Integration Test |
| HW.3 | HW | planned | Webcam and Headset Concurrent Operation |
| HW.4 | HW | planned | End-to-End Integration Run |
| HW.5 | HW | planned | First-Person View Assessment |

---

## Suggested sequence

`M0` (done) ➔ `M1` (done: features & avatars) ➔ `M2` (done: analytics & evaluation) ➔ `M3` (done: security & hardening) ➔ `M4` (done: foundation hardening before new game & dashboard features) ➔ `M5` (done: dashboard & game experience, first-person view and tracking safeguards; their human checks moved to HW) ➔ `M6` (done: camera tracking mechanics, webcam only, no headset) ➔ `M7` (done: pre-study data readiness, backlog TASK-003..TASK-006)

In progress: `M8` (active: visual and UX polish; M8.2 and M8.6 done 2026-11-24, the other children wait) and `M9` (active since 2026-11-16: manuscript finalization; the progress pointer is on M9).

Unscheduled (no number yet): `HW` Hardware Integration & Field Validation; its place in the sequence is not decided (it takes the next free `M` number when scheduled).

---

## M0 — Core Working Prototype & Clinical Baseline

- **Status:** done
- **Objective:** Establish a working end-to-end prototype featuring single-webcam computer vision motion tracking, a Unity 6 VR clinic environment with Quest Link, real-time exercise scoring and posture checks, gamification, and a local therapist dashboard with clinical protocol support.
- **Success criteria:**
  - Webcam tracks 2D joint angles via MediaPipe and streams over UDP to Unity at ~30 FPS.
  - Unity renders the 3D clinic room, coach avatar, and power meter HUD in VR and desktop fallback.
  - Repetition counter accurately assesses ROM within tolerance, invalidates compensation postures, and alerts on safety limits.
  - Therapist dashboard at `http://localhost:8000` manages prescriptions and tracks adherence across OHSU knee and MGB rotator cuff protocols.
- **Children:**
  - `M0.1`: MediaPipe 2D Pose Tracker & UDP Streaming
  - `M0.2`: Unity VR & Desktop Clinic Environment with OpenXR
  - `M0.3`: Real-Time Kinematics, Posture Checks & Safety Limits
  - `M0.4`: Dual-Mode HUD, Gamification & Multimodal Feedback
  - `M0.5`: Clinical REST API, SQLite Persistence & Therapist Dashboard
- **Done when:** End-to-end integration test passes from camera capture through exercise completion to SQLite session persistence.

### M0.1 — MediaPipe 2D Pose Tracker & UDP Streaming
- **Status:** done
- **Objective:** Single-camera MediaPipe Pose landmark extraction and socket streaming.

### M0.2 — Unity VR & Desktop Clinic Environment with OpenXR
- **Status:** done
- **Objective:** OpenXR runtime setup with Meta Quest Link and desktop windowed fallback.

### M0.3 — Real-Time Kinematics, Posture Checks & Safety Limits
- **Status:** done
- **Objective:** 2D joint angle calculation, range-of-motion validity, and compensation detection.

### M0.4 — Dual-Mode HUD, Gamification & Multimodal Feedback
- **Status:** done
- **Objective:** VR and desktop heads-up displays, rep counters, audio cues, and XP system.

### M0.5 — Clinical REST API, SQLite Persistence & Therapist Dashboard
- **Status:** done
- **Objective:** Python HTTP server, relational database, and therapist monitoring web app.

---

## M1 — Feature Expansion: Exercise Library & Avatar Guidance

- **Status:** done
- **Objective:** Broaden core feature capabilities by expanding the catalog of trackable rehabilitation exercises, upgrading humanoid coach avatars, and adding rich visual guidance cues (pacing rhythms, hold countdowns).
- **Success criteria:**
  - Additional validated clinical exercises added to `LIBRARY` in `server.py`, `FigureVisualizer.cs`, and `angles.py` / `MotionInput.cs` as needed.
  - Multi-avatar selector allowing patient selection of distinct humanoid coach models.
  - Real-time pacing cues and visual hold ring/timer during static endurance poses.
- **Children:**
  - `M1.1`: Extended Clinical Exercises & Pose Visualizers
  - `M1.2`: Multi-Avatar Coach Selection & Visual Pacing / Hold Timers
- **Done when:** Newly added exercises can be selected on the dashboard, performed in VR with clear avatar visual cues, and accurately scored by the evaluator.

### M1.1 — Extended Clinical Exercises & Pose Visualizers
- **Status:** done
- **Objective:** Expanded clinical exercise movements with visual skeleton overlays.

### M1.2 — Multi-Avatar Coach Selection & Visual Pacing / Hold Timers
- **Status:** done
- **Objective:** Selectable coach avatars with procedural animations, pacing halos, and hold timers.

---

## M2 — Clinical Evaluation & Analytics Export Pipeline

- **Status:** done
- **Objective:** Implement comprehensive data export and analytical utilities to evaluate system accuracy, confusion matrices, and adherence metrics for the capstone research manuscript (Section 3.9).
- **Success criteria:**
  - One-click export of detailed `performance_record` telemetry (mean angle error, accuracy %, unsafe reps, session timestamps) to CSV/JSON.
  - Automated evaluation scripts comparing MediaPipe detected angles against goniometer baseline measurements.
- **Children:**
  - `M2.1`: Performance Metric Export (CSV / JSON)
  - `M2.2`: Confusion Matrix & Angle Error Analysis Scripts
- **Done when:** Research evaluation datasets can be generated directly from clinical session logs with reproducible statistical metrics.

### M2.1 — Performance Metric Export (CSV / JSON)
- **Status:** done
- **Objective:** Telemetry export routes for performance records and clinical session logs.

### M2.2 — Confusion Matrix & Angle Error Analysis Scripts
- **Status:** done
- **Objective:** Analytical evaluation benchmarks asserting accuracy against clinical baselines.

---

## M3 — Security, Therapist Authentication & Production Hardening

- **Status:** done
- **Objective:** Finalize security, authentication, and access controls across the clinical backend and dashboard as the concluding phase before deployment.
- **Success criteria:**
  - Therapist login authentication required to access `dashboard.html` and administrative REST endpoints.
  - Secure credential storage (hashed and salted passwords) in `theraquest.db`.
  - Separation between patient-accessible telemetry upload endpoints and therapist-only prescription/clinical note endpoints.
- **Children:**
  - `M3.1`: Dashboard Authentication & Session Security (done)
  - `M3.2`: Clinical Endpoint Authorization & Patient Code Isolation (done)
- **Done when:** Unauthenticated users cannot view patient logs, alter prescriptions, or access clinical records via browser or curl.

### M3.1 — Dashboard Authentication & Session Security
- **Status:** done
- **Objective:** Implement clinician credentials, session tokens, in-app clinical modals, and protocol lifecycle management with database performance hardening.
- **Success criteria:**
  - PBKDF2/SHA-256 password hashing with unique 16-byte salts and `therapist_session` table with 24-hour token expiration.
  - REST endpoints for authentication (`/api/auth/login`, `/api/auth/logout`, `/api/auth/me`).
  - In-app modals (`#confirmModal`, `#addExerciseModal`, `#noteModal`, `#newPatModal`, `#protocolModal`, `#protocolPhasesWidget`) and floating toasts replacing all native browser dialogs.
  - Full protocol lifecycle management (authoring, library deletion, and patient detachment).
  - SQLite WAL mode, 11 database performance indexes, and N+1 query elimination.
- **Done when:** Dashboard requires therapist authentication, all browser popups are replaced with in-app clinical modals, and performance indexes are verified via automated regression testing.

### M3.2 — Clinical Endpoint Authorization & Patient Code Isolation
- **Status:** done
- **Objective:** Enforce token verification on all protected clinical REST endpoints, separate VR telemetry upload from therapist administrative routes, and ensure patient code isolation (see [[30_DECISIONS]] DEC-009).
- **Success criteria:**
  - All therapist routes (`/api/patients*`, `/api/protocols*`, `/api/library`, `/api/sessions/{id}/clinical`, `/api/export*`) reject requests lacking a valid bearer token with `401 Unauthorized`; `/api/patients/{id}/program` is therapist-only for both `GET` and `PUT`.
  - The Unity client uses dedicated patient-scoped routes (`GET /api/vr/program`, `POST /api/vr/sessions`) authorized by the `X-Patient-Code` header, without clinician credentials.
  - A patient code can only read or write its own record (`403` on `patient_id` mismatch), and VR routes accept loopback clients only (`403` from other hosts).
  - Offline-queued Unity uploads still drain after the change (re-sent to `POST /api/vr/sessions`; the legacy `POST /api/sessions` is removed, and refused lines are kept in a rejected file).
  - Automated authorization test suite asserting 401s on unauthenticated therapist requests and patient-code isolation on VR routes.
- **Done when:** Direct curl/HTTP calls to clinical endpoints without a valid therapist token are strictly rejected, and the VR client can still load its prescription and upload sessions using only its patient code.

---

## M4 — Foundation Hardening (pre-feature stabilization)

- **Status:** done
- **Objective:** Fix the underlying security, data-integrity, deployability, measurement and research-integrity problems found in the 2026-10-20 project-wide audit, so new game and dashboard features are built on a safe, testable base.
- **Success criteria:**
  - Project is under version control with generated folders ignored, and the live database lives outside OneDrive (DEC-010).
  - No unauthenticated path can read the database or plant script in the dashboard; no default password ships.
  - A built Unity player can be pointed at any patient without the Editor, runs over OpenXR, and never runs a session without a server-issued (or cached) prescription.
  - Tracker never scores hidden landmarks or wrong-direction movements as valid.
  - Every evaluation report states its data source; synthetic results are labelled (DEC-011).
  - Adding an exercise that uses an existing pose needs only a server `LIBRARY` entry (DEC-012).
- **Children:**
  - `M4.1`: Repository & Environment Safety (done)
  - `M4.2`: Backend Security & Data Integrity (done)
  - `M4.3`: Unity Client Robustness & Deployability (done)
  - `M4.4`: Tracker Measurement Correctness (done)
  - `M4.5`: Evaluation Pipeline Integrity (done)
  - `M4.6`: Single Source of Exercise Definitions (done)
- **Done when:** all children are done and the server, tracker, evaluation and Unity EditMode test suites pass, followed by a human Play-mode check. (The headset check moved to HW.2 on 2026-10-25.)

### M4.1 — Repository & Environment Safety
- **Status:** done
- **Objective:** Protect the work and the clinical data from loss.
- **Deliverables:** git repository with `.gitignore`; configurable database path defaulting to `%LOCALAPPDATA%\TheraQuest` with one-time migration; pinned Python dependencies; consolidated launchers; README brought up to date.
- **Completion criteria:** `git status` is clean after opening Unity and running the server; the server writes its database outside OneDrive; `--reset` also clears WAL side files.
- **Dependencies:** none
- **Systems:** ClinicalBackend, MotionTracking

### M4.2 — Backend Security & Data Integrity
- **Status:** done
- **Objective:** Close the security holes and make session recording trustworthy.
- **Deliverables:** static path containment; CORS removed; dashboard output escaping; first-run password, change-password, login throttling, hashed tokens with purge; 400/404 error mapping; server-side completion rules, idempotent session uploads, atomic XP; protocol replacement that keeps therapist-authored protocols; prescription bounds on every write path; migration ordering; `test_backend.py`.
- **Completion criteria:** the backend test suites pass, including traversal, stored-script, idempotency, migration and throttling cases.
- **Dependencies:** M4.1
- **Systems:** ClinicalBackend, TherapistDashboard

### M4.3 — Unity Client Robustness & Deployability
- **Status:** done
- **Verification so far:** EditMode tests pass (26); Windows player builds and starts with `-patient` in desktop fallback; Editor Play-mode check (online, offline cache, queue flush, Therapist page) passed 2026-10-22; built player with `-patient` against a running server and tracker passed 2026-10-25 (human-verified).
- **Objective:** Make the VR client deployable to a clinic and robust to bad input and failures.
- **Deliverables:** patient code from command line / config / PIN-protected therapist page; OpenXR packages and loader; cached last program instead of hardcoded offline program; input source locked during sessions; resilient offline queue with session UUIDs; prescription validation; loopback-only UDP receiver; locomotion lock; quit checkpoint; EditMode tests.
- **Completion criteria:** EditMode tests pass; a built player runs with `-patient`; desktop fallback works. (Amended 2026-10-25 by the human: the headset run moved to HW.2, because no headset is available yet.)
- **Dependencies:** M4.2 (session UUID, 4xx semantics)
- **Systems:** SessionOrchestration, ExerciseEvaluation, VRClinicExperience

### M4.4 — Tracker Measurement Correctness
- **Status:** done
- **Objective:** Only measure what the camera can actually see, in the right direction.
- **Deliverables:** per-landmark visibility; visibility-checked posture metrics; zero-length vectors reported as not visible; signed side-view elevation angles; camera reconnect; verified model download; tests.
- **Completion criteria:** `test_angles.py` covers each case and passes; UDP payload stays backward compatible.
- **Dependencies:** none (Unity/server use of the signed angles lands in M4.6)
- **Systems:** MotionTracking

### M4.5 — Evaluation Pipeline Integrity
- **Status:** done
- **Objective:** Make research metrics come only from real, labelled data.
- **Deliverables:** synthetic run renamed `--self-test` with a banner and computed status; CSV templates for goniometer, therapist rep labels, SUS and PT survey; per-rep `rep_event` log from Unity; confusion matrix from labels joined to rep events; webcam-only filtering; tests.
- **Completion criteria:** a known CSV yields known metrics; with no real inputs the report says "not measured", never PASS.
- **Dependencies:** M4.2, M4.3
- **Systems:** ClinicalBackend, ExerciseEvaluation

### M4.6 — Single Source of Exercise Definitions
- **Status:** done
- **Objective:** Stop exercise rules being duplicated across server and Unity.
- **Deliverables:** `LIBRARY` fields for posture, posture checks, direction and figure pose sent in the VR program; Unity `MotionInput`, `HumanoidCoach` and `FigureVisualizer` read them instead of switching on codes.
- **Completion criteria:** a new exercise using an existing pose works after adding only a `LIBRARY` entry.
- **Dependencies:** M4.3, M4.4
- **Systems:** ExerciseEvaluation, AvatarCoach, ClinicalBackend


## M5 — Dashboard & Game Experience

- **Status:** done (reopened 2026-11-01 by the human for M5.8 and M5.9; closed 2026-11-05 when the human moved the remaining checks to HW.3 and HW.5)
- **Objective:** Make the therapist dashboard easier and safer to use, give therapists patient/protocol management and early warnings, and make the patient game more rewarding and polished. Scope chosen by the human on 2026-10-26; showing the unused dashboard data (TASK-001) and the high-priority backlog (TASK-003..TASK-006) are deliberately outside M5.
- **Success criteria:**
  - The dashboard app works fully by keyboard, fits its window from the minimum size up (DEC-013), and shows honest empty, loading and error states.
  - Therapists can edit and archive patients and edit protocol phases without losing clinical records.
  - The caseload flags patients who need attention, with the reasons and the input sources counted.
  - The game has clear pacing between exercises, a rewarding summary and a progress page (history, streak, level, badges).
  - Placeholder sounds, music, badge art and text rendering are replaced with licensed assets, with credits recorded.
- **Children:**
  - `M5.1`: Dashboard UX & Accessibility Polish (done)
  - `M5.2`: Patient & Protocol Management (done)
  - `M5.3`: Clinical Insights & Attention Flags (done)
  - `M5.4`: Session Flow Polish (done)
  - `M5.5`: Session Summary & Progress Screens (done)
  - `M5.6`: Audio & Visual Assets
  - `M5.7`: Additional Built-in Clinical Protocols (done)
  - `M5.8`: First-Person Exercise View & Default Height (done)
  - `M5.9`: Tracking Reliability & Loss Safeguards (done)
- **Done when:** all children are done; the server, tracker, evaluation and Unity EditMode test suites pass; the human has done a dashboard walkthrough and a Play-mode walkthrough of the game (listed in `pending_human_tests` while open; the milestone is TBF until then).
- **Dependencies:** M4. The dashboard children (M5.1–M5.3) and the game children (M5.4–M5.6) don't depend on each other.

### M5.1 — Dashboard UX & Accessibility Polish
- **Status:** done
- **Human check:** passed 2026-10-28 (reported by the human).
- **Verification so far (2026-10-26):** server tests pass (backend 30, authorization 13, including the new session-paging test). Browser check on a throwaway database: sign-in, caseload, chart and dialogs work by keyboard (Tab stays inside dialogs; Escape closes them and returns focus); no horizontal scroll at the app's minimum window size (980 × 640) on any view; empty states for a patient with no sessions; inline errors with Retry when the server stops; no console errors; no requests outside localhost. Left: the human walkthrough in the desktop app (`pending_human_tests`).
- **Objective:** Make the existing dashboard robust, accessible and consistent before adding features to it.
- **Deliverables:** empty, loading and inline error states (no fake "No Data" chart point; library/protocol load failures shown); keyboard-reachable navigation; dialogs that close on Escape, trap and restore focus, with labelled fields; tab roles on sub-tabs; status not shown by colour alone; layout that fits the app window from its minimum 980 × 640 up (DEC-013; the narrow-screen rules added also cover a small Edge fallback window); colours from CSS variables and no emoji in status text; unused Tailwind script removed; no `@latest` CDN fallback; session time shown, paging past 50 rows, duplicate CSV button removed.
- **Completion criteria:** the dashboard app is fully usable by keyboard and at its minimum window size; empty and error states are correct; the server test suites pass; human walkthrough in the desktop app.
- **Dependencies:** M4.2
- **Systems:** TherapistDashboard

### M5.2 — Patient & Protocol Management
- **Status:** done
- **Human check:** passed 2026-10-28 (reported by the human).
- **Verification so far (2026-10-26):** backend tests 39 (9 new: edit, code lock, length limits, archive/unarchive, archived VR program refused while queued uploads still save, built-in read-only, add/edit phase, criteria bounds, wrong-protocol phase, patients on an edited phase keep their prescription) and authorization tests (new routes refuse missing and bad tokens) pass; migration test checks `archived_at`. Browser check on a throwaway database at the app's minimum window size: edit details, archive with confirmation, archived banner and Reactivate, caseload hides archived unless "Show archived patients", phase editor (edit and add) on a custom protocol, read-only note on built-in protocols. Decision: DEC-014. Left: the human check in the desktop app (`pending_human_tests`).
- **Objective:** Let therapists correct and retire records and refine protocols without touching the database.
- **Deliverables:** edit patient details; archive / unarchive patients (records kept, archived hidden from the caseload by default; decision recorded); edit and add phases on therapist-authored protocols (built-in protocols read-only); new endpoints with authorization, bounds checks and escaping as in M4.2; schema migration in the existing order; tests. The patient name field keeps its current behaviour (TASK-004 decides its future).
- **Completion criteria:** backend and authorization tests cover each new endpoint, including unauthorized access and archived-patient behaviour, and pass.
- **Dependencies:** M5.1
- **Systems:** ClinicalBackend, TherapistDashboard

### M5.3 — Clinical Insights & Attention Flags
- **Status:** done
- **Human check:** passed 2026-10-28 (reported by the human).
- **Verification so far (2026-10-26):** backend tests 51 pass (9 new: no flags for a quiet patient, pain spike, pain rising across sessions, accuracy drop and a small dip not flagged, unsafe reps with old sessions ignored, missed days, no missed days before enrolment, no flags when archived; sources counted per flag). Browser check at the app's minimum window on a throwaway database: flagged patient sorted first with chips, chart notice with reasons and counted sources (non-webcam sessions called out), Clinical Status box from the flags. Left: the human check (`pending_human_tests`) and PT review of the thresholds (TASK-007).
- **Objective:** Show the therapist which patients need attention first, and why.
- **Deliverables:** server-computed per-patient flags (pain rising over recent sessions, accuracy dropping, missed scheduled days, unsafe reps); a "needs attention" column and sort on the caseload; reasons in the chart header; thresholds as named placeholder constants for PT review (see TASK-007); each flag states which input sources it counted (simulated sessions still count until TASK-003 is decided); tests.
- **Completion criteria:** each flag has tests for firing and not firing; the caseload sorts by attention.
- **Dependencies:** M5.1
- **Systems:** ClinicalBackend, TherapistDashboard

### M5.4 — Session Flow Polish
- **Status:** done
- **Human check:** passed 2026-10-28 (reported by the human).
- **Verification so far (2026-10-26):** Agent play-test in the Unity Editor (simulated input, offline cached program; the offline upload queue was backed up and restored after each run) on a seated, a standing and a side-lying exercise: get-ready card, countdown, keyboard hints and the queued-sessions line show correctly; auto-focus frames the coach at get-ready and again at Go once the coach takes the exercise pose (found during the play-test: the coach stands idle until Go, so a seated exercise was framed as standing). Also fixed the 'Moved too quickly (01s)' number format. Unity EditMode tests 35 pass (9 new: countdown 3-2-1-Go, countdown frozen while paused, restart keeps every attempt and unsafe rep while resetting the sets, control hints per device, four auto-focus framing cases: standing, on the table, small motions, coach to the side, and the too-fast message format); no compile errors. Restart design: the sets start again from set 1, but all attempts stay in the rep log and the upload (attempt numbers keep counting), so the therapist and the evaluation see them; the session UUID is unchanged. Left: human Play-mode check (`pending_human_tests`); the Unity Editor was not open, so nothing was checked in Play mode.
- **Objective:** Give the patient clear pacing and control during a session.
- **Deliverables:** auto-focus on the exercise (added by the human 2026-10-26: on the laptop the camera eases in to frame the coach at every exercise; in the headset only an instant re-center, to avoid motion sickness); 3-2-1 countdown and transition card between exercises; exercise-complete celebration; "Restart exercise" in the pause menu (rep log and session UUID stay consistent); queued offline uploads shown on the menu; control hints from the active input mode; EditMode tests for new pure logic.
- **Completion criteria:** EditMode tests pass; restart keeps the uploaded session correct; human Play-mode check.
- **Dependencies:** M4.3
- **Systems:** SessionOrchestration, VRClinicExperience

### M5.5 — Session Summary & Progress Screens
- **Status:** done
- **Human check:** passed 2026-10-28 (reported by the human).
- **Verification so far (2026-10-26):** server tests 54 pass (3 new: progress in the VR program and not in the dashboard's program endpoint, structured rewards xpGained / levelBefore / levelAfter in the upload response, recent-session limit); Unity EditMode tests 42 pass (7 new: XP span within a level and across a level-up, exercise lines, notes left to the animation, badge gallery, Progress page text, gamification scoring). Agent play-test against a throwaway server and database (the offline queue and program cache were backed up and restored): Progress page, full session summary with per-exercise lines, XP bar and new badges. Found and fixed during the play-test: the summary's starting XP was stale when queued offline sessions were sent at load (now from the server's xpGained); the Progress page overflowed the view (tall menu pages now scale down); badge names wrapped mid-name. Progress data rides on GET /api/vr/program (loopback, patient code, DEC-009) and is cached with the program for offline use. Left: human Play-mode check (`pending_human_tests`).
- **Objective:** Make progress visible and rewarding to the patient.
- **Deliverables:** short summary (changed by the human 2026-10-26: no per-exercise breakdown, notes or therapist numbers on the patient's summary; totals, a STOP-line warning when needed, saved status), animated XP fill, badge reveal online and offline, and a clear level-up moment (not a string match); main-menu Progress page with recent sessions, streak, level/XP and a badge gallery (earned and locked); progress data from a loopback-only, patient-code-scoped VR route or the program payload (DEC-009), shown as cached when offline; server tests; EditMode tests for summary/progress shaping and `GamificationManager`.
- **Completion criteria:** server and EditMode tests pass; human Play-mode check online and offline.
- **Dependencies:** M5.4
- **Systems:** Gamification, SessionOrchestration, ClinicalBackend, VRClinicExperience

### M5.6 — Audio & Visual Assets
- **Status:** done
- **Human check:** passed 2026-10-28 (reported by the human).
- **Verification so far (2026-10-26):** all six items in, every asset chosen by the human from previews and credited in `Assets/TheraQuest/CREDITS.md` with its licence file alongside (all CC0 except the fonts: Apache 2.0, SIL OFL, Bitstream Vera/DejaVu). Fonts: Luckiest Guy (44 px and up) and Nunito, outlines in a lighter shade of the text colour (subtitles keep a dark outline). Sound: new hold-complete chime (Kenney); menu click, STOP warning, level up stay generated by the human's choice, the badge chime gets a generated reverb tail. Music: nine CC0 lo-fi tracks (omfgdude, Holizna) as a shuffled playlist at the Music volume. Badge icons: seven Kenney icons, gold when earned and grey when locked, on the HUD chips, the summary reveal and the Progress page. Coach idle: Quaternius Universal Animation Library `Idle_Loop` (Humanoid). TextMeshPro for all HUD and menu text, approved by the human (DEC-015). Assets load from `Resources`, and each falls back (generated loop and chimes, ★ chips, hand-made sway, default font) when missing; checked in Play mode with the assets moved out. Unity EditMode tests 49 pass (6 new). The agent play-tested in the Editor (simulated input, throwaway server, offline queue and program cache restored) and checked screenshots of the menu, HUD, summary and Progress page. Follow-up requested by the human the same day: every display-font label is outlined (lighter shade of its colour; white text on pills and tiles gets a darker shade of the pill); a VR headset logo (Font Awesome `vr-cardboard`, SIL OFL) sits beside the game name on the main menu; the Progress page has three tabs (Profile, Recent sessions, Badges with how to earn each), switched with Left / Right or a click; the HUD cards, summary card and menu are sized to their content (the hold bar and new-badge row appear only when used). Play-mode screenshots checked; EditMode tests still 49. Second follow-up (same day): five-colour palette for all panels and text (DEC-016; red kept only for safety warnings), headset logo moved after the game name and tilted 30° away from it, navy text outlined in off-white and pop-ups in a darker shade, and the Badges tab shows one card per badge (icon, name, how to earn it at the bottom; locked cards greyed). EditMode tests 50 pass. Third follow-up (2026-10-27): badge cards lost their coloured top bar; the coach area was fixed: the exercise mat now follows the coach and its chair or bed for every posture (it had the coach on its front edge with props hanging off), the coach stands with no props on menus and waits seated or lying in the coming exercise's posture during get-ready (it used to stand beside the chair or bed), resting legs lie straight on the bed (shins had sunk through the mattress), and seated hands rest at the knees. Checked in Play mode for standing, seated, lying and side-lying; EditMode tests 50 pass. Correction (2026-10-27): the coach idle had not actually been playing, because none of the 16 coach models imported as a Humanoid (the Quaternius rig keeps its feet under the root); `CoachModelImporter` now maps the rig by hand, the idle clip drives the trunk, head and arms (standing legs stay hand-posed, since the retargeted clip took a stride), and a new test checks every coach model is a valid Humanoid. Verified in Play mode on the male and female coaches; EditMode tests 51 pass. A cartoon coach style (DEC-017: toon shading, outlines, stylised proportions) was added and then removed at the human's request on 2026-10-27 (DEC-017 superseded); the Little Guys coaches (DEC-018) now show as modelled, with a plain Built-in material in place of the pack's URP one; checked in Play mode on both genders. Coach follow-up (2026-10-27, human requests): old Quaternius coaches deleted; upright T-pose avatars for the Little Guys so the idles stand straight with open hands; talking gestures while the coach speaks; coach 0.6 m further back on a yoga mat; lying exercises on the mat, no bed; checked in Play mode for all four postures; EditMode tests 51 pass. Room assets (2026-10-27, TASK-014, DEC-019): equipment from the Low Poly Gym Pack and furniture from the Kenney Furniture Kit replace the primitive decorations, and the seated-exercise chair is a Kenney model; checked in Play mode; EditMode tests 52 pass. Coach and room follow-up (2026-10-28, human requests): the coach keeps its model's own body shape (the idle clips move only the arms; hips, spine, neck, head and legs stay as modelled in every posture), its shoe soles rest on top of the mat standing and the body rests on it lying (heights measured from the posed mesh; the mat now fits the whole body lying down), and its face blinks every few seconds, smiles softly (more on good reps), looks concerned on a warning and (second request the same day) keeps its mouth still while speaking; its arms hang relaxed at the sides, hand-posed, with open fingers, and its shoulder joints sit at the sides of the chest (the Little Guys' collarbones set them behind it); third request: both hands hang the same distance from the hips (the idle reused the 0° shoulder pose, which put one hand into the waist), palms face the thighs and the fingers rest in a gentle curl; room models with floating parts or the wrong look were replaced (rowing machine for the exercise bike, weight-plate stack and dumbbells for the kettlebells, a sofa for the chair-like benches, a glass look for the mirror). Measured and checked in Play mode on both coaches and all four postures; EditMode tests 52 pass. Left: the human Play-mode check (`pending_human_tests`) and confirming the source of the older rep sounds (CREDITS.md "Not yet recorded").
- **Objective:** Replace placeholder sounds, art and text rendering.
- **Deliverables:** real sound effects (level-up, badge, warning, click, hold complete); a music track; one icon per badge; a coach idle animation; TextMeshPro for HUD and menu text; assets only from CC0/licensed sources or supplied by the human, with a credits file recording source and licence; generated chimes kept as a fallback.
- **Completion criteria:** every asset is credited; the game runs with assets present and with them missing; human Play-mode check (legibility, volume).
- **Dependencies:** M5.5 (badge reveal and progress page use the badge icons)
- **Systems:** VRClinicExperience, AvatarCoach, Gamification


### M5.7 — Additional Built-in Clinical Protocols
- **Status:** done
- **Human check:** passed 2026-10-28 (reported by the human).
- **Objective:** Give therapists more evidence-based protocols to assign (requested by the human 2026-10-26): ACL reconstruction, hip fracture fixation, a second total knee arthroplasty source, ORIF for ankle, distal radius and tibial plateau fractures, and lateral ankle sprain.
- **Deliverables:** seven `PROTOCOLS` entries summarized from published documents (ACL, TKA, ankle ORIF and ankle sprain: Mass General Brigham; distal radius ORIF: Brigham and Women's 2021; tibial plateau ORIF: Twin Cities Orthopedics, Dr. Butterfield 04/2024; hip fracture fixation: Dr. Jason Ferrel 07/2024), with the camera-measurable exercises in VR phases and the rest listed as done without the camera; protocol version 3; the built-in reload keeps unchanged protocols so patients on them keep their phase; tests.
- **Completion criteria:** backend tests pass, including reload and data-shape tests; the protocols appear read-only in the library; human check that the phases read correctly.
- **Verification so far (2026-10-26):** backend tests 42 pass (3 new: unchanged built-in keeps patients on their phase, changed built-in is replaced, every built-in is well formed); the upgrade was run on a copy of the live database (OHSU and MGB rotator cuff kept, seven added); the library shows all nine read-only. Left: the human check (`pending_human_tests`) and the licensed-PT review of targets (TASK-007).
- **Dependencies:** M5.2 (read-only built-ins, DEC-014)
- **Systems:** ClinicalBackend, TherapistDashboard

### M5.8 — First-Person Exercise View & Default Height
- **Status:** done
- **Objective:** Change the exercise from watching a coach in the room to following a guide on the patient's own body, seen in first person, from the same default height for everyone (requested by the human 2026-11-01; DEC-021).
- **Deliverables:** a see-through target limb at the prescribed angle, extending from the patient's default body, which is the exercise's threshold, plus a live limb following the tracker's angle; the old gold threshold shapes, ghost and Guide Mode removed; a floating coach window under the quest card showing the coach holding the target pose, still, with an arrow and word guides; the coach in the room only on menus and the summary; a side mirror panel and a reach chime for limbs that end behind the patient (shoulder extension, hip extension, hamstring curl); a default view height per posture that the headset is calibrated to; a tutorial before the first exercise of every session, skippable and not scored or saved; tests.
- **Completion criteria:** EditMode tests pass; every posture works in Play mode. The headset path is checked in HW.2. (Amended 2026-11-05 by the human: the human Play-mode check moved to HW.5, for future assessment.)
- **Verification so far (2026-11-01):** Unity EditMode tests 57 pass (9 new; the 4 old coach-framing tests were replaced). Agent play-test in the Editor with simulated input and the offline cached program (saved game data restored afterwards): tutorial steps advance with no attempts recorded; standing arm, seated knee, standing behind-body leg with the mirror, lying and side-lying exercises; coach window and word guide; coach back in the room on the summary; no console errors. Found and fixed during the play-test: looking right along a sideways arm showed only its end (the view's turn is now limited), lying views ran along the limb (the view is lifted), the word guide hid the arrow. Lying and side-lying remain the hardest views to read, because the leg runs away from the eye. Not tested: anything in a headset (HW.2), and real webcam input with this view (HW.3).
- **Dependencies:** M5.4, M5.6
- **Systems:** VRClinicExperience, AvatarCoach, SessionOrchestration

### M5.9 — Tracking Reliability & Loss Safeguards
- **Status:** done
- **Objective:** Keep tracking steady and honest when joints are hidden or the detector glitches, so an estimated position is never taken for a detected movement (requested by the human 2026-11-01; DEC-022).
- **Deliverables:** per-landmark history and trust states; One Euro smoothing of verified landmarks; Kalman prediction for short gaps with a time limit; use of MediaPipe visibility and presence; rejection of implausible jumps; reacquisition with reset history and a forced fresh detection when a pose can't be tracked; rep counting paused while the exercise's joint is unverified, resuming on recovery, and an unjudgeable rep dropped; a "Move back into view" prompt; the live limb in orange while it is only an estimate; estimates marked in the tracker preview; tests.
- **Completion criteria:** tracker and Unity EditMode tests pass. (Amended 2026-11-01 by the human: the real webcam testing moved to HW.3, for future assessment.)
- **Verification so far (2026-11-01):** tracker tests pass (32 new in `test_tracking.py`, existing `test_angles.py` unchanged and passing; the first live webcam run showed the forced fresh detection firing for a person with legs out of frame, so it now needs no joint verified at all); Unity EditMode tests 66 pass (9 new). The real MediaPipe lite model was run on a screenshot of the coach with blank frames as a simulated person leaving: it reports presence, the pose went tracking, degraded, lost, reacquiring, tracking, and no angle was measured during the gap. End to end in Play mode with UDP packets: counting paused, the prompt showed, the limb used the estimate while the scored angle stayed at the last measured value, and counting resumed. Not tested, moved to HW.3: exercising in front of the real webcam; the thresholds are untuned starting values.
- **Dependencies:** M4.4, M5.8
- **Systems:** MotionTracking, ExerciseEvaluation, SessionOrchestration

## M6 — Camera Tracking Mechanics

- **Status:** done
- **Objective:** Make the single-webcam tracking more complete and better tested without needing a headset (requested by the human 2026-11-05): repeatable offline testing from recorded landmarks, readings for extension exercises when the facing direction is unclear, a camera setup check before counting, a live limb that shows out-of-plane movement, ankle exercises, and real-webcam tuning of the M5.9 safeguards.
- **Success criteria:**
  - A recorded session can be replayed through the tracker and gives the same packets every time.
  - Side-view shoulder and hip extension have a signed reading in at least ~95% of frames on real recordings, with the right sign facing both ways.
  - The patient is told, before counting, when the camera view, distance or framing is wrong for the exercise.
  - The live limb shows movement out of the exercise's plane; scoring is unchanged (DEC-023).
  - Ankle exercises are tracked and in the library (TASK-012).
  - The tracking safeguards pass a real-person webcam test and their thresholds are tuned.
- **Children:** `M6.1` Landmark Record & Replay Harness; `M6.2` Facing Direction & Extension Readings; `M6.3` Camera Setup Assistant; `M6.4` Out-of-Plane Live Limb & Ankle Exercises; `M6.5` Webcam Field Test & Tuning.
- **Done when:** all children are done.
- **Dependencies:** M5.9
- **Systems:** MotionTracking, ExerciseEvaluation, VRClinicExperience

### M6.1 — Landmark Record & Replay Harness
- **Status:** done
- **Objective:** Record the tracker's raw landmarks (never video, DEC-024) so tuning and checks can be repeated offline from one session with a real person.
- **Deliverables:** `tracker.py --record <file>` writes one JSON line per frame (timestamp, 2D landmarks with visibility and presence, 3D world landmarks); `--replay <file>` sends a recording through the same tracking and measuring code to UDP, in real time or `--fast`; recordings kept in a git-ignored `tracker/recordings/` folder; `tracker/report.py` summarises a recording (share of time in each tracking state, share of frames with no signed angle per side, pauses, jump rejections); tests.
- **Completion criteria:** tracker tests pass; a recording replays to identical packets on every run; a synthetic recording works end to end (amended 2026-11-05: `--fake` sends angles, not landmarks, so the end-to-end check uses `recording.synthetic`).
- **Verification (2026-11-05):** tracker tests 71 pass (9 new in `test_replay.py`: identical replays, replay equals the live loop, landmarks-only files, camera-lost event, real-time pacing, bad file refused, date-only file names, report counts). `tracker.py --replay --fast` sent all 360 packets of a synthetic recording to a UDP listener, and `report.py` summarised it. The real MediaPipe result was checked to carry the 2D and world landmark fields the recorder saves (x, y, z, visibility, presence). Not yet done: a recording of a real person (the first one is part of M6.5, or earlier as input for M6.2).
- **Dependencies:** M5.9
- **Systems:** MotionTracking

### M6.2 — Facing Direction & Extension Readings
- **Status:** done
- **Objective:** Give shoulder and hip extension a reading when the face can't be seen, by telling which way the patient faces from MediaPipe's 3D world landmarks (DEC-023).
- **Deliverables:** facing direction from the world landmarks first, the current nose/ear test as fallback, and a short, time-limited hold of the last known direction; packet fields only added (e.g. the facing source), -999 still sent when nothing is known; tests.
- **Completion criteria:** tracker tests pass; on real recordings the share of side-view frames with no signed angle is under ~5%, and flexion reads positive and extension negative facing both ways.
- **Amended 2026-11-07 by the human (slim M6.2, DEC-025):** the recordings showed the facing direction is not the problem, so the world-landmark facing test, the nose fallback and the facing hold were not built (the signed angle needs the shoulder-hip trunk line anyway, so no facing test can help when the hips are hidden). Instead the knee re-trust delay was tuned: `REACQUIRE_FRAMES` 3 -> 2. The human accepted closing M6.2 with the hip above the ~5% target; the remaining hip gap (MediaPipe's low knee confidence) moves to M6.5.
- **Findings so far (2026-11-06, real recording on the laptop webcam, 126 s, 37 fps):** shoulder: in truly side-on frames (shoulder width under 8% of the image) the current nose/ear test leaves only 2.4% with no signed angle; the 13.2% overall comes from frames where the patient faces or turns toward the camera. Flexion read up to about +88° and extension to about -60° facing both ways. A nose-ahead-of-the-shoulders test (2D or world) is undecided in only 0.2-1.1% of side-on frames and needs no hip. Hip: not measurable, because knees and ankles were in frame in only 11-14% of frames (camera framing). Camera fixes made for this (tracker.py): capture on its own thread, detection on a 640-px copy, the fastest backend chosen per camera (camera 0 gave 13 fps through DirectShow and 60 through Media Foundation), Media Foundation hardware transforms off (opening fell from ~30 s to ~2 s).
- **Findings (2026-11-06, second real recording, whole body side-on, 138 s, 39 fps, 95% tracking):** shoulder signed angle missing in 3.1% of all frames; hip in 8.3% overall and 9.2% of side-on frames, with sane values (about -24° extension to +75° flexion). Of the 161 side-on frames without a hip reading, 158 are the knee (or hip) not verified and only 3 are an unknown facing direction: half of those knee frames are confident detections still waiting the 3 frames of `REACQUIRE_FRAMES`, the rest are MediaPipe confidence 0.2-0.5. So the hip target depends on knee tracking (tuning in M6.5), not on facing. A separate hip-only recording with the legs half out of frame (ankles in frame 33%) gave wild hip values (±180°) and 4,858 rejected jumps: legs cut off by the frame give unusable hip angles, which M6.3 must catch.
- **Result (2026-11-07):** with `REACQUIRE_FRAMES` 2, on the whole-body recording: shoulder signed angle missing in 3.0% of frames (met), hip in 7.2% overall and 7.1% side-on (was 9.2%; above the ~5% target, accepted), 95.4% tracking; signs correct facing both ways. On the cut-off-legs recording this lets about 26% more implausible hip angles (over 120 degrees) through than 3 frames did (96 vs 76 of about 2,900 readings); they come from leg mis-detections, mostly with knee and ankle in frame. Also tried: re-trust after 1 frame (hip 4.5%, 132 implausible) and confidence 0.4 (hip 4.8-5.1%, 91-106 implausible), rejected as weakening DEC-022. Tracker tests 77 pass. Camera fixes in `tracker.py`, made while recording: capture on its own thread, detection on a 640-px copy, the fastest camera backend chosen by measured frame rate, Media Foundation hardware transforms off. Note: recordings hold no images (DEC-024), so a different pose model (e.g. `full`) can only be compared live, not on a recording.
- **Dependencies:** M6.1
- **Systems:** MotionTracking, ExerciseEvaluation

### M6.3 — Camera Setup Assistant
- **Status:** done
- **Objective:** Check the camera placement for each exercise before counting starts, instead of only telling the patient where to put the camera.
- **Deliverables:** tracker setup checks sent in the packet: the joints the exercise needs are inside the frame with a margin, the body's size in frame (distance), front or side view as the exercise needs, enough landmark confidence (lighting); a short setup step in Unity after get-ready (icons and one line, green when every check passes, skippable); Unity reads `trackingState`; tests.
- **Completion criteria:** tracker and Unity EditMode tests pass; in Play mode, replayed packets show each failed check's message and the step passes when the checks pass.
- **Verification (2026-11-07):** tracker tests 84 pass (7 new setup tests); Unity EditMode tests 73 pass (7 new `CameraSetupTests`, batch mode). Thresholds set from the M6.2 recordings: side view below 0.35 shoulder width / torso length, front above 0.55; too close above 0.42 torso / image height (the whole-body recording sat at about 0.47, with the ankles below the image), too far below 0.12; poor light below 0.6 median confidence. Distance is checked only standing or seated. In Play mode (offline cached program, webcam source, get-ready card of the heel slide) real UDP packets gave each message: set up, whole leg not in view, wrong view, poor light, nobody in view; the real recording replayed with `tracker.py --replay` gave "Step back so your whole leg is in view" for the heel slide and "Step back a little from the camera" for a standing shoulder exercise. No console errors. With the Editor unfocused its player loop stalls, so the get-ready card itself showed "The camera isn't running" (packets older than 1 s count as not receiving); the messages were read from the same check on the received packets. Saved game data restored afterwards. Not tested: a live person adjusting to the messages (M6.5).
- **Dependencies:** M6.2
- **Systems:** MotionTracking, VRClinicExperience, SessionOrchestration

### M6.4 — Out-of-Plane Live Limb & Ankle Exercises
- **Status:** done
- **Objective:** Let the live limb show movement that leaves the exercise's plane, keeping the default body and height (amends DEC-021, see DEC-023), and track the ankle (TASK-012).
- **Deliverables:** a display-only out-of-plane angle from the world landmarks, used by the first-person live limb (target limb and scoring unchanged); an ankle angle from the knee, ankle and foot landmarks; ankle exercises in `LIBRARY` (e.g. seated dorsiflexion/plantarflexion, standing heel raise) with Unity pose geometry; the ankle ORIF and ankle sprain protocols use them (targets are placeholders until TASK-007); tests.
- **Completion criteria:** server, tracker and Unity EditMode tests pass; the new exercises and the out-of-plane limb work in Play mode with replayed or simulated input.
- **Result (2026-11-07):** Tracker: `ankleDF` / `anklePF` in `angles.py` measure the shin (ankle to knee) against the heel-to-toes line (landmarks 29-32), 0 at a right angle; a 4-landmark `JOINTS` entry, so per-side angles, best side and the setup framing checks cover it. The packet adds `dirL` / `dirR`: unit directions of the upper arm and thigh in the body frame (+x patient's right, +y up, +z forward) from the world landmarks, sent only from verified landmarks, display only. Server: `anklePump` (lying, toes up, `ankleDF`, target 15, safety 20), `seatedHeelRaise` and `heelRaise` (`anklePF`, target 30, safety 45/50) with poses and normal ROM (dorsiflexion 0-20°, plantarflexion 0-50°); ankle ORIF phases I-III and lateral ankle sprain phases II-III use them (phase I of the ORIF only lying, as its precautions say); `PROTOCOL_VERSION` 4. Targets are placeholders (TASK-007). Unity: ankle fields in the packet models, the foot turns in `FirstPersonMath.Limbs`, the coach (`HumanoidCoach`) and the old figure, the view frames the foot, the setup line says "foot". The live limb leans out of the exercise's plane for one limb swinging from the shoulder or hip (`FirstPersonMath.OutOfPlane` / `Tilt`, from `MotionInput.DisplayTilt`), with a dead zone of 15° for arms and 8° for legs and a 35° cap; the target limb and scoring never use it (DEC-023).
- **Verification (2026-11-07):** tracker tests 94 pass (10 new: ankle angles, limb directions facing the camera and side-on, directions only with world landmarks); server tests 68 pass (1 new; it caught the ankle pump's safety max above normal dorsiflexion, fixed to 20); Unity EditMode tests 79 pass (6 new `AnkleAndTiltTests`). On the real whole-body side-on recording, side-view frames read arms about 20° out of the plane while hanging (median; they hang outside the hips) and legs about 4°, which set the dead zones; ankles had a reading in only 394 of 5,392 frames there (feet mostly below the image), and standing read about 14° of plantarflexion (median), so the ankle's neutral needs checking live. In Play mode, guides built for the heel raise, ankle pump, seated heel raise and a shoulder flexion with and without a 30° lean rendered as expected, with no console errors. Not tested: the coach's ankle motion on screen, and a real person (M6.5).
- **Dependencies:** M6.2
- **Systems:** MotionTracking, ExerciseEvaluation, VRClinicExperience

### M6.5 — Webcam Field Test & Tuning
- **Status:** done
- **Objective:** Test the tracking with a real person in front of the laptop webcam, without a headset, and tune it (the no-headset webcam parts of HW.3, moved here 2026-11-05).
- **Deliverables:** one guided recording session by the human (normal reps per posture, a joint hidden for about a second, stepping out for over 2 s, facing both ways, webcam unplugged and reconnected); thresholds in `tracker/tracking.py` and the setup checks tuned from the replayed recordings; one final live run; findings recorded.
- **Added 2026-11-07 (from M6.2):** knee tracking for hip readings: the hip signed angle was still missing in ~7% of side-on frames, mostly MediaPipe knee confidence 0.2-0.5; try the `full` model live and decide whether the hip can reach ~5% without letting implausible angles through. Also look at implausible hip angles (over 120 degrees) from leg mis-detections.
- **Added 2026-11-07 (from M6.4):** the ankle's neutral reading (a standing recording read about 14° plantarflexion; feet must be fully in frame), the out-of-plane dead zones (15° arms, 8° legs) and cap, and a look at the coach's ankle motion.
- **Completion criteria:** with a real person, normal reps give no false pauses, rejected movement or lag; a hidden joint pauses counting with "Move back into view" and an orange limb and then resumes; stepping out over 2 s drops the rep; movement made while hidden never counts; the webcam reconnects; side-view frames with no signed angle are under ~5%; the human confirms.
- **Findings (2026-11-09, guided recording `m6-5-lite.jsonl`, lite model, 718 s, 20,407 frames):** side-view signed angle missing in 0.3% of frames (shoulder) and 0.7% (hip), under the ~5% target, so the full model was not needed (the human skipped the full-model recording). The view thresholds (0.35 / 0.55) sit in the gap of the shoulder/torso histogram and stay. The ankle reads about 3° standing with the feet framed (the earlier 14° came from feet out of frame). Hanging arms read 17° out of plane (90th percentile 20°), legs 5° (12°), so the dead zones became 20° / 12°. Hip readings over 120° occur only seated. Heel raise peaks: 20-32° one way, 15-16° the other, 19-29° seated (the human kept the 30° ±10° target). With nobody in view the tracker drops to about 8 fps (harmless).
- **Result (2026-11-12):** Tracker: One Euro 1.0 / 1.5 (standing-knee jitter 95th percentile 13.7° -> 8.7°). Side selection (DEC-026): side-on the limb nearer the camera (world-landmark depth, set at 0.08 m, cleared under 0.03 m), unless the far limb reads more than 35° above it (kept while 15° above); facing the camera the larger reading; otherwise the current side unless the other is seen better by 0.15 (knee flips on the recording 62 -> 0). Unity: reps under 0.35 s are noise, under 0.6 s too fast; after a gap drops a rep the limb must come down before a new one; every webcam exercise first measures the patient's resting angle (still for 1 s, at most 60% of the target and 25°) and scores movement above it; side-on, a one-limb exercise measures whichever limb reads the larger angle (the tracker swaps left and right when the legs overlap); a fall of over 25° in one frame is held up to 0.3 s; live limb display smoothing 0.06 s; the hamstring curl's foot stays at a right angle to the shin (guide and coach). Server: the hamstring curl's thigh check is 30° (a normal curl swings the thigh about 28° back). P-001's program was changed for standing and seated testing (heel slide and side-lying hip abduction off, hamstring curl and standing hip abduction on, knee extension target 50 ±10; database backed up first).
- **Verification (2026-11-12):** tracker tests 96 pass, server tests 68 pass, Unity EditMode tests 86 pass. Replays of the recording: knee side flips 62 -> 0, far-leg curls read 89-96° instead of about 10°. Several live runs with the human at the laptop webcam, each problem fixed and run again; the human confirmed the final run ("All working") and closed M6.5. Hidden joint, stepping out and the webcam unplug were part of the guided recording and the live checklist; they were not rechecked one by one after the last tuning.
- **Dependencies:** M6.1, M6.2, M6.3 (M6.4 for the ankle exercises)
- **Systems:** MotionTracking, ExerciseEvaluation

## M7 — Pre-Study Data Readiness

- **Status:** done (2026-11-12)
- **Objective:** Make the clinical data trustworthy and safe before real study data is collected (approved by the human 2026-11-12; from backlog TASK-003..TASK-006): only real webcam sessions drive clinical rules, patient identity follows one clear decision (DEC-027), the database has an encrypted backup that can be restored, and the Unity data folder name is final.
- **Success criteria:**
  - Keyboard, simulated and unknown-source sessions stay on record and are labelled, but never change adherence, streaks, phase readiness, attention flags, rep progression, XP or badges.
  - The patient's name appears only in the therapist dashboard; exports, VR routes, logs and recordings carry the code only (DEC-027).
  - An encrypted backup can be made while the server runs and restored to a new file that passes an integrity check.
  - Unity `companyName` is `TheraQuest`.
- **Children:** `M7.1` Only Webcam Sessions Count; `M7.2` Patient Name and Code; `M7.3` Encrypted Backup and Restore; `M7.4` Unity Company Name.
- **Plan:** `docs/superpowers/plans/2026-11-12-m7-pre-study-data-readiness.md` (repository root). Suggested order M7.4 → M7.1 → M7.2 → M7.3; M7.1 and M7.2 both edit `server.py` and `dashboard.html`, so not in parallel.
- **Done when:** all children are done.
- **Dependencies:** M4, M5
- **Systems:** ClinicalBackend, TherapistDashboard, SessionOrchestration, Gamification, VRClinicExperience

### M7.1 — Only Webcam Sessions Count
- **Status:** done (2026-11-12). Counted sources are `COUNTED_SOURCES` in `server.py`; the dashboard KPIs and per-exercise table also use only counted sessions. Live database check: it holds 5 simulated sessions (all P-001), not 6; they no longer affect adherence, readiness or flags. Past XP and badges are unchanged (not retroactive).
- **Objective:** Keep non-webcam sessions out of every clinical and game rule (TASK-003; the human chose "exclude from all rules" on 2026-11-12).
- **Deliverables:** one list of counted input sources (`webcam` only) used by `day_statuses` (adherence, streak), `readiness`, `attention_flags`, the session upload (XP, badges, Progression Controller) and `vr_progress` totals; the upload response says when a session was not counted; an input-source tag per row in the dashboard Session History; one short line in the Unity session summary for a non-webcam session ("Practice: not counted"); tests.
- **Completion criteria:** server and Unity EditMode tests pass, with new tests for each rule above, unknown-source uploads and idempotent re-upload; the live database's simulated sessions no longer change adherence, readiness or flags. XP and badges already earned from past simulated sessions are left as they are (not retroactive).
- **Dependencies:** none
- **Systems:** ClinicalBackend, TherapistDashboard, SessionOrchestration, Gamification

### M7.2 — Patient Name and Code
- **Status:** done (2026-11-12). The telemetry export lost its `patient_name` column; `get_program(for_vr=True)` drops the name for the VR program and upload responses; name must be text of at most 200 characters on add and edit.
- **Objective:** Keep the patient's real name with their code, used only inside the therapist dashboard (TASK-004, DEC-027).
- **Deliverables:** `name` removed from VR client payloads (`vr_progress`, prescription fetch) and the unused Unity `DataModels` field; exports and evaluation reports checked to hold the code only; server-side name validation (type, length); dashboard label "Patient full name (dashboard only)"; `schema.sql` comment updated; tests.
- **Completion criteria:** server and Unity EditMode tests pass, with tests that exports and VR routes never contain a name.
- **Dependencies:** M7.1 (same files)
- **Systems:** ClinicalBackend, TherapistDashboard, SessionOrchestration

### M7.3 — Encrypted Backup and Restore
- **Status:** done (2026-11-12): code and 11 automated tests, plus a real backup and restore checked by the human.
- **Objective:** A password-encrypted backup of the clinical database to a drive the clinic controls, and a safe restore (TASK-005; the human chose an encrypted file on 2026-11-12).
- **Deliverables:** `server/backup.py` with `backup <folder>` (consistent snapshot through the SQLite backup API while the server runs, key from the password by Scrypt, authenticated encryption, a versioned header) and `restore <file> <out.db>` (decrypts to a new file only, runs an integrity check, never overwrites the live database); `cryptography` pinned in `server/requirements.txt` (used only by the backup tool); `Backup_Database.bat`; a README section (where to keep backups, that a lost password can't be recovered, how to restore); tests.
- **Completion criteria:** backup tests pass (round trip, wrong password, tampered file, header version, existing output refused, backup during an open write); one real backup and restore of the live database on this PC.
- **Dependencies:** none
- **Systems:** ClinicalBackend

### M7.4 — Unity Company Name
- **Status:** done (2026-11-12): company name set, test and README note added; the game ran in Play mode on the new data folder and loaded the P-001 program. No old data was copied; the old offline queue file was gone by then.
- **Objective:** Set the final Unity company name before any clinic install, since the player's data folder is named after it (TASK-006).
- **Deliverables:** `companyName: TheraQuest`; this PC's player data (config.json, PIN, cached program, offline queue, checked empty first) copied by hand from `LocalLow\DefaultCompany\TheraQuestVR` to `LocalLow\TheraQuest\TheraQuestVR`; a README note; a check that the company name is not `DefaultCompany`.
- **Completion criteria:** Unity EditMode tests pass; the game starts with its saved settings and program on this PC.
- **Dependencies:** none
- **Systems:** VRClinicExperience

## M8 — Visual & UX Polish

- **Status:** active (started 2026-11-14)
- **Objective:** Make the game look and feel finished and the therapist app clearer at a glance, before the study and the hardware run (approved by the human 2026-11-14). The game moves to URP (DEC-028); the room, feedback, hologram and menus get a visual pass; the dashboard gets a visual refresh and shows data the server already sends.
- **Success criteria:**
  - The game renders with URP with no Built-in shaders, no pink materials and no frame-time loss against the Built-in baseline.
  - Room, hologram, coach window, feedback effects and menus are approved by the human from before and after screenshots or Play mode.
  - VR comfort rules hold: no motion blur, vignette, chromatic aberration, film grain, depth of field or camera shake; UI transitions 0.25 s or shorter that never move the view; red only for safety (DEC-016).
  - The dashboard shows a patient header, the 14-day adherence calendar, phase history and per-exercise stats (counted sessions only), keeps every M5.1 accessibility rule and fits 980 × 640.
  - Every new asset is chosen by the human, credited in `CREDITS.md` with its licence, and has a fallback when missing (DEC-015).
- **Children:** `M8.1` URP Migration; `M8.2` Clinic Room Look; `M8.3` Feedback Motion; `M8.4` Hologram & Coach Window; `M8.5` Menus & Summary Polish; `M8.6` Dashboard Visual Refresh; `M8.7` Dashboard Hidden Data.
- **Plan:** `docs/superpowers/plans/2026-11-14-m8-visual-and-ux-polish.md` (repository root; holds the per-child steps and tests). Game track M8.1 → M8.2 → M8.4 → M8.3 → M8.5; dashboard track M8.6 → M8.7. The two tracks share no files and may run in parallel sessions; within a track run one child at a time (M8.3 and M8.5 both edit `UIKit.cs`; M8.6 and M8.7 both edit `dashboard.html`).
- **Done when:** all children are done.
- **Dependencies:** M5, M7. No hardware needed; HW.2 later confirms URP in the headset.
- **Systems:** VRClinicExperience, AvatarCoach, Gamification, TherapistDashboard

### M8.1 — URP Migration
- **Status:** done
- **Objective:** Render the game with URP, looking at least as good as now (DEC-028).
- **Deliverables:** one URP pipeline asset and Forward renderer (MSAA 4x, HDR, soft shadows) assigned in Graphics and every Quality level; imported model materials converted; `Hologram.shader` ported to URP HLSL; `HumanoidCoach` uses the Little Guys URP material (no `Standard` swap); runtime materials made through one URP helper; OpenXR setup re-run under URP; EditMode tests.
- **Completion criteria:** EditMode tests that the URP asset is assigned everywhere, no material under `Assets/TheraQuest` or made at runtime uses a Built-in shader, and the hologram shader is supported; full `run_tests.py` green; Play mode (menu, get-ready, all four postures, summary, Progress page) has no pink or missing materials against before screenshots; frame time on this PC not worse than the Built-in baseline.
- **Dependencies:** none
- **Systems:** VRClinicExperience, AvatarCoach

### M8.2 — Clinic Room Look
- **Status:** done (2026-11-24, approved by the human). Frame time 4.16 ms in Editor Play mode vs the 4.32 ms M8.1 reference (budget 4.75 ms). Standing, seated and lying "after" screenshots taken (Assets/Screenshots/M8.2, the human folder); no "before" exists, it was never captured. Later polish asked by the human 2026-11-19 to 2026-11-23: coach 1.2 m back, panels 1.65 m away in the headset, smaller exercise area with a rug texture, arm hologram guide 1.5 in forward, one window design (UIKit.Window), Joint Angle logo and app icon, cartoon title with outline and shadow, round-ended strips, status bubble aligned and cream for every tone, return-phase guidance (Lowering state), wrapping menu subtitle. Not adopted: the gritty/flat look trial (smoother wall, brighter lights), which was never built in. Not done: the free-look test during an exercise; the human closed the milestone without it.
- **Objective:** A calm, bright clinic whose lighting draws the eye to the exercise spot and coach window.
- **Deliverables:** soft directional sunlight with soft shadows, warm lamps, ambient light and a reflection probe rendered after the runtime room build; floor, wall and ceiling textures chosen by the human (current colours as fallback); one Volume with neutral tonemapping, gentle grading, light bloom and SSAO; exercise spot and mat readable on the new floor.
- **Completion criteria:** human approves before and after screenshots from the standing, seated and lying viewpoints; frame time within 10% of M8.1; room builds with every texture missing; full suite green.
- **Dependencies:** M8.1
- **Systems:** VRClinicExperience

### M8.3 — Feedback Motion
- **Status:** active (started 2026-11-24, in parallel with M8.4 and M8.5 by the human request; the UIKit helper was committed first so M8.5 could go ahead)
- **Objective:** Make important moments feel responsive without hurting comfort.
- **Deliverables:** one `UIKit` panel fade/scale helper (0.15 to 0.25 s, unscaled time) used by menus, HUD cards, pop-ups, summary and Progress page; small effects for a good rep, hold progress and hold complete, combo pulse, level-up and badge reveal (assets chosen by the human, static fallback); STOP and posture faults keep their instant red warning with no celebration.
- **Completion criteria:** EditMode tests (transition limits and skip-to-end, no reward effect on STOP or unsafe reps, effects only for counted events) pass; full suite green; human checks each moment in Play mode.
- **Dependencies:** M8.1; not in parallel with M8.5 (`UIKit.cs`)
- **Systems:** VRClinicExperience, Gamification

### M8.4 — Hologram & Coach Window
- **Status:** planned
- **Objective:** The target limb, live limb and coach window are the clearest things in view.
- **Deliverables:** reworked URP hologram (fresnel rim, soft fill, alpha clip where possible, palette colours for target and live limb, steady glow inside tolerance); framed coach window with a soft backdrop and restyled arrows and word guides; same frame for the side mirror; documented shader parameters checked in the Frame Debugger.
- **Completion criteria:** EditMode tests (glow only when the evaluator reports in-tolerance; frames inside the comfortable field-of-view limits) pass; full suite green; human approves before and after screenshots for all four postures.
- **Dependencies:** M8.1
- **Systems:** VRClinicExperience, AvatarCoach

### M8.5 — Menus & Summary Polish
- **Status:** planned
- **Objective:** Consistent, tidy menus that stay short.
- **Deliverables:** named type-size and spacing scale in `UIKit` used by the main menu, Settings, Progress tabs and summary; one card and button style with distinct hover, focus and pressed states for mouse, keyboard and controller; clearer summary and Progress hierarchy with no added content; menu and HUD distances re-checked against the `VRClinicExperience` invariants.
- **Completion criteria:** EditMode tests (button state colours distinct; menu pages fit at the smallest text preset) pass; full suite green; human Play-mode check of every menu page and the summary.
- **Dependencies:** M8.3 (`UIKit.cs`)
- **Systems:** VRClinicExperience, Gamification

### M8.6 — Dashboard Visual Refresh
- **Status:** done (2026-11-24, approved by the human). New theme (left sidebar, slim top bar, greeting and key-numbers strip, neutral greys) approved from before/after screenshots on 2026-11-19; Backup and Protocol library dialogs rebuilt, themed picker panels in Create protocol; clinician sign-up form. Browser check at 1440x900, 980x640 and 600x800 passed; server tests 106 pass; exe rebuilt. Commits dca99a9, 0122d06, 9556728, 7545a6c; a4f21aa stops the app reusing a server on port 8000 that uses another database file (found during the walkthrough).
- **Objective:** The therapist sees what matters for a patient at a glance.
- **Deliverables:** type and spacing scale in the `:root` tokens; one button, card and table style; patient chart header (code, name, protocol and phase, adherence, last session, flags); caseload table polish (flag chips, hover and focus, sticky header); Chart.js styled from tokens; before and after screenshots on a throwaway database.
- **Completion criteria:** server tests pass; browser check at 980 × 640 and full size (no horizontal scroll, no console errors, keyboard use and dialogs as in M5.1); therapist exe rebuilt; human walkthrough in the desktop app.
- **Dependencies:** none
- **Systems:** TherapistDashboard

### M8.7 — Dashboard Hidden Data
- **Status:** planned
- **Objective:** Show the data the server already sends but the page hides.
- **Deliverables:** 14-day adherence calendar on the Activity tab (status by text or icon, not colour alone); phase history timeline; per-exercise stats table from counted sessions only (M7.1); empty, loading and error states; server tests only if the payload must change.
- **Completion criteria:** server tests pass; browser check on a throwaway database with a patient with no sessions, one with missed days and one with a phase change; exe rebuilt; human walkthrough in the desktop app.
- **Dependencies:** M8.6 (`dashboard.html`)
- **Systems:** TherapistDashboard

## M9 — Manuscript Finalization & Polish

- **Status:** active (started 2026-11-16)
- **Objective:** Make the existing capstone manuscript (Chapters 1 to 3 and its lists; working copy `Research/THERAQUEST- MANUSCRIPT.md`) read as finished and describe the system as it is actually built (approved by the human 2026-11-16). No new chapters. Section 3.9 Data Analysis and all results and metrics are out of scope. The master is the human's Google Doc / Word file, so every edit is also delivered as a change list (DEC-029).
- **Success criteria:**
  - `Research/M9-audit.md` has no open item except those the human chose to leave.
  - The human approved Chapters 1, 2 and 3 and the figure set.
  - Section 3.9 and the embedded image lines of the `.md` are byte-identical to the start.
  - A change list exists for every chapter so the master can be brought in line.
  - Research aims, objectives, benchmark targets, participants and instruments are changed only with the human's yes; no invented citations, numbers or results.
- **Children:** `M9.1` Manuscript Audit; `M9.2` Language and Flow Edit; `M9.3` Sync with the Built System; `M9.4` Figures and Screenshots.
- **Plan:** `docs/superpowers/plans/2026-11-16-m9-manuscript-finalization.md` (repository root; holds the rules, the first-read findings and the verification commands). Order M9.1 → M9.2 → M9.3 → M9.4; review by chapter; one chapter per session.
- **Done when:** all children are done.
- **Dependencies:** none to start. M9.4 game screenshots need the human's approval of the M8.2 look (otherwise they are provisional).
- **Systems:** none changed; all `brain/systems` files are read as the reference for M9.3.

### M9.1 — Manuscript Audit
- **Status:** done (2026-11-16: audit in `Research/M9-audit.md`, 138 items; the human answered D1 to D15; only the real dates for D3 are still to be supplied)
- **Objective:** List every place where the manuscript text, figures and tables disagree with the built system or have structure or language problems, before anything is edited.
- **Deliverables:** `Research/M9-audit.md` with one table per chapter (ID, section, quoted text, problem type, proposed action) and one list of open decisions for the human (tense of Chapter 3, the 2.3 numbering, title-page date and timeline, how much new system detail to add, which figures to redraw, keep or drop). The human first confirms that the 9 October `.md` still matches the master, or re-exports it.
- **Completion criteria:** the manuscript is not edited in this child; the human has read the audit and answered the open decisions.
- **Dependencies:** none
- **Systems:** none changed

### M9.2 — Language and Flow Edit
- **Status:** done (2026-11-17: Chapters 1, 2 and 3 approved and committed, one commit each; change lists in `Research/M9-changes-chapter-N.md`; system wording left in Part D of each list for M9.3)
- **Objective:** Chapters 1, 2 and 3 read cleanly and consistently without any change of meaning.
- **Deliverables:** per chapter: grammar, clarity, consistent terms (1.6 Definition of Terms is the reference), consistent tense as decided in M9.1, headings and numbering repaired, captions and contents entries matched to the lists; `Research/M9-changes-chapter-N.md` (section, original text, new text, reason). Chapter 3 skips 3.9. Chapter 2 claims about other systems get a language edit only.
- **Completion criteria:** hash checks for Section 3.9 and the image lines unchanged; no empty headings and numbering in order; the human approves each chapter; one commit per approved chapter.
- **Dependencies:** M9.1
- **Systems:** none changed

### M9.3 — Sync with the Built System
- **Status:** active (paused by the human 2026-11-17 while M10 runs; nothing edited yet)
- **Objective:** The manuscript describes the system that exists.
- **Deliverables:** every system-mismatch item from the audit resolved in 1.1, 1.3, 1.5, 1.6, 3.2 to 3.7 and 3.10 (single external webcam and 2D angles, tethered Quest Link with desktop fallback, MediaPipe Pose and OpenCV, SQLite, therapist desktop app, first-person view, patient code and name rule, encrypted backup, actual timeline), each checked against [[00_PROJECT]], [[30_DECISIONS]], the systems files and the code, and appended to the chapter change list with its source.
- **Completion criteria:** every system-mismatch item is closed or marked kept by the human; items that change a research claim were applied only after the human's yes; hash checks unchanged; the human approves.
- **Dependencies:** M9.2 (same file)
- **Systems:** none changed

### M9.4 — Figures and Screenshots
- **Status:** planned
- **Objective:** Figures, tables and their lists match the text and the built system.
- **Deliverables:** for each figure the audit marks as not matching, a corrected version built from the real system saved in `Research/Figures/figures/` beside the old one for the human to keep or replace; screenshots only where the human wants them (throwaway database, patient codes only, DEC-027); captions, List of Figures and List of Tables updated; a placement list (figure number, caption, after which paragraph) for the master. The base64 image lines in the `.md` are not regenerated.
- **Completion criteria:** every figure and table label in the body matches its list entry and the reverse; the human approves the figure set.
- **Dependencies:** M9.3; M8.2 approval for final game screenshots
- **Systems:** none changed

## M10 — XR Environment & VR Integration

- **Status:** active (started 2026-11-17; the human has a Meta Quest available)
- **Objective:** Move the game's VR side from hand-written `UnityEngine.XR` device reads to a standard Unity XR setup built on the XR Interaction Toolkit (DEC-030): one XR Origin rig, controller input through input actions, ray-pointed menus, toolkit locomotion and headset-ready panels, with the desktop mode still working when no headset is present.
- **Scope chosen by the human (2026-11-17):** controllers and the XRI rig. No hand tracking (it stays in [[VRClinicExperience]] Future Changes). Not built or tested on the XR Device Simulator alone: work starts when a Meta Quest is available.
- **Success criteria:**
  - The game runs in the headset over Quest Link on the XR Origin rig, and in desktop mode with Link off, from the same scene and build (DEC-002).
  - Every menu and in-session action can be done with the Quest controllers by pointing and pressing; keyboard and mouse still work on the laptop.
  - The comfort invariants in [[VRClinicExperience]] hold: the game never moves or turns the headset view on its own; only the instant re-center does.
  - First-person exercise view, default heights, HUD, coach window and subtitles (DEC-021) behave as before on the new rig.
  - All EditMode tests pass; the headset frame rate stays comfortable under URP (DEC-028).
- **Children:** `M10.1` XR Origin Rig & Quest Link Lifecycle; `M10.2` Controller Input & Ray Menus; `M10.3` Comfort Locomotion in the Rig; `M10.4` Headset Panels & Rendering.
- **Done when:** all children are done and the human has run a session in the headset on the new rig.
- **Dependencies:** access to a Meta Quest headset and a VR-ready PC; HW.1 (Link installed and set as the OpenXR runtime). HW.2 tests the result of M10. M8.4 and M8.5 touch the same panels: do not run them in a parallel session with M10.4.
- **Note:** the human's uncommitted changes already add `com.unity.xr.interaction.toolkit` 3.6.1, `com.unity.xr.hands` 1.9.0, `com.unity.xr.compositionlayers` 2.6.1, XR Management 4.7.0, `Assets/XRI/` and changed OpenXR settings (seen 2026-11-17). The human chose to commit them as they are (7bf9360, 2026-11-17). XR Hands and Composition Layers stay unused until M10.4 decides on Composition Layers.

### M10.1 — XR Origin Rig & Quest Link Lifecycle
- **Status:** done (2026-11-23: the human passed all five headset checks on a Quest 2 over Link; fixes in 209766b)
- **Objective:** One camera rig that works in the headset and on the laptop, and a clean start, stop and loss of the Link connection.
- **Deliverables:** the package set agreed and committed (XR Hands removed unless the human wants it kept); an XR Origin (floor tracking origin) built by `TheraQuestSceneBuilder` and used by `HeadTracking`, `FirstPersonGuide` and `PlayerMover` in place of the current rig; instant re-center and the per-posture default height kept; `TheraQuest → Set Up OpenXR` updated for the new packages; start with Link on, start with Link off, headset taken off (session pauses) and Link lost mid-session (falls back to desktop without losing the session); EditMode tests for the rig set-up and the fallback choice.
- **Completion criteria:** the game starts in both modes from one build; re-center and default heights give the same view as before; the existing EditMode suite passes; the human sees the room in the headset.
- **Dependencies:** HW.1; the human's answer on the uncommitted package changes
- **Systems:** VRClinicExperience, SessionOrchestration

### M10.2 — Controller Input & Ray Menus
- **Status:** done (2026-11-23: the human checked controllers only and keyboard and mouse only on a Quest 2 over Link; f9fa740)
- **Note (2026-11-19, human request):** thumbsticks no longer walk; walking is keyboard only, in the headset too. Sticks turn and drive menus only, and only with a thumb on them.
- **Objective:** Controllers drive the game through input actions, and menus are used by pointing at them.
- **Deliverables:** an input actions asset (XRI defaults where they fit) read through `InputHelper`, replacing the direct `UnityEngine.XR` device reads; the current mapping kept (A select, B pause, Y re-center, thumbsticks for menus, walking and turning); a controller ray with the XR UI input module on the world-space menus, pause menu, settings and summary screens; visible controller models or pointers; keyboard and mouse unchanged; EditMode tests for the action mapping.
- **Completion criteria:** main menu, settings, pause, summary and Progress page can each be completed with controllers only and with keyboard and mouse only; no script reads XR devices directly any more.
- **Dependencies:** M10.1
- **Systems:** VRClinicExperience, SessionOrchestration

### M10.3 — Comfort Locomotion in the Rig
- **Status:** active (next up; M10.2 done 2026-11-23)
- **Objective:** Walking and turning use the toolkit's locomotion on the XR Origin and keep the comfort rules.
- **Deliverables:** snap turn (30°), optional smooth turn and thumbstick walking through XRI locomotion providers, with the room boundaries of `PlayerMover`; locomotion locked during exercises; re-center to the exercise spot; settings (snap or smooth) still saved in `GameSettings`; tests for the exercise lock and the boundaries.
- **Completion criteria:** the invariants in [[VRClinicExperience]] hold in the headset (no view movement the patient did not ask for); the patient cannot leave the room or move during an exercise.
- **Dependencies:** M10.1, M10.2
- **Systems:** VRClinicExperience

### M10.4 — Headset Panels & Rendering
- **Status:** planned
- **Objective:** Everything the patient reads is sharp, comfortable and in the right place in the headset.
- **Deliverables:** HUD, floating menus, coach window, subtitles and the lying-posture panel positions checked and corrected on the new rig; text sharpness in the headset (composition layers only if plain world-space panels are not sharp enough; otherwise the package is removed); URP settings checked in stereo (MSAA, SSAO, bloom, shadows) against the comfort ban list of DEC-028; headset frame time measured for a full session.
- **Completion criteria:** the human can read every panel standing, seated and lying without strain; the headset frame rate stays at the Link refresh rate through a session, or the cost is recorded with the setting that was lowered.
- **Dependencies:** M10.1; M8.2 approval (room look); not in parallel with M8.4 or M8.5
- **Systems:** VRClinicExperience, AvatarCoach

## HW — Hardware Integration & Field Validation (unscheduled)

- **Status:** planned (unscheduled: not yet numbered or placed in the sequence)
- **Objective:** Bring together the real hardware the project needs (Meta Quest headset over Quest Link, a VR-ready Windows PC, a clinic webcam) and test how well the whole system works on it: VR client, motion tracker, clinical server and therapist dashboard running together on one machine, as a patient and therapist would use them.
- **Success criteria:**
  - The VR client runs in the headset over Quest Link (OpenXR) with head tracking and controller input, and falls back to desktop mode when Link is off (DEC-002).
  - Tracker, VR client and server run together on the target PC without dropping below a comfortable headset frame rate or the tracker's working rate (~30 FPS).
  - A full session done in the headset with the webcam tracker reaches the dashboard with correct per-rep data.
  - Every hardware problem found is fixed, or recorded with a workaround, in the brain.
- **Children:**
  - `HW.1`: Hardware Setup & Compatibility Baseline
  - `HW.2`: Headset Integration Test
  - `HW.3`: Webcam and Headset Concurrent Operation
  - `HW.4`: End-to-End Integration Run
  - `HW.5`: First-Person View Assessment
- **Done when:** all children are done; the findings and the clinic setup steps are recorded.
- **Dependencies:** M4 (software foundation); access to the hardware.

### HW.1 — Hardware Setup & Compatibility Baseline
- **Status:** planned
- **Objective:** Get the hardware working with the software stack and record what a clinic machine needs.
- **Deliverables:** Meta Quest Link app installed and set as the active OpenXR runtime; headset connection by cable and/or Air Link; webcam chosen and mounted (USB on a tripod preferred); a clinic setup checklist covering PC/GPU, cable, camera placement, 2 x 2 m space and lighting (README).
- **Completion criteria:** the built player and the Editor both start in the headset; the tracker sees the webcam; the checklist is written from the real setup.
- **Dependencies:** M4
- **Systems:** VRClinicExperience, MotionTracking

### HW.2 — Headset Integration Test
- **Status:** planned
- **Objective:** Verify the VR client on the real headset (moved here from M4.3's completion criteria on 2026-10-25).
- **Deliverables:** test run covering head tracking and recentering (Y / R), controller mapping (A select, B pause, thumbsticks for menus, walking and turning), locomotion locked during exercises, HUD and menu legibility and comfort at the configured distances, subtitles, pause and quit in the headset, and the desktop fallback with Link off; the first-person view (M5.8): default height calibration standing, seated and lying, the limbs lining up with where the patient feels their body, and the panels' position when lying; fixes for problems found.
- **Completion criteria:** every item passes in the headset, or has a recorded fix or workaround; a session done in the headset uploads to the dashboard.
- **Dependencies:** HW.1; M10 (the test runs on the M10 rig and input, added 2026-11-17)
- **Systems:** VRClinicExperience, SessionOrchestration

### HW.3 — Webcam and Headset Concurrent Operation
- **Status:** planned
- **Objective:** Check that tracking and VR rendering can share one PC, and that tracking works for a patient wearing a headset.
- **Note (2026-11-05):** the parts below that need no headset (signed-angle footage check with the headset off, live webcam reconnect, real-webcam safeguard tests and threshold tuning) are done in M6.5; what stays here is repeating them with the headset on and the shared-PC load measurements.
- **Deliverables:** measurements of headset frame rate, tracker rate and CPU/GPU load with everything running; a real side-view footage check of the signed elevation angles with `tracker/check_signed.py` (moved here from M4.6 verification on 2026-10-25): shoulder and hip extension must read negative and flexion positive, facing both ways, with and without the headset, measuring the share of frames where the facing direction can't be told; tracker accuracy and visibility while the patient wears the headset (the headset can hide the face landmarks used to tell facing direction); front and side camera placement checked for each tracked exercise; live webcam unplug and reconnect test (open from M4.4); the first-person view driven by the real tracker (moved from M5.8 on 2026-11-01); real webcam testing of the tracking safeguards (moved from M5.9 on 2026-11-01): normal reps with no false pauses, rejected movement or lag; a joint hidden for about a second pauses counting with "Move back into view" and an orange limb, then resumes; stepping out mid-rep for over 2 s drops that rep; movement made while hidden never counts; the thresholds in `tracker/tracking.py` tuned from these results.
- **Completion criteria:** the headset frame rate and tracker rate stay usable during a full session; signed angles have the right sign and the facing direction is missing in under ~5% of frames (at ~20% or more, Unity keeps the last known direction across short gaps), with the headset on and off; posture checks work with the headset on, or a fix is made; camera placement guidance is confirmed or corrected; the tracking safeguards behave as listed above with a real person, or their thresholds are corrected.
- **Dependencies:** HW.1, HW.2
- **Systems:** MotionTracking, ExerciseEvaluation, VRClinicExperience

### HW.4 — End-to-End Integration Run
- **Status:** planned
- **Objective:** Run the complete clinical workflow on the real hardware.
- **Deliverables:** therapist prescribes on the dashboard; patient runs the session in the headset with webcam tracking; the session, adherence, per-rep log and clinical notes appear on the dashboard; offline mode and the upload queue tested on the real setup; a findings list with each problem fixed or recorded.
- **Completion criteria:** at least one complete prescribe → exercise → review cycle succeeds on the target hardware with no manual workarounds; findings are recorded in the brain.
- **Dependencies:** HW.2, HW.3
- **Systems:** SessionOrchestration, ClinicalBackend, TherapistDashboard, VRClinicExperience, MotionTracking

### HW.5 — First-Person View Assessment
- **Status:** planned
- **Objective:** Judge the first-person exercise view (M5.8, DEC-021) as a patient would, the check moved here from M5.8 on 2026-11-05 at the human's request.
- **Deliverables:** a play-through of a full session on the laptop (keyboard or simulated input is enough) and, once HW.2 and HW.3 are available, in the headset with the webcam: the tutorial reads well; the holographic limb can be seen and followed for an arm, a seated knee, and a lying or side-lying leg (the hardest views); the coach window, arrow and word guide are clear and uncluttered; the side mirror and reach chime work for a behind-the-body exercise (shoulder extension, hip extension, hamstring curl); fixes or recorded changes for what doesn't work.
- **Completion criteria:** the human has played a session and judged each item above, and each problem found is fixed or recorded in the brain.
- **Dependencies:** none for the laptop play-through; HW.2 and HW.3 for the headset and webcam parts
- **Systems:** VRClinicExperience, AvatarCoach, SessionOrchestration
