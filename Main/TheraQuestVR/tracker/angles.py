"""
TheraQuest - Joint Angle Calculator (Motion Tracking Module, Section 3.6.3).

Pure math, no camera or MediaPipe needed, so it can be unit-tested on its own.

Every angle is a "range of motion" (ROM) value that starts at 0 degrees in the
resting position and increases as the patient moves toward the therapist's
target. Unity compares it to the target angle. One measured angle serves
several exercises; the camera view decides which plane of motion it sees.

  shoulderElev  angle between trunk (shoulder->hip) and upper arm (shoulder->elbow)
                0 = arm at the side. Abduction / scaption (front view),
                flexion / wall slide (side view)
  elbowFlex     180 - interior elbow angle (shoulder-elbow-wrist)
                0 = arm straight, ~140 = fully bent
  hipElev       180 - interior hip angle (shoulder-hip-knee)
                0 = leg in line with the trunk. Hip abduction (front view),
                straight leg raise / marching (side view)
  kneeFlex      180 - interior knee angle (hip-knee-ankle)
                0 = leg straight. Heel slides, mini squat (side view)
  kneeExt       interior knee angle - 90
                0 = knee bent to 90, 90 = leg straight. Seated knee extension,
                sit-to-stand (side view)

Signed variants (side view only; per side in "L"/"R" and best side at top level):
  shoulderElevSigned  same magnitude as shoulderElev, signed by direction
  hipElevSigned       same magnitude as hipElev, signed by direction
                Measured from the trunk direction (shoulder->hip line, pointing
                toward the feet) to the limb (shoulder->elbow / hip->knee).
                Sign convention:
                  POSITIVE = limb in front of the trunk (shoulder / hip FLEXION)
                  NEGATIVE = limb behind the trunk (shoulder / hip EXTENSION)
                "Front" is the side of the trunk line the nose is on (the ear as a
                fallback), which holds standing, seated or lying in side view.
                In front view the sign is meaningless; use the unsigned field.
                SIGNED_INVALID (-999) = can't be measured (a landmark hidden, or
                facing unknown). -1 is a real signed value, so it can't be used.

"Not visible": every unsigned angle, trunkLean and elbowDrift is -1 when ANY
landmark it uses has visibility below MIN_VISIBILITY, or when landmarks sit on
top of each other so that no angle exists.

MediaPipe Pose landmark indices used below:
  0 nose, 7/8 ears, 11/12 shoulders, 13/14 elbows, 15/16 wrists, 23/24 hips,
  25/26 knees, 27/28 ankles
  (odd = patient's LEFT side, even = patient's RIGHT side)
"""
import math

NOSE, L_EAR, R_EAR = 0, 7, 8
L_SHOULDER, R_SHOULDER = 11, 12
L_ELBOW, R_ELBOW = 13, 14
L_WRIST, R_WRIST = 15, 16
L_HIP, R_HIP = 23, 24
L_KNEE, R_KNEE = 25, 26
L_ANKLE, R_ANKLE = 27, 28

# Which three landmarks (a, b, c) form the measured angle at joint b, per side.
JOINTS = {
    "shoulderElev": {"L": (L_HIP, L_SHOULDER, L_ELBOW), "R": (R_HIP, R_SHOULDER, R_ELBOW)},
    "elbowFlex":    {"L": (L_SHOULDER, L_ELBOW, L_WRIST), "R": (R_SHOULDER, R_ELBOW, R_WRIST)},
    "hipElev":      {"L": (L_SHOULDER, L_HIP, L_KNEE), "R": (R_SHOULDER, R_HIP, R_KNEE)},
    "kneeFlex":     {"L": (L_HIP, L_KNEE, L_ANKLE), "R": (R_HIP, R_KNEE, R_ANKLE)},
    "kneeExt":      {"L": (L_HIP, L_KNEE, L_ANKLE), "R": (R_HIP, R_KNEE, R_ANKLE)},
}

# Signed variants: (joint, limb end) per side, and the unsigned angle they mirror.
SIGNED = {
    "shoulderElevSigned": {"L": (L_SHOULDER, L_ELBOW), "R": (R_SHOULDER, R_ELBOW), "base": "shoulderElev"},
    "hipElevSigned":      {"L": (L_HIP, L_KNEE), "R": (R_HIP, R_KNEE), "base": "hipElev"},
}
TRUNK = {"L": (L_SHOULDER, L_HIP), "R": (R_SHOULDER, R_HIP)}
EAR = {"L": L_EAR, "R": R_EAR}

MIN_VISIBILITY = 0.5
NOT_VISIBLE = -1.0
SIGNED_INVALID = -999.0


def angle_at(a, b, c):
    """Interior angle ABC in degrees, using 2D image coordinates (x, y).
    Returns -1 when A or C sits on B (zero-length vector: no angle exists)."""
    v1 = (a[0] - b[0], a[1] - b[1])
    v2 = (c[0] - b[0], c[1] - b[1])
    n1 = math.hypot(*v1)
    n2 = math.hypot(*v2)
    if n1 == 0 or n2 == 0:
        return NOT_VISIBLE
    cos = (v1[0] * v2[0] + v1[1] * v2[1]) / (n1 * n2)
    cos = max(-1.0, min(1.0, cos))
    return math.degrees(math.acos(cos))


def signed_angle(v1, v2):
    """Signed angle in degrees from vector v1 to v2 (-180..180), None if either has zero length."""
    if math.hypot(*v1) == 0 or math.hypot(*v2) == 0:
        return None
    cross = v1[0] * v2[1] - v1[1] * v2[0]
    dot = v1[0] * v2[0] + v1[1] * v2[1]
    return math.degrees(math.atan2(cross, dot))


def to_rom(name, interior):
    if name == "shoulderElev":
        return interior
    if name in ("elbowFlex", "hipElev", "kneeFlex"):
        return 180.0 - interior
    if name == "kneeExt":
        return interior - 90.0
    raise ValueError(name)


def _visibility(points, idxs):
    """A joint is only as visible as its least-visible landmark."""
    return min(points[i][2] for i in idxs)


def _visible(points, idxs):
    return _visibility(points, idxs) >= MIN_VISIBILITY


def _vec(p, q):
    return (q[0] - p[0], q[1] - p[1])


def facing(px, side):
    """+1 / -1: which side of this side's trunk line (shoulder->hip) is the patient's
    front, judged by where the nose (or the ear) lies. 0 when it can't be told."""
    sh, hip = TRUNK[side]
    if not _visible(px, (sh, hip)):
        return 0
    trunk = _vec(px[sh], px[hip])
    for head in (NOSE, EAR[side]):
        if px[head][2] < MIN_VISIBILITY:
            continue
        to_head = _vec(px[sh], px[head])
        cross = trunk[0] * to_head[1] - trunk[1] * to_head[0]
        if cross != 0:
            return 1 if cross > 0 else -1
    return 0


def side_signed(px, side):
    """Signed shoulder / hip elevation for one side (sign convention at the top of the file)."""
    face = facing(px, side)
    trunk = _vec(*(px[i] for i in TRUNK[side]))
    out = {}
    for name, spec in SIGNED.items():
        joint, end = spec[side]
        ang = None
        if face != 0 and _visible(px, (joint, end)):
            ang = signed_angle(trunk, _vec(px[joint], px[end]))
        out[name] = SIGNED_INVALID if ang is None else round(face * ang, 1)
    return out


def best_side(points, name):
    """Pick the side whose three landmarks the camera sees most clearly."""
    vl = _visibility(points, JOINTS[name]["L"])
    vr = _visibility(points, JOINTS[name]["R"])
    return ("L", vl) if vl >= vr else ("R", vr)


def side_angles(px, side):
    """All angles for one side of the body; -1 where the camera can't see the joint well."""
    out = {}
    for name in JOINTS:
        idxs = JOINTS[name][side]
        interior = angle_at(*(px[i] for i in idxs)) if _visible(px, idxs) else NOT_VISIBLE
        if interior < 0:
            out[name] = NOT_VISIBLE
            continue
        out[name] = round(max(0.0, min(180.0, to_rom(name, interior))), 1)
    out.update(side_signed(px, side))
    return out


def empty_packet():
    """Packet sent when nobody is in view."""
    blank = {name: NOT_VISIBLE for name in JOINTS}
    blank.update({name: SIGNED_INVALID for name in SIGNED})
    return {"visible": False, "side": "", **blank, "trunkLean": NOT_VISIBLE, "elbowDrift": NOT_VISIBLE,
            "L": dict(blank), "R": dict(blank)}


def measure(points, width, height):
    """
    points: list of 33 (x, y, visibility) tuples with x, y normalised 0..1
            (exactly what MediaPipe returns).
    Returns the packet dict that is sent to Unity. Angles that can't be
    measured reliably are -1 (signed variants: SIGNED_INVALID).
      top-level angles  from whichever side the camera sees best (per angle)
      "L" / "R"         every angle for that side, used when the therapist
                        sets the operated side
    """
    px = [(p[0] * width, p[1] * height, p[2]) for p in points]
    per_side = {"L": side_angles(px, "L"), "R": side_angles(px, "R")}
    out = {"visible": True}
    sides = {}
    for name in JOINTS:
        side, _ = best_side(px, name)
        sides[name] = side
        out[name] = per_side[side][name]
    for name, spec in SIGNED.items():
        out[name] = per_side[sides[spec["base"]]][name]
    out["side"] = sides["shoulderElev"]
    out["L"], out["R"] = per_side["L"], per_side["R"]

    # Error Detector inputs (posture checks); -1 when a landmark they need is hidden.
    # Trunk lean: angle of the shoulder-midpoint -> hip-midpoint line from vertical.
    out["trunkLean"] = NOT_VISIBLE
    if _visible(px, (L_SHOULDER, R_SHOULDER, L_HIP, R_HIP)):
        sm = ((px[L_SHOULDER][0] + px[R_SHOULDER][0]) / 2, (px[L_SHOULDER][1] + px[R_SHOULDER][1]) / 2)
        hm = ((px[L_HIP][0] + px[R_HIP][0]) / 2, (px[L_HIP][1] + px[R_HIP][1]) / 2)
        if sm != hm:
            out["trunkLean"] = round(abs(math.degrees(math.atan2(sm[0] - hm[0], hm[1] - sm[1]))), 1)

    # Elbow drift during elbow flexion: how far the upper arm swings away from the trunk.
    idxs = JOINTS["shoulderElev"][sides["elbowFlex"]]
    drift = angle_at(*(px[i] for i in idxs)) if _visible(px, idxs) else NOT_VISIBLE
    out["elbowDrift"] = round(drift, 1) if drift >= 0 else NOT_VISIBLE
    return out
