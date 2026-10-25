# TherapistDashboard

## Purpose
Delivers a web browser interface for physical therapists to monitor patient adherence, customize exercise prescriptions, record clinical progress notes, and approve protocol stage advancements.

## Status
`in-progress` (M5.1, M5.2, M5.3 and M5.7 are TBF, waiting on the human checks in the desktop app)

## Responsibilities
- Serve as a formal clinical Rehabilitation Monitoring & Prescription System (RMS) designed specifically for Physical Therapists.
- Enforce Clinician Authentication with a dedicated in-app login view (`#viewLogin`), first-run login creation (`#setupForm`), password change (`#passwordModal`, forced after a demo-password sign-in), bearer token persistence in localStorage, and clean sign-out.
- Provide a Patient Caseload Directory for managing enrolled patients, diagnosis filtering, and quick chart access; archived patients are hidden unless "Show archived patients" is ticked.
- Patient chart actions (M5.2): Edit Details (name and condition; the code is fixed) and Archive / Reactivate with a confirmation and an "Archived on …" notice (DEC-014).
- Attention flags (M5.3): the caseload shows flag chips per patient and sorts "Needs attention first" by default; the chart shows a "Needs attention" notice with each reason and the input sources it counted, and the Clinical Status box is driven by the server's flags (no client-side pain rule).
- Protocol Phase Editor (M5.2): edit or add phases, criteria and VR exercises of therapist-authored protocols; built-in protocols show a read-only note.
- Show adherence (rate and completed/scheduled sessions). The server also sends a 14-day calendar with Complete / Incomplete / Missed statuses, phase history and per-exercise stats; the page does not show them yet (left out of M5 by the human; see TASK-001 for the export buttons).
- Provide an interactive prescription editor and customized Add Movement modal (`#addExerciseModal`) allowing therapists to modify targets, tolerance, repetitions, sets, limb sides, and rest times prior to prescribing.
- Feature a compressed Protocol Library catalog that displays protocol names and opens a dedicated Phase Inspector widget (`#protocolPhasesWidget`) detailing phases, timelines, clinical goals, precautions, ROM milestones, and exercises with quick-apply controls.
- Visualize session performance logs with per-exercise accuracy scores and dual-axis Chart.js progression charts with in-place data updates.
- Eradicate native browser popups (`confirm()`, `alert()`) in favor of in-app HTML modals (`#confirmModal`, `#noteModal`, `#newPatModal`) and floating toasts (`#toastContainer`).
- Provide clinical assessment input modal for therapists to record pre/post session pain ratings (0–10 VAS), soreness duration (<2h vs >2h), and joint swelling changes (cm).
- Highlight protocol stage progression readiness indicators ("Ready for Phase II?") and facilitate one-click approval workflows.
- Deliver a formal, clean, hospital-grade Light Mode interface with zero patient gamification elements (no XP, levels, coins, or stars) centered around therapist decision-making.
- Accessibility (M5.1): keyboard-reachable navigation and tabs (`tablist`/`tab` roles, arrow keys), dialogs with `aria-modal`, Escape to close, focus trap and focus return, labelled form fields, status shown with text or icons and not by colour alone, inline error / empty / loading states with Retry, and a layout that fits the app window from its minimum size (980 × 640) up.
- Session History shows date and time and pages in steps of 50 ("Show older sessions", `?sessions=` on the dashboard endpoint).

## Dependencies
- Inter-system: Relies on `ClinicalBackend` for REST endpoints and data persistence.
- Frontend Libraries: Local offline vendor stack in `/static/vendor/` (`chart.umd.min.js` 4.5.1, `lucide.min.js` 1.59.0); the CDN fallback is pinned to the same versions. Tailwind and Google Fonts were removed in M5.1 (system font stack); `static/vendor/tailwind.min.js` is unused.

## Runtime References
- `Main/TheraQuestVR/server/app.py`: Standalone native desktop application runner using Windows WebView2.
- `Main/TheraQuestVR/server/dashboard.html`: Single-page responsive HTML5/CSS/JavaScript dashboard featuring a tabbed clinical command center.
- `Start_Therapist_App.bat`: One-click Windows desktop application launcher.

## Invariants
- Only exercises cleared for single-camera active tracking are surfaced for VR prescription; off-camera protocol exercises are cataloged separately under "Without camera".
- Clinical note entries must be timestamped and permanently associated with patient session records.
- Preserves full zero-dependency vanilla JS architecture served directly by `server.py` at `http://localhost:8000`.
- All user-facing dialogues must be in-app HTML modals; no native browser `alert()` or `confirm()` calls are permitted.
- Dialogs open and close only through `openDialog()` / `closeDialog()`, and each dialog has an entry in `DIALOG_CLOSERS` so Escape works.
- Colours come from the `:root` tokens (script-drawn colours via `cssVar()`); no external fonts and no unpinned CDN URLs.
- Every value from the API placed into HTML goes through `esc()` (which also escapes `'`); record names are never interpolated into inline `onclick` strings — handlers look records up by id.

## Notes
- Delivered as a desktop app, not a website (DEC-013). Runs as a native desktop application via `app.py` (powered by Windows WebView2, eliminating browser address bars/tabs). Strict clinical light mode with clean CSS utility classes and debounced icon rendering.

## Future Changes
- Comparative chart overlays showing patient progress against normative cohort recovery curves.
- Multi-clinician caseload filtering and clinic-level administrative reports.
