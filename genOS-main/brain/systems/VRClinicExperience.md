# VRClinicExperience

## Purpose
Renders an immersive 3D physical therapy clinic environment in Unity 6, handles OpenXR VR head/controller tracking with desktop fallback, and displays dual-mode HUD feedback.

## Status
`stable`

## Responsibilities
- Build the clinic at runtime: walls, windows, posters and lights from primitives; gym equipment and furniture as 3D models from `Resources/Room` (DEC-019); the coach's yoga mat.
- Provide OpenXR VR head tracking and controller input mappings for Meta Quest (via Quest Link), with automated fallback to keyboard/mouse desktop controls.
- Offer comfortable locomotion: snap turning (30°), smooth turning, walking (WASD/thumbstick), and instant recentering to the exercise spot (R key or Y button).
- Render dual-mode HUD:
  - Patient View: Clean power meter gauge, green target zone, star indicator, rep dots, and friendly coach tips.
  - Therapist View: Raw measured joint angles, exact accuracy %, camera FPS, and tracker link status.
- Present closed-caption subtitles for all audio instructions and sound effects.
- First-person exercise view (DEC-021): target and live limbs from a fixed default body, the side mirror for limbs behind the patient, and one default view height per posture.

## Dependencies
- Unity 6 LTS Universal Render Pipeline (URP).
- Unity XR Plug-in Management + OpenXR (loader on for Windows with Initialize on Startup and the Oculus Touch profile; `TheraQuest → Set Up OpenXR` reapplies it). No XR Interaction Toolkit: input goes through `UnityEngine.XR` device reads.
- Inter-system: Relies on `ExerciseEvaluation` and `Gamification` for HUD data binding.

## Runtime References
- `Main/TheraQuestVR/unity/Assets/TheraQuest/Scripts/ClinicRoom.cs`: Room geometry and clinic layout generation.
- `Main/TheraQuestVR/unity/Assets/TheraQuest/Scripts/HUDController.cs`: Dual-mode HUD UI drawing and state display.
- `Main/TheraQuestVR/unity/Assets/TheraQuest/Scripts/HeadTracking.cs`: OpenXR camera rig management and recentering.
- `Main/TheraQuestVR/unity/Assets/TheraQuest/Scripts/FirstPersonGuide.cs`: Default body proportions and heights, target and live limbs, side mirror.
- `Main/TheraQuestVR/unity/Assets/TheraQuest/Scripts/PlayerMover.cs`: Smooth/snap locomotion and player boundaries.
- `Main/TheraQuestVR/unity/Assets/TheraQuest/Scripts/Subtitles.cs`: Accessibility caption overlays.
- `Main/TheraQuestVR/unity/Assets/TheraQuest/Editor/TheraQuestSceneBuilder.cs`: Scene builder automation.

## Invariants
- In the headset the view is never moved or turned by the game on its own (motion sickness); only an instant re-center is allowed, which also sets the default height. Turning the view to the moving limb (ViewFocus) runs on the laptop screen only.
- Every patient sees from the posture's default height, whatever their own; the patient's real height never changes the guide.
- The application must remain fully functional in desktop mode when no VR headset is detected.
- HUD elements must remain readable and positioned within the comfortable field of view (FOV), with configurable `hudScale` defaulting to `0.00092f` for high legibility at 1.45m VR distance.
- Floating menus are positioned at 1.35m depth with 0.00115f scale to prevent visual fatigue.

## Notes
- Anti-aliasing (SMAA) is applied to ensure sharp edges and avoid VR pixelation artifacts.
- Subtitle presets support 3 typography scales (34pt, 44pt, 56pt) for maximum legibility.
- All HUD and menu text is TextMeshPro made through `UIKit.Label` (DEC-015); don't add `UnityEngine.UI.Text`.

## Future Changes
- Hand tracking support via Quest OpenXR Hand Tracking extension.
- Additional calming virtual environments (e.g. outdoor nature garden, beach).
