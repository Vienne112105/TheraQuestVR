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
- Coach avatar must remain in resting idle during menus and free-roam, never moving unprompted before session begins. On menus, the summary and in free roam it stands facing the player with no chair; during a session's get-ready cards and between exercises it waits, still, in the coming exercise's start position on its chair or on the mat.
- The coach exercises on a yoga mat that `HumanoidCoach` builds at runtime and turns and fits to each posture; lying and side-lying exercises happen on the mat on the floor (no bed). The coach always faces the way it should face, whatever an idle clip does.
- Holographic range-of-motion guidance marker must be visible in both Coach Mode and Silhouette Mode.

## Notes
- The standing idle is Quaternius' CC0 `Idle_Loop` (`Resources/CoachAnimations`, M5.6), loaded when the coach's Idle Clip field is empty; without it the hand-made breathing and sway are used. It plays only on Humanoid avatars: the bundled Quaternius coach rigs keep their feet under the root, so `CoachModelImporter` maps them by hand (feet = the ankle end bones); the clip drives trunk, head and arms while standing legs stay hand-posed.
- Animation: Little Guys use upright T-pose avatars (`Resources/CoachAvatars`, built by `TheraQuest > Build Coach T-Pose Avatars`) for the CC0 idle and talking clips; the talking idle blends in while the coach speaks (lines from `Subtitles.Say` marked as the coach's).
- Look (DEC-018): the coach models are shown as modelled, with no extra stylisation; a material made for another render pipeline is swapped at runtime for a plain Standard one with the same texture, so it never draws pink.
- Users can drop any Mixamo Humanoid FBX into `Assets/TheraQuest/Coaches/Male/` or `Assets/TheraQuest/Coaches/Female/` to expand the coach roster automatically.

## Future Changes
- Multi-coach vocalization and lip-syncing.
- Augmented visual cues on the coach indicating movement pacing and hold countdowns.
