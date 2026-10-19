# TherapistDashboard

## Purpose
Delivers a web browser interface for physical therapists to monitor patient adherence, customize exercise prescriptions, record clinical progress notes, and approve protocol stage advancements.

## Status
`stable`

## Responsibilities
- Serve as a formal clinical Rehabilitation Monitoring & Prescription System (RMS) designed specifically for Physical Therapists.
- Enforce Clinician Authentication with a dedicated in-app login view (`#viewLogin`), credential validation, bearer token persistence in localStorage, and clean sign-out.
- Provide a Patient Caseload Directory for managing enrolled patients, diagnosis filtering, and quick chart access.
- Display patient adherence calendar with clinical statuses: Complete, Incomplete, and Missed sessions.
- Provide an interactive prescription editor and customized Add Movement modal (`#addExerciseModal`) allowing therapists to modify targets, tolerance, repetitions, sets, limb sides, and rest times prior to prescribing.
- Feature a compressed Protocol Library catalog that displays protocol names and opens a dedicated Phase Inspector widget (`#protocolPhasesWidget`) detailing phases, timelines, clinical goals, precautions, ROM milestones, and exercises with quick-apply controls.
- Visualize session performance logs with per-exercise accuracy scores and dual-axis Chart.js progression charts with in-place data updates.
- Eradicate native browser popups (`confirm()`, `alert()`) in favor of in-app HTML modals (`#confirmModal`, `#noteModal`, `#newPatModal`) and floating toasts (`#toastContainer`).
- Provide clinical assessment input modal for therapists to record pre/post session pain ratings (0–10 VAS), soreness duration (<2h vs >2h), and joint swelling changes (cm).
- Highlight protocol stage progression readiness indicators ("Ready for Phase II?") and facilitate one-click approval workflows.
- Deliver a formal, clean, hospital-grade Light Mode interface with zero patient gamification elements (no XP, levels, coins, or stars) centered around therapist decision-making.
- Implement ARIA accessibility standards (`role="dialog"`, `aria-modal="true"`, `role="status"`, `aria-live="polite"`).

## Dependencies
- Inter-system: Relies on `ClinicalBackend` for REST endpoints and data persistence.
- Frontend Libraries: Local offline vendor stack in `/static/vendor/` (`chart.umd.min.js`, `lucide.min.js`, `tailwind.min.js`) with automatic CDN fallback.

## Runtime References
- `Main/TheraQuestVR/server/app.py`: Standalone native desktop application runner using Windows WebView2.
- `Main/TheraQuestVR/server/dashboard.html`: Single-page responsive HTML5/CSS/JavaScript dashboard featuring a tabbed clinical command center.
- `Start_Therapist_App.bat`: One-click Windows desktop application launcher.

## Invariants
- Only exercises cleared for single-camera active tracking are surfaced for VR prescription; off-camera protocol exercises are cataloged separately under "Without camera".
- Clinical note entries must be timestamped and permanently associated with patient session records.
- Preserves full zero-dependency vanilla JS architecture served directly by `server.py` at `http://localhost:8000`.
- All user-facing dialogues must be in-app HTML modals; no native browser `alert()` or `confirm()` calls are permitted.

## Notes
- Runs as a native desktop application via `app.py` (powered by Windows WebView2, eliminating browser address bars/tabs). Strict clinical light mode with clean CSS utility classes and debounced icon rendering.

## Future Changes
- Comparative chart overlays showing patient progress against normative cohort recovery curves.
- Multi-clinician caseload filtering and clinic-level administrative reports.
