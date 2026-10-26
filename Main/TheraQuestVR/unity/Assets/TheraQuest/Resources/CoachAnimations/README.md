# Coach Idle Animations

`Idle_Loop.anim` is the coach's standing idle: the `Idle_Loop` clip from Quaternius' Universal Animation Library
(CC0, see `Assets/TheraQuest/CREDITS.md` and `Idle_Loop-LICENSE.txt`), imported as a Humanoid clip, looping, with
the root baked in place. `HumanoidCoach` loads it from Resources when its Idle Clip field is empty, and plays it on
the limbs the exercise doesn't move while the coach stands. Without it the coach uses its hand-made breathing and sway.

To use another idle (e.g. Mixamo "Breathing Idle", downloaded "Without Skin"), drop the FBX in this folder
(`CoachModelImporter` makes it Humanoid and looping) and assign its clip to the coach's Idle Clip field.
