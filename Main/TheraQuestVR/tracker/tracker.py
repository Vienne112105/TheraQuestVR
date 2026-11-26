"""
TheraQuest - Motion Tracking Module (webcam + MediaPipe Pose -> Unity over UDP)

Pipeline (Section 3.6.3, Motion Tracking Module):
  Frame Preprocessor -> Pose Estimator -> Landmark Tracking -> Joint Angle Calculator -> Motion Data Packager

Usage:
  python tracker.py                 # webcam 0, sends to Unity on 127.0.0.1:5005
  python tracker.py --camera 1      # use a second (USB) webcam
  python tracker.py --fake          # no camera: sends simulated angles (tests the Unity link)
  python tracker.py --record        # also save the landmarks (no images) to recordings/<date-time>.jsonl
  python tracker.py --replay FILE   # no camera: send a recording to Unity as if it were live (--fast: no waiting)

Press Q in the preview window to quit, R to lock onto a new patient (the first body found is the patient, M10.5).
"""
import argparse
import hashlib
import json
import math
import os
import socket
import sys
import threading
import time
import urllib.request

import recording
from patient_lock import Body, DIFFERENT
from tracking import POSE_LOST, POSE_TRACKING, PoseTracker, landmark_confidence

# Pinned model version "1" (not "latest"), so every install runs the same model.
# Sizes / SHA-256 were computed from these exact URLs on 2026-10-20.
MODELS = {
    "lite": {
        "url": "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task",
        "size": 5777746,
        "sha256": "59929e1d1ee95287735ddd833b19cf4ac46d29bc7afddbbf6753c459690d574a",
    },
    "full": {
        "url": "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_full/float16/1/pose_landmarker_full.task",
        "size": 9398198,
        "sha256": "5134a3aad27a58b93da0088d431f366da362b44e3ccfbe3462b3827a839011b1",
    },
}

CAMERA_BACKOFF_MAX = 10.0     # seconds between camera reopen attempts (1, 2, 4, 8, 10, 10 ...)
CAMERA_FPS_REQUEST = 60       # ask for more than needed: the camera gives its highest rate up to this
DETECT_WIDTH = 640            # MediaPipe scales to 256 px inside anyway; a smaller copy only saves time
PREVIEW_WIDTH = 960           # the preview window is drawn at most this wide
GOOD_CAMERA_FPS = 25          # a backend this fast is kept without trying the others

BONES = [(11, 12), (11, 13), (13, 15), (12, 14), (14, 16), (11, 23), (12, 24),
         (23, 24), (23, 25), (25, 27), (24, 26), (26, 28)]


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def model_ok(path, spec):
    """True if the file at `path` is exactly the pinned model (size and SHA-256 match)."""
    return (os.path.isfile(path) and os.path.getsize(path) == spec["size"]
            and _sha256(path) == spec["sha256"])


def ensure_model(kind, here=None, fetch=urllib.request.urlretrieve):
    """Return the path of a verified model file, downloading it if missing or corrupt.
    The download goes to a temp file and only replaces the real file once verified,
    so an interrupted download can never be mistaken for a good model."""
    spec = MODELS[kind]
    here = here or os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(here, f"pose_landmarker_{kind}.task")
    if model_ok(path, spec):
        return path
    if os.path.exists(path):
        print(f"Pose model ({kind}) is incomplete or corrupt; downloading again")
    else:
        print(f"Downloading pose model ({kind}) ... one time only")
    tmp = path + ".part"
    try:
        fetch(spec["url"], tmp)
        if not model_ok(tmp, spec):
            raise RuntimeError(f"Downloaded pose model ({kind}) failed size/SHA-256 check")
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)
    return path


def is_all_black(frame):
    return hasattr(frame, "max") and frame.max() == 0


def camera_backends(cv2):
    # DirectShow first on Windows; Media Foundation as well, because some virtual cameras (DroidCam Video)
    # only open through it, and some webcams only send compressed (fast) video through it.
    return (cv2.CAP_DSHOW, cv2.CAP_MSMF) if os.name == "nt" else (cv2.CAP_ANY,)


def measure_fps(cap, frames=15, skip=5, clock=time.perf_counter):
    """Frames per second a capture really delivers (the camera's own reported rate is often wrong).
    The first `skip` frames are read and dropped: they may be waiting in a buffer and come at once."""
    for _ in range(skip):
        cap.read()
    start, got = clock(), 0
    for _ in range(frames):
        ok, _ = cap.read()
        got += bool(ok)
    elapsed = clock() - start
    return got / elapsed if elapsed > 0 else float("inf")


BUSY_BACKEND_RETRIES = 5      # a backend that failed to open is tried again this many times, 1 s apart


def open_camera(cv2, cam_index, rate=measure_fps, pause=time.sleep):
    """Open the camera through the backend that gives the most frames per second. The same webcam can send
    13 fps of raw video through DirectShow and 30 fps of compressed video through Media Foundation.
    A backend that fails to open is often still busy from a previous run (TASK-015), so while the one that
    did open is slow it is retried for a few seconds before settling for the slow one."""
    backends = camera_backends(cv2)
    best, best_fps, cap = None, -1.0, None
    failed = []

    def consider(backend):
        nonlocal best, best_fps, cap
        cap = open_with_backend(cv2, cam_index, backend)
        if not cap.isOpened():
            if backend != backends[-1] or best is not None:
                cap.release()
            return False
        if len(backends) == 1:
            best, best_fps = cap, float("inf")
            return True
        fps = rate(cap)
        if fps > best_fps:
            if best is not None:
                best.release()
            best, best_fps = cap, fps
        else:
            cap.release()
        return True

    for backend in backends:
        if not consider(backend):
            failed.append(backend)
        elif best_fps >= GOOD_CAMERA_FPS:
            break
    if best is not None and best_fps < GOOD_CAMERA_FPS:
        for _ in range(BUSY_BACKEND_RETRIES):
            if not failed or best_fps >= GOOD_CAMERA_FPS:
                break
            pause(1)
            failed = [b for b in failed if not consider(b)]
    return best if best is not None else cap


def open_with_backend(cv2, cam_index, backend):
    cap = cv2.VideoCapture(cam_index, backend)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    cap.set(cv2.CAP_PROP_FPS, CAMERA_FPS_REQUEST)
    if not cap.isOpened():
        return cap
    # Some webcams accept a size request and then send only black frames. If about
    # one second of frames is pure black (cameras may start with a few), reopen at
    # the camera's own size.
    for _ in range(30):
        ok, frame = cap.read()
        if ok and not is_all_black(frame):
            return cap
    cap.release()
    print(f"Camera {cam_index} gives black frames at 1280x720; using its default size.")
    return cv2.VideoCapture(cam_index, backend)


def wait_keep_responsive(cv2, seconds):
    """Sleep for `seconds` while still pumping the preview window; True if Q was pressed."""
    end = time.time() + seconds
    while True:
        if cv2.waitKey(50) & 0xFF in (ord("q"), ord("Q")):
            return True
        if time.time() >= end:
            return False
        time.sleep(0.01)   # waitKey returns at once when no window is open yet


def reopen_camera(cv2, cap, cam_index, sleep=wait_keep_responsive):
    """Camera stopped delivering frames: release it and retry with exponential backoff
    (1 s, 2 s, 4 s ... capped at CAMERA_BACKOFF_MAX). Returns the new capture, or None
    if the user pressed Q while waiting."""
    cap.release()
    delay = 1.0
    while True:
        print(f"Camera {cam_index} lost; reopening in {delay:.0f} s (Q to quit) ...")
        if sleep(cv2, delay):
            return None
        cap = open_camera(cv2, cam_index)
        if cap.isOpened():
            ok, _ = cap.read()
            if ok:
                print("Camera reconnected.")
                return cap
        cap.release()
        delay = min(delay * 2, CAMERA_BACKOFF_MAX)


class FrameGrabber:
    """Reads the camera on its own thread and keeps only the newest frame, so a slow detection step
    never makes the loop wait for the camera (or work on an old, buffered frame)."""

    def __init__(self, cap):
        self.cap = cap
        self._lock = threading.Condition()
        self._frame, self._ok, self._seq, self._taken = None, True, 0, 0
        self._running = True
        self._times = []
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def _loop(self):
        while self._running:
            ok, frame = self.cap.read()
            with self._lock:
                self._ok, self._seq = ok, self._seq + 1
                if ok:
                    self._frame = frame
                    self._times = (self._times + [time.time()])[-31:]
                self._lock.notify_all()
            if not ok:
                time.sleep(0.02)

    def read(self, timeout=1.0):
        """(ok, frame): the next frame not handed out yet; (False, None) on a failed read or a timeout."""
        with self._lock:
            if not self._lock.wait_for(lambda: self._seq > self._taken, timeout):
                return False, None
            self._taken = self._seq
            return (True, self._frame) if self._ok else (False, None)

    @property
    def fps(self):
        """Frames per second the camera is delivering (last ~30 frames)."""
        with self._lock:
            t = self._times
            return (len(t) - 1) / (t[-1] - t[0]) if len(t) > 1 and t[-1] > t[0] else 0.0

    def stop(self):
        """Stop reading; the capture itself stays open (the caller releases or reopens it)."""
        self._running = False
        self._thread.join(timeout=2.0)
        return self.cap


def detection_frame(cv2, frame):
    """A copy at most DETECT_WIDTH wide for MediaPipe; landmarks are 0..1, so they still fit the full frame."""
    h, w = frame.shape[:2]
    if w <= DETECT_WIDTH:
        return frame
    return cv2.resize(frame, (DETECT_WIDTH, round(h * DETECT_WIDTH / w)), interpolation=cv2.INTER_AREA)


def send(sock, addr, packet):
    sock.sendto(json.dumps(packet).encode("utf-8"), addr)


def run_fake(sock, addr):
    """Simulated patient: smooth reps on every joint, so Unity can be tested without a webcam."""
    print(f"Sending simulated angles to {addr[0]}:{addr[1]}  (Ctrl+C to stop)")
    t0 = time.time()
    while True:
        t = time.time() - t0
        wave = 0.5 - 0.5 * math.cos(2 * math.pi * t / 3.0)     # 0..1, one rep every 3 s
        angles = {
            "shoulderElev": round(92 * wave, 1),
            "elbowFlex": round(128 * wave, 1),
            "hipElev": round(47 * wave, 1),
            "kneeFlex": round(88 * wave, 1),
            "kneeExt": round(78 * wave, 1),
            "shoulderElevSigned": round(92 * wave, 1),
            "hipElevSigned": round(47 * wave, 1),
        }
        packet = {"ts": round(t, 3), "visible": True, "side": "R", "trackingState": POSE_TRACKING, "patient": "ok", "bodies": 1, **angles,
                  "trunkLean": 3.0, "elbowDrift": 8.0, "L": angles, "R": angles}
        send(sock, addr, packet)
        time.sleep(1 / 30)


def run_replay(sock, addr, path, fast):
    """Send a recording (M6.1) through the same tracking code as the live camera."""
    header, _ = recording.load(path)
    print(f"Replaying {path} ({header.get('model')} model, {header['width']}x{header['height']}) "
          f"to {addr[0]}:{addr[1]}{' as fast as possible' if fast else ''}  (Ctrl+C to stop)")
    n = 0
    for _, packet, _ in recording.replay(path, realtime=not fast):
        send(sock, addr, packet)
        n += 1
    print(f"Done: {n} packets sent.")


def raw_landmarks(result):
    """MediaPipe's poses (up to two bodies, M10.5) as plain tuples for a recording: a list of
    (2D [(x, y, visibility, presence)], 3D world [(x, y, z, visibility, presence)] or None), empty when nobody is found."""
    out = []
    worlds = getattr(result, "pose_world_landmarks", None) or []
    for k, lms in enumerate(result.pose_landmarks or []):
        pose = [(l.x, l.y, l.visibility, l.presence) for l in lms]
        world = [(l.x, l.y, l.z, l.visibility, l.presence) for l in worlds[k]] if k < len(worlds) else None
        out.append((pose, world))
    return out


def run_camera(sock, addr, cam_index, model_kind, mirror, record_path=None):
    # Media Foundation's hardware transforms can take ~30 s to open a webcam; without them it takes ~2 s.
    os.environ.setdefault("OPENCV_VIDEOIO_MSMF_ENABLE_HW_TRANSFORMS", "0")
    try:
        import cv2
        import mediapipe as mp
        from mediapipe.tasks import python as mp_python
        from mediapipe.tasks.python import vision
    except ImportError as e:
        sys.exit(f"Missing package: {e.name}. Run:  pip install -r requirements.txt")

    model_path = ensure_model(model_kind)

    def make_landmarker():
        return vision.PoseLandmarker.create_from_options(
            vision.PoseLandmarkerOptions(
                base_options=mp_python.BaseOptions(model_asset_path=model_path),
                running_mode=vision.RunningMode.VIDEO,
                num_poses=2,                 # the patient and one other body (Patient Lock, M10.5)
                min_pose_detection_confidence=0.5,
                min_pose_presence_confidence=0.5,
                min_tracking_confidence=0.5,
            )
        )

    landmarker = make_landmarker()
    pose = PoseTracker()

    cap = open_camera(cv2, cam_index)
    if not cap.isOpened():
        sys.exit(f"Could not open camera {cam_index}. Try --camera 1, or close other apps using the webcam.")

    print(f"Camera {cam_index}: {int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))}x{int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))} "
          f"through {cap.getBackendName()} (the preview shows the live frame rates)")
    grabber = FrameGrabber(cap)
    print(f"Tracking. Sending to Unity at {addr[0]}:{addr[1]}. Press Q in the window to quit.")
    t0 = time.time()
    last_ts = -1
    fps, fps_t, fps_n = 0.0, time.time(), 0
    misses = 0
    recorder = None
    if record_path:
        print(f"Recording landmarks (no images) to {record_path}")

    while True:
        ok, frame = grabber.read()
        if not ok:
            # A few dropped frames are normal; a run of them means the camera is gone.
            misses += 1
            if misses < 10:
                if wait_keep_responsive(cv2, 0.05):
                    break
                continue
            pose.reset()                 # no estimate survives losing the camera
            empty = pose.packet(1, 1)
            empty["ts"] = round(time.time() - t0, 3)
            send(sock, addr, empty)      # tell Unity nobody is tracked while we reconnect
            if recorder:
                recorder.camera_lost(empty["ts"])
            cap = reopen_camera(cv2, grabber.stop(), cam_index)
            if cap is None:
                grabber = None
                break
            grabber = FrameGrabber(cap)
            misses = 0
            continue
        misses = 0
        h, w = frame.shape[:2]

        # Frame Preprocessor: BGR -> RGB (MediaPipe expects RGB)
        rgb = cv2.cvtColor(detection_frame(cv2, frame), cv2.COLOR_BGR2RGB)
        image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

        # Pose Estimator (timestamps must strictly increase)
        ts = int((time.time() - t0) * 1000)
        if ts <= last_ts:
            ts = last_ts + 1
        last_ts = ts
        result = landmarker.detect_for_video(image, ts)
        found = raw_landmarks(result)
        if record_path:
            if recorder is None:
                recorder = recording.Recorder(record_path, w, h, model_kind)
            if found:
                recorder.frame(ts / 1000, found[0][0], found[0][1], found[1:])
            else:
                recorder.frame(ts / 1000, None, None)

        # Landmark Tracking: trust, smoothing, short-term prediction (tracking.py, DEC-022). Only the locked
        # patient's body is tracked; any other body is never measured (patient_lock.py, M10.5).
        bodies = [Body([(x, y, landmark_confidence(v, p)) for x, y, v, p in lm], wd) for lm, wd in found]
        pose.update_bodies(bodies, ts / 1000, w / h)
        if pose.should_redetect(ts / 1000):
            # MediaPipe re-detects by itself when it finds nobody; a pose it keeps reporting but we
            # can't track may be a bad lock, so restart it to force a fresh detection.
            landmarker.close()
            landmarker = make_landmarker()

        # Joint Angle Calculator + Motion Data Packager: measured angles use verified landmarks only
        packet = pose.packet(w, h)
        packet["ts"] = round(ts / 1000, 3)
        draw_skeleton(cv2, frame, pose)
        send(sock, addr, packet)

        # Mirror only the preview (detection runs on the raw frame so left/right stay correct)
        if mirror:
            frame = cv2.flip(frame, 1)
        if packet.get("patient") == DIFFERENT:
            cv2.putText(frame, "Another person - paused until the patient is back (R: new patient)", (20, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (60, 60, 255), 2)
        elif packet["trackingState"] == POSE_TRACKING:
            draw_text(cv2, frame, packet)
        else:
            text = "No person detected - step into view" if packet["trackingState"] == POSE_LOST else "Move back into view"
            cv2.putText(frame, text, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (60, 60, 255), 2)

        fps_n += 1
        if time.time() - fps_t >= 1:
            fps, fps_t, fps_n = fps_n / (time.time() - fps_t), time.time(), 0
        cv2.putText(frame, f"{fps:.0f} fps (camera {grabber.fps:.0f})", (w - 290, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                    (200, 200, 200), 2)
        if w > PREVIEW_WIDTH:
            frame = cv2.resize(frame, (PREVIEW_WIDTH, round(h * PREVIEW_WIDTH / w)), interpolation=cv2.INTER_AREA)
        cv2.imshow("TheraQuest tracker (Q to quit)", frame)
        key = cv2.waitKey(1) & 0xFF
        if key in (ord("q"), ord("Q")):
            break
        if key in (ord("r"), ord("R")):
            pose.relock()
            print("Patient lock cleared: the next body found is the patient.")

    if grabber is not None:
        grabber.stop().release()
    if recorder:
        recorder.close()
        print(f"Saved {recorder.frames} frames to {recorder.path}")
    cv2.destroyAllWindows()


def draw_skeleton(cv2, frame, pose):
    """Verified landmarks in the usual colours; estimates in orange, as hollow circles, so they can't be mistaken."""
    h, w = frame.shape[:2]
    tracks = pose.tracks
    P = lambda i: (int(tracks[i].x * w), int(tracks[i].y * h))
    for a, b in BONES:
        if tracks[a].has_position and tracks[b].has_position:
            verified = tracks[a].reliable and tracks[b].reliable
            cv2.line(frame, P(a), P(b), (180, 220, 210) if verified else (44, 114, 243), 3 if verified else 1)
    for i in (11, 12, 13, 14, 15, 16, 23, 24, 25, 26, 27, 28):
        if tracks[i].reliable:
            cv2.circle(frame, P(i), 6, (124, 138, 11), -1)
        elif tracks[i].has_position:
            cv2.circle(frame, P(i), 6, (44, 114, 243), 2)


def draw_text(cv2, frame, packet):
    lines = [
        f"Shoulder:   {packet['shoulderElev']:6.1f}",
        f"Elbow flex: {packet['elbowFlex']:6.1f}",
        f"Hip:        {packet['hipElev']:6.1f}",
        f"Knee flex:  {packet['kneeFlex']:6.1f}",
        f"Trunk lean: {packet['trunkLean']:6.1f}",
        f"Side: {packet['side']}",
    ]
    for k, text in enumerate(lines):
        cv2.putText(frame, text, (20, 40 + 30 * k), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)


def main():
    ap = argparse.ArgumentParser(description="TheraQuest webcam motion tracker")
    ap.add_argument("--camera", type=int, default=0, help="webcam index (0 = built-in)")
    ap.add_argument("--host", default="127.0.0.1", help="IP of the computer running Unity")
    ap.add_argument("--port", type=int, default=5005)
    ap.add_argument("--model", choices=["lite", "full"], default="lite",
                    help="lite = faster, full = more accurate")
    ap.add_argument("--no-mirror", action="store_true", help="don't mirror the preview")
    ap.add_argument("--fake", action="store_true", help="send simulated angles, no camera")
    ap.add_argument("--record", nargs="?", const="", default=None, metavar="FILE",
                    help="also save the landmarks (never images) to FILE, default recordings/<date-time>.jsonl")
    ap.add_argument("--replay", metavar="FILE", help="send a recording instead of using the camera")
    ap.add_argument("--fast", action="store_true", help="with --replay: send as fast as possible")
    args = ap.parse_args()
    if args.replay and (args.fake or args.record is not None):
        ap.error("--replay can't be combined with --fake or --record")
    record_path = None
    if args.record is not None:
        if args.fake:
            ap.error("--record needs the camera (it saves landmarks, and --fake has none)")
        record_path = args.record or recording.default_path()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    addr = (args.host, args.port)
    try:
        if args.fake:
            run_fake(sock, addr)
        elif args.replay:
            run_replay(sock, addr, args.replay, args.fast)
        else:
            run_camera(sock, addr, args.camera, args.model, not args.no_mirror, record_path)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
