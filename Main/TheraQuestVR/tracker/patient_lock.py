"""
TheraQuest - Patient Lock (M10.5): the exercise must be done by the patient, not by another person.

The detector looks for up to two bodies. The first body found in a session is the patient: its
signature (body proportions, from the 3D world landmarks, so they hold from any camera angle, and
where it stands) is remembered. After that only the body that matches the signature is passed on to
the tracking and scoring code; any other body is never measured.

Status sent to the game ("patient" in the packet):
  locking    learning who the patient is (about half a second)
  ok         the locked patient is the tracked body
  away       the patient is not in view and nobody else has taken their place (the usual tracking-loss pause)
  different  the patient is not in view and another body stands where the patient was: the session pauses
             until the patient is tracked again

A person who is only in view (beside the patient, or behind them and further from the camera) never
changes the status: another body counts only once the patient is no longer tracked and it has taken
their place. Pure Python (no camera or MediaPipe), so it can be tested on its own.
"""
import math
from collections import namedtuple

Body = namedtuple("Body", "pts world")        # pts: 33 (x, y, confidence); world: 33 (x, y, z, vis, pres) or None

LOCKING, OK, AWAY, DIFFERENT = "locking", "ok", "away", "different"

SEEN = 0.5                    # confidence at which a landmark counts as seen
LOCK_FRAMES = 15              # frames of the same body (about 0.5 s) before it is locked as the patient
LOCK_GAP = 1.0                # seconds without the candidate before the locking starts over
PROP_TOL = 0.12               # mean relative difference between two bodies' proportions that still counts as the same body
CONT_DIST = 0.6               # torso lengths: a body this close to where the patient just was gets 1.4 times the tolerance
CONT_TOL = 1.4
CONT_SECONDS = 0.5
SWAP_SECONDS = 1.0            # the patient must be missing this long, with another body in place, to count as replaced
CLEAR_SECONDS = 1.0           # the other body must be gone this long before "different" ends (when the patient is not back)
PLACE_X, PLACE_Y = 1.5, 2.0   # torso lengths: how far from the patient's place a body still counts as standing in it
PLACE_SIZE = (0.7, 1.6)       # its size (torso length) relative to the patient's: smaller means further back, i.e. only in view
RELOCK_AFTER = 120.0          # seconds of nobody in view before the next person found becomes the patient (a new session)

CORE_IDX = (11, 12, 23, 24)
# proportion name -> pairs of landmarks (both sides averaged), measured in 3D and divided by the torso length
BONES = {"sh": ((11, 12),), "hip": ((23, 24),), "ua": ((11, 13), (12, 14)), "fa": ((13, 15), (14, 16)),
         "th": ((23, 25), (24, 26)), "sk": ((25, 27), (26, 28))}
MIN_KEYS_LOCK, MIN_KEYS_MATCH = 4, 3


def _seen(pts, i):
    return pts[i][2] >= SEEN


def _centre(pts):
    ids = [i for i in CORE_IDX if _seen(pts, i)] or [i for i in range(len(pts)) if _seen(pts, i)]
    if not ids:
        return None
    return (sum(pts[i][0] for i in ids) / len(ids), sum(pts[i][1] for i in ids) / len(ids))


def _torso(pts, aspect):
    """Torso length in image-height units, or None when a shoulder or hip is not seen."""
    if not all(_seen(pts, i) for i in CORE_IDX):
        return None
    mx = lambda a, b: ((pts[a][0] + pts[b][0]) / 2 * aspect, (pts[a][1] + pts[b][1]) / 2)
    return math.dist(mx(11, 12), mx(23, 24))


def proportions(world):
    """{name: bone length / torso length} from the world landmarks that are seen; {} when the torso is not."""
    if world is None or not all(world[i][3] >= SEEN for i in CORE_IDX):
        return {}
    mid = lambda a, b: tuple((world[a][k] + world[b][k]) / 2 for k in range(3))
    torso = math.dist(mid(11, 12), mid(23, 24))
    if torso <= 1e-6:
        return {}
    out = {}
    for name, pairs in BONES.items():
        lens = [math.dist(world[a][:3], world[b][:3]) for a, b in pairs
                if world[a][3] >= SEEN and world[b][3] >= SEEN]
        if lens:
            out[name] = sum(lens) / len(lens) / torso
    return out


def proportion_distance(a, b):
    """Mean relative difference over the proportions both bodies have, or None with fewer than MIN_KEYS_MATCH."""
    keys = [k for k in a if k in b]
    if len(keys) < MIN_KEYS_MATCH:
        return None
    return sum(abs(a[k] - b[k]) / ((a[k] + b[k]) / 2) for k in keys) / len(keys)


class _View:
    """What the lock needs to know about one body this frame."""

    def __init__(self, index, body, aspect):
        self.index = index
        self.centre = _centre(body.pts)
        self.size = _torso(body.pts, aspect)
        self.props = proportions(body.world)
        self.aspect = aspect


class PatientLock:
    def __init__(self):
        self.reset()

    def reset(self):
        """Forget the patient: the next body found is the new patient."""
        self.status = LOCKING
        self.locked = False
        self.signature = {}
        self.home = None              # where the patient stood when locked (x, y), image units
        self.size = None              # the patient's torso length, image-height units (follows how near they stand)
        self.last_pos = None
        self.last_seen = None
        self.bodies = 0
        self._samples = []            # proportions gathered while locking
        self._pending = None          # centre of the body being learned
        self._pending_seen = None
        self._empty_since = None
        self._other_since = None      # when another body first stood in the patient's place
        self._other_gone_since = None
        self._swapped = False

    # ------------------------------------------------------------ one frame
    def update(self, bodies, t, aspect=1.0):
        """bodies: the detector's bodies this frame (up to two). Returns (index of the patient's body or None, status)."""
        views = [_View(i, b, aspect) for i, b in enumerate(bodies)]
        views = [v for v in views if v.centre is not None]
        self.bodies = len(views)
        if not self.locked:
            idx = self._lock_step(views, t)
        else:
            idx = self._track_step(views, t)
        return idx, self.status

    def camera_lost(self):
        """No frames at all: the patient is not tracked, and nobody has taken their place."""
        if self.locked:
            self.status = AWAY
            self._other_since = self._other_gone_since = None
            self._swapped = False

    # ------------------------------------------------------------ locking
    def _lock_step(self, views, t):
        self.status = LOCKING
        if not views:
            if self._pending_seen is not None and t - self._pending_seen > LOCK_GAP:
                self._samples, self._pending = [], None
            return None
        # The first body found: the one already being learned if it is still there, else the nearest (largest) one.
        pick = None
        if self._pending is not None:
            near = min(views, key=lambda v: math.dist(v.centre, self._pending))
            if math.dist(near.centre, self._pending) <= CONT_DIST * (near.size or 0.3) * 2:
                pick = near
        if pick is None:
            pick = max(views, key=lambda v: v.size or 0.0)
            self._samples = []
        self._pending, self._pending_seen = pick.centre, t
        if len(pick.props) >= MIN_KEYS_LOCK and pick.size:
            self._samples.append((pick.props, pick.size, pick.centre))
        if len(self._samples) >= LOCK_FRAMES:
            self._lock(t)
        return pick.index

    def _lock(self, t):
        keys = set.intersection(*[set(p) for p, _, _ in self._samples])
        self.signature = {k: sum(p[k] for p, _, _ in self._samples) / len(self._samples) for k in keys}
        n = len(self._samples)
        self.size = sum(s for _, s, _ in self._samples) / n
        self.home = (sum(c[0] for _, _, c in self._samples) / n, sum(c[1] for _, _, c in self._samples) / n)
        self.last_pos, self.last_seen = self._samples[-1][2], t
        self.locked, self.status = True, OK
        self._samples = []

    # ------------------------------------------------------------ tracking the patient
    def _distance(self, centre):
        """How far a body is from where the patient was last, in torso lengths."""
        dx, dy = centre[0] - self.last_pos[0], centre[1] - self.last_pos[1]
        return math.hypot(dx, dy) / (self.size or 0.3)

    def _matches(self, v, gap):
        dp = proportion_distance(self.signature, v.props)
        dist = self._distance(v.centre)
        if dp is None:           # not enough of the body is measured: only where it stands can tell
            return (dist <= 1.0 + 2 * gap), dist
        near = dist <= CONT_DIST and gap <= CONT_SECONDS
        ok = dp <= PROP_TOL or (near and dp <= CONT_TOL * PROP_TOL)
        return ok, dp + 0.3 * dist

    def _in_place(self, v):
        """True when this body stands where the patient stood (last position or where they were locked)."""
        for ref in (self.last_pos, self.home):
            dx, dy = abs(v.centre[0] - ref[0]) / (self.size or 0.3), abs(v.centre[1] - ref[1]) / (self.size or 0.3)
            if dx <= PLACE_X and dy <= PLACE_Y:
                break
        else:
            return False
        if v.size and self.size:
            ratio = v.size / self.size
            return PLACE_SIZE[0] <= ratio <= PLACE_SIZE[1]
        return True

    def _track_step(self, views, t):
        gap = t - self.last_seen
        matched, others = None, []
        for v in views:
            ok, score = self._matches(v, gap)
            if ok and (matched is None or score < matched[1]):
                if matched is not None:
                    others.append(matched[0])
                matched = (v, score)
            else:
                others.append(v)
        if matched is not None:
            v = matched[0]
            self.last_pos, self.last_seen = v.centre, t
            if v.size:
                self.size = 0.9 * self.size + 0.1 * v.size
            self.status = OK
            self._other_since = self._other_gone_since = None
            self._swapped = False
            self._empty_since = None
            return v.index

        # The patient is not tracked
        if not views:
            self._empty_since = self._empty_since if self._empty_since is not None else t
            if t - self._empty_since >= RELOCK_AFTER:
                self.reset()
                self.status = LOCKING
                return None
        else:
            self._empty_since = None
        placed = [v for v in others if self._in_place(v)]
        if placed:
            self._other_gone_since = None
            if self._other_since is None:
                self._other_since = t
            if t - self._other_since >= SWAP_SECONDS or self._swapped:
                self._swapped = True
        else:
            self._other_since = None
            if self._swapped:
                if self._other_gone_since is None:
                    self._other_gone_since = t
                if t - self._other_gone_since >= CLEAR_SECONDS:
                    self._swapped = False
        self.status = DIFFERENT if self._swapped else AWAY
        return None
