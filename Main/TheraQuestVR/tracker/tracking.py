"""
TheraQuest - Landmark tracking around MediaPipe (Motion Tracking Module).

Pure math, no camera or MediaPipe needed, so it can be unit-tested on its own.

MediaPipe gives a new set of landmarks every frame. This module keeps each one's
recent history and decides how far it can be trusted (DEC-022):

  TRACKED      confident detection, seen for a few frames in a row. Smoothed with a
               One Euro filter. The only state whose position is ever measured or scored.
  REACQUIRING  confident again after a gap, not yet for long enough to trust.
  UNRELIABLE   low confidence: a Kalman estimate that leans only weakly on the detection.
  PREDICTED    missing or rejected: the Kalman filter carries it on for a limited time,
               slowing down, then holding still.
  LOST         missing for too long: no position at all. History is dropped, so recovery
               starts fresh instead of from old coordinates.

A preserved or predicted coordinate is an estimate of where the joint probably is, not
a new detection. So the two outputs stay apart:
  scoring_points()   only TRACKED landmarks are visible; every other one has visibility 0,
                     which makes any angle that needs it -1 (not measured).
  estimate_points()  also includes the estimates, for display only.

Coordinates are MediaPipe's normalised 0..1 image coordinates; times are seconds.
"""
import math
from collections import deque

from angles import (JOINTS, L_ANKLE, L_ELBOW, L_HIP, L_KNEE, L_SHOULDER, L_WRIST, MIN_VISIBILITY, R_ANKLE, R_ELBOW,
                    R_HIP, R_KNEE, R_SHOULDER, R_WRIST, empty_packet, limb_directions, measure)

TRACKED, REACQUIRING, UNRELIABLE, PREDICTED, LOST = "tracked", "reacquiring", "unreliable", "predicted", "lost"

HIGH_CONFIDENCE = MIN_VISIBILITY   # at or above: use the detection
LOW_CONFIDENCE = 0.2               # below: treat the landmark as missing
HOLD_SECONDS = 0.5                 # how long an estimate may stand in for a landmark
REACQUIRE_FRAMES = 2               # confident frames in a row before a landmark is trusted again (DEC-025)
HISTORY_FRAMES = 15                # motion history kept per landmark

MAX_SPEED = 4.0                    # image widths or heights per second; faster is not a real movement
JUMP_SLACK = 0.08                  # jump allowance on top of MAX_SPEED, for detection noise
MAX_DT = 0.25                      # a long stall between frames must not unlock huge jumps or predictions
COAST_DECAY_SECONDS = 0.3          # predicted velocity fades with this time constant

# One Euro filter: little smoothing when moving fast (no lag), more when nearly still (no jitter).
# M6.5: 1.5 / 6.0 left a standing knee jittering (95th percentile 13.7 degrees a frame); 1.0 / 1.5 gives 8.7 for
# about 2 frames more lag, which Unity's lighter display smoothing gives back.
EURO_MIN_CUTOFF = 1.0
EURO_BETA = 1.5
EURO_D_CUTOFF = 1.0

# Kalman filter noise (normalised units). A low-confidence detection counts far less than a good one.
KALMAN_PROCESS = 4.0
KALMAN_R_GOOD = 2.5e-5
KALMAN_R_WEAK = 2.5e-3

# Whole-pose states sent to Unity as "trackingState"
POSE_TRACKING, POSE_DEGRADED, POSE_REACQUIRING, POSE_LOST = "tracking", "degraded", "reacquiring", "lost"
CORE = {
    "L": (L_SHOULDER, L_ELBOW, L_WRIST, L_HIP, L_KNEE, L_ANKLE),
    "R": (R_SHOULDER, R_ELBOW, R_WRIST, R_HIP, R_KNEE, R_ANKLE),
}
CORE_NEEDED = 4                    # verified landmarks on the better side for the pose to count as tracking
REDETECT_AFTER = 3.0               # seconds of a detected pose with no verified joint before forcing a fresh detection
REDETECT_EVERY = 10.0              # rebuilding the detector is slow: at most this often

# Camera setup checks (M6.3), from the detector's raw landmarks. Unity decides what each exercise needs.
FRAME_MARGIN = 0.01                # a landmark this close to the image edge, or past it, is out of frame
SIDE_VIEW_RATIO = 0.35             # shoulder width / torso length below this: side-on to the camera
FRONT_VIEW_RATIO = 0.55            # above this: facing the camera; in between: turned part way

# Which side's limb to measure (M6.5). Side-on, the far limb is mostly hidden behind the body but MediaPipe still
# guesses it, and picking the clearer side frame by frame flipped the knee reading between the legs (about 24 degrees
# each time). So the side nearest the camera (world-landmark depth) is measured while it can be; otherwise the current
# side is kept unless the other is clearly better seen.
NEAR_SET_M = 0.08                  # depth gap (metres) between the body's sides that makes one side the near side
NEAR_CLEAR_M = 0.03                # below this gap neither side is nearer (facing the camera)
SIDE_KEEP_MARGIN = 0.15            # confidence the other side must gain before the measured side switches
# Side-on, the far limb is measured instead when it reads clearly more than the near one: the patient is moving the
# far leg (field test: the far leg's hamstring curl read ~90 while the near, standing leg read ~10). Standing still,
# the far limb never read 35 above the near one in the recording; once switched, it stays while 15 above.
FAR_LEAD_DEG = 35.0
FAR_KEEP_DEG = 15.0


class OneEuroFilter:
    """One Euro filter for one value (Casiez, Roussel and Vogel, CHI 2012)."""

    def __init__(self, min_cutoff=EURO_MIN_CUTOFF, beta=EURO_BETA, d_cutoff=EURO_D_CUTOFF):
        self.min_cutoff, self.beta, self.d_cutoff = min_cutoff, beta, d_cutoff
        self.reset()

    def reset(self):
        self.x = None
        self.dx = 0.0

    @staticmethod
    def _alpha(cutoff, dt):
        tau = 1.0 / (2.0 * math.pi * cutoff)
        return 1.0 / (1.0 + tau / dt)

    def __call__(self, value, dt):
        if self.x is None:
            self.x = value
            return value
        dx = (value - self.x) / dt
        a_d = self._alpha(self.d_cutoff, dt)
        self.dx += a_d * (dx - self.dx)
        cutoff = self.min_cutoff + self.beta * abs(self.dx)
        self.x += self._alpha(cutoff, dt) * (value - self.x)
        return self.x


class Kalman1D:
    """Constant-velocity Kalman filter for one coordinate: predicts, then corrects with a measurement."""

    def __init__(self, position):
        self.p, self.v = position, 0.0
        self.pp, self.pv, self.vv = 1e-3, 0.0, 1.0   # covariance; the velocity is unknown at first

    def predict(self, dt, damping=1.0):
        self.p += self.v * dt
        self.v = max(-MAX_SPEED, min(MAX_SPEED, self.v * damping))
        q = KALMAN_PROCESS
        self.pp += dt * (2.0 * self.pv + dt * self.vv) + q * dt ** 3 / 3.0
        self.pv += dt * self.vv + q * dt ** 2 / 2.0
        self.vv += q * dt

    def update(self, z, r):
        s = self.pp + r
        k_p, k_v = self.pp / s, self.pv / s
        err = z - self.p
        self.p += k_p * err
        self.v = max(-MAX_SPEED, min(MAX_SPEED, self.v + k_v * err))
        self.vv -= k_v * self.pv
        self.pv -= k_v * self.pp
        self.pp -= k_p * self.pp


class LandmarkTrack:
    """History and trust state of one landmark."""

    def __init__(self):
        self.state = LOST
        self.history = deque(maxlen=HISTORY_FRAMES)   # (t, x, y, state) as output
        self.x = self.y = 0.0
        self.confidence = 0.0
        self._kx = self._ky = None
        self._euro_x, self._euro_y = OneEuroFilter(), OneEuroFilter()
        self._good_run = 0
        self._gap = 0.0
        self._suspect = None
        self._suspect_run = 0

    @property
    def reliable(self):
        return self.state == TRACKED

    @property
    def has_position(self):
        return self.state != LOST

    @property
    def velocity(self):
        """Estimated (vx, vy) in image units per second; (0, 0) when lost."""
        return (self._kx.v, self._ky.v) if self._kx is not None else (0.0, 0.0)

    def reset(self):
        self.state = LOST
        self.confidence = 0.0
        self.history.clear()
        self._kx = self._ky = None
        self._euro_x.reset()
        self._euro_y.reset()
        self._good_run = 0
        self._gap = 0.0
        self._suspect = None
        self._suspect_run = 0

    def _restart(self, x, y):
        self.reset()
        self._kx, self._ky = Kalman1D(x), Kalman1D(y)
        self.x, self.y = self._euro_x(x, 1.0), self._euro_y(y, 1.0)
        self._good_run = 1
        self.state = TRACKED if REACQUIRE_FRAMES <= 1 else REACQUIRING

    def _is_jump(self, x, y, dt):
        return math.hypot(x - self._kx.p, y - self._ky.p) > MAX_SPEED * dt + JUMP_SLACK

    def _accept(self, x, y, dt):
        if self.state != TRACKED and self.state != REACQUIRING:
            self._euro_x.reset()   # the filter's memory is from before the gap
            self._euro_y.reset()
        self._kx.update(x, KALMAN_R_GOOD)
        self._ky.update(y, KALMAN_R_GOOD)
        self.x, self.y = self._euro_x(x, dt), self._euro_y(y, dt)
        self._good_run += 1
        self._gap = 0.0
        self._suspect_run = 0
        self.state = TRACKED if self.state == TRACKED or self._good_run >= REACQUIRE_FRAMES else REACQUIRING

    def _coast(self, state, dt):
        self._good_run = 0
        self._gap += dt
        if self._gap > HOLD_SECONDS:
            self.reset()
            return
        self.x, self.y = max(-0.2, min(1.2, self._kx.p)), max(-0.2, min(1.2, self._ky.p))
        self.state = state

    def update(self, x, y, confidence, dt):
        """One frame: (x, y, confidence) from the detector, or confidence 0 when it is missing."""
        self.confidence = confidence
        self._step(x, y, confidence, min(max(dt, 1e-3), MAX_DT))
        if self.has_position:
            self.history.append((self.x, self.y, self.state))

    def _step(self, x, y, confidence, dt):
        if self._kx is None:
            if confidence >= HIGH_CONFIDENCE:
                self._restart(x, y)
            return

        damping = math.exp(-dt / COAST_DECAY_SECONDS) if self.state in (PREDICTED, UNRELIABLE) else 1.0
        self._kx.predict(dt, damping)
        self._ky.predict(dt, damping)

        if confidence < LOW_CONFIDENCE:
            self._coast(PREDICTED, dt)
        elif not self._is_jump(x, y, dt):
            if confidence >= HIGH_CONFIDENCE:
                self._accept(x, y, dt)
            else:
                self._kx.update(x, KALMAN_R_WEAK)
                self._ky.update(y, KALMAN_R_WEAK)
                self._coast(UNRELIABLE, dt)
        elif confidence >= HIGH_CONFIDENCE and self._confirm_jump(x, y):
            self._restart(x, y)   # it really is there now (it moved while unseen, or the first track was wrong)
        else:
            self._coast(PREDICTED, dt)

    def _confirm_jump(self, x, y):
        """A far-away detection counts only if several frames in a row agree on it."""
        if self._suspect is not None and math.hypot(x - self._suspect[0], y - self._suspect[1]) <= JUMP_SLACK:
            self._suspect_run += 1
        else:
            self._suspect_run = 1
        self._suspect = (x, y)
        return self._suspect_run >= REACQUIRE_FRAMES


class PoseTracker:
    """All 33 landmarks of one person, and the whole pose's state."""

    COUNT = 33

    def __init__(self):
        self.tracks = [LandmarkTrack() for _ in range(self.COUNT)]
        self._last_t = None
        self._pose_seen = False
        self._bad_since = None
        self._last_redetect = None
        self._raw = None
        self._world = None
        self._near = None
        self._sides = {}
        self.state = POSE_LOST

    def reset(self):
        """Forget everything (the camera was lost): no estimate survives this."""
        for track in self.tracks:
            track.reset()
        self._last_t = None
        self._pose_seen = False
        self._bad_since = None
        self._raw = None
        self._world = None
        self._near = None
        self._sides = {}
        self.state = POSE_LOST

    def update(self, points, t, world=None):
        """points: 33 (x, y, confidence) tuples from the detector, or None when no pose was found.
        world: the same 33 landmarks in metres (x, y, z, ...), for the display-only limb directions."""
        dt = t - self._last_t if self._last_t is not None else 1.0 / 30.0
        self._last_t = t
        self._pose_seen = points is not None
        self._raw = points
        self._world = world if points is not None else None
        for i, track in enumerate(self.tracks):
            if points is None:
                track.update(0.0, 0.0, 0.0, dt)
            else:
                track.update(*points[i], dt)
        self.state = self._pose_state()
        # Only a pose with nothing verified looks like a bad lock: part of the body out of frame is normal
        if any(self.tracks[i].reliable for idxs in CORE.values() for i in idxs):
            self._bad_since = None
        elif self._bad_since is None:
            self._bad_since = t

    def _pose_state(self):
        verified = max(sum(self.tracks[i].reliable for i in idxs) for idxs in CORE.values())
        if verified >= CORE_NEEDED:
            return POSE_TRACKING
        core = [self.tracks[i] for idxs in CORE.values() for i in idxs]
        if any(track.state == REACQUIRING for track in core):
            return POSE_REACQUIRING
        return POSE_DEGRADED if any(track.has_position for track in core) else POSE_LOST

    def should_redetect(self, t):
        """True when MediaPipe keeps finding a pose with no verified joint: it may be locked onto a bad one, so
        the caller should restart it to force a fresh detection. MediaPipe already detects again by itself
        when it finds no pose at all, so this only applies while one is being reported."""
        if not self._pose_seen or self._bad_since is None or t - self._bad_since < REDETECT_AFTER:
            return False
        if self._last_redetect is not None and t - self._last_redetect < REDETECT_EVERY:
            return False
        self._last_redetect = t
        return True

    def scoring_points(self):
        """Verified landmarks only: everything else has visibility 0, so no angle can use it."""
        return [(t.x, t.y, max(t.confidence, HIGH_CONFIDENCE)) if t.reliable else (t.x, t.y, 0.0) for t in self.tracks]

    def estimate_points(self):
        """Every landmark that has any position, verified or not. For display only, never for scoring."""
        return [(t.x, t.y, 1.0) if t.has_position else (t.x, t.y, 0.0) for t in self.tracks]

    def setup(self, width, height):
        """Camera setup checks from this frame's raw detection (M6.3), or None when nobody is detected.
          valid              always true (lets Unity tell a packet with setup checks from an older tracker's)
          framedL / framedR  per measured angle: every landmark it needs is detected and inside the image
          view               "side" | "front" | "" (turned part way, or can't tell)
          size               torso length / image height (distance: bigger = closer), -1 if unknown
          light              median confidence of the landmarks inside the image (low in poor light), 0..1
        These only guide the patient's setup; scoring still uses verified landmarks only (DEC-022)."""
        raw = self._raw
        if raw is None:
            return None

        def inside(i):
            x, y, c = raw[i]
            return c >= LOW_CONFIDENCE and FRAME_MARGIN <= x <= 1 - FRAME_MARGIN and FRAME_MARGIN <= y <= 1 - FRAME_MARGIN

        framed = {side: {name: all(inside(i) for i in idxs[side]) for name, idxs in JOINTS.items()} for side in ("L", "R")}
        px = [(x * width, y * height) for x, y, _ in raw]
        mid = lambda a, b: ((px[a][0] + px[b][0]) / 2, (px[a][1] + px[b][1]) / 2)
        view, size = "", -1.0
        if all(inside(i) for i in (L_SHOULDER, R_SHOULDER, L_HIP, R_HIP)):
            torso = math.dist(mid(L_SHOULDER, R_SHOULDER), mid(L_HIP, R_HIP))
            if torso > 0:
                ratio = math.dist(px[L_SHOULDER], px[R_SHOULDER]) / torso
                view = "side" if ratio < SIDE_VIEW_RATIO else "front" if ratio > FRONT_VIEW_RATIO else ""
                size = round(torso / height, 3)
        seen = sorted(raw[i][2] for idxs in CORE.values() for i in idxs if inside(i))
        light = round(seen[len(seen) // 2], 2) if seen else 0.0
        return {"valid": True, "framedL": framed["L"], "framedR": framed["R"], "view": view, "size": size,
                "light": light}

    def near_side(self):
        """"L" / "R": the side of the body nearer the camera, from the world landmarks' depth, with hysteresis;
        None facing the camera or without world landmarks."""
        w = self._world
        if w is None or not all(self.tracks[i].reliable for i in (L_SHOULDER, R_SHOULDER, L_HIP, R_HIP)):
            return self._near
        gap = (w[R_SHOULDER][2] + w[R_HIP][2] - w[L_SHOULDER][2] - w[L_HIP][2]) / 2   # > 0: left is nearer
        if abs(gap) >= NEAR_SET_M:
            self._near = "L" if gap > 0 else "R"
        elif abs(gap) < NEAR_CLEAR_M:
            self._near = None
        return self._near

    def _preferences(self, view):
        """Which side to measure. Side-on: only the limb nearer the camera (the far one is hidden). Facing the
        camera: the limb that moves, i.e. the larger reading (the standing leg in a hip abduction reads 0).
        Otherwise keep the current side unless the other is clearly better seen."""
        near = self.near_side()
        if view == "side" and near:
            return {name: (near, None, FAR_KEEP_DEG if self._sides.get(name, near) != near else FAR_LEAD_DEG)
                    for name in JOINTS}
        if view == "front":
            return {name: ("max", 0.0) for name in JOINTS}
        return {name: (side, SIDE_KEEP_MARGIN) for name, side in self._sides.items()}

    def packet(self, width, height):
        """The packet for Unity. Measured angles come only from verified landmarks; when part of the body
        is only estimated, "estL" / "estR" carry its angles separately, for display."""
        scoring = self.scoring_points()
        verified = any(self.tracks[i].reliable for idxs in CORE.values() for i in idxs)
        setup = self.setup(width, height)
        view = setup["view"] if setup else ""
        packet = measure(scoring, width, height, self._preferences(view)) if verified else empty_packet()
        if verified:
            for name in JOINTS:
                if packet[name] >= 0:
                    self._sides[name] = "L" if packet["L"][name] == packet[name] else "R"

        packet["trackingState"] = self.state
        # Display only (M6.4): which way the upper arms and thighs point in 3D, from verified landmarks
        if verified and self._world is not None:
            for side, dirs in (limb_directions(self._world, lambda i: self.tracks[i].reliable) or {}).items():
                packet["dir" + side] = dirs
        if setup is not None:
            packet["setup"] = setup
        partial = any(not self.tracks[i].reliable for idxs in CORE.values() for i in idxs)
        if partial and self.state != POSE_LOST:
            estimate = measure(self.estimate_points(), width, height)
            packet["estL"], packet["estR"] = estimate["L"], estimate["R"]
        return packet


def landmark_confidence(visibility, presence):
    """A landmark is only as trusted as the lower of the model's two scores; a missing score doesn't count."""
    scores = [s for s in (visibility, presence) if s is not None]
    return min(scores) if scores else 1.0
