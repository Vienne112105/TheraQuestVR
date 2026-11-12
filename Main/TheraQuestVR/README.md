# TheraQuest VR: working prototype

A gamified VR physical therapy system with webcam motion tracking and adherence monitoring.
It runs on one Windows laptop and shows in a Meta Quest through **Quest Link**, or on the laptop screen when no headset is plugged in.
No Android build is needed.

```
 Webcam ──► tracker.py (Python + MediaPipe)  ──UDP 5005──►  Unity app (VR or desktop)
                                                               │  HTTP 8000
                                                               ▼
                                     server.py (SQLite database) ──► Therapist dashboard (browser)
```

| Folder | What it is | Manuscript module (Section 3.6.3) |
|---|---|---|
| `tracker/` | Webcam → MediaPipe Pose → joint angles → Unity | Motion Tracking |
| `unity/Assets/TheraQuest/` | VR scene, scoring, feedback, game, session flow | VR Environment, Exercise Evaluation, Feedback Generation, Gamification |
| `server/` | Database, API and therapist dashboard | Adherence Monitoring, Data Layer |

---

## 1. Install the tools (one time)

1. **Python 3.12** (or 3.11) from python.org. During setup tick **"Add python.exe to PATH"**.
   MediaPipe may not install on the newest Python yet; the pinned packages are tested with 3.12.
2. **Unity Hub** → install **Unity 6** (the project uses `6000.6.5f1`; see `unity/ProjectSettings/ProjectVersion.txt`). The default modules are enough. You do **not** need Android Build Support.
3. **Meta Quest Link** app for Windows (only for VR). Connect the Quest with a USB-C cable or Air Link.
4. A **webcam**. The laptop's built-in one works for testing. A USB webcam on a tripod is better for real sessions.

## 2. Launch the Therapist Desktop Application

Double-click **`Start_Therapist_App.bat`**, or run:

```
cd server
python app.py
```

This launches the **Therapist Command Center as a native desktop application window** (powered by Windows WebView2, without any browser URL bars, navigation buttons, or tabs).
For the native window, install the optional package once: `pip install -r server/requirements.txt`. Without it, the launcher opens Edge in app mode.
You can also view the dashboard via browser at **http://localhost:8000**.

**Sign in.** The dashboard needs a therapist login. There is no default password: the first time you open the dashboard on this computer, it asks you to create the clinician login (at least 8 characters). Use **Password** in the top bar to change it later. A database from an older version that still has the demo password asks for a new one at the next sign-in. After 5 wrong passwords, sign-in for that username pauses for 5 minutes.

The server listens on this computer only. To open the dashboard from another computer on the clinic network, start it with `python server.py --host 0.0.0.0` (the VR routes still accept only this computer).

**Where the data lives.** The database is stored at `%LOCALAPPDATA%\TheraQuest\theraquest.db`, outside the project folder, so OneDrive or git never sync patient data (DEC-010).
Set the environment variable `THERAQUEST_DB` to use another path. The first run copies an older `server/theraquest.db` there once; delete the old copy after you've checked the dashboard.
The first run of a new database creates patient **P-001** and the evidence-based clinical protocols.
`python server.py --reset` deletes the database (including its `-wal` / `-shm` files) and starts fresh.

## 3. Start the motion tracker

Double-click **`start_tracker.bat`**. On the first run it checks for Python 3.11 / 3.12, creates `tracker\.venv` and installs the pinned packages from `tracker/requirements.txt`. If the install fails, it stops and retries on the next run.

To check the angle math: `cd tracker` then `.venv\Scripts\python -m unittest test_angles`.

To run every test suite (server, tracker, evaluation, Unity EditMode) and get one summary: `python run_tests.py` in this folder. Unity is skipped while its Editor has the project open; `--no-unity` and `--only server,tracker` narrow the run. Exit code 1 means a suite failed.

Manual use:

```
cd tracker
.venv\Scripts\activate
python tracker.py              # built-in webcam
python tracker.py --camera 1   # USB webcam
python tracker.py --fake       # no camera: sends simulated reps to Unity (to test the link)
python tracker.py --record     # also saves the landmarks (never images) to tracker/recordings/<date-time>.jsonl
python tracker.py --replay recordings/FILE.jsonl [--fast]   # sends a recording to Unity as if it were live
python report.py recordings/FILE.jsonl                      # tracking-state, signed-angle and pause summary
```

A preview window shows your skeleton and the live angles. The first run downloads the pose model (about 6 MB).

**Where to put the camera.** The tracker measures angles in 2D, so the camera must see the movement side-on to it:

| Exercise | Camera position |
|---|---|
| Shoulder abduction, scaption | **In front** of the patient, whole upper body in view |
| Shoulder flexion, wall slide | **At the side** of the moving arm |
| Elbow flexion | **At the side** of the moving arm |
| Standing hip abduction | **In front**, whole body in view |
| Straight leg raise, heel slide | **At the side**, patient lying on their back, whole body in view |
| Standing march, mini squat, sit to stand | **At the side**, whole body in view |
| Seated knee extension | **At the side** of the moving leg, patient seated |

Unity shows the start position and camera view before each exercise and waits for Start.

The tracker sends 5 angles (`shoulderElev`, `elbowFlex`, `hipElev`, `kneeFlex`, `kneeExt`) for the best-seen side and for each side separately (`L`, `R`).
In side view it also sends `shoulderElevSigned` and `hipElevSigned` (+ = limb in front of the trunk, − = behind). Unity uses them so that an extension exercise only scores movement backwards, and a flexion exercise never scores movement behind the trunk.
When the therapist sets an exercise's operated side, Unity uses that side; otherwise it uses whichever side the camera sees best.

Use good lighting, keep 2–3 m away, and don't stand in front of a window.

## 4. Set up the Unity project

1. Unity Hub → **Add → Add project from disk** → choose the `unity` folder.
   The first open takes a while: Unity rebuilds its `Library` cache, which is not stored in git.
2. Open `Assets/TheraQuest/TheraQuest.unity`. (If the scene is missing, use the menu **TheraQuest → Create Scene**: it builds the room, the coach figure, the HUD and all the managers, and connects everything.)
3. Choose the patient (see **Which patient this computer is for** below). In the Editor the simplest way is the **TheraQuest** object → **Api Client → Patient Code** (e.g. `P-001`). Unity loads that patient's program from `/api/vr/program` and uploads to `/api/vr/sessions`, from this computer only.
4. Press **Play**. You'll see the scene on the laptop screen (desktop mode).

**Which patient this computer is for.** The app takes the patient code and server address from the first of these that is set:

1. The command line: `TheraQuestVR.exe -patient P-002 -server http://127.0.0.1:8000` (both optional).
2. `config.json` in the app's data folder (`%USERPROFILE%\AppData\LocalLow\TheraQuest\TheraQuestVR\` for a built player; before 2026-11-12 the folder was `...\DefaultCompany\TheraQuestVR\`, so copy `config.json`, the PIN, the cached program and an unsent `pending_sessions.jsonl` over by hand once on a machine that used the old name). Keys: `patientCode`, `serverUrl`, `pinHash`. The Therapist page writes it.
3. The Inspector values on **Api Client**.

The app never runs a session on a made-up program. It uses the program the server sent, or the last one it received for that patient (saved in the same data folder). With neither, the menu explains why and **Start** stays disabled.
Sessions recorded offline wait in `pending_sessions.jsonl` and upload when the server is back. Sessions the server refuses (for example another patient's) move to `rejected_sessions.jsonl` instead of being deleted.

**Therapist page (PIN).** Main menu → **Therapist** (only between sessions). There is no default PIN: the first visit asks the therapist to choose a 4-digit PIN, which is stored only as a hash in `config.json`. After 5 wrong PINs the page locks for a minute. The page can:
- switch this computer to another patient code `P-000` … `P-999` (other codes: start with `-patient`),
- change the **motion input** (webcam → keyboard → simulated); it can't change during a session,
- turn **Show numbers (therapist)** on or off,
- change the PIN.

You don't need to run **Create Scene** again after updating the scripts: the menu, music, subtitles,
clinic room and walking are added automatically when you press Play.

**Playing**

Press Play and the **main menu** opens in front of you:
- **Start today's quest** brings you to the exercise spot and starts the session.
- **Explore the clinic** lets you walk around the room.
- **Coach** and **Guide** choose the avatar and how it guides you.
- **Settings** has music volume, effects volume, subtitles on/off and size, snap or smooth turning, and walking speed. Settings are saved.
- **Therapist** (PIN) chooses the patient and motion input. Its **Show numbers (therapist)** switches the HUD from the simple patient view to one with degrees, accuracy % and tracker details. The patient view uses a power meter (green zone, ★ at the target, red STOP line), rep dots and friendly coach lines. The dashboard always has the full data.

During a session, **Esc / B pauses** the exercise. The pause menu can resume, take you back to the exercise spot, open Settings, or end the session and save it.
**Subtitles** at the bottom of your view caption the coach's instructions and every sound cue, for example *[Perfect chime] Perfect! 97%*.

**Controls**

| Action | Keyboard / mouse | Quest controller |
|---|---|---|
| Start / select | Space or Enter | A or right trigger |
| Pause / menu / back | Esc, P or Backspace | B, or Menu (left) |
| Menu: choose / change value | Arrow keys (the mouse can click too) | Either thumbstick |
| Walk | W A S D (Shift = faster) | Left thumbstick |
| Turn / look around | Q / E, Left / Right, or hold the right mouse button | Right thumbstick (snap 30° or smooth) |
| Back to the exercise spot | R | Y |
| Move limb (keyboard input mode) | Up / Down | Right thumbstick up / down |

Walking is turned off while an exercise is running, so the patient stays at the station.

To watch a full session without the camera, choose **Therapist → Motion input → Simulated**, go back, then **Start today's quest**. The session runs by itself and uploads to the dashboard.

**Coach characters and Mixamo**

The coach can be any Humanoid character. Characters in a `Coaches` folder (for example `Assets/ThirdParty/Coaches`) are set up automatically: Humanoid rig and smooth shading. The game camera also uses anti-aliasing (SMAA) for smooth edges. In the editor, keep the Game view **Scale at 1x**, because a lower scale makes everything look pixelated.

To use characters and animations from [Mixamo](https://www.mixamo.com/) (free with an Adobe account):
1. **Characters:** pick a character, then Download → Format **FBX for Unity (.fbx)**, Pose **T-pose**. Put the file in `Assets/ThirdParty/Coaches/`.
2. **Idle animation (recommended):** search for **"Breathing Idle"**, then Download → **FBX for Unity**, **Without Skin**. Put it in `Assets/ThirdParty/CoachAnimations/`. It's imported as a looping Humanoid clip and becomes the coach's resting animation, so the limbs that aren't exercising breathe and shift weight like a real person.
3. Run **TheraQuest → Create Scene** again. Each character in `Coaches` becomes a choice under **Main menu → Coach**. The idle clip is also picked up automatically by an existing scene.
4. If a Mixamo character looks white or untextured, select the FBX → Inspector → **Materials → Extract Textures**.

The exercise movements are still driven by the tracker angles, so they work with every character.

## 5. Show it in the Quest (Quest Link)

1. In the **Meta Quest Link** PC app: Settings → General → **OpenXR Runtime → Set Meta Quest Link as active**.
2. The project already has OpenXR set up for Windows: **XR Plug-in Management → OpenXR** with **Initialize XR on Startup** and the **Oculus Touch Controller Profile**. If those settings get lost, run **TheraQuest → Set Up OpenXR** in Unity.
3. Under **XR Plug-in Management → OpenXR**, fix any yellow warnings with the "Fix All" button.
4. Put on the headset, enable **Link** (Quick Settings → Link), then press **Play** in Unity.
   The scene appears in the headset with head tracking. Press **Y** (or R) to recenter.

Without the headset connected, the same Play button falls back to desktop mode.

**Make a standalone .exe:** File → Build Profiles → Windows → Build. Run the .exe while the server and tracker are running, for example `TheraQuestVR.exe -patient P-002`, or set the patient once on the Therapist page.

## 6. A full test run (checklist)

1. `start_server.bat` → dashboard opens.
2. `start_tracker.bat` → preview window shows your skeleton.
3. Unity → Play. The HUD's left panel should say **"Tracker connected · ~30 fps"**.
4. Stand where the camera sees you, press Start, and do the reps.
   - Each rep is scored by **Angle Error = |θexpected − θdetected|**. It counts if it's within the tolerance.
   - Points, combo, badges and stars appear in the HUD. Feedback appears in the banner with tones.
5. When the session finishes, refresh the dashboard. You'll see the session, its accuracy, the adherence calendar and any stage-up.

## 7. Protocols, phases and clinical notes

Rehab protocols are stored as **Protocol → Phases → Exercises** (tables `protocol`, `protocol_phase`, `phase_exercise`).
Two protocols are loaded from the published documents (`PROTOCOLS` in `server.py`):

| Protocol | Phases | Tracked in VR (single webcam) |
|---|---|---|
| **OHSU Health Total Knee Best Practice Rehab Guideline** (HC-REH-400.30.3, Nov 2023) | I Immediate post-op · II Motion and mobility · III Intermediate · IV Advanced strengthening · V Return to activities (no VR) | Heel slides, LAQ / seated knee extension, mini squats, side-lying hip abduction, SLR, standing hamstring curls, standing hip abduction and extension, sit to stand, marching, mini lunges, wall slides to 90° (5 s holds in Phase IV) |
| **Mass General Brigham, Arthroscopic Rotator Cuff Repair, Large to Massive Tears** | I Immobilization (no VR) · II Passive ROM (no VR) · III AAROM then AROM · IV Initial strengthening · V Advanced strengthening · VI Return to sport (no VR) | Supine cane flexion, wall slide, active forward reach, active shoulder elevation, straight-arm shoulder extension, biceps curls, full can (scaption), wall push-ups |

- Phase names, time frames, goals, precautions, ROM goals and progression rules follow the documents. Each phase also lists the protocol's exercises that **can't be tracked with one camera** (quad sets, ankle pumps, isometrics, shoulder rotation, bike, manual therapy and so on) under "Without camera" on the dashboard.
- MGB Phase IV forbids straight-arm lateral raises, so shoulder abduction isn't in that phase.
- The documents don't give angles or reps for most exercises. Targets come from the phase ROM goals where the document has them. Sets × reps use OHSU's "2×8" rule. Safety limits are starting points. **Have your physical therapist confirm every number.**
- **Normal ROM** for each exercise (AAOS values as tabulated in **Norkin & White, *Measurement of Joint Motion: A Guide to Goniometry***) is shown next to the prescription. The dashboard warns when a target or safety max goes past it.
- Updating from an older version replaces the earlier example protocols. Patients on an old phase keep their exercises as a custom program.

**Using it**

- **Assign a phase** on the dashboard (Protocol & phase panel). Its exercises replace the prescription, and the therapist can still change any value.
- **Phases marked "not for VR"** (immobilization, passive motion, return to sport) have no VR session. TheraQuest is only for patients cleared for active exercise; put this in Scope and Limitations.
- **Clinical notes are recorded by the therapist, not the patient.** In the session log, **Record** opens fields for pain before → after (0–10), soreness (under / over 2 hours) and swelling increase (cm).
- **Progression check:** the dashboard looks at the most recent 3 complete sessions in the phase and checks the protocol's criteria:
  - every exercise at ≥ 85% accuracy (the ROM goal)
  - pain up by no more than 2 points (OHSU) or no increase in pain (MGB)
  - soreness gone within 2 hours and swelling up by less than 2 cm (OHSU)
  - no reps past the safety limit

  When everything is met it shows **"Ready for Phase II?"**. Nothing changes until the therapist presses **Approve**, and every phase change is logged in `phase_history`.

## 8. How the rules work (keep these consistent with Chapter 3)

- **Rep counter:** a rep starts above 60% of the target angle and ends below 25%. The peak angle is scored.
- **Accuracy:** within tolerance = 85–100% (linear), outside = 85% minus 3% per extra degree.
- **Posture checks:** trunk lean > 12° (shoulder exercises, hip abduction and extension, march), upper arm > 30° from trunk (elbow flexion), knee bent > 15° (straight leg raise), thigh > 20° from vertical (hamstring curl), trunk lean > 35° (mini squat, lunge, wall squat). Any of them invalidates the rep. Each exercise's checks are part of its `LIBRARY` entry in `server.py`.
- **Safety max:** going past it shows a red STOP warning with a warning tone. The rep isn't counted, and it's logged as unsafe for the therapist (0 = no limit).
- **Hold:** when set, the patient must stay inside target ± tolerance for that many seconds (up to 0.3 s of jitter is forgiven).
- **Sets:** reps are per set. After each set there's a rest countdown, and reps aren't counted during it.
- **Points:** 10 × accuracy × combo (×1.0 to ×2.0); invalid rep = 2; completed session +50.
- **Stars:** 3 at ≥ 90% average accuracy, 2 at ≥ 75%, otherwise 1. Ending early gives 0.
- **Progression:** a completed session with ≥ 85% accuracy and no unsafe reps on an exercise adds +2 reps per set next time, up to the therapist's cap.
- **Adherence status:** *complete* = every exercise reached its rep target; *incomplete* = started but not finished; *missed* = a scheduled day with no session.
- **XP levels:** 100 XP for level 2, then +60 more XP per level.

Thresholds live in `server.py` `LIBRARY` (posture checks per exercise), `ExerciseEvaluator.cs` (scoring), `GamificationManager.cs` (points, badges) and `server.py` (progression, adherence, and the exercise `LIBRARY` defaults). The library's targets, safety limits, holds, sets and rest are **placeholders**. Tune them with your physical therapist and document the final values in your manuscript.

## Backup and restore of the patient database

The database holds patient names, so every backup is encrypted. Needs `pip install -r server/requirements.txt` once.

- **Back up:** double-click `Backup_Database.bat`, type the folder (a USB drive is best; keep it somewhere other than this PC), then choose a password of at least 12 characters and type it twice. It is safe to do while the server is running. The file is named `theraquest-YYYYMMDD-HHMMSS.tqbak`.
- **A lost password means the backup cannot be recovered.** Nobody can reset it. Keep the password somewhere other than the backup drive.
- **Restore:** `python server/backup.py restore <file.tqbak> <new-name.db>` asks for the password and writes a NEW database file after checking it; it never overwrites an existing file or the live database. To use it: close the TheraQuest app, move the live `theraquest.db` (and any `theraquest.db-wal` / `-shm` next to it, in `%LOCALAPPDATA%\TheraQuest\`) aside, copy the restored file in as `theraquest.db`, then start the app again.
- Back up before updating the software and after each study visit. Do not put the `.tqbak` files in this project folder or in git.

## 9. Troubleshooting

| Problem | Fix |
|---|---|
| HUD says "No tracker data" | Start `tracker.py`. Allow Python **and** Unity through Windows Firewall (Private networks) when asked. Check that nothing else uses UDP port 5005. |
| HUD says "(offline)" | Start `server.py` first, then press Play again. Offline sessions are saved and upload automatically later. |
| `pip install mediapipe` fails | Use Python 3.11 or 3.12, delete `tracker\.venv` and run `start_tracker.bat` again. |
| Camera won't open | Close Zoom, Teams or the Camera app. Try `--camera 1`. |
| Angles jump around | Improve the lighting, move back so the whole limb is in frame, use `--model full`. |
| Nothing in the headset | Quest Link must be the active OpenXR runtime, and Link must be on *before* pressing Play. |
| Pink objects | The project isn't using URP or Built-in correctly. Use the Universal 3D template. |

## 10. Next steps for the capstone

- **Patient privacy:** use patient codes (P-001), not names. The database stays on the clinic laptop, outside synced folders. This supports your Ethical Considerations section and the Data Privacy Act of 2012 (RA 10173).
- **Adding exercises:** on the dashboard, pick one from **Add exercise**. To create a new type that moves like an existing one, add one entry to `LIBRARY` in `server.py` with its posture, pose, direction and posture checks (`_rules(...)`); Unity needs no change. A new kind of movement also needs a pose in `FigureVisualizer.cs` and `HumanoidCoach.cs` (and in `POSES`). A new measured angle also goes in `tracker/angles.py` and `AngleSet`.
- **Evaluation data:** every rep attempt is uploaded with its session (`rep_event` table): peak angle, error, counted or not, posture fault. The dashboard's export links add `&kind=reps` for one row per rep. `evaluation/evaluate_clinical_metrics.py` computes the Section 3.9 metrics **only from real data**:
  - therapist rep labels (`--rep-labels`) → confusion matrix, matched to rep events by `session_uuid`, exercise code and attempt number
  - goniometer readings of the same reps (`--goniometer`) → angle error
  - SUS answers (`--sus`) and the PT evaluation survey (`--pt-survey`)

  Blank CSV templates are in `evaluation/templates/`. Only webcam sessions count unless you pass `--include-non-webcam`. A metric without input is reported as **not measured**, and the overall status is never PASS on missing data. `--self-test` runs the formulas on synthetic example vectors and labels the output **SYNTHETIC EXAMPLE DATA** (`evaluation/self_test_report.md`); never report those numbers as results.
- **Avatar:** replace the primitive coach figure with a rigged character (e.g. from Mixamo) driven by the same angles.
