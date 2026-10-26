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
| M5 | — | active | Dashboard & Game Experience |
| M5.1 | M5 | TBF | Dashboard UX & Accessibility Polish |
| M5.2 | M5 | TBF | Patient & Protocol Management |
| M5.3 | M5 | TBF | Clinical Insights & Attention Flags |
| M5.4 | M5 | TBF | Session Flow Polish |
| M5.5 | M5 | TBF | Session Summary & Progress Screens |
| M5.6 | M5 | TBF | Audio & Visual Assets |
| M5.7 | M5 | TBF | Additional Built-in Clinical Protocols |
| HW | — | planned | Hardware Integration & Field Validation |
| HW.1 | HW | planned | Hardware Setup & Compatibility Baseline |
| HW.2 | HW | planned | Headset Integration Test |
| HW.3 | HW | planned | Webcam and Headset Concurrent Operation |
| HW.4 | HW | planned | End-to-End Integration Run |

---

## Suggested sequence

`M0` (done) ➔ `M1` (done: features & avatars) ➔ `M2` (done: analytics & evaluation) ➔ `M3` (done: security & hardening) ➔ `M4` (done: foundation hardening before new game & dashboard features) ➔ `M5` (active: dashboard & game experience)

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

- **Status:** active
- **Objective:** Make the therapist dashboard easier and safer to use, give therapists patient/protocol management and early warnings, and make the patient game more rewarding and polished. Scope chosen by the human on 2026-10-26; showing the unused dashboard data (TASK-001) and the high-priority backlog (TASK-003..TASK-006) are deliberately outside M5.
- **Success criteria:**
  - The dashboard app works fully by keyboard, fits its window from the minimum size up (DEC-013), and shows honest empty, loading and error states.
  - Therapists can edit and archive patients and edit protocol phases without losing clinical records.
  - The caseload flags patients who need attention, with the reasons and the input sources counted.
  - The game has clear pacing between exercises, a rewarding summary and a progress page (history, streak, level, badges).
  - Placeholder sounds, music, badge art and text rendering are replaced with licensed assets, with credits recorded.
- **Children:**
  - `M5.1`: Dashboard UX & Accessibility Polish (TBF)
  - `M5.2`: Patient & Protocol Management (TBF)
  - `M5.3`: Clinical Insights & Attention Flags (TBF)
  - `M5.4`: Session Flow Polish (TBF)
  - `M5.5`: Session Summary & Progress Screens (TBF)
  - `M5.6`: Audio & Visual Assets
  - `M5.7`: Additional Built-in Clinical Protocols (TBF; added by the human 2026-10-26)
- **Done when:** all children are done; the server, tracker, evaluation and Unity EditMode test suites pass; the human has done a dashboard walkthrough and a Play-mode walkthrough of the game (listed in `pending_human_tests` while open; the milestone is TBF until then).
- **Dependencies:** M4. The dashboard children (M5.1–M5.3) and the game children (M5.4–M5.6) don't depend on each other.

### M5.1 — Dashboard UX & Accessibility Polish
- **Status:** TBF
- **Verification so far (2026-10-26):** server tests pass (backend 30, authorization 13, including the new session-paging test). Browser check on a throwaway database: sign-in, caseload, chart and dialogs work by keyboard (Tab stays inside dialogs; Escape closes them and returns focus); no horizontal scroll at the app's minimum window size (980 × 640) on any view; empty states for a patient with no sessions; inline errors with Retry when the server stops; no console errors; no requests outside localhost. Left: the human walkthrough in the desktop app (`pending_human_tests`).
- **Objective:** Make the existing dashboard robust, accessible and consistent before adding features to it.
- **Deliverables:** empty, loading and inline error states (no fake "No Data" chart point; library/protocol load failures shown); keyboard-reachable navigation; dialogs that close on Escape, trap and restore focus, with labelled fields; tab roles on sub-tabs; status not shown by colour alone; layout that fits the app window from its minimum 980 × 640 up (DEC-013; the narrow-screen rules added also cover a small Edge fallback window); colours from CSS variables and no emoji in status text; unused Tailwind script removed; no `@latest` CDN fallback; session time shown, paging past 50 rows, duplicate CSV button removed.
- **Completion criteria:** the dashboard app is fully usable by keyboard and at its minimum window size; empty and error states are correct; the server test suites pass; human walkthrough in the desktop app.
- **Dependencies:** M4.2
- **Systems:** TherapistDashboard

### M5.2 — Patient & Protocol Management
- **Status:** TBF
- **Verification so far (2026-10-26):** backend tests 39 (9 new: edit, code lock, length limits, archive/unarchive, archived VR program refused while queued uploads still save, built-in read-only, add/edit phase, criteria bounds, wrong-protocol phase, patients on an edited phase keep their prescription) and authorization tests (new routes refuse missing and bad tokens) pass; migration test checks `archived_at`. Browser check on a throwaway database at the app's minimum window size: edit details, archive with confirmation, archived banner and Reactivate, caseload hides archived unless "Show archived patients", phase editor (edit and add) on a custom protocol, read-only note on built-in protocols. Decision: DEC-014. Left: the human check in the desktop app (`pending_human_tests`).
- **Objective:** Let therapists correct and retire records and refine protocols without touching the database.
- **Deliverables:** edit patient details; archive / unarchive patients (records kept, archived hidden from the caseload by default; decision recorded); edit and add phases on therapist-authored protocols (built-in protocols read-only); new endpoints with authorization, bounds checks and escaping as in M4.2; schema migration in the existing order; tests. The patient name field keeps its current behaviour (TASK-004 decides its future).
- **Completion criteria:** backend and authorization tests cover each new endpoint, including unauthorized access and archived-patient behaviour, and pass.
- **Dependencies:** M5.1
- **Systems:** ClinicalBackend, TherapistDashboard

### M5.3 — Clinical Insights & Attention Flags
- **Status:** TBF
- **Verification so far (2026-10-26):** backend tests 51 pass (9 new: no flags for a quiet patient, pain spike, pain rising across sessions, accuracy drop and a small dip not flagged, unsafe reps with old sessions ignored, missed days, no missed days before enrolment, no flags when archived; sources counted per flag). Browser check at the app's minimum window on a throwaway database: flagged patient sorted first with chips, chart notice with reasons and counted sources (non-webcam sessions called out), Clinical Status box from the flags. Left: the human check (`pending_human_tests`) and PT review of the thresholds (TASK-007).
- **Objective:** Show the therapist which patients need attention first, and why.
- **Deliverables:** server-computed per-patient flags (pain rising over recent sessions, accuracy dropping, missed scheduled days, unsafe reps); a "needs attention" column and sort on the caseload; reasons in the chart header; thresholds as named placeholder constants for PT review (see TASK-007); each flag states which input sources it counted (simulated sessions still count until TASK-003 is decided); tests.
- **Completion criteria:** each flag has tests for firing and not firing; the caseload sorts by attention.
- **Dependencies:** M5.1
- **Systems:** ClinicalBackend, TherapistDashboard

### M5.4 — Session Flow Polish
- **Status:** TBF
- **Verification so far (2026-10-26):** Agent play-test in the Unity Editor (simulated input, offline cached program; the offline upload queue was backed up and restored after each run) on a seated, a standing and a side-lying exercise: get-ready card, countdown, keyboard hints and the queued-sessions line show correctly; auto-focus frames the coach at get-ready and again at Go once the coach takes the exercise pose (found during the play-test: the coach stands idle until Go, so a seated exercise was framed as standing). Also fixed the 'Moved too quickly (01s)' number format. Unity EditMode tests 35 pass (9 new: countdown 3-2-1-Go, countdown frozen while paused, restart keeps every attempt and unsafe rep while resetting the sets, control hints per device, four auto-focus framing cases: standing, on the table, small motions, coach to the side, and the too-fast message format); no compile errors. Restart design: the sets start again from set 1, but all attempts stay in the rep log and the upload (attempt numbers keep counting), so the therapist and the evaluation see them; the session UUID is unchanged. Left: human Play-mode check (`pending_human_tests`); the Unity Editor was not open, so nothing was checked in Play mode.
- **Objective:** Give the patient clear pacing and control during a session.
- **Deliverables:** auto-focus on the exercise (added by the human 2026-10-26: on the laptop the camera eases in to frame the coach at every exercise; in the headset only an instant re-center, to avoid motion sickness); 3-2-1 countdown and transition card between exercises; exercise-complete celebration; "Restart exercise" in the pause menu (rep log and session UUID stay consistent); queued offline uploads shown on the menu; control hints from the active input mode; EditMode tests for new pure logic.
- **Completion criteria:** EditMode tests pass; restart keeps the uploaded session correct; human Play-mode check.
- **Dependencies:** M4.3
- **Systems:** SessionOrchestration, VRClinicExperience

### M5.5 — Session Summary & Progress Screens
- **Status:** TBF
- **Verification so far (2026-10-26):** server tests 54 pass (3 new: progress in the VR program and not in the dashboard's program endpoint, structured rewards xpGained / levelBefore / levelAfter in the upload response, recent-session limit); Unity EditMode tests 42 pass (7 new: XP span within a level and across a level-up, exercise lines, notes left to the animation, badge gallery, Progress page text, gamification scoring). Agent play-test against a throwaway server and database (the offline queue and program cache were backed up and restored): Progress page, full session summary with per-exercise lines, XP bar and new badges. Found and fixed during the play-test: the summary's starting XP was stale when queued offline sessions were sent at load (now from the server's xpGained); the Progress page overflowed the view (tall menu pages now scale down); badge names wrapped mid-name. Progress data rides on GET /api/vr/program (loopback, patient code, DEC-009) and is cached with the program for offline use. Left: human Play-mode check (`pending_human_tests`).
- **Objective:** Make progress visible and rewarding to the patient.
- **Deliverables:** short summary (changed by the human 2026-10-26: no per-exercise breakdown, notes or therapist numbers on the patient's summary; totals, a STOP-line warning when needed, saved status), animated XP fill, badge reveal online and offline, and a clear level-up moment (not a string match); main-menu Progress page with recent sessions, streak, level/XP and a badge gallery (earned and locked); progress data from a loopback-only, patient-code-scoped VR route or the program payload (DEC-009), shown as cached when offline; server tests; EditMode tests for summary/progress shaping and `GamificationManager`.
- **Completion criteria:** server and EditMode tests pass; human Play-mode check online and offline.
- **Dependencies:** M5.4
- **Systems:** Gamification, SessionOrchestration, ClinicalBackend, VRClinicExperience

### M5.6 — Audio & Visual Assets
- **Status:** TBF
- **Verification so far (2026-10-26):** all six items in, every asset chosen by the human from previews and credited in `Assets/TheraQuest/CREDITS.md` with its licence file alongside (all CC0 except the fonts: Apache 2.0, SIL OFL, Bitstream Vera/DejaVu). Fonts: Luckiest Guy (44 px and up) and Nunito, outlines in a lighter shade of the text colour (subtitles keep a dark outline). Sound: new hold-complete chime (Kenney); menu click, STOP warning, level up stay generated by the human's choice, the badge chime gets a generated reverb tail. Music: nine CC0 lo-fi tracks (omfgdude, Holizna) as a shuffled playlist at the Music volume. Badge icons: seven Kenney icons, gold when earned and grey when locked, on the HUD chips, the summary reveal and the Progress page. Coach idle: Quaternius Universal Animation Library `Idle_Loop` (Humanoid). TextMeshPro for all HUD and menu text, approved by the human (DEC-015). Assets load from `Resources`, and each falls back (generated loop and chimes, ★ chips, hand-made sway, default font) when missing; checked in Play mode with the assets moved out. Unity EditMode tests 49 pass (6 new). The agent play-tested in the Editor (simulated input, throwaway server, offline queue and program cache restored) and checked screenshots of the menu, HUD, summary and Progress page. Follow-up requested by the human the same day: every display-font label is outlined (lighter shade of its colour; white text on pills and tiles gets a darker shade of the pill); a VR headset logo (Font Awesome `vr-cardboard`, SIL OFL) sits beside the game name on the main menu; the Progress page has three tabs (Profile, Recent sessions, Badges with how to earn each), switched with Left / Right or a click; the HUD cards, summary card and menu are sized to their content (the hold bar and new-badge row appear only when used). Play-mode screenshots checked; EditMode tests still 49. Second follow-up (same day): five-colour palette for all panels and text (DEC-016; red kept only for safety warnings), headset logo moved after the game name and tilted 30° away from it, navy text outlined in off-white and pop-ups in a darker shade, and the Badges tab shows one card per badge (icon, name, how to earn it at the bottom; locked cards greyed). EditMode tests 50 pass. Third follow-up (2026-10-27): badge cards lost their coloured top bar; the coach area was fixed: the exercise mat now follows the coach and its chair or bed for every posture (it had the coach on its front edge with props hanging off), the coach stands with no props on menus and waits seated or lying in the coming exercise's posture during get-ready (it used to stand beside the chair or bed), resting legs lie straight on the bed (shins had sunk through the mattress), and seated hands rest at the knees. Checked in Play mode for standing, seated, lying and side-lying; EditMode tests 50 pass. Correction (2026-10-27): the coach idle had not actually been playing, because none of the 16 coach models imported as a Humanoid (the Quaternius rig keeps its feet under the root); `CoachModelImporter` now maps the rig by hand, the idle clip drives the trunk, head and arms (standing legs stay hand-posed, since the retargeted clip took a stride), and a new test checks every coach model is a valid Humanoid. Verified in Play mode on the male and female coaches; EditMode tests 51 pass. A cartoon coach style (DEC-017: toon shading, outlines, stylised proportions) was added and then removed at the human's request on 2026-10-27 (DEC-017 superseded); the Little Guys coaches (DEC-018) now show as modelled, with a plain Built-in material in place of the pack's URP one; checked in Play mode on both genders. Left: the human Play-mode check (`pending_human_tests`) and confirming the source of the older rep sounds and coach models (CREDITS.md "Not yet recorded").
- **Objective:** Replace placeholder sounds, art and text rendering.
- **Deliverables:** real sound effects (level-up, badge, warning, click, hold complete); a music track; one icon per badge; a coach idle animation; TextMeshPro for HUD and menu text; assets only from CC0/licensed sources or supplied by the human, with a credits file recording source and licence; generated chimes kept as a fallback.
- **Completion criteria:** every asset is credited; the game runs with assets present and with them missing; human Play-mode check (legibility, volume).
- **Dependencies:** M5.5 (badge reveal and progress page use the badge icons)
- **Systems:** VRClinicExperience, AvatarCoach, Gamification


### M5.7 — Additional Built-in Clinical Protocols
- **Status:** TBF
- **Objective:** Give therapists more evidence-based protocols to assign (requested by the human 2026-10-26): ACL reconstruction, hip fracture fixation, a second total knee arthroplasty source, ORIF for ankle, distal radius and tibial plateau fractures, and lateral ankle sprain.
- **Deliverables:** seven `PROTOCOLS` entries summarized from published documents (ACL, TKA, ankle ORIF and ankle sprain: Mass General Brigham; distal radius ORIF: Brigham and Women's 2021; tibial plateau ORIF: Twin Cities Orthopedics, Dr. Butterfield 04/2024; hip fracture fixation: Dr. Jason Ferrel 07/2024), with the camera-measurable exercises in VR phases and the rest listed as done without the camera; protocol version 3; the built-in reload keeps unchanged protocols so patients on them keep their phase; tests.
- **Completion criteria:** backend tests pass, including reload and data-shape tests; the protocols appear read-only in the library; human check that the phases read correctly.
- **Verification so far (2026-10-26):** backend tests 42 pass (3 new: unchanged built-in keeps patients on their phase, changed built-in is replaced, every built-in is well formed); the upgrade was run on a copy of the live database (OHSU and MGB rotator cuff kept, seven added); the library shows all nine read-only. Left: the human check (`pending_human_tests`) and the licensed-PT review of targets (TASK-007).
- **Dependencies:** M5.2 (read-only built-ins, DEC-014)
- **Systems:** ClinicalBackend, TherapistDashboard

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
- **Deliverables:** test run covering head tracking and recentering (Y / R), controller mapping (A select, B pause, thumbsticks for menus, walking and turning), locomotion locked during exercises, HUD and menu legibility and comfort at the configured distances, subtitles, pause and quit in the headset, and the desktop fallback with Link off; fixes for problems found.
- **Completion criteria:** every item passes in the headset, or has a recorded fix or workaround; a session done in the headset uploads to the dashboard.
- **Dependencies:** HW.1
- **Systems:** VRClinicExperience, SessionOrchestration

### HW.3 — Webcam and Headset Concurrent Operation
- **Status:** planned
- **Objective:** Check that tracking and VR rendering can share one PC, and that tracking works for a patient wearing a headset.
- **Deliverables:** measurements of headset frame rate, tracker rate and CPU/GPU load with everything running; a real side-view footage check of the signed elevation angles with `tracker/check_signed.py` (moved here from M4.6 verification on 2026-10-25): shoulder and hip extension must read negative and flexion positive, facing both ways, with and without the headset, measuring the share of frames where the facing direction can't be told; tracker accuracy and visibility while the patient wears the headset (the headset can hide the face landmarks used to tell facing direction); front and side camera placement checked for each tracked exercise; live webcam unplug and reconnect test (open from M4.4).
- **Completion criteria:** the headset frame rate and tracker rate stay usable during a full session; signed angles have the right sign and the facing direction is missing in under ~5% of frames (at ~20% or more, Unity keeps the last known direction across short gaps), with the headset on and off; posture checks work with the headset on, or a fix is made; camera placement guidance is confirmed or corrected.
- **Dependencies:** HW.1, HW.2
- **Systems:** MotionTracking, ExerciseEvaluation, VRClinicExperience

### HW.4 — End-to-End Integration Run
- **Status:** planned
- **Objective:** Run the complete clinical workflow on the real hardware.
- **Deliverables:** therapist prescribes on the dashboard; patient runs the session in the headset with webcam tracking; the session, adherence, per-rep log and clinical notes appear on the dashboard; offline mode and the upload queue tested on the real setup; a findings list with each problem fixed or recorded.
- **Completion criteria:** at least one complete prescribe → exercise → review cycle succeeds on the target hardware with no manual workarounds; findings are recorded in the brain.
- **Dependencies:** HW.2, HW.3
- **Systems:** SessionOrchestration, ClinicalBackend, TherapistDashboard, VRClinicExperience, MotionTracking
