"""Run with:  python test_angles.py   (no camera or MediaPipe needed)"""
import hashlib
import math
import os
import shutil
import tempfile
import unittest
from unittest import mock

from angles import SIGNED_INVALID, empty_packet, measure, angle_at

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
        new = {"shoulderElevSigned", "hipElevSigned"}
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

    def test_reopen_camera_quit_while_waiting(self):
        cv2, _ = self._fake_cv2([False])
        self.assertIsNone(self.tracker.reopen_camera(cv2, mock.Mock(), 0, sleep=lambda _c, _s: True))

    def test_wait_keeps_pumping_window(self):
        cv2 = mock.Mock()
        cv2.waitKey.side_effect = [-1, -1, ord("q")]
        self.assertTrue(self.tracker.wait_keep_responsive(cv2, 5))
        self.assertEqual(cv2.waitKey.call_count, 3)


if __name__ == "__main__":
    unittest.main(verbosity=2)
