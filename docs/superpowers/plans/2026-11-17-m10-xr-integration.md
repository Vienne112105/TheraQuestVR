# M10 XR Environment & VR Integration: plan (M10.1 in detail)

- **Milestone:** M10 (roadmap `genOS-main/brain/50_ROADMAP.md`), decision DEC-030. Children M10.2 to M10.4 are only outlined here; each gets its own detailed plan when it starts.
- **Branch:** `m10-xr-integration` (from `m9-manuscript`). The human's XR packages are committed as `7bf9360`.
- **Hardware:** the human has a Meta Quest. Every headset check below is done by the human, over Quest Link.
- **Agents:** `unity-architect` (one job per component, no `GameObject.Find`, a class over about 150 lines gets split) and `xr-interface-architect` (comfort-based placement, motion constraints, a fallback for every input).

## What exists today (read 2026-11-17)

- `HeadTracking.cs` (88 lines) is on the Main Camera, which sits under an empty `Rig`. Each frame it reads the head with `UnityEngine.XR.InputDevices`. It sets Floor tracking itself, adds the per-posture height offset (`FirstPersonMath.HeightOffset`, DEC-021), and turns the rig in `Recenter`. On the laptop it puts the camera at `desktopEyeHeight` and applies the mouse pitch.
- `InputHelper.cs` reads the controllers through `XRNode` (this is M10.2's work, not M10.1's).
- `PlayerMover.cs` moves and turns the `Rig` (M10.3).
- "Headset on?" is asked in three different ways: `HeadTracking.HeadsetActive`, and `XRSettings.isDeviceActive` in `HUDController` and in `SessionFlow.ControlHints`.
- `SessionManager.Awake` already adds missing parts at runtime (`PlayerMover`, `ViewFocus`, `ClinicRoom`, and so on).
- `TheraQuest.unity` holds the human's uncommitted scene changes, so **this plan does not edit the scene file**: the XR Origin is assembled at runtime on the existing `Rig`, the same way `SessionManager` already adds parts.

## Restraint check

- **Kept:** the default-height logic, the `FlatYaw` re-center math, and the desktop camera code. All of them are tested and already meet DEC-021.
- **Replaced:** the hand-written head reads, which become an XR Origin plus a `TrackedPoseDriver`, the standard and maintained path.
- **Not used in M10.1:** the XR Interaction Toolkit interactors (they arrive in M10.2), XR Hands, and Composition Layers. M10.1 needs only `Unity.XR.CoreUtils` (`XROrigin`) and the Input System (`TrackedPoseDriver`).
- **No scene rebuild,** and no new ScriptableObject until there is shared data to hold.

## M10.1: steps (tests written first)

1. **`XrMode` (new, plain C#, about 60 lines).** This is the single answer to "is the headset in use?". It has a pure state machine: `Desktop`, `Headset`, `HeadsetOff` (worn, then taken off) and `LinkLost`. Its inputs each frame are whether the XR display is running and whether the user is present.
   - Its events are `HeadsetRemoved`, `HeadsetBack` and `FellBackToDesktop`.
   - Tests in `XrModeTests`:
     - Start with no display: `Desktop`.
     - Display running and user present: `Headset`.
     - Presence lost: `HeadsetOff` plus `HeadsetRemoved`.
     - Display stops mid-session: `LinkLost` and `FellBackToDesktop`, with the session kept.
     - Display comes back: `Headset`.
     - Presence briefly flickering for under 0.5 s does not fire anything.
2. **One source.** `HeadTracking.HeadsetActive`, `HUDController` and `SessionFlow.ControlHints` all read `XrMode`. Test: no file in `Scripts/` uses `XRSettings.isDeviceActive` (a file scan, like the URP no-Built-in-shader test).
3. **`XrRig` (new, about 80 lines).** It builds the rig at runtime and can safely run more than once.
   - On the existing `Rig` it adds `XROrigin` (Floor tracking origin). It puts a `Camera Offset` object between `Rig` and `Main Camera`.
   - It adds a `TrackedPoseDriver` (Input System, the XR HMD centre-eye position and rotation) to the camera, set not to write when nothing is tracked, so the desktop pose stays.
   - `SessionManager.Awake` calls it before it adds `PlayerMover`.
   - Tests in `XrRigTests`:
     - It builds Rig → Camera Offset → Main Camera with the `XROrigin` fields set.
     - A second run changes nothing.
     - `HeadTracking`, `PlayerMover` and `ViewFocus` still find the rig. This changes `SessionManager`, which currently uses `head.transform.parent`; the rig becomes the XR Origin's object.
     - `HUDController`'s rig yaw is unchanged.
4. **`HeadTracking` slimmed down.**
   - In the headset it no longer writes the camera pose; the `TrackedPoseDriver` does. It writes only the height offset, on `Camera Offset`'s local Y.
   - `SetEyeHeight` and `Recenter` keep their maths. `Recenter` turns and moves the XR Origin object.
   - The desktop branch is unchanged.
   - Tests: on the desktop the camera is at the posture eye height and pitch, as before; the height offset reaches `Camera Offset`; `Recenter` gives the same yaw as today's `FlatYaw` cases.
5. **Lifecycle wiring.**
   - `HeadsetRemoved` pauses the session through the existing `Pause()`. `HeadsetBack` leaves it paused; the patient resumes with A.
   - `FellBackToDesktop` keeps the session and the reps already done, switches the control hints to the keyboard ones, and shows a short subtitle ("Headset disconnected: carry on with the keyboard or reconnect").
   - Tests drive `XrMode` with fake inputs and check that the pause and hint switch happen.
6. **`TheraQuest → Set Up OpenXR`.**
   - It also enables the Meta Quest Touch Plus profile (Quest 3) beside Oculus Touch, if you confirm which Quest you have.
   - It checks that the headset-tracking settings the XR Origin needs are present.
   - The existing `ProjectSettingsTests` style check covers this.
7. **Asmdef.** Add `Unity.XR.CoreUtils` to `TheraQuest.Runtime` and the test assembly.
8. **Verification.**
   - The EditMode suite is fully green (it was 137 before; new tests are added on top).
   - `python run_tests.py`.
   - Play mode with Link off shows no change on the laptop.
   - Then the **human headset checks** (in `pending_human_tests` if they cannot be done in the same session):
     - The room appears in the headset over Link, at the right height standing, seated and lying.
     - Y re-center faces the coach.
     - Taking the headset off pauses; putting it back on and pressing A resumes.
     - Unplugging Link mid-set falls back to the laptop, keeps the reps, and the session still uploads.
     - Starting with Link off gives desktop mode.
9. **Brain.**
   - [[VRClinicExperience]]: replace the "No XR Interaction Toolkit" dependency note, and update the runtime references (`XrMode`, `XrRig`).
   - Roadmap: set M10.1 to done, or to TBF while only the headset checks are left.
   - Commit per step.

## Outline of the next children (detailed when each starts)

- **M10.2 Controller Input & Ray Menus:**
  - An input actions asset read through `InputHelper` (keyboard plus XRI default controller actions), with the current A, B, Y and thumbstick mapping kept.
  - XR UI Input Module and a ray interactor per controller on the world-space menus.
  - Controller models.
  - Test: no `XRNode` reads are left.
- **M10.3 Comfort Locomotion:** `PlayerMover`'s walk, snap turn and smooth turn moved to XRI locomotion providers on the XR Origin, keeping the room bounds, `walkLocked` and `GameSettings`.
- **M10.4 Headset Panels & Rendering:**
  - Panel placement and sharpness on the new rig. Composition Layers are used only if needed; otherwise the package is removed.
  - Stereo URP check against DEC-028.
  - Headset frame time measured.
  - Not run in parallel with M8.4 or M8.5.

## M10.2: what was built (2026-11-23)

- `Resources/Input/TheraQuestControls.inputactions`: map Controllers (A select, triggers, B or left Menu back, Y re-center, left stick click quest, sticks with touch, aim poses, tracked) and map Headset (worn, tracked, eye position), on the generic `<XRController>` usages so Quest 2, 3 and Pro all work.
- `XrControls` loads a runtime copy and enables it; `InputHelper`, `XrMode` and `HeadTracking` read through it. Test: no script reads `XRNode`, `InputDevices` or `CommonUsages`.
- `ControllerRays` (added by `SessionManager` on the rig): a TrackedPoseDriver, a simple handle and an `XRRayInteractor` (UI only, 6 m) per hand; shown only while a menu is open in the headset. The trigger reaches the ray through an `InputActionReference`, because the toolkit turns direct actions off when a ray hides, which would also silence the trigger elsewhere.
- Menus: `XRUIInputModule` (rays and mouse) and a `TrackedDeviceGraphicRaycaster` on the menu canvas. While a ray points at a button the right trigger only clicks it (`InputHelper.RayOnMenu`).
- Not done here: XRI controller models (simple handles instead), locomotion providers (M10.3).

## Questions for the human before M10.1 starts

1. Which headset do you have: Quest 2, Quest 3, Quest 3S or Quest Pro? (Step 6 profile.)
2. Is the Meta Quest Link app installed, and set as the active OpenXR runtime? HW.1 lists this as needed; if not, it is the first thing to do.
3. Building the XR Origin at runtime keeps your uncommitted `TheraQuest.unity` untouched. Is that fine, or do you want it saved in the scene once your scene changes are committed?
