# M9.1 — Manuscript Audit, second run

- **File audited:** `Research/THERAQUEST- MANUSCRIPT DRAFT 2.3.docx`, accept-all-changes view (`redline.py text --view accept`). Draft 2.4 was not used (the plan for it, Chapter 2 and 3 system wording, is still open).
- **Date:** 2026-11-25. **Nothing in the manuscript was edited.**
- **Read in full:** front matter, Chapters 1 and 2, Chapter 3 (3.1 to 3.8, 3.10) and the contents lists. **Section 3.9 was not audited** (out of scope, DEC-031); it is touched only under "Reported only". The reference list was checked only for the Schmidt and Lee entry.
- **Checked against:** the brain (`VRClinicExperience`, `ClinicalBackend`, `TherapistDashboard`, `Gamification`, DEC-021 to DEC-031), `server/schema.sql`, `server/server.py` (`day_statuses`) and the first audit `Research/M9-audit.md` with your answers D1 to D15.
- **How to find a place:** search the quoted words in Draft 2.3.
- **Method:** each item is either (a) an item from the first audit that Draft 2.3 did **not** fix yet (status OPEN), (b) something Draft 2.3 introduced or left, or (c) NEW since the first audit (the built system changed in M8 and M10). Items are labelled with the same problem types as before: SYS (does not match the built system), STR, LANG, CITE, FIG, DEC (needs your decision first).

**Result in one line:** Chapter 1 now matches the system. Chapter 2 has 5 items (2 are the planned D4 and D8 wording). Chapter 3 has 24; most are the planned Part D wording (D3, D4, D5, D7, D8, D10, D11, D15) not yet applied to Draft 2.3, plus the new ones from M8 and M10 and from the database growth.

---

## Chapter 1

No SYS items. Draft 2.3 already carries the D4 headset wording, D5 webcam wording, D6 softened aims, D7 adherence wording (Scope 4, 1.6), D14 SUS-only and the patient-code definition.

| ID | Section | Quoted text | Type | Problem and proposed action |
|----|---------|-------------|------|-----------------------------|
| N1-1 | 1.1 | "recent evidence indicating that only about 43% of patients fully adhere" | CITE | Number comes from Shahidi et al. (2022); not re-verified against the paper in this run. Check once before submission. |
| N1-2 | 1.5 Scope 6, 1.5 Limitations "Sample Size", 1.3 | "will" wording for the evaluation | DEC | Correct under D1 (the evaluation has not happened). If the evaluation is finished before submission this changes to past tense. Keep until you tell me. |
| N1-3 | Front page | "April 2026" | DEC | D3 still open: real dates not supplied. The system work now runs to November 2026, so April 2026 contradicts 3.4.1. |

## Chapter 2

| ID | Section | Quoted text | Type | Problem and proposed action |
|----|---------|-------------|------|-----------------------------|
| N2-1 | 2.2.5, paragraph 3 | "Modern system architectures increasingly shift toward standalone HMD units (such as Meta Quest)… complex configurations requiring multi-camera calibration or tethered cabling create technical barriers" | SYS | OPEN (C2-14, D4). The built system is tethered over Quest Link with a desktop fallback, so the chapter argues against its own setup. Add the one sentence agreed in D4 (the PC runs the tracker and the database). The wording is already in `M9-changes-chapter-2.md` Part D. |
| N2-2 | 2.3 opening and 2.3.3 Flow Theory | "immersive and adaptive activities"; "adaptive difficulty levels, the system aims to maintain an optimal balance" | SYS | OPEN (C2-21, D8). The system does not adjust difficulty by itself: it recommends the next phase and the therapist approves. Rewards are XP levels, badges, stars and combo streaks. |
| N2-3 | 2.2.5, paragraph 4 | "adaptive difficulty scaling, and instant corrective prompts" | SYS | NEW. Written as a general literature claim, but a reader will read it as a feature of TheraQuest VR. Reword to "range-of-motion validation and instant corrective prompts", or add "in the reviewed systems". |
| N2-4 | 2.3.1 and reference list | "(Schmidt & Lee, 2011)" in the text and on Figure 2.3.1 | CITE | The reference list has Schmidt, Lee, Winstein, Wulf and Zelaznik (2018, 6th ed.). Year mismatch, flagged in the first audit (R6) and still there. You decide which edition you used; I will not change it alone. |
| N2-5 | Table 1 | Row "Navea et al. (2025a)" | CITE | The "a" suffix remains although 2025b was removed (D12). Drop the "a", or keep both only if both references exist. |

## Chapter 3 (3.1 to 3.8 and 3.10; 3.9 skipped)

| ID | Section | Quoted text | Type | Problem and proposed action |
|----|---------|-------------|------|-----------------------------|
| N3-1 | 3.3 Initial Planning; 3.3 Deployment | "standalone VR HMDs"; "target standalone VR hardware" | SYS | OPEN (D4). Change to a headset tethered over Quest Link plus the PC, with desktop mode when no headset is connected. |
| N3-2 | 3.3 Requirements; 3.4.1 March | "pose classification" | SYS | OPEN (D15). The tracker does not classify the exercise; the prescription names it and each repetition is judged correct or incorrect. Replace with "joint angle measurement" or "repetition classification". |
| N3-3 | 3.4.1 | "In September (Evaluation Phase), the working system is assessed… Finally, in October–November (Deployment Phase)" | DEC | OPEN (D3). Present tense and planned dates next to past-tense phases. Needs the real dates. Also the Gantt figure 3.4.1.1 (M9.4). |
| N3-4 | 3.4.2 Functional Requirements, adherence | "This focuses on session completion rather than long-term behavioral tracking or frequency analysis." | SYS | OPEN (D7). The dashboard shows a 14-day adherence calendar with six day states (Done, Partly, Missed, To do, Rest, Before enrolment), an adherence percentage and attention flags. State this instead. |
| N3-5 | 3.6.3 Adherence Monitoring Module, last paragraph | "does not analyze long-term behavioral patterns" and "Status Classifier… complete, incomplete, or missed" | SYS | OPEN (D7). Same fix. The statuses in the database are complete, incomplete and missed (`adherence_record.status`); the calendar adds day states. Both belong in the paragraph. |
| N3-6 | 3.5.1 and 3.6.1 | "user authentication"; "Log In step… determines whether the user is a Patient or a Physical Therapist" | SYS | OPEN (D11). Built: the therapist signs in with a password in the desktop app; the patient's game loads the program by patient code on the same PC (loopback only). Also the use case diagram 3.5.1.1 and flowchart 3.6.1.1 (M9.4). |
| N3-7 | 3.5.2 ERD text | Seven entities: Physical Therapist, Patient, Rehabilitation Program, Exercise, Session, Adherence Record, Performance Record | SYS | NEW. `schema.sql` now also has protocol, protocol_phase, phase_exercise, phase_history, rep_event, patient_badge, therapist login sessions, and the patient table keeps name, code, archive date and protocol phase. Decide how much to add (D9 rule: one or two sentences where the text is silent or wrong). Minimum: a sentence saying the figure shows the core entities and the built database adds protocols with phases, rep-level events and badges. Redraw is M9.4. |
| N3-8 | 3.5.2 ERD, Exercise entity | "references its parent program through the program_id foreign key… one-to-many relationship with the Rehabilitation Program" | SYS | NEW. In the built database exercises are prescribed through protocol phases (`phase_exercise`); program-to-exercise is no longer a plain parent link. Fix together with N3-7. |
| N3-9 | 3.5.2 ERD, Performance Record | "many-to-many bridge between the Session and Exercise entities" | LANG | NEW. A one-to-many link from each side is described, not a many-to-many in the usual sense; the sentence is confusing. Reword. |
| N3-10 | 3.6.3 VR Environment Module, paragraph 1 | "physical gestures and head movements from the patient"; "hand movements, head orientation, and positional data… forwards these to the motion tracking pipeline" | SYS | NEW (changed by M10). The game reads the headset pose and Quest controllers only; there is no hand tracking (DEC-030). The headset and controller data are not sent to the tracker: the tracker reads the external webcam and sends joint angles to the game over UDP. Reword: controllers and headset drive menus, the view and re-centering; body movement comes from the webcam. |
| N3-11 | 3.6.3 Motion Tracking Module | "camera sensors such as built-in VR cameras or external webcams, positional data from VR tracking hardware including controllers and headset orientation, and raw video frames" | SYS | OPEN (D5). Built: one external webcam, no VR cameras, no controller input. Remove the second source and the VR cameras. |
| N3-12 | 3.6.3 Motion Tracking Module | "The Frame Preprocessor normalizes and denoises each incoming video frame" | SYS | NEW. The tracker resizes a copy of the frame for detection and smooths landmarks over time (One Euro filter, Kalman prediction for short gaps); it does not denoise images. The five-stage list should name the real steps: capture, pose estimation, landmark smoothing and loss handling, joint angle calculation, packaging. Check against `tracker/` before editing. |
| N3-13 | 3.6.3 Motion Tracking Module | "The Movement Classifier compares the detected gesture patterns against known exercise types to determine which movement the patient is currently performing." | SYS | OPEN (D15). Remove; the exercise comes from the prescription. |
| N3-14 | 3.6.3 Gamification Module | "Progression Controller manages the advancement of rehabilitation difficulty… adjusting the level or complexity"; "next-level trigger that advances the exercise difficulty when performance thresholds are met" | SYS | OPEN (D8). Built: XP and levels, badges, stars, combo streaks; the system recommends the next phase and the therapist approves. |
| N3-15 | 3.6.3 Feedback Generation Module | "voice instructions"; "corrective guidance text that is also logged to the performance database" | SYS | NEW. Feedback is visual (target limb, coach window, arrow, word cues), sounds and subtitles, not voice instructions; check what is stored per repetition (`rep_event`) before keeping "corrective guidance text logged". |
| N3-16 | 3.7.1 Hardware | "camera sensors… built-in VR tracking cameras or external webcams" | SYS | OPEN (D5). Same as N3-11. Also add that the computer runs the tracker, the game and the therapist app together. |
| N3-17 | 3.7.1 Software | "OpenCV or MediaPipe, or any similar libraries… pose estimation and gesture recognition" | SYS | NEW. Built: MediaPipe Pose and OpenCV; no gesture recognition. Name the actual libraries and drop "gesture recognition". |
| N3-18 | 3.7.2 Class Diagram | `VRSystem`, `PhysicalTherapist`, `PerformanceRecord`, `AdherenceRecord` classes | FIG | OPEN (D13, M9.4). Redraw against the built code; text follows the figure. |
| N3-19 | 3.7.3 System Testing | Only manual testing described | SYS | NEW. The build has automated suites (server, authorization, tracker, evaluation, Unity EditMode, record and replay of landmarks). Add two sentences (D9 rule: only because the current text is silent about the main testing method). No numbers unless you want them. |
| N3-20 | 3.8.3 Research Instrument, Motion Tracking Accuracy | "expected and detected joint coordinates" | SYS | NEW. The system records joint angles and per-repetition events, not coordinates. Section 3.9 uses the same wording (Euclidean distance error): you decide that separately. |
| N3-21 | 3.8.3 | Two separate headings "Evaluation Statements for Physical Therapists" and "Expert Evaluation of System Outputs" | STR | NEW. Same instrument described twice. Merge, or say the second is the review procedure and the first is the form. |
| N3-22 | 3.10 Ethical Considerations | "Participant identities are anonymized in all reports and publications"; "securely stored" | SYS | OPEN (D10). Built: names are stored locally with consent; only the patient code leaves the dashboard (exports, reports, the game); backups are encrypted; the data stays on the clinic PC (RA 10173). Wording to be proposed for your yes. |
| N3-23 | 3.2 item 8 | "Improved exercise accuracy… More effective rehabilitation outcomes" listed as outcomes | DEC | NEW. These are expected effects the study does not measure (no comparison group, D6). Prefix with "Expected outcomes" or remove the last one. Research claim: your yes first. |
| N3-24 | 3.6.2 and 3.6.3 module figures | Figures 3.6.2.1, 3.6.3.1 to 3.6.3.6 | FIG | OPEN (D13, M9.4). The six module figures and the architecture figure need the same corrections as N3-10 to N3-15. |

## From the Gemini alignment notes (added 2026-11-25)

Source: `3 Quick Alignment Notes for Manuscript _ Defense by Gemini AI.docx` (Downloads). Each point was checked against Draft 2.3, `schema.sql`, `LIBRARY` in `server.py` and `evaluation/evaluate_clinical_metrics.py`. IDs start with G.

| ID | Section | Quoted text | Type | Problem and proposed action |
|----|---------|-------------|------|-----------------------------|
| G-1 | 1.5 Limitations "Scope of Clinical Application"; 3.8.2 | "Orthopedic Physical Therapy"; "5 to 10 physical therapy patients" | DEC | The clinical stage of the patients is not stated (early passive-only, active range of motion, late strengthening). Gemini suggests outpatient or subacute patients cleared for active, low-to-moderate-load exercise. This is a research-scope claim: I will not write a stage without your yes. |
| G-2 | 1.5 Scope or 3.6.3 | No list of exercises | DEC | The prototype exercises are not listed. `LIBRARY` holds 28 exercises (shoulder, elbow, hip, knee, ankle), each with a posture and a front or side camera plane. Options: none, a short grouped sentence (D9 rule), or a table of exercise, posture, tracked joint and camera plane. A table goes beyond D9, so your yes first. |
| G-3 | 1.5 Limitations, 3.10, 3.7.1 | No sentence on cable and fall safety with an occluding headset | SYS | Raised for a panel question. The built game has safe-limit STOP warnings, a tracking-loss pause, seated and supported exercise options and a headset-off pause. The manuscript is silent. Proposed: one or two sentences in 1.5 or 3.10 naming these. Check wording against `ExerciseEvaluation` and `VRClinicExperience` before editing. |
| G-4 | 3.6.3 Figure 3.6.3.6 (image) vs 3.6.3 text and 3.8.3 | Figure labels "Complete, partial, or missed"; text says "complete, incomplete, or missed" | FIG | Could not read the figure text (an image), so this is the human's report, not verified. Database and prose use incomplete; the dashboard calendar says "Partly". Choose one word everywhere, define the boundary of each state in one sentence, and fix the figure in M9.4. Related to N3-5. |
| G-5 | 3.5.2 ERD text; Figures 3.5.2.1 and 3.7.2.1 | Patient entity lists "name, age, and gender" and no patient code | SYS | Confirmed: the database field is `patient.code` (for example P-001), the only identifier that leaves the dashboard (DEC-027); the table has no age or gender column (it has name, condition, XP, phase, archive date). Add the code to the text and both figures, say in 3.10 that names stay on the therapist PC, and drop age and gender unless you add them. Merge with N3-7 and N3-22. |
| G-6 | 3.10 first sentence | "to protect the rights, safety, and well-being of all participants." | LANG | Confirmed: the paragraph has no subject (also C3-60 from the first audit). Gemini's example opening: "Ethical guidelines are strictly observed throughout this study to protect…". Needs your yes because it is ethics text. |

## Reported only from the Gemini notes (Section 3.9, not changed)

| ID | Section | Point | Check |
|----|---------|-------|-------|
| G-R1 | 3.9.1 and Table 3 | The 3D Euclidean distance formula needs a z value and a common coordinate space, but the system measures 2D joint angles from one webcam; Table 3 gives no number or unit. | Confirmed. `evaluate_clinical_metrics.py` marks the measure "not measured: needs 3D reference joint positions, which this single-webcam study does not collect", so the method text describes something the study's own tooling cannot do. Gemini's Option A (2D distance on normalized landmarks, with angle error) matches the system; its Option B (MediaPipe world landmarks) is weaker because z is estimated, not measured, and no 3D reference exists. Your call; D5 left 3.9 alone. |
| G-R2 | 3.9.1 equations | In the pasted text the root sign, squares and the absolute-value bars on Angle Error were lost. | Not checked here (equations were out of scope). Please look at them in Word. |
| G-R3 | Heading 3.9.4 | "3.9. 4Expert Evaluation of System Outputs" spacing typo. | Confirmed in Draft 2.3. |
| G-R4 | Table 6 (3.9.2) | The sentence "The Evaluation of Statements shall be evaluated similarly to…" could point to Tables 4 and 5. | Not re-read. |

New questions from this section:

| ID | Question |
|----|----------|
| Q5 | G-1: which patient stage should the manuscript state? I cannot choose it for you. |
| Q6 | G-2: list the exercises as one grouped sentence (**recommended**), a table, or not at all? |
| Q7 | G-3: add one or two sentences on the safety features (**recommended**)? |
| Q8 | G-R1: keep the 3D formula, or change 3.9.1 to the 2D version? |

## Decisions that are still open from the first audit

- **D3** (real dates and the title-page date): blocks N1-3, N3-3 and the Gantt figure.
- **D10 and D11** wording: proposed in `M9-changes-chapter-3.md` Part D, waiting for your yes.

## New questions for you

| ID | Question |
|----|----------|
| Q1 | N3-7 and N3-8: how much of the new database to describe? **Recommended:** one sentence under the ERD text plus the redrawn figure in M9.4. |
| Q2 | N3-19: add two sentences on automated testing and landmark replay? **Recommended:** yes, no numbers. |
| Q3 | N2-4: which Schmidt and Lee edition did you read (2011 or 2018)? |
| Q4 | N3-23: soften the outcomes list to "expected outcomes"? **Recommended:** yes. |

## Reported only (not audited, out of scope)

- 3.9 still says "observation checklist results" and "user feedback questionnaires", instruments 3.8.3 does not describe (reported in the first audit; D14 covered 3.1 to 3.8 only).
- 3.9.1 uses Euclidean distance error in coordinates; the system measures 2D joint angles (D5 left 3.9 alone).
- The List of Tables lists Tables 2 to 9, all in 3.9; unchanged by design.

## Counts

38 items: Chapter 1 has 3 (DEC or CITE, none SYS), Chapter 2 has 5, Chapter 3 has 24 and the Gemini notes add 6 (G-1 to G-6); 4 more points in Section 3.9 are reported only (G-R1 to G-R4). Items marked OPEN come from the first audit and were not fixed in Draft 2.3; the others are new or were left by Draft 2.3.
