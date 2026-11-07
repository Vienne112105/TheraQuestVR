"""Run with:  python test_angles.py   (no camera or MediaPipe needed)"""
import hashlib
import math
import os
import shutil
import tempfile
import unittest
from unittest import mock

import numpy as np

from angles import SIGNED_INVALID, angle_at, empty_packet, limb_directions, measure

W, H = 640, 480


def base_pose():
    """A person standing upright, arms hanging, facing the camera (pixel coords)."""
    p = [(320, 240, 0.0)] * 33
    pts = {
        11: (360, 160), 12: (280, 160),   # shoulders (patient's left is on image right)
        13: (360, 240), 14: (280, 240),   # elbows straight down
        15: (360, 310), 16: (280, 310),   # wrists
        23: (360, 300), 24: (280, 300),   # hips
        25: (360, 380), 26: (280, 380),   # knees
        27: (360, 460), 28: (280, 460),   # ankles
        29: (360, 468), 30: (280, 468),   # heels (feet toward the camera: heel and toes close together)
        31: (360, 472), 32: (280, 472),   # toes
    }
    p = list(p)
    for i, (x, y) in pts.items():
        p[i] = (x, y, 0.99)
    return p


def normalise(p):
    return [(x / W, y / H, v) for x, y, v in p]


def rot(origin, length, deg_from_down, direction=1):
    """Point at `length` from origin, rotated `deg_from_down` from straight down."""
    t = math.radians(deg_from_down)
    return (origin[0] + direction * math.sin(t) * length, origin[1] + math.cos(t) * length)


class AngleTests(unittest.TestCase):
    def test_interior(self):
        self.assertAlmostEqual(angle_at((0, 1), (0, 0), (1, 0)), 90.0, places=4)
        self.assertAlmostEqual(angle_at((0, 1), (0, 0), (0, -1)), 180.0, places=4)

    def test_rest_pose_is_zero(self):
        m = measure(normalise(base_pose()), W, H)
        self.assertLess(m["shoulderElev"], 3)
        self.assertLess(m["elbowFlex"], 3)
        self.assertLess(m["hipElev"], 3)
        self.assertLess(m["kneeFlex"], 3)
        self.assertLess(m["trunkLean"], 1)

    def test_shoulder_abduction_90(self):
        p = base_pose()
        sh = p[11][:2]
        el = rot(sh, 80, 90, +1)
        wr = rot(sh, 150, 90, +1)
        p[13] = (*el, 0.99); p[15] = (*wr, 0.99)
        p[14] = (p[14][0], p[14][1], 0.3)   # right arm less visible -> left side chosen
        m = measure(normalise(p), W, H)
        self.assertAlmostEqual(m["shoulderElev"], 90, delta=1.0)

    def test_elbow_flexion_120(self):
        p = base_pose()
        el = p[13][:2]
        wr = rot(el, 70, 120, +1)
        p[15] = (*wr, 0.99)
        p[16] = (p[16][0], p[16][1], 0.2)
        m = measure(normalise(p), W, H)
        self.assertAlmostEqual(m["elbowFlex"], 120, delta=1.0)

    def test_knee_extension_seated(self):
        p = base_pose()
        hip = (300, 300); knee = (380, 300)       # thigh horizontal (seated, side view)
        ankle = rot(knee, 90, 60, +1)             # shin raised 60 deg from hanging
        p[23] = (*hip, 0.99); p[25] = (*knee, 0.99); p[27] = (*ankle, 0.99)
        for i in (24, 26, 28):
            p[i] = (p[i][0], p[i][1], 0.1)
        m = measure(normalise(p), W, H)
        self.assertAlmostEqual(m["kneeExt"], 60, delta=1.0)

    def test_trunk_lean(self):
        p = base_pose()
        for i in (11, 12):
            p[i] = (p[i][0] + 40, p[i][1], 0.99)    # shoulders shifted sideways
        m = measure(normalise(p), W, H)
        self.assertGreater(m["trunkLean"], 12)

    def test_sit_to_stand_uses_knee_extension(self):
        p = base_pose()                            # standing: knee straight
        m = measure(normalise(p), W, H)
        self.assertAlmostEqual(m["kneeExt"], 90, delta=1.0)

    def test_hip_abduction_25(self):
        p = base_pose()
        hip = p[23][:2]
        knee = rot(hip, 80, 25, +1)                # leg out to the side, front view
        p[25] = (*knee, 0.99); p[27] = (*rot(knee, 80, 25, +1), 0.99)
        for i in (24, 26, 28):
            p[i] = (p[i][0], p[i][1], 0.1)
        m = measure(normalise(p), W, H)
        self.assertAlmostEqual(m["hipElev"], 25, delta=1.0)

    def test_straight_leg_raise_45_lying(self):
        p = base_pose()
        sh, hip = (100, 300), (300, 300)          # lying on the back, side view
        knee = (hip[0] + 90 * math.cos(math.radians(45)), hip[1] - 90 * math.sin(math.radians(45)))
        ankle = (hip[0] + 180 * math.cos(math.radians(45)), hip[1] - 180 * math.sin(math.radians(45)))
        p[11] = (*sh, 0.99); p[23] = (*hip, 0.99); p[25] = (*knee, 0.99); p[27] = (*ankle, 0.99)
        for i in (12, 24, 26, 28):
            p[i] = (p[i][0], p[i][1], 0.1)
        m = measure(normalise(p), W, H)
        self.assertAlmostEqual(m["hipElev"], 45, delta=1.0)
        self.assertLess(m["kneeFlex"], 2)          # knee kept straight

    def test_knee_flexion_mini_squat(self):
        p = base_pose()
        knee = p[25][:2]
        ankle = rot(knee, 80, 45, -1)              # shin swings back 45 deg
        p[27] = (*ankle, 0.99)
        for i in (24, 26, 28):
            p[i] = (p[i][0], p[i][1], 0.1)
        m = measure(normalise(p), W, H)
        self.assertAlmostEqual(m["kneeFlex"], 45, delta=1.0)

    def test_both_sides_reported(self):
        p = base_pose()
        sh = p[12][:2]
        p[14] = (*rot(sh, 80, 60, -1), 0.99)       # right arm raised 60, left arm down
        m = measure(normalise(p), W, H)
        self.assertAlmostEqual(m["R"]["shoulderElev"], 60, delta=1.0)
        self.assertLess(m["L"]["shoulderElev"], 3)

    def test_hidden_joint_reports_minus_one(self):
        p = [(x, y, 0.1) for x, y, _ in base_pose()]
        m = measure(normalise(p), W, H)
        self.assertEqual(m["kneeExt"], -1.0)
        self.assertEqual(m["L"]["hipElev"], -1.0)


def side_view(facing_right=True):
    """Patient standing side-on, left side to the camera, arm and leg hanging (pixel coords).
    Right-side landmarks are hidden, the nose points the way the patient faces."""
    d = 1 if facing_right else -1
    p = [(320, 240, 0.0)] * 33
    pts = {
        0: (320 + d * 25, 110),               # nose, in front of the shoulder
        11: (320, 160), 13: (320, 240), 15: (320, 310),
        23: (320, 300), 25: (320, 380), 27: (320, 460),
    }
    for i, (x, y) in pts.items():
        p[i] = (x, y, 0.99)
    for i in (12, 14, 16, 24, 26, 28):
        p[i] = (320, 240, 0.1)
    return p, d


class M44Tests(unittest.TestCase):
    """Milestone M4.4: tracker measurement correctness."""

    def test_one_hidden_landmark_hides_joint(self):
        # Mean visibility (0.99 + 0.99 + 0.0) / 3 = 0.66 used to pass; min must not.
        p = base_pose()
        p[15] = (p[15][0], p[15][1], 0.0)           # left wrist hidden
        p[16] = (p[16][0], p[16][1], 0.0)           # right wrist hidden
        m = measure(normalise(p), W, H)
        self.assertEqual(m["L"]["elbowFlex"], -1.0)
        self.assertEqual(m["R"]["elbowFlex"], -1.0)
        self.assertEqual(m["elbowFlex"], -1.0)
        self.assertGreaterEqual(m["L"]["shoulderElev"], 0)   # unaffected joints still measured

    def test_zero_length_vector_is_not_visible(self):
        self.assertEqual(angle_at((5, 5), (5, 5), (9, 1)), -1.0)
        p = base_pose()
        p[15] = p[13]                                 # wrist collapsed onto elbow
        p[16] = p[14]
        p[25] = p[23]; p[26] = p[24]                  # knees collapsed onto hips
        m = measure(normalise(p), W, H)
        self.assertEqual(m["L"]["elbowFlex"], -1.0)   # used to report 180
        self.assertEqual(m["L"]["hipElev"], -1.0)
        self.assertEqual(m["L"]["kneeFlex"], -1.0)

    def _arm(self, deg_forward, facing_right):
        p, d = side_view(facing_right)
        sh = p[11][:2]
        p[13] = (*rot(sh, 80, abs(deg_forward), d if deg_forward >= 0 else -d), 0.99)
        return measure(normalise(p), W, H)

    def test_shoulder_signed_forward_vs_backward(self):
        for facing_right in (True, False):
            fwd = self._arm(90, facing_right)
            back = self._arm(-40, facing_right)
            self.assertAlmostEqual(fwd["L"]["shoulderElevSigned"], 90, delta=1.0)
            self.assertAlmostEqual(back["L"]["shoulderElevSigned"], -40, delta=1.0)
            self.assertAlmostEqual(fwd["shoulderElevSigned"], 90, delta=1.0)
            # unsigned field unchanged: both directions read as positive magnitude
            self.assertAlmostEqual(fwd["L"]["shoulderElev"], 90, delta=1.0)
            self.assertAlmostEqual(back["L"]["shoulderElev"], 40, delta=1.0)

    def test_hip_signed_forward_vs_backward(self):
        for facing_right in (True, False):
            for deg in (60, -20):
                p, d = side_view(facing_right)
                hip = p[23][:2]
                knee = rot(hip, 80, abs(deg), d if deg >= 0 else -d)
                p[25] = (*knee, 0.99); p[27] = (*rot(knee, 80, abs(deg), d if deg >= 0 else -d), 0.99)
                m = measure(normalise(p), W, H)
                self.assertAlmostEqual(m["L"]["hipElevSigned"], deg, delta=1.0)
                self.assertAlmostEqual(m["L"]["hipElev"], abs(deg), delta=1.0)

    def test_hip_signed_lying_leg_raise(self):
        p = base_pose()
        sh, hip = (100, 300), (300, 300)              # lying on the back, head on the left
        knee = (hip[0] + 90 * math.cos(math.radians(45)), hip[1] - 90 * math.sin(math.radians(45)))
        p[0] = (80, 270, 0.99)                        # nose points at the ceiling
        p[11] = (*sh, 0.99); p[23] = (*hip, 0.99); p[25] = (*knee, 0.99)
        m = measure(normalise(p), W, H)
        self.assertAlmostEqual(m["L"]["hipElevSigned"], 45, delta=1.0)

    def test_signed_invalid_when_facing_unknown(self):
        p, _ = side_view()
        p[0] = (p[0][0], p[0][1], 0.0)                # nose and ears hidden
        m = measure(normalise(p), W, H)
        self.assertEqual(m["L"]["shoulderElevSigned"], SIGNED_INVALID)
        self.assertEqual(m["R"]["hipElevSigned"], SIGNED_INVALID)
        self.assertGreaterEqual(m["L"]["shoulderElev"], 0)

    def test_posture_minus_one_when_hips_hidden(self):
        p = base_pose()
        for i in (23, 24):
            p[i] = (p[i][0], p[i][1], 0.1)
        m = measure(normalise(p), W, H)
        self.assertEqual(m["trunkLean"], -1.0)
        self.assertEqual(m["elbowDrift"], -1.0)

    def test_packet_keeps_existing_fields(self):
        old = {"visible", "side", "shoulderElev", "elbowFlex", "hipElev", "kneeFlex",
               "kneeExt", "trunkLean", "elbowDrift", "L", "R"}
        side_old = {"shoulderElev", "elbowFlex", "hipElev", "kneeFlex", "kneeExt"}
        new = {"shoulderElevSigned", "hipElevSigned", "ankleDF", "anklePF"}   # signed: M4.4, ankle: M6.4
        for pkt in (measure(normalise(base_pose()), W, H), empty_packet()):
            self.assertEqual(set(pkt), old | new)
            for s in ("L", "R"):
                self.assertEqual(set(pkt[s]), side_old | new)


class TrackerHelperTests(unittest.TestCase):
    """Model download and camera reconnect, with cv2 / network mocked out."""

    def setUp(self):
        import tracker
        self.tracker = tracker
        self.dir = tempfile.mkdtemp()
        self.payload = b"model-bytes" * 100
        self.spec = {"url": "http://example.invalid/m.task", "size": len(self.payload),
                     "sha256": hashlib.sha256(self.payload).hexdigest()}
        self._saved = dict(tracker.MODELS)
        tracker.MODELS["test"] = self.spec

    def tearDown(self):
        self.tracker.MODELS.clear()
        self.tracker.MODELS.update(self._saved)
        shutil.rmtree(self.dir, ignore_errors=True)

    def _fetch(self, data):
        def fetch(url, dest):
            with open(dest, "wb") as f:
                f.write(data)
        return fetch

    def test_models_pinned_not_latest(self):
        for spec in self._saved.values():
            self.assertNotIn("/latest/", spec["url"])
            self.assertEqual(len(spec["sha256"]), 64)

    def test_partial_file_is_replaced(self):
        path = os.path.join(self.dir, "pose_landmarker_test.task")
        with open(path, "wb") as f:
            f.write(self.payload[:10])                # truncated earlier download
        out = self.tracker.ensure_model("test", here=self.dir, fetch=self._fetch(self.payload))
        with open(out, "rb") as f:
            self.assertEqual(f.read(), self.payload)
        self.assertFalse(os.path.exists(path + ".part"))

    def test_bad_download_never_installed(self):
        with self.assertRaises(RuntimeError):
            self.tracker.ensure_model("test", here=self.dir, fetch=self._fetch(b"x" * len(self.payload)))
        self.assertEqual(os.listdir(self.dir), [])

    def test_good_file_not_downloaded_again(self):
        path = os.path.join(self.dir, "pose_landmarker_test.task")
        with open(path, "wb") as f:
            f.write(self.payload)
        def fail(url, dest):
            raise AssertionError("should not download")
        self.assertEqual(self.tracker.ensure_model("test", here=self.dir, fetch=fail), path)

    def _fake_cv2(self, opens):
        """opens: list of booleans, whether each successive VideoCapture works."""
        cv2 = mock.Mock(CAP_DSHOW=700, CAP_ANY=0, CAP_PROP_FRAME_WIDTH=3, CAP_PROP_FRAME_HEIGHT=4)
        caps = []
        for good in opens:
            cap = mock.Mock()
            cap.isOpened.return_value = good
            cap.read.return_value = (good, object() if good else None)
            caps.append(cap)
        cv2.VideoCapture.side_effect = caps
        patcher = mock.patch.object(self.tracker, "camera_backends", lambda _cv2: (_cv2.CAP_DSHOW,))
        patcher.start()
        self.addCleanup(patcher.stop)
        return cv2, caps

    def test_reopen_camera_backoff(self):
        cv2, caps = self._fake_cv2([False, False, False, False, False, True])
        delays = []
        sleep = lambda _cv2, s: delays.append(s) or False
        cap = self.tracker.reopen_camera(cv2, mock.Mock(), 0, sleep=sleep)
        self.assertIs(cap, caps[-1])
        self.assertEqual(delays, [1, 2, 4, 8, 10, 10])
        for c in caps[:-1]:
            c.release.assert_called_once()

    def test_black_frames_fall_back_to_default_size(self):
        cv2, caps = self._fake_cv2([True, True])
        caps[0].read.return_value = (True, np.zeros((720, 1280, 3), np.uint8))
        self.assertIs(self.tracker.open_camera(cv2, 1), caps[1])
        caps[0].release.assert_called_once()
        caps[1].set.assert_not_called()

    def test_real_picture_keeps_requested_size(self):
        cv2, caps = self._fake_cv2([True])
        caps[0].read.return_value = (True, np.full((720, 1280, 3), 90, np.uint8))
        self.assertIs(self.tracker.open_camera(cv2, 1), caps[0])
        caps[0].release.assert_not_called()

    def test_second_backend_tried_when_first_fails(self):
        cv2, caps = self._fake_cv2([False, True])
        with mock.patch.object(self.tracker, "camera_backends", lambda _cv2: (700, 1400)):
            self.assertIs(self.tracker.open_camera(cv2, 0), caps[1])
        self.assertEqual([c.args[1] for c in cv2.VideoCapture.call_args_list], [700, 1400])
        caps[0].release.assert_called_once()

    def test_faster_backend_is_chosen(self):
        cv2, caps = self._fake_cv2([True, True])
        for c in caps:
            c.read.return_value = (True, np.full((720, 1280, 3), 90, np.uint8))
        speeds = {id(caps[0]): 13.0, id(caps[1]): 29.0}
        with mock.patch.object(self.tracker, "camera_backends", lambda _cv2: (700, 1400)):
            self.assertIs(self.tracker.open_camera(cv2, 0, rate=lambda c: speeds[id(c)]), caps[1])
        caps[0].release.assert_called_once()
        caps[1].release.assert_not_called()

    def test_fast_first_backend_skips_the_rest(self):
        cv2, caps = self._fake_cv2([True, True])
        caps[0].read.return_value = (True, np.full((720, 1280, 3), 90, np.uint8))
        with mock.patch.object(self.tracker, "camera_backends", lambda _cv2: (700, 1400)):
            self.assertIs(self.tracker.open_camera(cv2, 0, rate=lambda c: 30.0), caps[0])
        self.assertEqual(cv2.VideoCapture.call_count, 1)

    def test_slower_second_backend_is_released(self):
        cv2, caps = self._fake_cv2([True, True])
        for c in caps:
            c.read.return_value = (True, np.full((720, 1280, 3), 90, np.uint8))
        speeds = {id(caps[0]): 20.0, id(caps[1]): 10.0}
        with mock.patch.object(self.tracker, "camera_backends", lambda _cv2: (700, 1400)):
            self.assertIs(self.tracker.open_camera(cv2, 0, rate=lambda c: speeds[id(c)]), caps[0])
        caps[1].release.assert_called_once()

    def test_reopen_camera_quit_while_waiting(self):
        cv2, _ = self._fake_cv2([False])
        self.assertIsNone(self.tracker.reopen_camera(cv2, mock.Mock(), 0, sleep=lambda _c, _s: True))

    def test_wait_keeps_pumping_window(self):
        cv2 = mock.Mock()
        cv2.waitKey.side_effect = [-1, -1, ord("q")]
        self.assertTrue(self.tracker.wait_keep_responsive(cv2, 5))
        self.assertEqual(cv2.waitKey.call_count, 3)


class CaptureTests(unittest.TestCase):
    """Threaded camera reading and the smaller detection copy (no real camera needed)."""

    def setUp(self):
        import tracker
        self.tracker = tracker

    def test_grabber_hands_out_each_new_frame_once(self):
        import time as _time
        import numpy as np

        class Cap:
            n = 0

            def read(self):
                _time.sleep(0.01)
                Cap.n += 1
                return True, np.full((4, 4), Cap.n % 255, np.uint8)

        g = self.tracker.FrameGrabber(Cap())
        try:
            ok1, f1 = g.read()
            ok2, f2 = g.read()
            self.assertTrue(ok1 and ok2)
            self.assertNotEqual(int(f1[0, 0]), int(f2[0, 0]))
        finally:
            g.stop()

    def test_grabber_reports_a_failed_camera(self):
        class Dead:
            def read(self):
                return False, None

        g = self.tracker.FrameGrabber(Dead())
        try:
            self.assertEqual(g.read(), (False, None))
        finally:
            g.stop()

    def test_detection_copy_is_at_most_detect_width(self):
        import cv2
        import numpy as np
        small = self.tracker.detection_frame(cv2, np.zeros((720, 1280, 3), np.uint8))
        self.assertEqual(small.shape[:2], (360, self.tracker.DETECT_WIDTH))
        frame = np.zeros((480, 640, 3), np.uint8)
        self.assertIs(self.tracker.detection_frame(cv2, frame), frame)


def side_foot(toes_up=0.0):
    """Side view facing image right: shin straight down from the knee, foot forward from the heel,
    tilted up by toes_up degrees (negative = pointed down). Only the left leg is visible."""
    p = [(0.0, 0.0, 0.0)] * 33
    knee, ankle, heel = (300, 300), (300, 400), (290, 410)
    t = math.radians(toes_up)
    toe = (heel[0] + 60 * math.cos(t), heel[1] - 60 * math.sin(t))
    for i, xy in {11: (300, 100), 23: (300, 220), 25: knee, 27: ankle, 29: heel, 31: toe}.items():
        p[i] = (xy[0], xy[1], 0.99)
    return normalise(p)


class AnkleTests(unittest.TestCase):
    """Ankle angles (M6.4): the shin against the heel-to-toes line, 0 at a right angle."""

    def test_foot_at_right_angle_is_zero(self):
        m = measure(side_foot(0), W, H)["L"]
        self.assertAlmostEqual(m["ankleDF"], 0, delta=0.5)
        self.assertAlmostEqual(m["anklePF"], 0, delta=0.5)

    def test_toes_up_is_dorsiflexion(self):
        m = measure(side_foot(15), W, H)["L"]
        self.assertAlmostEqual(m["ankleDF"], 15, delta=0.5)
        self.assertEqual(m["anklePF"], 0)

    def test_toes_down_is_plantarflexion(self):
        m = measure(side_foot(-30), W, H)["L"]
        self.assertAlmostEqual(m["anklePF"], 30, delta=0.5)
        self.assertEqual(m["ankleDF"], 0)

    def test_hidden_heel_is_not_measured(self):
        p = side_foot(10)
        p[29] = (p[29][0], p[29][1], 0.1)
        m = measure(p, W, H)["L"]
        self.assertEqual(m["ankleDF"], -1.0)
        self.assertEqual(m["anklePF"], -1.0)


def world_pose(facing="camera", arm=(0.0, 1.0, 0.0)):
    """World landmarks (metres; x right, y down, z away from the camera) of a person standing upright,
    with the left upper arm along `arm` (world axes). facing: "camera" or "right" (image right, side-on)."""
    w = [(0.0, 0.0, 0.0, 0.99, 0.99)] * 33
    if facing == "camera":
        lsh, rsh, lhip, rhip = (0.2, -0.5, 0), (-0.2, -0.5, 0), (0.1, 0, 0), (-0.1, 0, 0)
    else:   # facing +x (turned to their left): the right shoulder is toward the camera (-z)
        lsh, rsh, lhip, rhip = (0, -0.5, 0.2), (0, -0.5, -0.2), (0, 0, 0.1), (0, 0, -0.1)
    pts = {11: lsh, 12: rsh, 23: lhip, 24: rhip,
           13: tuple(lsh[k] + 0.3 * arm[k] for k in range(3)), 14: (rsh[0], rsh[1] + 0.3, rsh[2]),
           25: (lhip[0], 0.4, lhip[2]), 26: (rhip[0], 0.4, rhip[2])}
    w = list(w)
    for i, (x, y, z) in pts.items():
        w[i] = (x, y, z, 0.99, 0.99)
    return w


class LimbDirectionTests(unittest.TestCase):
    """Display-only limb directions in the body frame (M6.4): +x patient's right, +y up, +z forward."""

    def arm(self, facing, arm):
        return limb_directions(world_pose(facing, arm), lambda i: True)["L"]["arm"]

    def assertDir(self, got, want):
        for g, w in zip(got, want):
            self.assertAlmostEqual(g, w, delta=0.01)

    def test_hanging_arm_points_down(self):
        self.assertDir(self.arm("camera", (0, 1, 0)), (0, -1, 0))
        self.assertDir(limb_directions(world_pose(), lambda i: True)["L"]["leg"], (0, -1, 0))

    def test_arm_forward_points_forward_facing_camera(self):
        self.assertDir(self.arm("camera", (0, 0, -1)), (0, 0, 1))      # toward the camera

    def test_arm_out_to_the_left_side(self):
        self.assertDir(self.arm("camera", (1, 0, 0)), (-1, 0, 0))      # patient's left is image right

    def test_side_on_forward_and_sideways(self):
        self.assertDir(self.arm("right", (1, 0, 0)), (0, 0, 1))        # forward is image right
        self.assertDir(self.arm("right", (0, 0, 1)), (-1, 0, 0))       # out to the left: away from the camera

    def test_unusable_trunk_or_limb(self):
        self.assertIsNone(limb_directions(world_pose(), lambda i: i != 23))
        dirs = limb_directions(world_pose(), lambda i: i != 13)
        self.assertNotIn("arm", dirs["L"])
        self.assertIn("leg", dirs["L"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
