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
            self.assertLessEqual(set(rec), {"t", "pose", "world", "event"})
            if rec["pose"] is not None:
                self.assertEqual(len(rec["pose"]), 33)
                self.assertEqual(len(rec["pose"][0]), 4)
                self.assertEqual(len(rec["world"][0]), 5)

    def test_round_trip_matches_live_tracking(self):
        """A recording written by Recorder and replayed gives the packets the live loop would have sent."""
        from tracking import PoseTracker, landmark_confidence
        header, records = recording.load(self.path)
        live = PoseTracker()
        expected = []
        for rec in records:
            pts = None if rec["pose"] is None else [(x, y, landmark_confidence(v, p)) for x, y, v, p in rec["pose"]]
            live.update(pts, rec["t"], rec["world"])
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


if __name__ == "__main__":
    unittest.main()
