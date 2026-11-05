"""
Summarise a tracker recording (M6.1): how well the tracking held up, without Unity.

    python report.py recordings/20261105-101500.jsonl
    python report.py FILE --side R        # signed-angle counts for one side instead of the best-seen side

Replays the recording through the same tracking code as the live camera, then reports:
  - time in each whole-pose tracking state (tracking / degraded / reacquiring / lost)
  - frames with no signed side-view angle (-999: can't tell front from back), as check_signed.py counts
  - pauses: times a measured angle went missing while a person was still in view (Unity pauses counting)
  - rejected jumps: landmark frames the detector reported confidently but the tracker refused as implausible
"""
import argparse
from collections import Counter

import recording
from check_signed import INVALID
from tracking import LOW_CONFIDENCE, POSE_LOST, PREDICTED

SIGNED = ("shoulderElevSigned", "hipElevSigned")
MEASURES = ("shoulderElev", "elbowFlex", "hipElev", "kneeFlex")


def summarise(path, side=None):
    states = Counter()
    seen = 0
    missing = Counter()
    gaps = Counter()          # measure -> number of pauses
    had = {m: False for m in MEASURES}   # the previous frame had a reading
    jumps = 0
    lost_camera = 0
    frames = 0
    first_t = last_t = None
    for rec, packet, pose in recording.replay(path):
        frames += 1
        first_t = rec["t"] if first_t is None else first_t
        last_t = rec["t"]
        if rec.get("event") == "camera_lost":
            lost_camera += 1
            continue
        states[packet["trackingState"]] += 1
        jumps += sum(1 for t in pose.tracks if t.state == PREDICTED and t.confidence >= LOW_CONFIDENCE)
        person = packet["trackingState"] != POSE_LOST
        s = packet.get(side, packet) if side else packet
        if packet.get("visible"):
            seen += 1
            for k in SIGNED:
                if s.get(k, INVALID) <= INVALID + 1:
                    missing[k] += 1
        for m in MEASURES:
            reading = s.get(m, -1) >= 0
            if person and had[m] and not reading:
                gaps[m] += 1              # a reading was there and went away while someone is in view
            had[m] = reading
    return {
        "frames": frames,
        "seconds": 0.0 if first_t is None else last_t - first_t,
        "states": dict(states),
        "with_person": seen,
        "signed_missing": dict(missing),
        "pauses": dict(gaps),
        "rejected_jumps": jumps,
        "camera_lost": lost_camera,
    }


def pct(n, total):
    return f"{100.0 * n / total:.1f}%" if total else "-"


def main():
    ap = argparse.ArgumentParser(description="Summarise a TheraQuest tracker recording")
    ap.add_argument("file")
    ap.add_argument("--side", choices=["L", "R"], default=None, help="one side instead of the best-seen side")
    args = ap.parse_args()
    r = summarise(args.file, args.side)
    measured = sum(r["states"].values())
    print(f"{args.file}: {r['frames']} frames, {r['seconds']:.1f} s, camera lost {r['camera_lost']} time(s)")
    print("Tracking state:")
    for state in ("tracking", "degraded", "reacquiring", "lost"):
        n = r["states"].get(state, 0)
        print(f"  {state:12s} {n:6d}  {pct(n, measured)}")
    print(f"Frames with a person: {r['with_person']}")
    for k in SIGNED:
        n = r["signed_missing"].get(k, 0)
        print(f"  {k:20s} can't tell direction in {n} ({pct(n, r['with_person'])})")
    print("Pauses (angle missing while a person is in view):")
    for m in MEASURES:
        print(f"  {m:14s} {r['pauses'].get(m, 0)}")
    print(f"Rejected jumps (landmark frames): {r['rejected_jumps']}")


if __name__ == "__main__":
    main()
