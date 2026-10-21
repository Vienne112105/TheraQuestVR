# SessionOrchestration

## Purpose
Coordinates the patient workout lifecycle: patient profile selection, prescription retrieval, exercise sequencing, inter-set rest intervals, camera guidance, and HTTP session data upload.

## Status
`stable`

## Responsibilities
- Manage the rehabilitation session state machine: Idle -> Prescription Fetch -> Exercise Intro & Camera Placement -> Countdown -> Active Sets -> Rest Countdowns -> Exercise Completion -> Session Upload.
- Fetch patient prescription from the clinical backend over HTTP, identified by the configured synthetic patient code (no clinician credentials; see [[30_DECISIONS]] DEC-009).
- Cache completed session metrics locally if the network/server is offline, with automated retry when reconnected; every upload carries a `session_uuid` so retries are never counted twice.
- Resolve the patient code and server URL from the command line (`-patient`, `-server`), `config.json` in the persistent data folder, or the Inspector; a PIN-protected therapist page in the main menu changes the patient code, input source and therapist numbers (M4.3).
- Cache the last server-issued program per patient and use it when the server is unreachable; with no cached program, no session starts. Caches from before the exercise rules (cache schema 1) are ignored.
- Present pause/resume menu (triggered by Esc or Quest B button) allowing exercise recentering, setting adjustments, or early save/exit.
- Track total session duration, per-exercise reps completed, mean angle error, and unsafe rep counts, and upload the per-rep log with the session.

## Dependencies
- Inter-system: Coordinates `ExerciseEvaluation`, `VRClinicExperience`, `AvatarCoach`, and communicates with `ClinicalBackend` via `ApiClient`.

## Runtime References
- `Main/TheraQuestVR/unity/Assets/TheraQuest/Scripts/SessionManager.cs`: Primary session state machine, countdown timers, set sequencing, and lifecycle coordinator.
- `Main/TheraQuestVR/unity/Assets/TheraQuest/Scripts/ApiClient.cs`: REST client handling GET/POST calls to `server.py` and offline session queueing.
- `Main/TheraQuestVR/unity/Assets/TheraQuest/Scripts/MenuController.cs`: Main menu and pause menu navigation.
- `Main/TheraQuestVR/unity/Assets/TheraQuest/Scripts/GameSettings.cs`: User settings persistence (audio volume, subtitles, input mode).

## Invariants
- Offline sessions must never be dropped; they must be written to disk and uploaded on subsequent app launches. Queued sessions the server refuses as another patient's are moved to a separate rejected file, not deleted.
- Sessions cannot advance to the next exercise without completing the configured set-rest countdown.
- A session never runs on a hardcoded program: only a server-issued or cached server program (with its phase VR gate) may be used.
- The input source is locked for the whole session; walking is disabled while an exercise runs.
- A session interrupted by quitting the app is queued as ended early, not lost.

## Notes
- Seamlessly falls back to simulated/keyboard motion mode when webcam tracking is unavailable.

## Future Changes
- Heart rate monitor or peripheral biometric integration.
