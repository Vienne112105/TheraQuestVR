# SessionOrchestration

## Purpose
Coordinates the patient workout lifecycle: patient profile selection, prescription retrieval, exercise sequencing, inter-set rest intervals, camera guidance, and HTTP session data upload.

## Status
`stable`

## Responsibilities
- Manage the rehabilitation session state machine: Idle -> Prescription Fetch -> Exercise Intro & Camera Placement -> Countdown -> Active Sets -> Rest Countdowns -> Exercise Completion -> Session Upload.
- Fetch patient prescription from the clinical backend over HTTP, identified by the configured synthetic patient code (no clinician credentials; see [[30_DECISIONS]] DEC-009).
- Cache completed session metrics locally if the network/server is offline, with automated retry when reconnected.
- Present pause/resume menu (triggered by Esc or Quest B button) allowing exercise recentering, setting adjustments, or early save/exit.
- Track total session duration, per-exercise reps completed, mean angle error, and unsafe rep counts.

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

## Notes
- Seamlessly falls back to simulated/keyboard motion mode when webcam tracking is unavailable.

## Future Changes
- Multi-patient switching directly within the VR menu.
- Heart rate monitor or peripheral biometric integration.
