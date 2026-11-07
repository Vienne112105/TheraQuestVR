"""Run with:  python test_tracking.py   (no camera or MediaPipe needed)"""
import random
import unittest

from angles import L_ELBOW, L_HIP, L_SHOULDER, L_WRIST, SIGNED_INVALID
from test_angles import H, W, base_pose, normalise
from tracking import (HOLD_SECONDS, LOST, MAX_DT, POSE_DEGRADED, POSE_LOST, POSE_REACQUIRING, POSE_TRACKING, PREDICTED,
                      REACQUIRE_FRAMES, REACQUIRING, REDETECT_AFTER, REDETECT_EVERY, TRACKED, UNRELIABLE, Kalman1D,
                      LandmarkTrack, OneEuroFilter, PoseTracker, landmark_confidence)

DT = 1 / 30


def run(track, x, y, conf, frames=1):
    for _ in range(frames):
        track.update(x, y, conf, DT)
    return track


def tracked_at(x=0.5, y=0.5):
    return run(LandmarkTrack(), x, y, 0.9, REACQUIRE_FRAMES + 2)


class FilterTests(unittest.TestCase):
    def test_one_euro_reduces_jitter_when_still(self):
        rng = random.Random(1)
        f = OneEuroFilter()
        raw = [0.5 + rng.gauss(0, 0.005) for _ in range(200)]
        out = [f(v, DT) for v in raw]
        spread = lambda xs: max(xs[50:]) - min(xs[50:])
        self.assertLess(spread(out), spread(raw) / 2)

    def test_one_euro_keeps_up_with_fast_movement(self):
        f = OneEuroFilter()
        for _ in range(30):
            f(0.2, DT)
        out = 0.2
        for i in range(1, 16):                                # 1 image height per second
            out = f(0.2 + i * DT, DT)
        self.assertLess(abs((0.2 + 15 * DT) - out), 0.05)

    def test_one_euro_reaches_a_held_peak(self):
        f = OneEuroFilter()
        out = 0.0
        for _ in range(45):
            out = f(0.7, DT)
        self.assertAlmostEqual(out, 0.7, places=2)            # measured peaks aren't shaved off

    def test_kalman_learns_velocity_and_predicts(self):
        k = Kalman1D(0.1)
        for i in range(1, 31):
            k.predict(DT)
            k.update(0.1 + 0.5 * i * DT, 2.5e-5)
        self.assertAlmostEqual(k.v, 0.5, delta=0.05)
        k.predict(0.1)
        self.assertAlmostEqual(k.p, 0.1 + 0.5 * (30 * DT + 0.1), delta=0.01)

    def test_kalman_correction_follows_trust(self):
        good, weak = Kalman1D(0.5), Kalman1D(0.5)
        for k, r in ((good, 2.5e-5), (weak, 2.5e-3)):
            k.predict(DT)
            k.update(0.52, r)
        self.assertGreater(abs(good.p - 0.5), abs(weak.p - 0.5))


class LandmarkStateTests(unittest.TestCase):
    def test_needs_several_frames_before_it_is_trusted(self):
        t = LandmarkTrack()
        for _ in range(REACQUIRE_FRAMES - 1):
            t.update(0.5, 0.5, 0.9, DT)
            self.assertEqual(t.state, REACQUIRING)
            self.assertFalse(t.reliable)
        t.update(0.5, 0.5, 0.9, DT)
        self.assertEqual(t.state, TRACKED)

    def test_low_confidence_is_flagged_unreliable(self):
        t = run(tracked_at(), 0.5, 0.5, 0.35)
        self.assertEqual(t.state, UNRELIABLE)
        self.assertFalse(t.reliable)
        self.assertTrue(t.has_position)

    def test_missing_keeps_a_position_for_a_limited_time_then_is_lost(self):
        t = tracked_at()
        run(t, 0, 0, 0.0)
        self.assertEqual(t.state, PREDICTED)
        self.assertAlmostEqual(t.x, 0.5, delta=0.02)
        run(t, 0, 0, 0.0, int(HOLD_SECONDS / DT) + 2)
        self.assertEqual(t.state, LOST)
        self.assertFalse(t.has_position)
        self.assertEqual(len(t.history), 0)                   # nothing old survives

    def test_prediction_continues_the_motion_but_slows_down(self):
        t = LandmarkTrack()
        for i in range(30):
            t.update(0.2 + 0.5 * i * DT, 0.5, 0.9, DT)
        vx = t.velocity[0]
        self.assertAlmostEqual(vx, 0.5, delta=0.1)
        before = t.x
        run(t, 0, 0, 0.0, 6)
        self.assertGreater(t.x, before)
        self.assertLess(t.velocity[0], vx / 1.5)

    def test_recovery_is_not_trusted_at_once(self):
        t = run(tracked_at(), 0, 0, 0.0, 3)
        t.update(0.5, 0.5, 0.9, DT)
        self.assertFalse(t.reliable)
        run(t, 0.5, 0.5, 0.9, REACQUIRE_FRAMES)
        self.assertTrue(t.reliable)

    def test_recovery_after_loss_starts_from_the_new_position(self):
        t = run(tracked_at(0.2, 0.2), 0, 0, 0.0, int(HOLD_SECONDS / DT) + 2)
        t.update(0.8, 0.8, 0.9, DT)
        self.assertEqual(t.state, REACQUIRING)
        self.assertEqual((t.x, t.y), (0.8, 0.8))

    def test_one_frame_jump_is_rejected(self):
        t = tracked_at()
        t.update(0.95, 0.1, 0.99, DT)
        self.assertEqual(t.state, PREDICTED)
        self.assertAlmostEqual(t.x, 0.5, delta=0.02)
        t.update(0.5, 0.5, 0.99, DT)                          # back on track, still needs to re-earn trust
        self.assertNotEqual(t.state, TRACKED)
        self.assertAlmostEqual(t.x, 0.5, delta=0.02)

    def test_jump_that_stays_there_is_accepted_after_confirmation(self):
        t = tracked_at()
        for _ in range(REACQUIRE_FRAMES):
            t.update(0.95, 0.1, 0.99, DT)
        self.assertEqual(t.state, REACQUIRING)
        self.assertEqual(t.x, 0.95)
        run(t, 0.95, 0.1, 0.99, REACQUIRE_FRAMES)
        self.assertTrue(t.reliable)

    def test_fast_real_movement_is_not_a_jump(self):
        t = tracked_at(0.1, 0.5)
        for i in range(1, 16):                                # 2 image widths per second
            t.update(0.1 + 2.0 * i * DT, 0.5, 0.9, DT)
            self.assertEqual(t.state, TRACKED)

    def test_a_stalled_frame_does_not_unlock_a_jump(self):
        t = tracked_at()
        t.update(0.5 + 4.0 * MAX_DT + 0.2, 0.5, 0.99, 5.0)    # 5 s gap between frames
        self.assertEqual(t.state, PREDICTED)

    def test_history_is_bounded(self):
        t = run(LandmarkTrack(), 0.5, 0.5, 0.9, 100)
        self.assertLessEqual(len(t.history), t.history.maxlen)


class PosePacketTests(unittest.TestCase):
    def setUp(self):
        self.pose = PoseTracker()
        self.t = 0.0

    def feed(self, points, frames=1):
        for _ in range(frames):
            self.t += DT
            self.pose.update(points, self.t)
        return self.pose.packet(W, H)

    def good(self):
        return normalise(base_pose())

    def hide(self, *idxs, conf=0.0):
        pts = list(self.good())
        for i in idxs:
            pts[i] = (pts[i][0], pts[i][1], conf)
        return pts

    def test_clear_view_measures_as_before(self):
        m = self.feed(self.good(), REACQUIRE_FRAMES + 1)
        self.assertTrue(m["visible"])
        self.assertEqual(m["trackingState"], POSE_TRACKING)
        self.assertGreaterEqual(m["L"]["elbowFlex"], 0)
        self.assertLess(m["L"]["elbowFlex"], 3)
        self.assertLess(m["shoulderElev"], 3)

    def test_nothing_is_measured_until_landmarks_are_trusted(self):
        m = self.feed(self.good())
        self.assertEqual(m["L"]["shoulderElev"], -1.0)
        self.assertEqual(m["trackingState"], POSE_REACQUIRING)

    def test_hidden_wrist_is_never_measured_but_can_be_shown(self):
        self.feed(self.good(), REACQUIRE_FRAMES + 1)
        m = self.feed(self.hide(L_WRIST))
        self.assertEqual(m["L"]["elbowFlex"], -1.0)           # preserved position: an estimate, so no reading
        self.assertGreaterEqual(m["L"]["shoulderElev"], 0)    # angles that don't use it still work
        self.assertGreaterEqual(m["estL"]["elbowFlex"], 0)    # estimate kept apart, for display
        self.assertLess(m["estL"]["elbowFlex"], 5)

    def test_low_confidence_wrist_is_not_measured(self):
        self.feed(self.good(), REACQUIRE_FRAMES + 1)
        m = self.feed(self.hide(L_WRIST, conf=0.35))
        self.assertEqual(m["L"]["elbowFlex"], -1.0)

    def test_angle_ignores_a_one_frame_jump(self):
        self.feed(self.good(), REACQUIRE_FRAMES + 1)
        pts = list(self.good())
        pts[L_WRIST] = (0.05, 0.05, 0.99)                     # implausible: elbow suddenly fully bent
        m = self.feed(pts)
        self.assertEqual(m["L"]["elbowFlex"], -1.0)
        m = self.feed(self.good(), REACQUIRE_FRAMES + 1)
        self.assertLess(m["L"]["elbowFlex"], 3)               # resumes only after it recovers

    def test_measurement_resumes_only_after_recovery(self):
        self.feed(self.good(), REACQUIRE_FRAMES + 1)
        self.feed(self.hide(L_WRIST), 5)
        m = self.feed(self.good())
        self.assertEqual(m["L"]["elbowFlex"], -1.0)
        m = self.feed(self.good(), REACQUIRE_FRAMES)
        self.assertGreaterEqual(m["L"]["elbowFlex"], 0)

    def test_person_gone_goes_from_estimate_to_lost(self):
        self.feed(self.good(), REACQUIRE_FRAMES + 1)
        m = self.feed(None)
        self.assertFalse(m["visible"])                        # nothing verified, however good the estimate
        self.assertEqual(m["L"]["shoulderElev"], -1.0)
        self.assertEqual(m["R"]["hipElevSigned"], SIGNED_INVALID)
        self.assertEqual(m["trackingState"], POSE_DEGRADED)
        self.assertIn("estL", m)
        m = self.feed(None, int(HOLD_SECONDS / DT) + 2)
        self.assertEqual(m["trackingState"], POSE_LOST)
        self.assertNotIn("estL", m)                           # never relies on old coordinates for long

    def test_person_returning_is_reacquired(self):
        self.feed(self.good(), REACQUIRE_FRAMES + 1)
        self.feed(None, int(HOLD_SECONDS / DT) + 2)
        self.assertEqual(self.feed(self.good())["trackingState"], POSE_REACQUIRING)
        m = self.feed(self.good(), REACQUIRE_FRAMES)
        self.assertEqual(m["trackingState"], POSE_TRACKING)
        self.assertTrue(m["visible"])

    def test_one_side_hidden_is_still_tracking(self):
        pts = self.good()
        pts = [(x, y, 0.0 if i in (12, 14, 16, 24, 26, 28) else v) for i, (x, y, v) in enumerate(pts)]
        m = self.feed(pts, REACQUIRE_FRAMES + 1)              # normal in side view
        self.assertEqual(m["trackingState"], POSE_TRACKING)
        self.assertEqual(m["R"]["shoulderElev"], -1.0)
        self.assertGreaterEqual(m["L"]["shoulderElev"], 0)

    def test_camera_reset_forgets_every_estimate(self):
        self.feed(self.good(), REACQUIRE_FRAMES + 1)
        self.pose.reset()
        m = self.pose.packet(W, H)
        self.assertEqual(m["trackingState"], POSE_LOST)
        self.assertFalse(m["visible"])

    def test_redetect_only_for_a_pose_that_cannot_be_tracked(self):
        bad = self.hide(*range(11, 33))
        self.feed(bad)
        self.assertFalse(self.pose.should_redetect(self.t))
        self.t += REDETECT_AFTER + 0.1
        self.feed(bad)
        self.assertTrue(self.pose.should_redetect(self.t))
        self.assertFalse(self.pose.should_redetect(self.t + 1))             # not every frame
        self.t += REDETECT_EVERY + 0.1
        self.feed(bad)
        self.assertTrue(self.pose.should_redetect(self.t))

    def test_no_redetect_when_only_part_of_the_body_is_in_frame(self):
        upper_only = self.hide(23, 24, 25, 26, 27, 28)        # sitting close: hips and legs out of frame
        m = self.feed(upper_only, REACQUIRE_FRAMES + 1)
        self.assertGreaterEqual(m["L"]["elbowFlex"], 0)
        self.t += REDETECT_AFTER + 1
        self.feed(upper_only)
        self.assertFalse(self.pose.should_redetect(self.t))

    def test_no_redetect_when_no_pose_or_tracking_fine(self):
        self.feed(self.good(), REACQUIRE_FRAMES + 1)
        self.t += REDETECT_AFTER + 1
        self.feed(self.good())
        self.assertFalse(self.pose.should_redetect(self.t))
        self.feed(None)
        self.t += REDETECT_AFTER + 1
        self.feed(None)
        self.assertFalse(self.pose.should_redetect(self.t))

    def test_hidden_hip_stops_only_the_angles_that_use_it(self):
        self.feed(self.good(), REACQUIRE_FRAMES + 1)
        m = self.feed(self.hide(L_HIP))
        self.assertEqual(m["L"]["shoulderElev"], -1.0)
        self.assertGreaterEqual(m["R"]["shoulderElev"], 0)


class ConfidenceTests(unittest.TestCase):
    def test_lowest_score_wins(self):
        self.assertEqual(landmark_confidence(0.9, 0.3), 0.3)
        self.assertEqual(landmark_confidence(0.2, 0.8), 0.2)

    def test_missing_scores_do_not_count(self):
        self.assertEqual(landmark_confidence(0.7, None), 0.7)
        self.assertEqual(landmark_confidence(None, 0.6), 0.6)
        self.assertEqual(landmark_confidence(None, None), 1.0)


class SetupTests(unittest.TestCase):
    """Camera setup checks (M6.3): computed from the raw detection, sent as packet["setup"]."""

    def pose_with(self, changes=None, conf=0.99):
        pts = normalise(base_pose())                     # standing, facing the camera, whole body in frame
        pts = [(x, y, conf if v > 0 else 0.0) for x, y, v in pts]
        for i, xy in (changes or {}).items():
            pts[i] = (xy[0], xy[1], pts[i][2])
        tracker = PoseTracker()
        tracker.update(pts, 0.0)
        return tracker

    def test_nobody_detected_has_no_setup(self):
        tracker = PoseTracker()
        tracker.update(None, 0.0)
        self.assertNotIn("setup", tracker.packet(W, H))

    def test_whole_body_in_frame_facing_camera(self):
        s = self.pose_with().packet(W, H)["setup"]
        self.assertTrue(all(s["framedL"].values()) and all(s["framedR"].values()))
        self.assertEqual(s["view"], "front")
        self.assertAlmostEqual(s["size"], 140 / H, places=3)
        self.assertGreater(s["light"], 0.9)

    def test_ankle_below_the_image_is_not_framed(self):
        s = self.pose_with({27: (360 / W, 1.08)}).packet(W, H)["setup"]
        self.assertFalse(s["framedL"]["kneeFlex"])
        self.assertTrue(s["framedL"]["hipElev"])           # the hip angle doesn't need the ankle
        self.assertTrue(s["framedR"]["kneeFlex"])

    def test_side_on_is_side_view(self):
        s = self.pose_with({11: (322 / W, 160 / H), 12: (318 / W, 160 / H)}).packet(W, H)["setup"]
        self.assertEqual(s["view"], "side")

    def test_turned_part_way_is_no_view(self):
        s = self.pose_with({11: (340 / W, 160 / H), 12: (280 / W, 160 / H)}).packet(W, H)["setup"]
        self.assertEqual(s["view"], "")                    # 60 / 140 px: between side and front

    def test_low_confidence_shows_as_poor_light(self):
        s = self.pose_with(conf=0.3).packet(W, H)["setup"]
        self.assertLess(s["light"], 0.5)

    def test_limb_directions_only_with_world_landmarks(self):
        from test_angles import world_pose
        tracker = PoseTracker()
        pts = [(x, y, 0.99 if v > 0 else 0.0) for x, y, v in normalise(base_pose())]
        for i in range(3):
            tracker.update(pts, i / 30)
        self.assertNotIn("dirL", tracker.packet(W, H))
        tracker.update(pts, 3 / 30, world_pose())
        pkt = tracker.packet(W, H)
        self.assertAlmostEqual(pkt["dirL"]["arm"][1], -1, delta=0.01)
        self.assertIn("leg", pkt["dirR"])

    def test_setup_never_changes_measured_angles(self):
        tracker = self.pose_with({27: (360 / W, 1.08)})
        packet = tracker.packet(W, H)
        self.assertEqual(packet["trackingState"], POSE_REACQUIRING)   # one frame: nothing verified yet
        self.assertEqual(packet["L"]["kneeFlex"], -1)

if __name__ == "__main__":
    unittest.main()
