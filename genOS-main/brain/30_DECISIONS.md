# Decisions

Authoritative decision log. AI records entries; humans approve intent-affecting decisions.
See `AGENTS.md` → Ownership.

Record a decision when intent, architecture, or constraints change in a way future agents cannot infer from runtime environment or source code.

**ID format:** `DEC-001`, `DEC-002`, …  
**Status:** `proposed` | `accepted` | `superseded` | `rejected`

Do not duplicate implementation details. Link to systems or runtime paths when useful.
Keep the Index in sync with entries below. Do not leave blank placeholder rows.

---

## Index

| ID | Status | Date | Title |
|----|--------|------|-------|
| DEC-001 | accepted | 2026-10-18 | Single-Webcam 2D Pose Estimation via MediaPipe & UDP |
| DEC-002 | accepted | 2026-10-18 | Quest Link OpenXR Runtime with Standalone Desktop Fallback |
| DEC-003 | accepted | 2026-10-18 | Local-First Clinical Architecture with Patient Pseudonymization |
| DEC-004 | accepted | 2026-10-19 | Dual-Tier Coach Persona Architecture with Procedural Styles & Silhouette Isolation |
| DEC-005 | accepted | 2026-10-19 | Dual-Gender Humanoid Models, Holographic Dual-Zone ROM Guidance, and Ergonomic HUD Scaling |
| DEC-006 | accepted | 2026-10-19 | Therapist Authentication, In-App Clinical Modals, and Offline Frontend Library Stack |
| DEC-007 | accepted | 2026-10-19 | Clinical Exercise Protocol Lifecycle and Patient Protocol Detachment |
| DEC-008 | accepted | 2026-10-19 | High-Concurrency Database Indexing, SQLite WAL Mode, and Query Batching Optimization |
| DEC-009 | accepted | 2026-10-19 | Separate Patient-Scoped VR Routes with Patient-Code and Loopback Authorization |
| DEC-010 | accepted | 2026-10-20 | Clinical Database Stored Outside the Synced Project Folder |
| DEC-011 | accepted | 2026-10-20 | Evaluation Reports Must Declare Their Data Source |
| DEC-012 | accepted | 2026-10-20 | Server Exercise Library Is the Single Source of Exercise Rules |
| DEC-013 | accepted | 2026-10-26 | Therapist Dashboard Is a Desktop App, Not a Website |
| DEC-014 | accepted | 2026-10-26 | Patients Are Archived, Never Deleted; Built-in Protocols Are Read-Only |
| DEC-015 | accepted | 2026-10-26 | Game Text Uses TextMeshPro; Game Assets Load from Resources with Generated Fallbacks |
| DEC-016 | accepted | 2026-10-26 | Five-Colour Game Palette; Red Only for Safety Warnings |
| DEC-017 | superseded | 2026-10-27 | Cartoon Coach: Toon Shading, Outlines and Stylised Proportions |
| DEC-018 | accepted | 2026-10-27 | Little Guys Coach Models |
| DEC-019 | accepted | 2026-10-27 | Clinic Room Decorations and Exercise Chair Are 3D Model Assets |
| DEC-020 | accepted | 2026-10-28 | The Repository Stays Private; Third-Party Asset Files Are Never Published |
| DEC-021 | accepted | 2026-11-01 | First-Person Exercise View, Coach Window and Default Height |
| DEC-022 | accepted | 2026-11-01 | Estimated Landmarks Are Never Measured or Scored |
| DEC-023 | accepted | 2026-11-05 | 3D World Landmarks for Facing Direction and the Out-of-Plane Live Limb |
| DEC-024 | accepted | 2026-11-05 | Tracking Recordings Hold Landmarks Only and Stay Local |
| DEC-025 | accepted | 2026-11-07 | Landmarks Are Trusted Again After 2 Confident Frames |
| DEC-026 | accepted | 2026-11-12 | Which Limb Is Measured, Resting Baseline and Rep Timing |
| DEC-027 | accepted | 2026-11-12 | Patient Records Hold Name and Code; Only the Code Leaves the Dashboard |
| DEC-028 | accepted | 2026-11-14 | The Game Renders with URP |
| DEC-029 | superseded | 2026-11-16 | The Manuscript Master Is the Google Doc / Word File; the Repo Copy Is a Working Copy |
| DEC-030 | accepted | 2026-11-17 | The VR Client Moves to the XR Interaction Toolkit, Controllers Only |
| DEC-031 | accepted | 2026-11-22 | Manuscript Edits Go into the Word Draft as Tracked Changes |

---

## Template

```markdown
### DEC-XXX: Title
- **Status:** proposed
- **Date:** YYYY-MM-DD
- **Reason:**
- **Impact:**
- **Supersedes:** none
```

---

## Decisions

### DEC-001: Single-Webcam 2D Pose Estimation via MediaPipe & UDP
- **Status:** accepted
- **Date:** 2026-10-18
- **Reason:** Patients and clinics require an affordable, zero-specialized-hardware solution for home and outpatient telerehab. MediaPipe running on a standard laptop webcam delivers ~30 FPS tracking without requiring depth cameras or wearable sensors.
- **Impact:** Angle estimation operates in 2D projections; patients must position the camera perpendicular to the primary exercise plane (sagittal for flexion, coronal for abduction). Exercises involving axial limb rotation cannot be tracked in VR and are designated as off-camera tasks.
- **Supersedes:** none

### DEC-002: Quest Link OpenXR Runtime with Standalone Desktop Fallback
- **Status:** accepted
- **Date:** 2026-10-18
- **Reason:** Eliminates complex Android cross-compilation and sideloading on Meta Quest headsets, while allowing the Python CV tracker and SQLite server to run concurrently on the same host Windows machine.
- **Impact:** Unity runs as a Windows PC application communicating with the headset via Meta Quest Link / OpenXR. When no headset is connected, it seamlessly falls back to desktop mode (windowed keyboard/mouse), allowing universal testing and access.
- **Supersedes:** none

### DEC-003: Local-First Clinical Architecture with Patient Pseudonymization
- **Status:** accepted
- **Date:** 2026-10-18
- **Reason:** Complies with data privacy regulations (Philippine Data Privacy Act RA 10173 and ethical research guidelines) by keeping patient performance records on the clinic machine without transmitting protected health information (PHI) to third-party cloud services.
- **Impact:** Patients are assigned synthetic codes (e.g., `P-001`), database persistence remains in local SQLite (`theraquest.db`), and the therapist dashboard operates locally on port 8000.
- **Supersedes:** none
- **Amended by:** [[30_DECISIONS#DEC-027: Patient Records Hold Name and Code; Only the Code Leaves the Dashboard|DEC-027]] (2026-11-12): records also hold the patient's real name, kept inside the dashboard; local-first storage is unchanged.

### DEC-004: Dual-Tier Coach Persona Architecture with Procedural Styles & Silhouette Isolation
- **Status:** accepted
- **Date:** 2026-10-19
- **Reason:** Out-of-the-box deployments may lack imported Mixamo/FBX humanoid models. Patients require selectable coaching aesthetics (Clinical, Athletic, ZenSage, HighContrast) and guidance modes (full coach demo vs silhouette target isolation) regardless of whether external 3D asset packages are present.
- **Impact:** `HumanoidCoach` acts as a unified facade: when zero rigged FBX avatars are present, it proxies style selection and guide mode down to `FigureVisualizer`, allowing full UI access to 4 coach personas and Silhouette isolation without external asset dependencies.
- **Supersedes:** none

### DEC-005: Dual-Gender Humanoid Models, Holographic Dual-Zone ROM Guidance, and Ergonomic HUD Scaling
- **Status:** accepted
- **Date:** 2026-10-19
- **Reason:** Patients benefit from personalized coach gender representation, clear 3D spatial boundaries showing where exercise motion ends with visual tolerance feedback, and legible floating interfaces that eliminate VR visual fatigue.
- **Impact:** `HumanoidCoach` scans gender-segregated coach directories (`Male`/`Female`), persists gender selection across sessions, and projects a holographic target orb with tolerance halos in both Coach and Silhouette modes. `SessionManager` restricts coach movement to active sessions, maintaining relaxed idle posture during menus. `HUDController` and `MenuController` scale cards by ~70% with inspector-tunable `hudScale`.
- **Supersedes:** none

### DEC-006: Therapist Authentication, In-App Clinical Modals, and Offline Frontend Library Stack
- **Status:** accepted
- **Date:** 2026-10-19
- **Reason:** Clinical environments require secure identity enforcement (therapist authentication), eliminating browser origin alerts (`localhost:8000 says`), air-gapped frontend library assets (Chart.js, Lucide, Tailwind) without cloud dependencies, and a customized exercise prescription flow to replace abrupt immediate adds.
- **Impact:** Passwords stored with PBKDF2-HMAC-SHA256 and unique 16-byte cryptographic salts; bearer token sessions managed via `therapist_session` table with 24-hour expiration. Browser `confirm()` and `alert()` eradicated in favor of custom in-app HTML modals (`#confirmModal`, `#addExerciseModal`) and floating toasts (`showToast`). Chart.js renders dual-axis ROM and repetition clinical trends directly from local `/static/vendor/` scripts with CDN fallback. Back button highlighted with crisp black border/ring for clinical hierarchy.
- **Supersedes:** none

### DEC-007: Clinical Exercise Protocol Lifecycle and Patient Protocol Detachment
- **Status:** accepted
- **Date:** 2026-10-19
- **Reason:** Standardized rehabilitation protocols were previously fixed to two hardcoded seeds with no facility for therapists to author new protocols, remove obsolete protocols, or cleanly detach protocols from patient charts without destroying active exercises.
- **Impact:** Implemented full lifecycle endpoints (`POST /api/protocols`, `DELETE /api/protocols/{id}`, and `DELETE /api/patients/{id}/protocol`). Added a dedicated Protocol Management modal (`#protocolModal`) supporting protocol authoring (phases, clinical goals, precautions, ROM milestones, and multi-selected exercises) and library deletion with automatic foreign key cascades. Added patient-level protocol detachment that preserves prescribed exercises as an independent custom prescription.
- **Supersedes:** none

### DEC-008: High-Concurrency Database Indexing, SQLite WAL Mode, and Query Batching Optimization
- **Status:** accepted
- **Date:** 2026-10-19
- **Reason:** High-frequency telemetry streams from Unity coupled with dashboard multi-table joins created potential lock contention, repetitive database round-trips (N+1 query patterns), and unnecessary DOM redraws during rapid clinical reviews.
- **Impact:** Enabled SQLite Write-Ahead Logging (`PRAGMA journal_mode = WAL;`, `synchronous = NORMAL;`, `temp_store = MEMORY;`, 32MB page cache); created 11 database indexes across sessions, adherence, performance records, and protocols; consolidated `list_protocols` to 3 bulk queries; batched prescription column updates; eliminated SQL injection risk in `delete_protocol` via parameterization; added Cache-Control headers for vendor assets; optimized Chart.js with in-place `.update()`; and throttled Lucide icon passes using `requestAnimationFrame`.
- **Supersedes:** none

### DEC-009: Separate Patient-Scoped VR Routes with Patient-Code and Loopback Authorization
- **Status:** accepted
- **Date:** 2026-10-19
- **Reason:** [[50_ROADMAP]] M3.2 lists `/api/patients/{id}/program` as therapist-only, but the Unity client reads its prescription from that same `GET` route with no credentials. The therapist dashboard never `GET`s it (it reads `/dashboard` and only `PUT`s `/program`), so the route mixes a patient read with a therapist write. Patient codes such as `P-001` are pseudonyms, not secrets, and the server binds `0.0.0.0`, so a patient code alone would let any device on the clinic network read or submit data for any patient.
- **Impact:**
  - All `/api/patients/*`, `/api/protocols*`, `/api/library`, `/api/sessions/{id}/clinical` and `/api/export*` routes require a valid therapist bearer token and return `401` otherwise (`/api/auth/login` and static assets remain open).
  - The VR client gets its own patient-scoped routes, `GET /api/vr/program` and `POST /api/vr/sessions`. They identify the patient by an `X-Patient-Code` header, resolve the code to `patient_id` on the server, and return `403` when a body `patient_id` does not match, so one code can never read or write another patient's record.
  - The VR routes accept requests only from loopback (`127.0.0.1` / `::1`), matching DEC-002 (Unity, tracker and server share one host). Requests from other hosts get `403`.
  - The legacy `POST /api/sessions` route is removed (amended during implementation: a code-checked alias was useless, because pre-DEC-009 Unity builds send no code). The updated client re-sends queued lines to `POST /api/vr/sessions`; lines without a stored code are attributed to the configured patient, and lines refused with `403` go to `rejected_sessions.jsonl` instead of being dropped.
  - Unity's `ApiClient` switches from the inspector `patientId` integer to a `patientCode` string and stores the code with each queued upload. Sessions recorded with the offline default program send `patient_id` 0, and the server attributes them by code.
  - Amends M3.2's completion criteria: `/api/patients/{id}/program` becomes fully therapist-only, and "patient synthetic code authorization" applies to the `/api/vr/*` routes.
- **Supersedes:** none

### DEC-010: Clinical Database Stored Outside the Synced Project Folder
- **Status:** accepted
- **Date:** 2026-10-20
- **Reason:** The project lives in OneDrive, which can sync or restore `theraquest.db` without its WAL side files and lock it mid-write, risking corruption or lost sessions. The database also should not end up in version control.
- **Impact:** The server reads its database path from `THERAQUEST_DB`, defaulting to `%LOCALAPPDATA%\TheraQuest\theraquest.db`; an existing `server/theraquest.db` is copied there once on first run. The project is placed under git with generated folders and database files ignored. Moving the whole project out of OneDrive is left to the human.
- **Supersedes:** none

### DEC-011: Evaluation Reports Must Declare Their Data Source
- **Status:** accepted
- **Date:** 2026-10-20
- **Reason:** The committed evaluation report presented hardcoded example inputs (confusion matrix, goniometer angles, SUS, therapist ratings) with a hardcoded PASS, which a reader could take as study results.
- **Impact:** The synthetic run becomes an explicit self-test with a "SYNTHETIC EXAMPLE DATA" banner and computed status. Real metrics come only from documented CSV inputs (goniometer readings, therapist rep labels, SUS, PT survey) and per-rep logs; metrics without real input are reported as "not measured".
- **Supersedes:** none

### DEC-012: Server Exercise Library Is the Single Source of Exercise Rules
- **Status:** accepted
- **Date:** 2026-10-20
- **Reason:** Exercise rules (posture checks, body position, coach pose, camera view) were duplicated in switch statements across `MotionInput`, `HumanoidCoach`, `FigureVisualizer` and the server, and had already started to disagree.
- **Impact:** Each `LIBRARY` entry carries posture, posture checks, movement direction and figure pose, sent to Unity in the VR program. Unity reads these instead of switching on exercise codes; animation curves stay in the coach, keyed by pose.
- **Supersedes:** none

### DEC-013: Therapist Dashboard Is a Desktop App, Not a Website
- **Status:** accepted
- **Date:** 2026-10-26
- **Reason:** The human confirmed (2026-10-26) that the therapist dashboard is delivered as an app. `Start_Therapist_App.bat` runs `app.py`, which starts the local server and shows `dashboard.html` in a native WebView2 window (minimum 980 × 640), with an Edge app window as the fallback. The local HTTP server is only how the app's window gets its page and how Unity reaches the API.
- **Impact:** Instructions, human tests and design targets refer to the desktop app, never "open http://localhost:8000 in a browser". Layout work targets the app window from its minimum size up; phone layouts are not a goal. The page may still open in a browser for development and automated checks.
- **Supersedes:** none

### DEC-014: Patients Are Archived, Never Deleted; Built-in Protocols Are Read-Only
- **Status:** accepted
- **Date:** 2026-10-26
- **Reason:** M5.2 lets therapists retire patients and refine protocols from the dashboard (archive-instead-of-delete was approved with the M5 plan). Clinical and research records must survive (Section 3.9 evaluation, RA 10173 accountability), and built-in protocols are reloaded from `PROTOCOLS` whenever `PROTOCOL_VERSION` changes, so edits to them would be lost.
- **Impact:** Archiving sets `patient.archived_at`; nothing is deleted. Archived patients are hidden from the caseload unless the therapist asks for them, the VR app gets 403 for a new program (no new sessions), and uploads of sessions already recorded (offline queue) are still accepted. Only therapist-authored protocols (`builtin = 0`) can have phases edited or added; built-in ones answer 403. Editing a phase does not change the prescription of patients already on it: a phase's exercises are copied to the patient when it is assigned. The patient code can't be edited (the VR app is configured with it).
- **Supersedes:** none

### DEC-015: Game Text Uses TextMeshPro; Game Assets Load from Resources with Generated Fallbacks
- **Status:** accepted
- **Date:** 2026-10-26
- **Reason:** Legacy `UnityEngine.UI.Text` blurs up close and at an angle in a headset; the human approved moving to TextMeshPro in M5.6 (before the pending Play-mode checks, so they check the final text once). The scene file holds the human's own unsaved work and can't be relied on to carry asset references into a build, and the game must keep running when an asset is missing (M5.6 completion criteria).
- **Impact:** All game text is `TextMeshProUGUI`, created only through `UIKit.Label`, which picks the font (SDF assets made at runtime from the TTFs in `Resources/Fonts`, DejaVu Sans Bold as the fallback for symbols), applies outlines through the text material (`UIKit.Stroke`) and makes on-top panels ignore depth with shared materials. TextMesh Pro essentials live in `Assets/TextMesh Pro`. Music, sounds, badge icons and the coach idle load from `Assets/TheraQuest/Resources` when their inspector field is empty; each has a fallback (generated loop and chimes, ★ chips, hand-made idle sway, TextMeshPro's default font). Badge icons inside text use `<sprite name="code">` from `Resources/Badges/BadgeSprites.asset`.
- **Supersedes:** none

### DEC-016: Five-Colour Game Palette; Red Only for Safety Warnings
- **Status:** accepted
- **Date:** 2026-10-26
- **Reason:** The human set the game's colours to five: navy #1D3557, blue #277DA1, orange #F3722C, green #43AA8B, off-white #F8F9FA. Asked about scope and warnings, the human chose panels and text only (the 3D clinic room keeps its own colours) and to keep red for safety warnings so they never look like ordinary orange hints.
- **Impact:** Every panel and text colour in the game (menus, HUD, summary, Progress page, subtitles, pop-ups, posters) comes from `UIKit`'s palette, which holds only these five colours and tints of them; the older role names stay (Teal = accent blue, Yellow = rewards orange, Pink = combo green, Purple = navy). Red `#E5484D` is used only for safety (STOP line, unsafe or too-far reps, posture faults). Outline rule: display text gets a lighter shade of its colour, navy text a light off-white outline, white text on pills a darker shade of the pill, and pop-ups a darker shade of their own colour. The therapist dashboard is not covered by this decision.
- **Supersedes:** none

### DEC-017: Cartoon Coach: Toon Shading, Outlines and Stylised Proportions
- **Status:** superseded (2026-10-27: the human asked to remove the stylisation; the toon shader, outlines and proportion changes are gone, see DEC-018)
- **Date:** 2026-10-27
- **Reason:** Asked to make the coaches either more realistic or more cartoony, the human chose cartoony for both genders. A stylised coach avoids the uncanny look of near-realistic people up close in VR, renders cheaply on headsets, and matches the game's XP, badge and palette style; realism would have needed new high-detail models.
- **Impact:** Every coach (male and female) uses the `TheraQuest/Toon Outline` shader (`Assets/TheraQuest/Shaders`, template `Resources/Toon/CoachToon`): two-tone cel shading with a cool shadow tint, a soft rim light, and an outline in a darker shade of each part's own colour (none on eyes and brows, thinner on hair). Head and hands are slightly larger and the neck shorter, on both the coach and its see-through guide so the guide still lines up. All values are inspector fields on `HumanoidCoach` (`toonStyle`, `outlineWidth`, `headScale`, `handScale`, `neckLength`); turning `toonStyle` off restores the models' own materials. The shader is written for the Built-in render pipeline, which is what the project renders with today.
- **Supersedes:** none

### DEC-018: Little Guys Coach Models
- **Status:** accepted
- **Date:** 2026-10-27
- **Reason:** The human asked to use "Little Guys - Free Sample" (Luceed Studio, Unity Asset Store) as the coach model. It ships with valid Humanoid avatars and a full skeleton, so the existing bone-driven coach posing works unchanged, and its chunky cartoon look fits DEC-017.
- **Impact:** The scene's female and male coach are `Free Woman Tall` and `Free Man Tall` (the Tall versions have longer limbs, so the exercise reads better); `TheraQuestSceneBuilder` picks them when the pack is present, else the older models in `Coaches/`. The pack's material is URP and this project renders with the Built-in pipeline, so `HumanoidCoach` draws it with a plain Standard material that keeps the pack's texture (no outline, no cel shading, no proportion changes: the human asked to remove the DEC-017 stylisation on 2026-10-27). Credited in `CREDITS.md` (Asset Store EULA). Follow-up 2026-10-27 (human): the old Quaternius coach models were deleted; the pack's avatars come from a curved-spine bind pose, so `CoachAvatarBuilder` makes upright T-pose avatars (`Resources/CoachAvatars`) that `HumanoidCoach` uses for the idle clips, and the coach keeps its chest facing forward whatever a clip does; the coach stands 0.6 m further back (`standBack`) on a runtime yoga mat, and lying exercises happen on the mat, with no bed.
- **Supersedes:** DEC-017

### DEC-019: Clinic Room Decorations and Exercise Chair Are 3D Model Assets
- **Status:** accepted
- **Date:** 2026-10-27
- **Reason:** The human asked to replace the primitive room decorations and the exercise props with real assets (TASK-014) and picked, from previews, the "Low Poly Gym Pack" by reodesuxz (itch.io, free for commercial use, no redistribution of the files) for the equipment and Kenney's "Furniture Kit" (CC0) for the furniture.
- **Impact:** Models live in `Assets/TheraQuest/Resources/Room/Gym` and `Room/Furniture` with their licence files, and `ClinicRoom` places them at runtime along the walls (the scene file is not changed); the coach area and HUD stay clear. The seated-exercise chair is Kenney's `chairCushion`, scaled by `PropBuilder.Chair` to each coach (primitives as fallback). Walls, windows, posters, the exercise-spot marker and the coach's yoga mat stay built in code. The parallel bars and treatment table are gone (the gym pack has none). Because the gym pack forbids redistributing its files, the repository must stay private or those files be removed before it is shared.
- **Supersedes:** none

### DEC-020: The Repository Stays Private; Third-Party Asset Files Are Never Published
- **Status:** accepted
- **Date:** 2026-10-28
- **Reason:** A licence audit found assets whose licences allow use in a shipped app but not publishing the raw files: the Low Poly Gym Pack (reodesuxz) and the Little Guys coaches (Unity Asset Store EULA). The human decided, quoted: "the repository wont be public ever, and if it ever will be, the asset files would not be shared publicly".
- **Impact:** These assets stay as they are; no CC0 replacement is needed. Shipping built apps with them is within their licences. If the repository is ever published, the restricted files (and the git history that contains them) must be left out first. The five old rep sounds still have no known source (CREDITS.md "Not yet recorded"); that matters for any public or commercial release.
- **Supersedes:** none

### DEC-021: First-Person Exercise View, Coach Window and Default Height
- **Status:** accepted
- **Date:** 2026-11-01
- **Reason:** The human asked to replace the third-person exercise with a first-person one: a holographic body part extending from the patient's body acts as the threshold, the coach becomes a still pose in a floating window with arrow and word guides, the yellow threshold shapes go, a tutorial comes first, and a default height removes the distortion caused by patients' different heights. The human also chose: limbs that end behind the patient get a side mirror panel and a chime; the coach stays in the room on menus and the summary; the tutorial plays every session and can be skipped.
- **Impact:** During a session the coach is drawn only by the window's own camera (it stays physically in the room, on a layer the main camera doesn't draw), holding the target pose without blinking or breathing. `FirstPersonGuide` draws a target limb and a live limb from one default body whose proportions are fixed, not the patient's. A headset hides the real arm, so the live limb is the patient's only view of it; it follows the tracker's single angle and always moves in the exercise's plane, so it can't show a limb moving out of that plane (posture checks still cover that). The view height depends only on the posture: 1.55 m standing, 1.15 m seated, lower lying down with a lift so the limbs can be seen; the headset is calibrated to it only at instant re-center moments (session start, Start pressed at get-ready, R / Y), keeping the rule that the game never moves the headset view on its own. Scoring is unchanged: the evaluator still uses the same angle, target and tolerance, and the hologram only shows them. Sessions' times start after the tutorial, and quitting during it saves nothing. On the laptop the view turns to the limb on its own, because the patient can't look around during an exercise. Guide Mode (Coach / Silhouette) is removed from Settings. M5.4's camera framing of the coach is replaced.
- **Supersedes:** the Silhouette guide mode of DEC-004 and the holographic target orb and tolerance halo of DEC-005 (the rest of both stands)

### DEC-022: Estimated Landmarks Are Never Measured or Scored
- **Status:** accepted
- **Date:** 2026-11-01
- **Reason:** The human asked for landmark persistence, smoothing and prediction, occlusion handling, reacquisition and tracking-loss safeguards, and stated that a preserved coordinate is an estimate, not a newly verified position, and must not be read as a correctly detected movement. The Section 3.9 metrics also depend on angles coming only from what the camera really saw (DEC-011).
- **Impact:** Each landmark has a trust state (`tracked`, `reacquiring`, `unreliable`, `predicted`, `lost`) in `tracker/tracking.py`. Only `tracked` landmarks reach the measured angles; any angle needing another one is -1, so Unity has no reading and pauses counting. Estimates travel only in the new `estL` / `estR` packet fields, drawn by the patient's live limb and nowhere else, and that limb shows orange then. Confidence is the lower of MediaPipe's visibility and presence. Trust returns only after 3 confident frames; a jump faster than is physically plausible is rejected unless several frames agree; an estimate lasts at most 0.5 s, then the landmark's history is dropped. During a gap the evaluator's hold timer stops and the rep's peak stays what was measured; a gap over 2 s drops the open rep without counting an attempt. A One Euro filter smooths verified landmarks, so measured angles are now filtered: the MAE evaluation (TASK-008) measures the filtered angle, which is what the game scores. All thresholds are starting values, not yet tuned on real footage. Posture checks stay lenient as before (a metric that can't be read never breaks a check), because the far shoulder and hip are often hidden in side view.
- **Supersedes:** none

### DEC-023: 3D World Landmarks for Facing Direction and the Out-of-Plane Live Limb
- **Status:** accepted
- **Date:** 2026-11-05
- **Reason:** The human started M6 (camera tracking mechanics) and chose, for the live limb, to show out-of-plane movement while keeping the default body and height. Side-view extension exercises have no reading whenever the nose and ears can't tell which way the patient faces (signed angle -999), and MediaPipe already gives 3D world landmarks that the tracker ignores.
- **Impact:** The tracker reads MediaPipe's world landmarks. They decide the facing direction first (the nose/ear test stays as the fallback), and they give a display-only out-of-plane angle for the first-person live limb. Scored angles stay the 2D angles of verified landmarks (DEC-022), so the Section 3.9 metrics are unchanged. DEC-021's fixed default body and per-posture height stay; only its "the live limb always moves in the exercise's plane" no longer holds once M6.4 is done. Packet fields are only added.
- **Supersedes:** none (amends DEC-021's live-limb sentence)
- **Amended 2026-11-07 (DEC-025):** the facing-direction part was not built: real recordings showed the nose/ear test already knows the facing direction in side view (3 of 1,756 side-on frames unknown). World landmarks are still recorded and stay planned for the out-of-plane live limb (M6.4) and the camera setup checks (M6.3).

### DEC-024: Tracking Recordings Hold Landmarks Only and Stay Local
- **Status:** accepted
- **Date:** 2026-11-05
- **Reason:** The human chose a record-and-replay tool so one webcam session can be used to tune and recheck the tracker offline. Video of a patient would be personal data under RA 10173 and is not needed for tuning.
- **Impact:** `tracker.py --record` saves landmark coordinates, confidences and timestamps per frame, never images. Recordings live in `tracker/recordings/`, which git ignores, and are named by date or patient code only, never by a real name. A recording replays through the same tracking and measuring code as the live camera.
- **Supersedes:** none

### DEC-025: Landmarks Are Trusted Again After 2 Confident Frames
- **Status:** accepted
- **Date:** 2026-11-07
- **Reason:** M6.2's real recordings showed that missing hip readings in side view came from the knee waiting to be trusted again, not from the facing direction. Replaying a whole-body recording with other settings: 3 frames (DEC-022's starting value) left the hip without a reading in 9.2% of side-on frames, 2 frames 7.1%, 1 frame 4.5%; confidence 0.4 instead of 0.5 gave 4.8-5.1%. Each easing also let more implausible hip angles through on a recording with the legs partly out of frame (76 with 3 frames, 96 with 2, 132 with 1). The human chose 2 frames.
- **Impact:** `REACQUIRE_FRAMES` in `tracker/tracking.py` is 2: a landmark seen confidently again is measured from its second frame in a row (about 50-70 ms at 30-40 fps). The confidence threshold stays 0.5 and every other DEC-022 rule stands. The hip signed reading is still missing in about 7% of side-on frames; the rest is handled in M6.5 with the other thresholds.
- **Supersedes:** DEC-022's "Trust returns only after 3 confident frames" (the rest of DEC-022 stands)

### DEC-026: Which Limb Is Measured, Resting Baseline and Rep Timing
- **Status:** accepted
- **Date:** 2026-11-12
- **Reason:** M6.5's live runs with the human: side-on the reading jumped between the near and the hidden far limb, the far leg's hamstring curl read about 10°, the tracker swapped left and right whenever the legs overlapped, slow reps were called too fast, and standing hip abduction never read 0 at rest. The human asked for a standing (resting) baseline for hip abduction and then for every exercise, and for only the moving limb to be tracked side-on.
- **Impact:** Tracker (`tracking.py`, `angles.py`): side-on the near limb is measured (world-landmark depth), unless the far one reads more than 35° above it; facing the camera the larger reading; otherwise the current side is kept unless the other is clearly better seen. Unity (`MotionInput`): with no operated side, side-on, an exercise moving one limb measures whichever limb reads the larger angle, whatever the tracker labels it; each webcam exercise waits for the patient to hold still for 1 s, takes that angle as resting (at most 60% of the target and 25°) and scores movement above it, refreshed whenever they rest again; a fall of over 25° within one frame is held up to 0.3 s. `ExerciseEvaluator`: a rep shorter than 0.35 s is dropped as noise, under 0.6 s is too fast. Scored angles still come only from verified landmarks (DEC-022); the baseline only subtracts the patient's own resting reading.
- **Supersedes:** none (the 0.85 s too-fast cutoff and the best-side-per-frame choice were starting values)

### DEC-027: Patient Records Hold Name and Code; Only the Code Leaves the Dashboard
- **Status:** accepted
- **Date:** 2026-11-12
- **Reason:** At the M7 kickoff (TASK-004) the human chose to keep each patient's real name together with their code, instead of code-only pseudonymization. The human approved the plan with the name meaning the patient's real name.
- **Impact:** The clinical database now holds personal information under RA 10173. The name is stored and shown only in the therapist dashboard. Everything that leaves the dashboard uses the code only: research exports (CSV/JSON), evaluation reports, VR client routes, logs and tracker recordings (M7.2). Database backups are encrypted (M7.3). Study participants must give informed consent for their name to be stored (a human and ethics task, not code). Local-first storage (DEC-003, DEC-010) and the private repository (DEC-020) are unchanged.
- **Supersedes:** the code-only pseudonymization part of DEC-003 (DEC-003 stays accepted for local-first storage)

### DEC-028: The Game Renders with URP
- **Status:** accepted
- **Date:** 2026-11-14
- **Reason:** At the M8 kickoff the human chose to switch the game from the Built-in render pipeline to the Universal Render Pipeline before the visual polish. `00_PROJECT.md` already names URP, the URP package was installed but unused, the Little Guys coach material is URP (DEC-018), and URP gives the lighting, shadows and post effects M8.2 and M8.4 need.
- **Impact:** M8.1 assigns one URP asset in Graphics and every Quality level, converts all materials, ports `Hologram.shader` to URP HLSL and removes the `Standard` material swap in `HumanoidCoach`. From then on no Built-in shader may be used in the game (EditMode test). The removed DEC-017 toon shader is not revived. VR comfort rules stay: no motion blur, vignette, chromatic aberration, film grain, depth of field or camera shake. The headset path under URP is untested until HW.2.
- **Supersedes:** none (the Built-in workaround noted under DEC-018 ends with M8.1)

### DEC-029: The Manuscript Master Is the Google Doc / Word File; the Repo Copy Is a Working Copy
- **Status:** superseded (by DEC-031, 2026-11-22: the hand-applied change-list workflow ended; its Section 3.9 and research-claim rules carry over)
- **Date:** 2026-11-16
- **Reason:** At the M9 kickoff the human said the capstone manuscript they submit lives in a Google Doc / Word file. `Research/THERAQUEST- MANUSCRIPT.md` is an export of it (9 October 2026) with the figures embedded as base64 image lines. The human also chose to leave Section 3.9 Data Analysis and all results and metrics out of M9, and to review edits by chapter.
- **Impact:** Agents edit only the repo `.md` and must deliver every edit as a per-chapter change list (`Research/M9-changes-chapter-N.md`: section, original text, new text, reason) so the human can apply it to the master by hand. New or corrected figures are delivered as image files plus a placement list; the base64 image lines in the `.md` are never edited or regenerated. Section 3.9 is not edited during M9; problems found there are only reported. Research aims, objectives, benchmark targets, participants and instruments change only with the human's yes. If the master has moved on since the export, the human re-exports before the audit (M9.1).
- **Supersedes:** none

### DEC-030: The VR Client Moves to the XR Interaction Toolkit, Controllers Only
- **Status:** accepted
- **Date:** 2026-11-17
- **Reason:** The human asked for a milestone on the Unity XR environment and the game's VR integration and had already added the XR Interaction Toolkit 3.6.1, XR Hands and Composition Layers packages to the project. Until now the game read `UnityEngine.XR` devices directly and used no toolkit ([[VRClinicExperience]]). Asked on 2026-11-17, the human chose controllers plus the XRI rig (no hand tracking) and chose to wait for a headset instead of building on the XR Device Simulator.
- **Impact:** M10 in [[50_ROADMAP]] replaces the hand-written rig, input reads and locomotion with an XR Origin, input actions, ray-pointed menus and XRI locomotion. Desktop fallback (DEC-002), the first-person view and default heights (DEC-021), the URP comfort ban list (DEC-028) and the invariants in [[VRClinicExperience]] stay in force. Hand tracking stays a future change; the XR Hands package is removed in M10.1 unless the human wants it kept, and Composition Layers stays only if M10.4 needs it. M10 does not start until a Meta Quest is available. HW.2 tests the M10 result.
- **Supersedes:** none (ends the "No XR Interaction Toolkit" note in [[VRClinicExperience]] once M10.1 is built)

### DEC-031: Manuscript Edits Go into the Word Draft as Tracked Changes
- **Status:** accepted
- **Date:** 2026-11-22
- **Reason:** On 2026-11-22 the human uploaded `Research/THERAQUEST- MANUSCRIPT DRAFT 2.2.docx` as the actual manuscript draft. It matched the original `.md` export except for three changes of the human's own (Objective 4c "System Usability (SUS)", the four theory headings renumbered 2.3.1 to 2.3.4, and five floating figures the export had lost), so none of the approved M9.2 edits had reached the master. Asked how to use it, the human chose to have every edit delivered as Word tracked changes in a copy of the docx.
- **Impact:** The newest numbered draft docx in `Research/` is the master. Agents never edit a draft in place: they write the edits with their sources to an edit list (`Research/M9-edits-draft-N.json`) and apply it with `Research/tools/redline.py` onto a copy, which becomes the next draft (Draft 2.3 holds all M9.2 edits and the M9.3 Chapter 1 sync). Every change is a tracked insertion or deletion by author "Claude"; the human accepts or rejects in Word. Checks before handing over: the docx skill's `validate.py --author Claude`, the reject view equals the previous draft, and the content hashes from `redline.py guard` (Section 3.9 text and equations, the images in order, the media set) are unchanged. Byte hashes are not used because Word rewrites the whole XML whenever it saves. The per-chapter change lists stay as the record with sources; the `.md` is frozen as a reference and no longer edited. Kept from DEC-029: Section 3.9 is not edited in M9, and research aims, objectives, benchmarks, participants, instruments, ethics wording and dates change only with the human's yes. Formatting fixes and the contents refresh are done through Word itself (COM, Track Changes on); Word records them under the signed-in Office account, so their author is reset to Claude in the XML afterwards.
- **Supersedes:** DEC-029
