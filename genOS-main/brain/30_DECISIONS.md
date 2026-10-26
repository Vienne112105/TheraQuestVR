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
