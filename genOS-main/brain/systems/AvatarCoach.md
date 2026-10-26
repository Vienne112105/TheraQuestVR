# AvatarCoach

## Purpose
Visualizes a virtual physical therapy coach avatar that demonstrates exercise movements, mirrors kinematic angles in real time, and provides visual guidance for the patient.

## Status
`stable`

## Responsibilities
- Drive 3D humanoid avatar bone rotations according to target angles and detected patient angles.
- Render visual guidance figures (wireframe/ghost demonstration avatar, geometric visualizer, or dual-zone holographic ROM guidance).
- Automatically configure imported Mixamo FBX avatars with Unity Humanoid rigs and smooth materials across gender-segregated folders (`Assets/TheraQuest/Coaches/Male` and `Female`).
- Maintain natural resting idle posture (breathing cycles, weight shifts, player eye tracking) prior to session start, only demonstrating repetitions during active exercise phases.
- Support runtime switching between coach avatars, genders, styles, and demonstration modes (Coach vs. Silhouette) from the main menu.

## Dependencies
- Unity Animation and Humanoid Rig system.
- Inter-system: Controlled by `SessionOrchestration` (`SessionManager.isSessionActive`) and synchronized with `ExerciseEvaluation`.

## Runtime References
- `Main/TheraQuestVR/unity/Assets/TheraQuest/Scripts/HumanoidCoach.cs`: IK/FK bone rotation controller, blend trees, animation sequencing, and holographic target guidance markers.
- `Main/TheraQuestVR/unity/Assets/TheraQuest/Scripts/FigureVisualizer.cs`: Kinematic figure drawing for exercise demonstration poses.
- `Main/TheraQuestVR/unity/Assets/TheraQuest/Editor/CoachModelImporter.cs`: FBX asset postprocessor for automatic Humanoid rigging.

## Invariants
- Coach movement demonstrations must align with clinical target angles defined in the active prescription.
- The coach and the figure choose animation, posture and facing from the exercise's `pose`, `posture` and `view` sent by the server (DEC-012), never from its code; an unknown pose falls back to one chosen by the measured angle and view.
- Coach avatar must remain in resting idle during menus and free-roam, never moving unprompted before session begins.
- Holographic range-of-motion guidance marker must be visible in both Coach Mode and Silhouette Mode.

## Notes
- The standing idle is Quaternius' CC0 `Idle_Loop` (`Resources/CoachAnimations`, M5.6), loaded when the coach's Idle Clip field is empty; without it the hand-made breathing and sway are used.
- Users can drop any Mixamo Humanoid FBX into `Assets/TheraQuest/Coaches/Male/` or `Assets/TheraQuest/Coaches/Female/` to expand the coach roster automatically.

## Future Changes
- Multi-coach vocalization and lip-syncing.
- Augmented visual cues on the coach indicating movement pacing and hold countdowns.
