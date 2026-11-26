"""Run with:  python test_replay.py   (no camera or MediaPipe needed)"""
import json
import os
import shutil
import tempfile
import unittest

import recording
import report
from tracking import POSE_LOST, POSE_TRACKING


class ReplayTests(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.path = recording.synthetic(os.path.join(self.dir, "synthetic.jsonl"))

    def tearDown(self):
        shutil.rmtree(self.dir)

    def packets(self, path=None):
        return [p for _, p, _ in recording.replay(path or self.path)]

    def test_replay_is_identical_every_run(self):
        self.assertEqual(json.dumps(self.packets()), json.dumps(self.packets()))

    def test_recording_holds_landmarks_only(self):
        header, records = recording.load(self.path)
        self.assertEqual(header["version"], recording.VERSION)
        self.assertEqual(len(records), 360)
        for rec in records:
            self.assertLessEqual(set(rec), {"t", "pose", "world", "event", "others"})
            if rec["pose"] is not None:
                self.assertEqual(len(rec["pose"]), 33)
                self.assertEqual(len(rec["pose"][0]), 4)
                self.assertEqual(len(rec["world"][0]), 5)

    def test_round_trip_matches_live_tracking(self):
        """A recording written by Recorder and replayed gives the packets the live loop would have sent."""
        from patient_lock import Body
        from tracking import PoseTracker, landmark_confidence
        header, records = recording.load(self.path)
        live = PoseTracker()
        expected = []
        for rec in records:
            bodies = [] if rec["pose"] is None else [
                Body([(x, y, landmark_confidence(v, p)) for x, y, v, p in rec["pose"]], rec["world"])]
            live.update_bodies(bodies, rec["t"], header["width"] / header["height"])
            pkt = live.packet(header["width"], header["height"])
            pkt["ts"] = round(rec["t"], 3)
            expected.append(pkt)
        self.assertEqual(json.dumps(expected), json.dumps(self.packets()))

    def test_replay_follows_the_arm_and_the_gaps(self):
        pk = self.packets()
        by_t = {p["ts"]: p for p in pk}
        self.assertEqual(by_t[1.5]["trackingState"], POSE_TRACKING)
        self.assertGreater(by_t[1.5]["L"]["shoulderElev"], 80)          # arm up at mid-rep
        self.assertLess(by_t[4.5]["L"]["elbowFlex"], 0)                 # wrist hidden: no elbow reading
        self.assertEqual(by_t[9.0]["trackingState"], POSE_LOST)         # nobody in view
        self.assertEqual(by_t[11.5]["trackingState"], POSE_TRACKING)    # back again

    def test_camera_lost_event_resets_tracking(self):
        path = os.path.join(self.dir, "lost.jsonl")
        header, records = recording.load(self.path)
        with recording.Recorder(path, header["width"], header["height"]) as rec:
            for r in records[:60]:
                rec.frame(r["t"], r["pose"], r["world"])
            rec.camera_lost(2.0)
            for r in records[60:63]:
                rec.frame(r["t"] + 0.1, r["pose"], r["world"])
        pk = self.packets(path)
        self.assertEqual(pk[59]["trackingState"], POSE_TRACKING)
        self.assertEqual(pk[60]["trackingState"], POSE_LOST)
        self.assertNotEqual(pk[61]["trackingState"], POSE_TRACKING)     # trust has to be rebuilt

    def test_realtime_replay_waits_between_frames(self):
        waits = []
        list(recording.replay(self.path, realtime=True, sleep=waits.append))
        self.assertGreater(sum(waits), 5.0)

    def test_not_a_recording_is_refused(self):
        bad = os.path.join(self.dir, "bad.jsonl")
        with open(bad, "w") as f:
            f.write('{"t": 0}\n')
        with self.assertRaises(ValueError):
            recording.load(bad)

    def test_default_path_is_a_date_in_recordings(self):
        p = recording.default_path(0)
        self.assertEqual(os.path.dirname(p), recording.RECORDINGS_DIR)
        self.assertRegex(os.path.basename(p), r"^\d{8}-\d{6}\.jsonl$")

    def test_report_counts(self):
        r = report.summarise(self.path, side="L")                       # the raised arm
        self.assertEqual(r["frames"], 360)
        self.assertGreater(r["states"]["tracking"], 250)
        self.assertGreater(r["states"]["lost"], 50)          # 2.5 s gone, minus the 0.5 s estimate
        self.assertEqual(r["pauses"]["shoulderElev"], 1)                # stepping out
        self.assertEqual(r["pauses"]["elbowFlex"], 2)                   # stepping out + the hidden wrist
        self.assertEqual(r["camera_lost"], 0)


class TwoPersonReplayTests(unittest.TestCase):
    """M10.5 Patient Lock on a recorded two-person sequence (recording.synthetic_two_people)."""

    @classmethod
    def setUpClass(cls):
        cls.dir = tempfile.mkdtemp()
        cls.path = recording.synthetic_two_people(os.path.join(cls.dir, "two.jsonl"))
        cls.packets = {round(p["ts"], 2): p for _, p, _ in recording.replay(cls.path)}

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.dir)

    def at(self, t):
        return self.packets[round(t, 2)]

    def test_recording_holds_two_bodies_without_images(self):
        _, records = recording.load(self.path)
        two = [r for r in records if r.get("others")]
        self.assertGreater(len(two), 300)
        self.assertEqual(len(two[0]["others"][0]["pose"]), 33)
        self.assertEqual(len(two[0]["others"][0]["world"][0]), 5)

    def test_patient_is_locked_in_the_first_half_second(self):
        self.assertEqual(self.at(0.1)["patient"], "locking")
        self.assertEqual(self.at(1.0)["patient"], "ok")
        self.assertEqual(self.at(1.0)["trackingState"], POSE_TRACKING)

    def test_bystander_walking_in_and_standing_beside_or_behind_does_not_pause(self):
        for t in (2.5, 4.0, 6.0, 9.0, 10.5, 11.9):                # B enters, stands beside, stands behind
            pk = self.at(t)
            self.assertEqual(pk["patient"], "ok", t)
            self.assertEqual(pk["trackingState"], POSE_TRACKING, t)
        self.assertEqual(self.at(6.0)["bodies"], 2)

    def test_patient_stepping_out_with_only_a_bystander_beside_is_away_not_different(self):
        self.assertEqual(self.at(12.5)["patient"], "away")
        self.assertEqual(self.at(12.9)["patient"], "away")

    def test_second_person_taking_the_place_pauses(self):
        self.assertEqual(self.at(13.5)["patient"], "away")          # not yet: a moment's gap is not a swap
        for t in (14.5, 16.0, 17.9):
            pk = self.at(t)
            self.assertEqual(pk["patient"], "different", t)
            self.assertEqual(pk["trackingState"], POSE_LOST, t)      # their body is never tracked or measured
            self.assertLess(pk["shoulderElev"], 0, t)                # no angle comes from the other person

    def test_the_other_person_leaving_ends_the_difference_but_not_the_loss(self):
        pk = self.at(19.2)
        self.assertEqual(pk["patient"], "away")
        self.assertEqual(pk["trackingState"], POSE_LOST)

    def test_patient_returning_resumes(self):
        self.assertEqual(self.at(20.0)["patient"], "ok")
        self.assertEqual(self.at(20.0)["trackingState"], POSE_TRACKING)
        self.assertGreater(max(self.at(t)["shoulderElev"] for t in (20.5, 21.0, 21.5, 22.0, 22.5)), 60)

    def test_replay_is_identical_every_run(self):
        a = json.dumps([p for _, p, _ in recording.replay(self.path)])
        b = json.dumps([p for _, p, _ in recording.replay(self.path)])
        self.assertEqual(a, b)

    def test_an_older_single_body_recording_still_replays(self):
        single = recording.synthetic(os.path.join(self.dir, "single.jsonl"))
        states = {p["ts"]: p for _, p, _ in recording.replay(single)}
        self.assertEqual(states[1.5]["patient"], "ok")
        self.assertEqual(states[11.5]["trackingState"], POSE_TRACKING)   # same patient back after nobody was in view


if __name__ == "__main__":
    unittest.main()
