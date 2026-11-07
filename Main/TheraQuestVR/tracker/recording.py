"""
TheraQuest - Record and replay the tracker's landmarks (M6.1, DEC-024).

A recording is a JSON Lines file:
  line 1   {"type": "header", "version": 1, "width": W, "height": H, "model": "lite", "created": "..."}
  then one line per camera frame:
           {"t": seconds, "pose": [[x, y, visibility, presence] * 33] or null,
                          "world": [[x, y, z, visibility, presence] * 33] or null}
  and      {"t": seconds, "event": "camera_lost"} when the webcam stopped delivering frames.

Only landmark numbers are saved, never images (DEC-024). Keep recordings in tracker/recordings/,
which git ignores, and name them by date or patient code, never by a real name.

Replaying sends a recording through the same PoseTracker and measure code as the live camera,
so a recording gives the same packets on every run. Pure Python: no camera or MediaPipe needed.
"""
import json
import math
import os
import time

from tracking import PoseTracker, landmark_confidence

VERSION = 1
HERE = os.path.dirname(os.path.abspath(__file__))
RECORDINGS_DIR = os.path.join(HERE, "recordings")


def default_path(now=None):
    """recordings/YYYYMMDD-HHMMSS.jsonl (a date, never a name)."""
    stamp = time.strftime("%Y%m%d-%H%M%S", time.localtime(now))
    return os.path.join(RECORDINGS_DIR, f"{stamp}.jsonl")


def _r(v, places=5):
    return None if v is None else round(float(v), places)


class Recorder:
    """Writes a recording while the tracker runs. Use as a context manager, or call close()."""

    def __init__(self, path, width, height, model="lite"):
        folder = os.path.dirname(os.path.abspath(path))
        os.makedirs(folder, exist_ok=True)
        self.path = path
        self.frames = 0
        self._f = open(path, "w", encoding="utf-8")
        self._write({"type": "header", "version": VERSION, "width": int(width), "height": int(height),
                     "model": model, "created": time.strftime("%Y-%m-%dT%H:%M:%S")})

    def _write(self, obj):
        self._f.write(json.dumps(obj, separators=(",", ":")) + "\n")

    def frame(self, t, pose, world=None):
        """pose: 33 (x, y, visibility, presence) or None; world: 33 (x, y, z, visibility, presence) or None."""
        self._write({
            "t": round(float(t), 4),
            "pose": None if pose is None else [[_r(x), _r(y), _r(v, 4), _r(p, 4)] for x, y, v, p in pose],
            "world": None if world is None else [[_r(x), _r(y), _r(z), _r(v, 4), _r(p, 4)]
                                                 for x, y, z, v, p in world],
        })
        self.frames += 1

    def camera_lost(self, t):
        self._write({"t": round(float(t), 4), "event": "camera_lost"})

    def close(self):
        if not self._f.closed:
            self._f.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


def load(path):
    """(header, records). Raises ValueError for a file that isn't a recording."""
    with open(path, encoding="utf-8") as f:
        lines = [json.loads(line) for line in f if line.strip()]
    if not lines or lines[0].get("type") != "header":
        raise ValueError(f"{path} is not a TheraQuest recording (no header line)")
    header = lines[0]
    if header.get("version") != VERSION:
        raise ValueError(f"{path}: recording version {header.get('version')} is not supported (expected {VERSION})")
    return header, lines[1:]


def replay(path, realtime=False, sleep=time.sleep):
    """Yield (record, packet, pose) for every frame, computed exactly as the live tracker does.
    `pose` is the PoseTracker after that frame (for reports); packets carry "ts" like live ones."""
    header, records = load(path)
    width, height = header["width"], header["height"]
    pose = PoseTracker()
    start_wall, start_t = time.monotonic(), None
    for rec in records:
        t = rec["t"]
        if realtime:
            if start_t is None:
                start_t = t
            wait = (t - start_t) - (time.monotonic() - start_wall)
            if wait > 0:
                sleep(wait)
        if rec.get("event") == "camera_lost":
            pose.reset()
            packet = pose.packet(1, 1)
        else:
            pts = None
            if rec.get("pose") is not None:
                pts = [(x, y, landmark_confidence(v, p)) for x, y, v, p in rec["pose"]]
            pose.update(pts, t, rec.get("world"))
            packet = pose.packet(width, height)
        packet["ts"] = round(t, 3)
        yield rec, packet, pose


def synthetic(path, seconds=12.0, fps=30.0):
    """Write a made-up recording for tests and demos: a person facing the camera raising the left arm
    sideways once every 3 s, the left wrist hidden for 1 s at t = 4 s, and nobody in view at 8-10.5 s."""
    W, H = 640, 480
    base = {11: (360, 160), 12: (280, 160), 23: (360, 300), 24: (280, 300), 25: (360, 380), 26: (280, 380),
            27: (360, 460), 28: (280, 460), 14: (280, 240), 16: (280, 310), 0: (320, 110), 7: (345, 105),
            8: (295, 105)}
    with Recorder(path, W, H, model="synthetic") as rec:
        for k in range(int(seconds * fps)):
            t = k / fps
            if 8.0 <= t < 10.5:
                rec.frame(t, None, None)
                continue
            lift = 90.0 * (0.5 - 0.5 * math.cos(2 * math.pi * t / 3.0))     # 0..90 degrees from down
            a = math.radians(lift)
            pts = dict(base)
            pts[13] = (360 + 80 * math.sin(a), 160 + 80 * math.cos(a))
            pts[15] = (360 + 150 * math.sin(a), 160 + 150 * math.cos(a))
            pose = []
            for i in range(33):
                x, y = pts.get(i, (320, 240))
                vis = 0.99 if i in pts else 0.05
                if i == 15 and 4.0 <= t < 5.0:
                    vis = 0.1
                pose.append((x / W, y / H, vis, 0.99 if i in pts else 0.1))
            world = [((x - 0.5) * 1.0, (y - 0.5) * 1.6, 0.0, v, p) for x, y, v, p in pose]
            rec.frame(t, pose, world)
    return path
