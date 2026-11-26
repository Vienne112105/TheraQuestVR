# MotionTracking

## Purpose
Captures single-webcam RGB video feed, performs real-time 2D human pose estimation via MediaPipe, calculates normalized biomechanical joint angles, and streams them with minimal latency to the VR client via UDP.

## Status
`stable`

## Responsibilities
- Acquire video frames from built-in or external USB webcams via OpenCV.
- Extract 33 2D pose landmarks using MediaPipe Pose solution.
- Compute joint angles (`shoulderElev`, `elbowFlex`, `hipElev`, `kneeFlex`, `kneeExt`) for left, right, and primary view sides, plus signed side-view elevation fields (`shoulderElevSigned`, `hipElevSigned`) that tell forward from backward movement (M4.4; consumed by Unity in M4.6).
- Keep each landmark's history and trust state, smooth verified landmarks, predict short gaps, reject implausible jumps and reacquire after loss (DEC-022).
- Recover from camera loss by reopening the camera with backoff while keeping the preview window responsive.
- Provide synthetic/fake motion generator for headless and camera-less testing.
- Broadcast serialized JSON angle payloads over UDP socket (default port 5005).

## Dependencies
- External: OpenCV (`cv2`), MediaPipe (`mediapipe`), NumPy.
- Inter-system: Relied upon by `ExerciseEvaluation` and `AvatarCoach` via `MotionReceiver.cs`.

## Runtime References
- `Main/TheraQuestVR/tracker/tracker.py`: Main capture loop, UDP socket broadcaster, and OpenCV skeleton preview window.
- `Main/TheraQuestVR/tracker/angles.py`: Biomechanical angle trigonometric computations and landmark vector calculations.
- `Main/TheraQuestVR/tracker/tracking.py`: Landmark trust states, One Euro and Kalman filters, whole-pose state and packet building.
- `Main/TheraQuestVR/tracker/test_angles.py`, `test_tracking.py`: Unit tests covering angle math, visibility, signed angles, camera reconnect, model download, filters, trust states and safeguards.
- `Main/TheraQuestVR/unity/Assets/TheraQuest/Scripts/MotionReceiver.cs`: Background thread UDP socket listener deserializing angle JSON; listens on 127.0.0.1 unless `listenOnAllInterfaces` is set.

## Invariants
- Angle computations must produce continuous degrees [0°, 180°].
- Tracking packets must be timestamped to enable latency and FPS calculation in the VR HUD.
- The system must gracefully handle frame drops and landmark occlusion without crashing.
- An angle is reported only when every landmark it uses is verified (DEC-022: confident for several frames in a row, not predicted or preserved); otherwise it is -1 (signed fields use -999, because -1 is a valid signed value). Zero-length vectors also count as not visible.
- Estimated positions leave the tracker only in `estL` / `estR`, for display. An estimate lasts a limited time, and losing the camera or a landmark drops its history.
- The UDP payload stays backward compatible: new fields are added, existing ones never change meaning.
- The pose model is downloaded to a temp file, verified, and only then moved into place (pinned version).
- Camera setup checks (`setup` in the packet, M6.3) come from the raw detection and only guide the patient's setup; nothing scored ever reads them.
- The limb directions (`dirL` / `dirR`, M6.4) come from the world landmarks of verified joints and only lean the first-person live limb; nothing scored ever reads them (DEC-023).
- Side-on, the measured side is the limb nearer the camera unless the far one clearly reads more (DEC-026); a hidden far limb never stands in for an unreadable near one.
- Recordings (`--record`) hold landmark numbers only, never images, and stay in the git-ignored `tracker/recordings/` (DEC-024). A replay goes through the same tracking and measuring code as the live camera, so it gives the same packets every run.
- Patient Lock (M10.5): the detector looks for up to two bodies. The first body found (the nearest, if two) is locked as the patient from its 3D bone proportions and where it stands (`tracker/patient_lock.py`). Only the locked body is tracked, measured and scored; another body's landmarks are never measured. `patient` in the packet is `locking | ok | away | different` (and `bodies` the count in view); an older tracker sends neither. A person who is only in view (beside the patient, or behind them and further back) never changes it: `different` needs the patient missing for 1 s with another body standing in their place. A new patient is locked by pressing R in the tracker window, or after 2 minutes with nobody in view. Recordings may hold the second body in `others`; old recordings replay as before. Nothing about a person leaves the tracker except these two fields: no image, no signature.

## Notes
- Single-camera 2D tracking requires positioning the webcam perpendicular to the motion plane (frontal view for abductions, sagittal/side view for flexions/extensions).
- Works with standard RGB webcams at 30 FPS without requiring depth sensors.

## Future Changes
- Multi-camera or depth camera support for non-planar rotational joint tracking.
- Automatic camera orientation and distance calibration detection.
