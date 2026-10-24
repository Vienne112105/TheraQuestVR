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
| M4 | — | active | Foundation Hardening (pre-feature stabilization) |
| M4.1 | M4 | done | Repository & Environment Safety |
| M4.2 | M4 | done | Backend Security & Data Integrity |
| M4.3 | M4 | TBF | Unity Client Robustness & Deployability |
| M4.4 | M4 | done | Tracker Measurement Correctness |
| M4.5 | M4 | done | Evaluation Pipeline Integrity |
| M4.6 | M4 | done | Single Source of Exercise Definitions |
| M5 | — | planned | Hardware Integration & Field Validation |
| M5.1 | M5 | planned | Hardware Setup & Compatibility Baseline |
| M5.2 | M5 | planned | Headset Integration Test |
| M5.3 | M5 | planned | Webcam and Headset Concurrent Operation |
| M5.4 | M5 | planned | End-to-End Integration Run |

---

## Suggested sequence

`M0` (done) ➔ `M1` (done: features & avatars) ➔ `M2` (done: analytics & evaluation) ➔ `M3` (done: security & hardening) ➔ `M4` (active: foundation hardening before new game & dashboard features) ➔ `M5` (planned: hardware integration & field validation, when the hardware is available)

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

- **Status:** active
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
  - `M4.3`: Unity Client Robustness & Deployability (TBF)
  - `M4.4`: Tracker Measurement Correctness (done)
  - `M4.5`: Evaluation Pipeline Integrity (done)
  - `M4.6`: Single Source of Exercise Definitions (done)
- **Done when:** all children are done and the server, tracker, evaluation and Unity EditMode test suites pass, followed by a human Play-mode check. (The headset check moved to M5.2 on 2026-10-25.)

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
- **Status:** TBF
- **Verification so far:** EditMode tests pass (26); Windows player builds and starts with `-patient` in desktop fallback; Editor Play-mode check (online, offline cache, queue flush, Therapist page) passed 2026-10-22. Still to verify by a human: built player against a running server and tracker (desktop).
- **Objective:** Make the VR client deployable to a clinic and robust to bad input and failures.
- **Deliverables:** patient code from command line / config / PIN-protected therapist page; OpenXR packages and loader; cached last program instead of hardcoded offline program; input source locked during sessions; resilient offline queue with session UUIDs; prescription validation; loopback-only UDP receiver; locomotion lock; quit checkpoint; EditMode tests.
- **Completion criteria:** EditMode tests pass; a built player runs with `-patient`; desktop fallback works. (Amended 2026-10-25 by the human: the headset run moved to M5.2, because no headset is available yet.)
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


## M5 — Hardware Integration & Field Validation

- **Status:** planned
- **Objective:** Bring together the real hardware the project needs (Meta Quest headset over Quest Link, a VR-ready Windows PC, a clinic webcam) and test how well the whole system works on it: VR client, motion tracker, clinical server and therapist dashboard running together on one machine, as a patient and therapist would use them.
- **Success criteria:**
  - The VR client runs in the headset over Quest Link (OpenXR) with head tracking and controller input, and falls back to desktop mode when Link is off (DEC-002).
  - Tracker, VR client and server run together on the target PC without dropping below a comfortable headset frame rate or the tracker's working rate (~30 FPS).
  - A full session done in the headset with the webcam tracker reaches the dashboard with correct per-rep data.
  - Every hardware problem found is fixed, or recorded with a workaround, in the brain.
- **Children:**
  - `M5.1`: Hardware Setup & Compatibility Baseline
  - `M5.2`: Headset Integration Test
  - `M5.3`: Webcam and Headset Concurrent Operation
  - `M5.4`: End-to-End Integration Run
- **Done when:** all children are done; the findings and the clinic setup steps are recorded.
- **Dependencies:** M4 (software foundation); access to the hardware.

### M5.1 — Hardware Setup & Compatibility Baseline
- **Status:** planned
- **Objective:** Get the hardware working with the software stack and record what a clinic machine needs.
- **Deliverables:** Meta Quest Link app installed and set as the active OpenXR runtime; headset connection by cable and/or Air Link; webcam chosen and mounted (USB on a tripod preferred); a clinic setup checklist covering PC/GPU, cable, camera placement, 2 x 2 m space and lighting (README).
- **Completion criteria:** the built player and the Editor both start in the headset; the tracker sees the webcam; the checklist is written from the real setup.
- **Dependencies:** M4
- **Systems:** VRClinicExperience, MotionTracking

### M5.2 — Headset Integration Test
- **Status:** planned
- **Objective:** Verify the VR client on the real headset (moved here from M4.3's completion criteria on 2026-10-25).
- **Deliverables:** test run covering head tracking and recentering (Y / R), controller mapping (A select, B pause, thumbsticks for menus, walking and turning), locomotion locked during exercises, HUD and menu legibility and comfort at the configured distances, subtitles, pause and quit in the headset, and the desktop fallback with Link off; fixes for problems found.
- **Completion criteria:** every item passes in the headset, or has a recorded fix or workaround; a session done in the headset uploads to the dashboard.
- **Dependencies:** M5.1
- **Systems:** VRClinicExperience, SessionOrchestration

### M5.3 — Webcam and Headset Concurrent Operation
- **Status:** planned
- **Objective:** Check that tracking and VR rendering can share one PC, and that tracking works for a patient wearing a headset.
- **Deliverables:** measurements of headset frame rate, tracker rate and CPU/GPU load with everything running; tracker accuracy and visibility while the patient wears the headset (the headset can hide the face landmarks used to tell facing direction); front and side camera placement checked for each tracked exercise; live webcam unplug and reconnect test (open from M4.4).
- **Completion criteria:** the headset frame rate and tracker rate stay usable during a full session; facing direction and posture checks work with the headset on, or a fix is made; camera placement guidance is confirmed or corrected.
- **Dependencies:** M5.1, M5.2
- **Systems:** MotionTracking, ExerciseEvaluation, VRClinicExperience

### M5.4 — End-to-End Integration Run
- **Status:** planned
- **Objective:** Run the complete clinical workflow on the real hardware.
- **Deliverables:** therapist prescribes on the dashboard; patient runs the session in the headset with webcam tracking; the session, adherence, per-rep log and clinical notes appear on the dashboard; offline mode and the upload queue tested on the real setup; a findings list with each problem fixed or recorded.
- **Completion criteria:** at least one complete prescribe → exercise → review cycle succeeds on the target hardware with no manual workarounds; findings are recorded in the brain.
- **Dependencies:** M5.2, M5.3
- **Systems:** SessionOrchestration, ClinicalBackend, TherapistDashboard, VRClinicExperience, MotionTracking
