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
- Unity XR Plug-in Management 4.7 + OpenXR (loader on for Windows with Initialize on Startup and the Quest Touch, Touch Plus and Touch Pro controller profiles; `TheraQuest → Set Up OpenXR` reapplies it).
- XR Interaction Toolkit 3.6 and XR Core Utils (DEC-030, M10). Since M10.1 the camera sits in a standard XR Origin (floor tracking) built at runtime by `XrRig`, with a TrackedPoseDriver on the camera; the scene file keeps its plain Rig → Main Camera. Since M10.2 the controllers and headset are read through input actions (`Resources/Input/TheraQuestControls.inputactions`) in `XrControls`, and menus take XRI ray interactors through `XRUIInputModule`.
- Inter-system: Relies on `ExerciseEvaluation` and `Gamification` for HUD data binding.

## Runtime References
- `Main/TheraQuestVR/unity/Assets/TheraQuest/Scripts/ClinicRoom.cs`: Room geometry and clinic layout generation.
- `Main/TheraQuestVR/unity/Assets/TheraQuest/Scripts/HUDController.cs`: Dual-mode HUD UI drawing and state display.
- `Main/TheraQuestVR/unity/Assets/TheraQuest/Scripts/HeadTracking.cs`: laptop camera pose, per-posture height offset on the Camera Offset, recentering; turns the pose driver on only in the headset.
- `Main/TheraQuestVR/unity/Assets/TheraQuest/Scripts/XrRig.cs`: builds the XR Origin (Rig → Camera Offset → Main Camera) at runtime.
- `Main/TheraQuestVR/unity/Assets/TheraQuest/Scripts/XrMode.cs`: the one answer to "is the headset in use?" (Desktop, Headset, HeadsetOff, LinkLost) and its change events.
- `Main/TheraQuestVR/unity/Assets/TheraQuest/Scripts/XrControls.cs`: the controllers and headset as the game reads them (input actions; buttons, sticks after the touch check and dead zone, worn, tracked eye position).
- `Main/TheraQuestVR/unity/Assets/TheraQuest/Scripts/ControllerRays.cs`: left and right controllers under the Camera Offset with UI-only rays, shown while a menu is open in the headset.
- `Main/TheraQuestVR/unity/Assets/TheraQuest/Scripts/XrQuality.cs`: the lighter headset look (URP renderer `TheraQuest_Renderer_Headset` without SSAO, 0.8 eye resolution); the laptop look is unchanged.
- `Main/TheraQuestVR/unity/Assets/TheraQuest/Scripts/FirstPersonGuide.cs`: Default body proportions and heights, target and live limbs, side mirror.
- `Main/TheraQuestVR/unity/Assets/TheraQuest/Scripts/PlayerMover.cs`: Smooth/snap locomotion and player boundaries.
- `Main/TheraQuestVR/unity/Assets/TheraQuest/Scripts/Subtitles.cs`: Accessibility caption overlays.
- `Main/TheraQuestVR/unity/Assets/TheraQuest/Editor/TheraQuestSceneBuilder.cs`: Scene builder automation.

## Invariants
- In the headset the view is never moved or turned by the game on its own (motion sickness); only an instant re-center is allowed, which also sets the default height. Turning the view to the moving limb (ViewFocus) runs on the laptop screen only.
- Every patient sees from the posture's default height, whatever their own; the patient's real height never changes the guide.
- The application must remain fully functional in desktop mode when no VR headset is detected.
- Only `XrControls` reads the XR devices, through input actions; no script asks `UnityEngine.XR.InputDevices` (EditMode test). In a headset menu the right trigger clicks the row a ray points at and does not also select the highlighted row.
- Only `XrMode` asks the XR runtime whether a headset is active; nothing else reads `XRSettings.isDeviceActive` (EditMode test). Taking the headset off pauses a running exercise; losing Link carries the session on in desktop mode with its reps kept.
- HUD elements must remain readable and positioned within the comfortable field of view (FOV), with configurable `hudScale` defaulting to `0.00092f` for high legibility at 1.45m VR distance.
- Floating menus are positioned at 1.35m depth with 0.00115f scale to prevent visual fatigue.
- In the headset the HUD panels and subtitles stay put in the room (human request, M10.1): they ride on the rig, so walking and turning carry them, but head movement does not. They are placed in front of the patient only at an instant re-center, when the headset is put on, or when the lying view changes. On the laptop they stay locked to the screen.
- Thumbsticks never walk the patient: walking is keyboard only, in the headset too (human request 2026-11-19, after a faulty Quest 2 stick read 0.87 untouched). Sticks count only with a thumb on them (touch sensor) and past a 0.3 dead zone; walking is also locked during exercises and on the summary.

## Notes
- Anti-aliasing (SMAA) is applied to ensure sharp edges and avoid VR pixelation artifacts.
- Subtitle presets support 3 typography scales (34pt, 44pt, 56pt) for maximum legibility.
- All HUD and menu text is TextMeshPro made through `UIKit.Label` (DEC-015); don't add `UnityEngine.UI.Text`.
- Quest Link facts seen on a Quest 2 (M10.1, 2026-11-18 to 2026-11-23):
  - Link only shows the game after "Unknown Sources" is on in the Meta Horizon Link app (Settings → General).
  - Taking the headset off reports "not worn" and Link stops the display on the next frame; `XrMode` treats that as HeadsetOff (pause), not Link lost.
  - Unplugging Link makes OpenXR ask to quit (ends Play mode in the Editor); `XrMode` refuses through `OpenXRRuntime.wantsToQuit`, so the session carries on on the laptop. Plugging back in needs a Play restart (the loader is shut down).
  - The headset reports a floor height (0) before tracking starts: the default-height offset waits for a tracked head above 0.1 m.
  - Play mode has no domain reload: XR statics and `onBeforeRender` hooks are reset at `SubsystemRegistration`.
  - Frame rate: with the laptop look (SSAO, full 3648 × 1872 eye buffers) an RTX 3050 laptop missed 60 to 185 of 4320 frames a minute and Link's guessed frames made edges wobble; with the headset look 3 in about 1230. The human's cable runs at USB 2 speed (USB2_DISCO), which limits Link and can drop the session; a USB 3 cable is advised.
- On the laptop the mouse looks around without a button whenever no menu is open (cursor locked and hidden); menus free the cursor for clicking.

## Future Changes
- Hand tracking support via Quest OpenXR Hand Tracking extension.
- Additional calming virtual environments (e.g. outdoor nature garden, beach).
