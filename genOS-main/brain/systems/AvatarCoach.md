# AvatarCoach

## Purpose
Visualizes a virtual physical therapy coach avatar: standing in the clinic on menus, and during a session holding each exercise's target pose in a floating window (DEC-021). The patient's own first-person guide limbs are `FirstPersonGuide`, in VRClinicExperience.

## Status
`stable`

## Responsibilities
- Drive 3D humanoid avatar bone rotations to the exercise's target angle.
- Render the coach window: its own camera, the still pose, and an arrow tracing how the moving limb gets there.
- Automatically configure imported Mixamo FBX avatars with Unity Humanoid rigs and smooth materials across gender-segregated folders (`Assets/TheraQuest/Coaches/Male` and `Female`).
- Maintain natural resting idle posture (breathing cycles, weight shifts, player eye tracking) on menus and the summary.
- Support runtime switching between coach avatars, genders and styles from the main menu.

## Dependencies
- Unity Animation and Humanoid Rig system.
- Inter-system: Controlled by `SessionOrchestration` (`SessionManager.isSessionActive`) and synchronized with `ExerciseEvaluation`.

## Runtime References
- `Main/TheraQuestVR/unity/Assets/TheraQuest/Scripts/HumanoidCoach.cs`: bone rotation controller, idle animation, and the coach window with its arrow.
- `Main/TheraQuestVR/unity/Assets/TheraQuest/Scripts/FigureVisualizer.cs`: Kinematic figure drawing for exercise demonstration poses.
- `Main/TheraQuestVR/unity/Assets/TheraQuest/Editor/CoachModelImporter.cs`: FBX asset postprocessor for automatic Humanoid rigging.

## Invariants
- Coach movement demonstrations must align with clinical target angles defined in the active prescription.
- The coach and the figure choose animation, posture and facing from the exercise's `pose`, `posture` and `view` sent by the server (DEC-012), never from its code; an unknown pose falls back to one chosen by the measured angle and view.
- Coach avatar must remain in resting idle during menus and free-roam, never moving unprompted before session begins. On menus, the summary and in free roam it stands facing the player with no chair.
- During a session the coach is not in the room's view. In its window it only poses (no breathing, sway, blinking or glances; human request 2026-11-01), in the target pose, also on get-ready cards and between exercises.
- The coach poses on a yoga mat that `HumanoidCoach` builds at runtime and turns and fits to each posture; lying and side-lying exercises happen on the mat on the floor (no bed). The coach always faces the way it should face, whatever an idle clip does.

## Notes
- The standing idle is Quaternius' CC0 `Idle_Loop` (`Resources/CoachAnimations`, M5.6), loaded when the coach's Idle Clip field is empty; without it the hand-made breathing and sway are used. It plays only on Humanoid avatars: the bundled Quaternius coach rigs keep their feet under the root, so `CoachModelImporter` maps them by hand (feet = the ankle end bones); the clip drives trunk, head and arms while standing legs stay hand-posed.
- Animation: Little Guys use upright T-pose avatars (`Resources/CoachAvatars`, built by `TheraQuest > Build Coach T-Pose Avatars`) for the CC0 idle and talking clips; the talking idle still blends in while the coach speaks, but with the body held in the model's shape it shows no gestures.
- Body and face (human request 2026-10-28): the model keeps its own shape (hips, spine, neck, head, legs, collarbones, wrists and fingers at rest); arms are always hand-posed, hanging relaxed at the sides when not exercising, so the idle clips add nothing visible. The collarbones are turned forward when the coach is built so the shoulder joints sit level with the chest bone, not behind it. Fingers get a gentle curl in their rest shape, the forearm turns so the palm faces the body (fading out as the arm rises sideways), and exercise arms start from the resting arm over the first 15 degrees. Standing soles, and the body lying on the back or side, rest on top of the mat (heights measured from the posed mesh when the coach is built). Face blend shapes (Blink, Smile, SmileTeeth, Surprise) drive blinking, a soft smile and a concerned look on warnings; the mouth does not move while the coach speaks; weights are scaled to each shape's own full weight (1 on the Little Guys).
- Look (DEC-018): the coach models are shown as modelled, with no extra stylisation; a material made for another render pipeline is swapped at runtime for a plain Standard one with the same texture, so it never draws pink.
- Users can drop any Mixamo Humanoid FBX into `Assets/TheraQuest/Coaches/Male/` or `Assets/TheraQuest/Coaches/Female/` to expand the coach roster automatically.

## Future Changes
- Multi-coach vocalization and lip-syncing.
- Augmented visual cues on the coach indicating movement pacing and hold countdowns.
