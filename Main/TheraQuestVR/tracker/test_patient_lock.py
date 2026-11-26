"""Run with:  python test_patient_lock.py   (no camera or MediaPipe needed)"""
import random
import unittest

import patient_lock as pl
import recording
from patient_lock import AWAY, DIFFERENT, LOCKING, OK, Body, PatientLock

W, H = 640, 480


def body(spec, cx, scale=300, ytop=60, lift=0.0, noise=0.0, rng=None):
    pose, world = recording._person(W, H, spec, cx, ytop, scale, lift)
    if noise:
        world = [(x * (1 + rng.uniform(-noise, noise)), y * (1 + rng.uniform(-noise, noise)), z, v, p)
                 for x, y, z, v, p in world]
    return Body([(x, y, v) for x, y, v, _ in pose], world)


PATIENT, OTHER = recording.PATIENT_BODY, recording.OTHER_BODY


class LockTests(unittest.TestCase):
    def run_frames(self, lock, frames, t0=0.0, dt=1 / 30):
        out, t = [], t0
        for bodies in frames:
            out.append(lock.update(bodies, t, W / H))
            t += dt
        return out, t

    def locked(self, **kw):
        lock = PatientLock()
        _, t = self.run_frames(lock, [[body(PATIENT, 240, **kw)]] * 20)
        self.assertTrue(lock.locked)
        return lock, t

    def test_first_body_found_is_locked_after_a_moment(self):
        lock = PatientLock()
        out, _ = self.run_frames(lock, [[body(PATIENT, 240)]] * 20)
        self.assertEqual(out[0], (0, LOCKING))
        self.assertEqual(out[-1], (0, OK))

    def test_nearest_body_is_locked_when_two_are_there_at_the_start(self):
        lock = PatientLock()
        out, _ = self.run_frames(lock, [[body(OTHER, 560, scale=200), body(PATIENT, 240)]] * 20)
        self.assertEqual(out[-1], (1, OK))

    def test_the_other_body_never_becomes_the_tracked_one(self):
        lock, t = self.locked()
        out, _ = self.run_frames(lock, [[body(OTHER, 560, 240), body(PATIENT, 240)]] * 30, t)
        self.assertTrue(all(idx == 1 and st == OK for idx, st in out))
        out, _ = self.run_frames(lock, [[body(PATIENT, 240), body(OTHER, 560, 240)]] * 30, t + 1)
        self.assertTrue(all(idx == 0 and st == OK for idx, st in out))

    def test_measurement_noise_does_not_lose_the_patient(self):
        rng = random.Random(7)
        lock, t = self.locked()
        frames = [[body(PATIENT, 240 + rng.uniform(-6, 6), lift=rng.uniform(0, 90), noise=0.04, rng=rng)]
                  for _ in range(300)]
        out, _ = self.run_frames(lock, frames, t)
        self.assertTrue(all(st == OK for _, st in out))

    def test_patient_walking_across_the_room_stays_locked(self):
        lock, t = self.locked()
        frames = [[body(PATIENT, 240 + k, scale=300 - k / 3)] for k in range(0, 200, 2)]
        out, _ = self.run_frames(lock, frames, t)
        self.assertTrue(all(st == OK for _, st in out))

    def test_someone_else_in_the_place_after_a_second_is_different(self):
        lock, t = self.locked()
        out, t = self.run_frames(lock, [[body(OTHER, 250)]] * 40, t)
        self.assertEqual(out[0][1], AWAY)            # first moments: not yet a swap
        self.assertEqual(out[-1], (None, DIFFERENT))

    def test_someone_else_far_from_the_place_is_only_away(self):
        lock, t = self.locked()
        out, _ = self.run_frames(lock, [[body(OTHER, 580, 240)]] * 90, t)
        self.assertEqual({st for _, st in out}, {AWAY})

    def test_a_person_standing_behind_is_not_a_replacement(self):
        lock, t = self.locked()
        out, _ = self.run_frames(lock, [[body(OTHER, 240, 190, 90)]] * 90, t)   # at the patient's spot but much further back
        self.assertEqual({st for _, st in out}, {AWAY})

    def test_different_ends_when_the_patient_is_back(self):
        lock, t = self.locked()
        _, t = self.run_frames(lock, [[body(OTHER, 250)]] * 60, t)
        self.assertEqual(lock.status, DIFFERENT)
        out, _ = self.run_frames(lock, [[body(PATIENT, 235)]], t)
        self.assertEqual(out[0], (0, OK))

    def test_different_ends_when_the_other_leaves_but_stays_away_until_the_patient_is_back(self):
        lock, t = self.locked()
        _, t = self.run_frames(lock, [[body(OTHER, 250)]] * 60, t)
        out, _ = self.run_frames(lock, [[]] * 45, t)
        self.assertEqual(out[0][1], DIFFERENT)
        self.assertEqual(out[-1], (None, AWAY))

    def test_camera_lost_is_away(self):
        lock, t = self.locked()
        _, t = self.run_frames(lock, [[body(OTHER, 250)]] * 60, t)
        lock.camera_lost()
        self.assertEqual(lock.status, AWAY)
        self.assertTrue(lock.locked)

    def test_nobody_for_two_minutes_starts_a_new_lock(self):
        lock, t = self.locked()
        _, t = self.run_frames(lock, [[]] * 3, t, dt=pl.RELOCK_AFTER / 2 + 1)
        self.assertFalse(lock.locked)
        out, _ = self.run_frames(lock, [[body(OTHER, 300)]] * 20, t)
        self.assertEqual(out[-1], (0, OK))           # the next person found is the patient

    def test_relock_by_hand(self):
        lock, t = self.locked()
        lock.reset()
        self.assertEqual(lock.status, LOCKING)
        out, _ = self.run_frames(lock, [[body(OTHER, 300)]] * 20, t)
        self.assertEqual(out[-1], (0, OK))

    def test_bodies_are_counted_and_unseen_ones_ignored(self):
        lock = PatientLock()
        ghost = Body([(0.5, 0.5, 0.0)] * 33, None)
        lock.update([body(PATIENT, 240), ghost], 0.0, W / H)
        self.assertEqual(lock.bodies, 1)

    def test_proportions_distinguish_the_two_builds_and_ignore_the_pose(self):
        a = pl.proportions(body(PATIENT, 240, lift=0).world)
        b = pl.proportions(body(PATIENT, 400, scale=200, lift=80).world)
        c = pl.proportions(body(OTHER, 240).world)
        self.assertLess(pl.proportion_distance(a, b), 0.01)
        self.assertGreater(pl.proportion_distance(a, c), pl.PROP_TOL * 1.5)
        self.assertIsNone(pl.proportion_distance({"sh": 1.0}, {"sh": 1.0}))
        self.assertEqual(pl.proportions(None), {})


if __name__ == "__main__":
    unittest.main()
