"""
TheraQuest - Record and replay the tracker's landmarks (M6.1, DEC-024).

A recording is a JSON Lines file:
  line 1   {"type": "header", "version": 1, "width": W, "height": H, "model": "lite", "created": "..."}
  then one line per camera frame:
           {"t": seconds, "pose": [[x, y, visibility, presence] * 33] or null,
                          "world": [[x, y, z, visibility, presence] * 33] or null}
           plus, when the detector found a second body (M10.5), "others": [{"pose": ..., "world": ...}]
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

from patient_lock import Body
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

    @staticmethod
    def _pose(pose):
        return None if pose is None else [[_r(x), _r(y), _r(v, 4), _r(p, 4)] for x, y, v, p in pose]

    @staticmethod
    def _world(world):
        return None if world is None else [[_r(x), _r(y), _r(z), _r(v, 4), _r(p, 4)] for x, y, z, v, p in world]

    def frame(self, t, pose, world=None, others=()):
        """pose: 33 (x, y, visibility, presence) or None; world: 33 (x, y, z, visibility, presence) or None.
        others: further bodies as (pose, world) pairs (M10.5)."""
        extra = {"others": [{"pose": self._pose(p), "world": self._world(w)} for p, w in others]} if others else {}
        self._write({
            "t": round(float(t), 4),
            "pose": None if pose is None else [[_r(x), _r(y), _r(v, 4), _r(p, 4)] for x, y, v, p in pose],
            "world": None if world is None else [[_r(x), _r(y), _r(z), _r(v, 4), _r(p, 4)]
                                                 for x, y, z, v, p in world],
            **extra,
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
            bodies = []
            for p, w in [(rec.get("pose"), rec.get("world"))] + [(o["pose"], o.get("world")) for o in rec.get("others", [])]:
                if p is not None:
                    bodies.append(Body([(x, y, landmark_confidence(v, c)) for x, y, v, c in p], w))
            pose.update_bodies(bodies, t, width / height)
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
            world = [((x - 0.5) * W / H, y - 0.5, 0.0, v, p) for x, y, v, p in pose]    # metres-like, same scale both ways
            rec.frame(t, pose, world)
    return path


# A body for the two-person recording: lengths in metres (standing, facing the camera)
PATIENT_BODY = dict(torso=0.50, sh=0.40, hip=0.26, ua=0.30, fa=0.26, th=0.42, sk=0.42)
OTHER_BODY = dict(torso=0.55, sh=0.34, hip=0.30, ua=0.26, fa=0.21, th=0.50, sk=0.37)


def _person(W, H, body, cx, ytop, scale, lift=0.0):
    """(pose, world) of one made-up body: shoulders at ytop, left arm raised `lift` degrees sideways, `scale` pixels
    per metre. Only the shoulders, hips, arms, legs and nose are seen, like the single-person recording."""
    a = math.radians(lift)
    m = {11: (body["sh"] / 2, 0.0), 12: (-body["sh"] / 2, 0.0), 23: (body["hip"] / 2, body["torso"]),
         24: (-body["hip"] / 2, body["torso"])}
    m[13] = (m[11][0] + body["ua"] * math.sin(a), body["ua"] * math.cos(a))
    m[15] = (m[13][0] + body["fa"] * math.sin(a), m[13][1] + body["fa"] * math.cos(a))
    m[14] = (m[12][0], body["ua"])
    m[16] = (m[12][0], body["ua"] + body["fa"])
    m[25], m[26] = (m[23][0], body["torso"] + body["th"]), (m[24][0], body["torso"] + body["th"])
    m[27], m[28] = (m[25][0], m[25][1] + body["sk"]), (m[26][0], m[26][1] + body["sk"])
    m[0] = (0.0, -0.22)
    pose, world = [], []
    for i in range(33):
        mx, my = m.get(i, (0.0, 0.2))
        vis = 0.99 if i in m else 0.05
        pose.append((min(1.0, max(0.0, (cx + mx * scale) / W)), min(1.0, max(0.0, (ytop + my * scale) / H)), vis,
                     0.99 if i in m else 0.1))
        world.append((mx, my - body["torso"] / 2, 0.0, vis, 0.99 if i in m else 0.1))
    return pose, world


def synthetic_two_people(path, fps=30.0):
    """A made-up 24 s recording with two people (M10.5), for tests and demos. P is the patient (arm raised once every
    3 s). B, a bystander of a different build, walks in at 2-5 s and stands beside P (and behind P for 8-11 s), until
    22 s. P steps out at 12 s. Q (another build again) takes P's place at 13-18 s and raises the arm. P is back at
    19.5 s. The detector's order of the two bodies swaps every second."""
    W, H = 640, 480
    with Recorder(path, W, H, model="synthetic") as rec:
        for k in range(int(24.0 * fps)):
            t = k / fps
            people = []
            lift = lambda: 90.0 * (0.5 - 0.5 * math.cos(2 * math.pi * t / 3.0))
            if t < 12.0 or t >= 19.5:
                people.append(_person(W, H, PATIENT_BODY, 240, 60, 300, lift()))
            if 2.0 <= t < 22.0:
                if 8.0 <= t < 11.0:
                    people.append(_person(W, H, OTHER_BODY, 240, 90, 190))             # behind the patient, further back
                else:
                    cx = 560 if t >= 5.0 else 650 - 90 * (t - 2.0) / 3.0
                    people.append(_person(W, H, OTHER_BODY, cx, 80, 240))
            if 13.0 <= t < 18.0:
                q = dict(OTHER_BODY, sh=0.37, ua=0.28)
                people.append(_person(W, H, q, 250, 60, 300, lift()))
            if int(t) % 2 == 1:
                people.reverse()
            if not people:
                rec.frame(t, None, None)
            else:
                rec.frame(t, people[0][0], people[0][1], people[1:])
    return path
