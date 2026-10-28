"""
TheraQuest - Motion Tracking Module (webcam + MediaPipe Pose -> Unity over UDP)

Pipeline (Section 3.6.3, Motion Tracking Module):
  Frame Preprocessor -> Pose Estimator -> Joint Angle Calculator -> Motion Data Packager

Usage:
  python tracker.py                 # webcam 0, sends to Unity on 127.0.0.1:5005
  python tracker.py --camera 1      # use a second (USB) webcam
  python tracker.py --fake          # no camera: sends simulated angles (tests the Unity link)

Press Q in the preview window to quit.
"""
import argparse
import hashlib
import json
import math
import os
import socket
import sys
import time
import urllib.request

from angles import empty_packet, measure

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
    # DirectShow first on Windows; Media Foundation as a fallback, because some
    # virtual cameras (DroidCam Video) only open through it.
    return (cv2.CAP_DSHOW, cv2.CAP_MSMF) if os.name == "nt" else (cv2.CAP_ANY,)


def open_camera(cv2, cam_index):
    *fallbacks, last = camera_backends(cv2)
    for backend in fallbacks:
        cap = open_with_backend(cv2, cam_index, backend)
        if cap.isOpened():
            return cap
        cap.release()
    return open_with_backend(cv2, cam_index, last)


def open_with_backend(cv2, cam_index, backend):
    cap = cv2.VideoCapture(cam_index, backend)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
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
        packet = {"ts": round(t, 3), "visible": True, "side": "R", **angles,
                  "trunkLean": 3.0, "elbowDrift": 8.0, "L": angles, "R": angles}
        send(sock, addr, packet)
        time.sleep(1 / 30)


def run_camera(sock, addr, cam_index, model_kind, mirror):
    try:
        import cv2
        import mediapipe as mp
        from mediapipe.tasks import python as mp_python
        from mediapipe.tasks.python import vision
    except ImportError as e:
        sys.exit(f"Missing package: {e.name}. Run:  pip install -r requirements.txt")

    landmarker = vision.PoseLandmarker.create_from_options(
        vision.PoseLandmarkerOptions(
            base_options=mp_python.BaseOptions(model_asset_path=ensure_model(model_kind)),
            running_mode=vision.RunningMode.VIDEO,
            num_poses=1,
            min_pose_detection_confidence=0.5,
            min_pose_presence_confidence=0.5,
            min_tracking_confidence=0.5,
        )
    )

    cap = open_camera(cv2, cam_index)
    if not cap.isOpened():
        sys.exit(f"Could not open camera {cam_index}. Try --camera 1, or close other apps using the webcam.")

    print(f"Tracking. Sending to Unity at {addr[0]}:{addr[1]}. Press Q in the window to quit.")
    t0 = time.time()
    last_ts = -1
    fps, fps_t, fps_n = 0.0, time.time(), 0
    misses = 0

    while True:
        ok, frame = cap.read()
        if not ok:
            # A few dropped frames are normal; a run of them means the camera is gone.
            misses += 1
            if misses < 10:
                if wait_keep_responsive(cv2, 0.05):
                    break
                continue
            empty = empty_packet()
            empty["ts"] = round(time.time() - t0, 3)
            send(sock, addr, empty)      # tell Unity nobody is tracked while we reconnect
            cap = reopen_camera(cv2, cap, cam_index)
            if cap is None:
                break
            misses = 0
            continue
        misses = 0
        h, w = frame.shape[:2]

        # Frame Preprocessor: BGR -> RGB (MediaPipe expects RGB)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

        # Pose Estimator (timestamps must strictly increase)
        ts = int((time.time() - t0) * 1000)
        if ts <= last_ts:
            ts = last_ts + 1
        last_ts = ts
        result = landmarker.detect_for_video(image, ts)

        if result.pose_landmarks:
            lms = result.pose_landmarks[0]
            pts = [(l.x, l.y, l.visibility if l.visibility is not None else 1.0) for l in lms]
            # Joint Angle Calculator + Motion Data Packager
            packet = measure(pts, w, h)
            packet["ts"] = round(ts / 1000, 3)
            draw_skeleton(cv2, frame, pts)
        else:
            packet = empty_packet()
            packet["ts"] = round(ts / 1000, 3)
        send(sock, addr, packet)

        # Mirror only the preview (detection runs on the raw frame so left/right stay correct)
        if mirror:
            frame = cv2.flip(frame, 1)
        if packet["visible"]:
            draw_text(cv2, frame, packet)
        else:
            cv2.putText(frame, "No person detected - step into view", (20, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, (60, 60, 255), 2)

        fps_n += 1
        if time.time() - fps_t >= 1:
            fps, fps_t, fps_n = fps_n / (time.time() - fps_t), time.time(), 0
        cv2.putText(frame, f"{fps:.0f} fps", (w - 110, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 200), 2)
        cv2.imshow("TheraQuest tracker (Q to quit)", frame)
        if cv2.waitKey(1) & 0xFF in (ord("q"), ord("Q")):
            break

    if cap is not None:
        cap.release()
    cv2.destroyAllWindows()


def draw_skeleton(cv2, frame, pts):
    h, w = frame.shape[:2]
    P = lambda i: (int(pts[i][0] * w), int(pts[i][1] * h))
    for a, b in BONES:
        if pts[a][2] > 0.5 and pts[b][2] > 0.5:
            cv2.line(frame, P(a), P(b), (180, 220, 210), 3)
    for i in (11, 12, 13, 14, 15, 16, 23, 24, 25, 26, 27, 28):
        if pts[i][2] > 0.5:
            cv2.circle(frame, P(i), 6, (124, 138, 11), -1)


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
    args = ap.parse_args()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    addr = (args.host, args.port)
    try:
        if args.fake:
            run_fake(sock, addr)
        else:
            run_camera(sock, addr, args.camera, args.model, not args.no_mirror)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
