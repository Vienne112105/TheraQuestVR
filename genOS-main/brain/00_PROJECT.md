# Project

Authoritative file for project intent. See `AGENTS.md` → Ownership.

**Ownership:** Humans own vision and intent. AI may reorganize, summarize, clarify, and maintain this document. AI must never change intent without explicit human approval.

---

## Vision

TheraQuest VR is a gamified virtual reality physical therapy and telerehabilitation system developed at Caraga State University (CCIS) that integrates single-webcam computer vision motion tracking with real-time adherence monitoring. The system addresses the persistent challenge of low patient adherence and unsupervised home exercise error by transforming orthopedic rehabilitation into an engaging, quantified, and clinically validated VR experience. By tracking joint kinematics without wearable sensors, evaluating posture alignment in real time, and monitoring adherence through an integrated therapist dashboard, TheraQuest VR provides accessible, motivating, and safe physical therapy support.

## Research Goal & Institutional Context

- **Academic Context:** Bachelor of Science in Information Technology (BSIT) Capstone Research, Caraga State University – Main Campus, CCIS (April 2026).
- **Institutional Alignment:** Aligned with CSU's LIKHA Summit agenda ("Innovating for a Sustainable Future: Research, Development, Innovation, and Extension in Practice") and United Nations Sustainable Development Goals:
  - **SDG 3:** Good Health and Well-Being (improving recovery adherence and physical function)
  - **SDG 4:** Quality Education (translating academic computer science into healthcare solutions)
  - **SDG 9:** Industry, Innovation and Infrastructure (advancing digital health and VR rehabilitation)
- **Primary Research Aim:** Design, develop, and evaluate an integrated system combining immersive VR (Unity 6 / Quest Link), markerless computer vision motion tracking (MediaPipe Pose / OpenCV), gamification (Flow Theory, COM-B model, self-determination theory), and adherence monitoring to demonstrate quantifiable improvements in exercise accuracy and patient compliance compared to conventional unmonitored home therapy.

## Scope

### In Scope
1. **Markerless Motion Tracking:** Real-time 2D joint angle estimation via MediaPipe Pose (33 body landmarks) streaming over UDP port 5005 to Unity at ~30 FPS.
2. **Immersive Rehabilitation Client:** Unity 6 Universal 3D VR environment accessible via Meta Quest (Quest Link / OpenXR) with automated fallback to desktop mode.
3. **Kinematic Evaluation & Safety Engine:** Repetition counting state machine, target ROM accuracy scoring, compensatory posture rejection (trunk lean > 12°/35°, limb abduction > 30°), hold duration timing, and safety maximum angle alerts.
4. **Gamification & Feedback Intervention:** Real-time audio-visual feedback (power meter gauge, star targets, audio chimes), combo multipliers, achievement badges, player XP leveling, and accessibility closed-caption subtitles.
5. **Clinical Protocol Management & Adherence Dashboard:** Python REST API service (`server.py`) and a therapist desktop app (`Start_Therapist_App.bat` → `app.py`, which runs the local server and shows `dashboard.html` in a native WebView2 window; an Edge app window is the fallback) providing prescription editing, adherence calendar logs, pain/soreness/swelling clinical notes, and automated phase progression evaluation (OHSU Knee and MGB Rotator Cuff protocols).
6. **Academic Evaluation Pipeline:** Data export and statistical tools measuring confusion matrix classification metrics (Accuracy, Precision, Recall, F1), Mean Absolute Angle Error (MAE), Euclidean coordinate deviation, and System Usability Scale (SUS) scores.

### Out of Scope & Limitations
1. **Passive and Non-Planar Movements:** Acute passive-only mobilization, isometric quad sets, and non-planar axial joint rotations are designated as off-camera protocol exercises (untracked in VR).
2. **Standalone Quest APK:** Runtime relies on tethered PC VR (Quest Link) or laptop desktop fallback to enable concurrent execution of the Python MediaPipe tracker and SQLite backend on the host machine.
3. **Diagnostic Replacement:** System is strictly an assistive rehabilitation support tool and does not diagnose injuries or replace clinical supervision by a licensed physical therapist.
4. **Local Data Privacy:** Strictly clinic-local data storage under the Philippine Data Privacy Act of 2012 (RA 10173). Each patient has a code (e.g. `P-001`) and a real name; the name stays inside the therapist dashboard, and everything that leaves it (exports, reports, the VR client, logs, recordings) uses the code only. Backups are encrypted, and study participants consent to their name being stored (DEC-027, approved by the human 2026-11-12).

## Target Environment & Stack

- **VR & Desktop Client:** Unity 6 LTS (Universal Render Pipeline / Universal 3D), OpenXR plugin, Meta Quest Link runtime, Windows 10/11.
- **Motion Tracking Service:** Python 3.11 / 3.12, MediaPipe Pose, OpenCV, NumPy, UDP Socket broadcasting (Port 5005).
- **Clinical Backend Service:** Python standard HTTP REST service (`http.server`), SQLite 3 (`theraquest.db`, Port 8000).
- **Therapist Dashboard:** Windows desktop app (pywebview / WebView2 window, minimum 980 × 640) showing a single-page HTML5, CSS3, Vanilla JavaScript UI with charting components, served by the local server on port 8000. Not a website: it is not meant to be opened in a browser or used on phones.

## Core User Workflow / Domain Loop

1. **Prescription & Protocol Assignment:** Physical therapist selects an evidence-based clinical protocol (OHSU Total Knee or MGB Rotator Cuff) and customizes target ROM angles, tolerances, sets, reps, and safety maxes in the therapist desktop app (`Start_Therapist_App.bat`).
2. **Session Initialization:** Patient launches the motion tracker (`tracker.py`) and Unity VR application. Unity fetches the patient's active prescription via HTTP REST.
3. **Setup & Guided Positioning:** Unity plays a short tutorial, presents camera setup instructions (frontal vs sagittal view), and shows the humanoid coach avatar holding the target pose in a floating window with arrow and word guides (DEC-021).
4. **Active Exercise Execution:**
   - In first person, from a default eye height, the patient moves their limb into a holographic target limb that extends from their body (DEC-021); webcam captures pose landmarks and streams joint angles over UDP.
   - Evaluator evaluates joint kinematics against target ROM: posture heuristics invalidate cheat reps, safety limits trigger red STOP alerts, and valid reps are counted.
   - Gamification engine triggers real-time chime feedback, combo streaks, and power meter visual cues.
5. **Session Upload & Clinical Review:** Upon session conclusion, Unity uploads full performance records (accuracy %, rep count, angle error, unsafe reps) to SQLite. The therapist inspects adherence calendars, enters clinical notes (pain 0-10, soreness, swelling), and reviews stage progression recommendations ("Ready for Phase II?").

## Constraints

- **Orthogonal Camera Alignment:** Webcam must be placed 2–3 meters away, perpendicular to the movement plane (frontal for abduction, sagittal for flexion/extension).
- **Active Exercise Clearance:** Patient must be cleared by a physician for active range of motion (AROM).
- **Lighting & Space:** Minimum 2x2 meter clear physical space with unobstructed ambient lighting (no backlit windows).

## Success Criteria & Benchmark Standards (Manuscript Section 3.9)

1. **Motion Tracking Classification (Confusion Matrix):**
   - **Classification Accuracy:** $\ge 85\%$
   - **Precision:** $\ge 80\%$
   - **Recall:** $\ge 80\%$
   - **F1-Score:** $\ge 80\%$
2. **Kinematic Angle Error:** Mean Absolute Error (MAE) within clinical goniometric tolerance ($\le 10^\circ$).
3. **System Usability Scale (SUS):** Mean score $> 68$ (Grade B / Acceptable benchmark).
4. **Clinical Adherence & Expert Acceptance:** Validated functionality and clinical relevance confirmed through formal evaluation with licensed physical therapists.
