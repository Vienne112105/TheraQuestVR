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
  ankleDF       90 - angle between the shin (ankle->knee) and the foot (heel->toes)
                0 = foot at a right angle to the shin, rises as the toes come up.
                Ankle pumps (side view)
  anklePF       that angle - 90: rises as the toes point down / the heel lifts.
                Heel raises (side view)

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
  25/26 knees, 27/28 ankles, 29/30 heels, 31/32 toes (foot index)
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
L_HEEL, R_HEEL = 29, 30
L_FOOT, R_FOOT = 31, 32

# Which landmarks form each measured angle, per side: three (a, b, c) give the angle at joint b; four
# (a, b, c, d) give the angle between the lines b->a and c->d (the ankle: shin against the foot).
JOINTS = {
    "shoulderElev": {"L": (L_HIP, L_SHOULDER, L_ELBOW), "R": (R_HIP, R_SHOULDER, R_ELBOW)},
    "elbowFlex":    {"L": (L_SHOULDER, L_ELBOW, L_WRIST), "R": (R_SHOULDER, R_ELBOW, R_WRIST)},
    "hipElev":      {"L": (L_SHOULDER, L_HIP, L_KNEE), "R": (R_SHOULDER, R_HIP, R_KNEE)},
    "kneeFlex":     {"L": (L_HIP, L_KNEE, L_ANKLE), "R": (R_HIP, R_KNEE, R_ANKLE)},
    "kneeExt":      {"L": (L_HIP, L_KNEE, L_ANKLE), "R": (R_HIP, R_KNEE, R_ANKLE)},
    "ankleDF":      {"L": (L_KNEE, L_ANKLE, L_HEEL, L_FOOT), "R": (R_KNEE, R_ANKLE, R_HEEL, R_FOOT)},
    "anklePF":      {"L": (L_KNEE, L_ANKLE, L_HEEL, L_FOOT), "R": (R_KNEE, R_ANKLE, R_HEEL, R_FOOT)},
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


def joint_angle(pts):
    """Interior angle for 3 points (at the middle one) or between the lines p1->p0 and p2->p3 for 4."""
    if len(pts) == 3:
        return angle_at(*pts)
    a, b, c, d = pts
    return _between(_vec(b, a), _vec(c, d))


def _between(v1, v2):
    n1, n2 = math.hypot(*v1), math.hypot(*v2)
    if n1 == 0 or n2 == 0:
        return NOT_VISIBLE
    cos = max(-1.0, min(1.0, (v1[0] * v2[0] + v1[1] * v2[1]) / (n1 * n2)))
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
    if name == "ankleDF":
        return 90.0 - interior
    if name == "anklePF":
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


def best_side(points, name, prefer=None, margin=0.0):
    """Pick the side whose landmarks the camera sees most clearly. A preferred side is kept unless the other
    side is seen better by more than `margin` (M6.5: stops the reading flipping between the near and far limb)."""
    vl = _visibility(points, JOINTS[name]["L"])
    vr = _visibility(points, JOINTS[name]["R"])
    if prefer == "L" and vl >= vr - margin:
        return "L", vl
    if prefer == "R" and vr >= vl - margin:
        return "R", vr
    return ("L", vl) if vl >= vr else ("R", vr)


def side_angles(px, side):
    """All angles for one side of the body; -1 where the camera can't see the joint well."""
    out = {}
    for name in JOINTS:
        idxs = JOINTS[name][side]
        interior = joint_angle([px[i] for i in idxs]) if _visible(px, idxs) else NOT_VISIBLE
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


def measure(points, width, height, prefer=None):
    """
    points: list of 33 (x, y, visibility) tuples with x, y normalised 0..1
            (exactly what MediaPipe returns).
    Returns the packet dict that is sent to Unity. Angles that can't be
    measured reliably are -1 (signed variants: SIGNED_INVALID).
      top-level angles  from whichever side the camera sees best (per angle)
      "L" / "R"         every angle for that side, used when the therapist
                        sets the operated side
    prefer: optional {angle name: (side, margin)}: keep that side for the top-level angle while it can be
            measured and the other side isn't seen better by more than margin. margin None = always that side,
            even when it can't be measured (-1): side-on, the far limb is hidden and must never stand in.
            side "max" = whichever side reads the larger angle (facing the camera: the limb that moves).
            A third item `lead` with margin None: the other side is taken instead when it reads more than `lead`
            degrees above the preferred one (side-on: the far leg doing the exercise, e.g. a hamstring curl).
    """
    px = [(p[0] * width, p[1] * height, p[2]) for p in points]
    per_side = {"L": side_angles(px, "L"), "R": side_angles(px, "R")}
    out = {"visible": True}
    sides = {}
    for name in JOINTS:
        want, margin, *more = (prefer or {}).get(name, (None, 0.0))
        lead = more[0] if more else None
        if want == "max":
            l, r = per_side["L"][name], per_side["R"][name]
            side = "L" if l >= r else "R"
        elif want and margin is None:
            side = want
            other = "R" if want == "L" else "L"
            if lead is not None and per_side[other][name] > max(per_side[want][name], 0.0) + lead:
                side = other
        else:
            if want and per_side[want][name] < 0:
                want = None   # the preferred side can't be measured now
            side, _ = best_side(px, name, want, margin)
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


# Limb directions in the patient's own body frame, from MediaPipe's world landmarks (metres; x right, y down,
# z away from the camera: a right-handed frame). Display only (DEC-023): Unity tilts the live limb out of the
# exercise's plane with them; nothing scored ever reads them.
LIMBS = {"arm": {"L": (L_SHOULDER, L_ELBOW), "R": (R_SHOULDER, R_ELBOW)},
         "leg": {"L": (L_HIP, L_KNEE), "R": (R_HIP, R_KNEE)}}


def _sub(p, q):
    return (p[0] - q[0], p[1] - q[1], p[2] - q[2])


def _dot(p, q):
    return p[0] * q[0] + p[1] * q[1] + p[2] * q[2]


def _unit(v):
    n = math.sqrt(_dot(v, v))
    return None if n < 1e-6 else (v[0] / n, v[1] / n, v[2] / n)


def body_frame(world):
    """(right, up, forward) unit vectors of the patient's body in world coordinates, or None when the
    shoulders and hips sit on top of each other. right = toward the patient's right shoulder."""
    mid = lambda a, b: tuple((world[a][k] + world[b][k]) / 2 for k in range(3))
    up = _unit(_sub(mid(L_SHOULDER, R_SHOULDER), mid(L_HIP, R_HIP)))
    across = _sub(world[R_SHOULDER], world[L_SHOULDER])
    if up is None:
        return None
    d = _dot(across, up)
    right = _unit((across[0] - d * up[0], across[1] - d * up[1], across[2] - d * up[2]))
    if right is None:
        return None
    # Right-handed world: up x right points out of the patient's chest
    forward = (up[1] * right[2] - up[2] * right[1], up[2] * right[0] - up[0] * right[2], up[0] * right[1] - up[1] * right[0])
    return right, up, forward


def limb_directions(world, usable):
    """{"L": {"arm": [x, y, z], "leg": [...]}, "R": {...}}: unit direction of the upper arm (shoulder->elbow)
    and thigh (hip->knee) in the body frame (+x the patient's right, +y up, +z forward, like Unity's).
    usable(i) says whether landmark i may be used; a limb or side that can't be measured is left out.
    None when the trunk can't be used."""
    if not all(usable(i) for i in (L_SHOULDER, R_SHOULDER, L_HIP, R_HIP)):
        return None
    frame = body_frame(world)
    if frame is None:
        return None
    out = {}
    for side in ("L", "R"):
        dirs = {}
        for limb, spec in LIMBS.items():
            a, b = spec[side]
            v = _unit(_sub(world[b], world[a])) if usable(a) and usable(b) else None
            if v is not None:
                dirs[limb] = [round(_dot(v, axis), 3) for axis in frame]
        if dirs:
            out[side] = dirs
    return out
