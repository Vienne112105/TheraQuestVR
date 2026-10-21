"""
Measures how often the tracker can't give a signed side-view angle (M4.6 check).

Run this INSTEAD of Unity (both listen on UDP 5005), with tracker.py running, from the tracker folder:
    python check_signed.py              # best-seen side
    python check_signed.py --side R     # one side (the one nearest the camera)

Do the extension exercise side-on to the camera, then press Ctrl+C for the summary.
Signed angles: + = limb in front of the trunk, - = behind it, -999 = can't tell (no reading in Unity).
"""
import argparse
import json
import socket
import time

INVALID = -999


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--side", choices=["L", "R"], default=None, help="read one side instead of the best-seen side")
    ap.add_argument("--port", type=int, default=5005)
    args = ap.parse_args()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("127.0.0.1", args.port))
    sock.settimeout(1.0)
    print(f"Listening on 127.0.0.1:{args.port} ... (Ctrl+C for the summary)")

    seen = 0
    missing = {"shoulderElevSigned": 0, "hipElevSigned": 0}
    no_person = 0
    last_print = 0.0
    try:
        while True:
            try:
                data, _ = sock.recvfrom(65535)
            except socket.timeout:
                print("  no packets: is tracker.py running?")
                continue
            p = json.loads(data)
            if not p.get("visible"):
                no_person += 1
                continue
            s = p.get(args.side, p) if args.side else p
            seen += 1
            for k in missing:
                if s.get(k, INVALID) <= INVALID + 1:
                    missing[k] += 1
            now = time.time()
            if now - last_print > 0.25:
                last_print = now
                sh, hp = s.get("shoulderElevSigned", INVALID), s.get("hipElevSigned", INVALID)
                fmt = lambda v: "  can't tell" if v <= INVALID + 1 else f"{v:+7.1f}"
                print(f"  side {s.get('side', p.get('side'))}  shoulder {fmt(sh)}   hip {fmt(hp)}"
                      f"   (unsigned shoulder {s.get('shoulderElev', -1):5.1f}, hip {s.get('hipElev', -1):5.1f})")
    except KeyboardInterrupt:
        pass

    print("\n--- Summary ---")
    print(f"Frames with a person: {seen}   (frames with nobody visible: {no_person})")
    if seen:
        for k, n in missing.items():
            print(f"{k:20s} can't tell direction in {n} of {seen} frames ({100.0 * n / seen:.1f}%)")


if __name__ == "__main__":
    main()
