"""
TheraQuest server: database + REST API + therapist dashboard.
Uses only the Python standard library (no pip install needed).

Run:   python server.py            -> http://localhost:8000  (dashboard)
       python server.py --port 8080
       python server.py --reset    -> delete the database and start fresh

Listens on 127.0.0.1 by default; --host 0.0.0.0 opens the dashboard to the clinic network.
Errors: 400 bad input, 401 not signed in, 403 forbidden, 404 unknown record, 409 conflict, 429 too many sign-ins.

VR API (Unity; header X-Patient-Code: P-001; accepted from this machine only)
  GET  /api/vr/program                       today's program (effective reps include stage)
  POST /api/vr/sessions                      upload a finished session (patient_id must match the code, or be 0;
                                             a repeated session_uuid returns the stored session)

Therapist API (header Authorization: Bearer <token> from /api/auth/login; 401 without it)
  GET  /api/auth/setup                       {"needsSetup": true} until the first clinician login exists (open)
  POST /api/auth/setup                       first run only, from this machine: create that login (open)
  POST /api/auth/login | /api/auth/logout    sign in (open) / sign out
  GET  /api/auth/me                          the signed-in clinician
  POST /api/auth/password                    change password {"current_password", "new_password"}
  GET  /api/patients                         list patients
  GET  /api/patients/{id}/program            program as Unity sees it
  PUT  /api/patients/{id}/program            therapist edits prescription
  GET  /api/protocols                        protocols with their phases
  POST /api/protocols                        therapist adds a new exercise protocol
  DELETE /api/protocols/{id}                 therapist removes an exercise protocol
  POST /api/patients/{id}/phase              therapist assigns / approves a phase  {"phase_id": 3, "note": "..."}
  DELETE /api/patients/{id}/protocol         therapist removes protocol from patient
  GET  /api/library                          exercises the therapist can add
  POST /api/patients/{id}/exercises          add one from the library  {"code": "slr"}
  DELETE /api/patients/{id}/exercises/{eid}  remove one (its history is kept)
  PUT  /api/sessions/{id}/clinical           therapist records pain, soreness and swelling for a session
  GET  /api/patients/{id}/dashboard          adherence + performance analytics
  GET  /api/patients/{id}/export             export telemetry as CSV or JSON (?format=csv|json)
  GET  /api/export                           export all patient telemetry (?format=csv|json)
  Both export routes take ?kind=reps for one row per rep attempt instead of one per exercise.
  Export routes also accept ?token=<token> so the dashboard's download links work.
"""
import argparse
import csv
import hashlib
import io
import json
import os
import secrets
import sqlite3
import sys
import threading
import time
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

HERE = os.path.dirname(os.path.abspath(__file__))


class ApiError(Exception):
    """An error caused by the request, sent to the client with its status and message."""
    status = 400


class BadRequest(ApiError):
    status = 400


class NotFound(ApiError):
    status = 404


class Conflict(ApiError):
    status = 409


class Forbidden(ApiError):
    status = 403


def default_db_path():
    """DEC-010: keep patient data out of the synced project folder. THERAQUEST_DB overrides."""
    if os.environ.get("THERAQUEST_DB"):
        return os.path.abspath(os.environ["THERAQUEST_DB"])
    base = os.environ.get("LOCALAPPDATA") or os.path.join(os.path.expanduser("~"), ".local", "share")
    return os.path.join(base, "TheraQuest", "theraquest.db")


DB_PATH = default_db_path()
LEGACY_DB_PATH = os.path.join(HERE, "theraquest.db")   # where the database lived before DEC-010


def migrate_legacy_db():
    """Copy an old server/theraquest.db to DB_PATH once (SQLite backup API, so WAL contents are included)."""
    if os.path.exists(DB_PATH) or not os.path.exists(LEGACY_DB_PATH):
        return False
    if os.path.normcase(os.path.abspath(DB_PATH)) == os.path.normcase(LEGACY_DB_PATH):
        return False
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    src, dst = sqlite3.connect(LEGACY_DB_PATH), sqlite3.connect(DB_PATH)
    try:
        src.backup(dst)
    finally:
        dst.close()
        src.close()
    print(f"Moved clinical data to {DB_PATH}.\n"
          f"The old copy is still at {LEGACY_DB_PATH}; delete it once you have checked the dashboard.")
    return True


def delete_db_files(path):
    for suffix in ("", "-wal", "-shm"):
        if os.path.exists(path + suffix):
            os.remove(path + suffix)

BADGES = {
    "first": "First steps", "perfect": "Perfect form", "combo10": "Combo 10",
    "fullrom": "Bullseye", "streak3": "On a roll", "adh80": "Consistent", "lv5": "Level 5",
}

# Exercise rules sent to Unity in the VR program (DEC-012): Unity reads these instead of switching on codes.
#   posture:   standing | seated | lying | sidelying (start position of the coach and figure)
#   pose:      coach / figure animation, one of POSES (several exercises can share one)
#   direction: flex | ext | abd | None. In side view, flex / ext use the tracker's signed elevation so a
#              movement the wrong way never scores; abd and None use the unsigned angle.
#   checks:    posture checks; the rep is invalid when `metric` goes over `max` (degrees). Metrics:
#              trunkLean, elbowDrift (packet level) or any tracker angle of the measured side (kneeFlex, hipElev, ...)
POSTURES = ("standing", "seated", "lying", "sidelying")
POSES = ("shoulderAbd", "scaption", "shoulderFlex", "supineFlex", "shoulderExt", "elbowFlex", "wallPushUp",
         "hipAbd", "hipExt", "slr", "march", "heelSlide", "hamstringCurl", "miniSquat", "miniLunge", "kneeExt",
         "sitToStand")
DIRECTIONS = ("flex", "ext", "abd", None)
CHECK_METRICS = ("trunkLean", "elbowDrift", "shoulderElev", "elbowFlex", "hipElev", "kneeFlex", "kneeExt")


def _rules(posture, pose, direction=None, checks=()):
    return {"posture": posture, "pose": pose, "direction": direction, "checks": [dict(c) for c in checks]}


def _check(metric, max_deg, message):
    return {"metric": metric, "max": max_deg, "message": message}


NO_CHECKS = ()
UPRIGHT = (_check("trunkLean", 12, "Keep your trunk upright"),)
NO_FORWARD_LEAN = (_check("trunkLean", 12, "Don't lean forward"),)
NO_SIDE_LEAN = (_check("trunkLean", 12, "Don't lean to the side"),)
NO_BACK_LEAN = (_check("trunkLean", 12, "Stand tall, don't lean back"),)
ELBOW_IN = (_check("elbowDrift", 30, "Keep your elbow at your side"),)
KNEE_STRAIGHT = (_check("kneeFlex", 15, "Keep your knee straight"),)
THIGH_DOWN = (_check("hipElev", 20, "Keep your thigh pointing down"),)
CHEST_UP = (_check("trunkLean", 35, "Keep your chest up"),)

# Exercise library: every movement the tracker can measure with one webcam (2D, one plane of motion).
# `measure` is the tracker angle; the rules (last item) drive the Unity coach, figure and posture checks.
# Default numbers are starting points; the protocol phase or the therapist sets the real prescription.
# A new exercise that uses an existing pose needs only an entry here (DEC-012).
#   code: (name, joint, measure, view, start position, target, tol, safety max, hold s, sets, reps, rest s, cue,
#          _rules(posture, pose, direction, checks))
LIBRARY = {
    # Shoulder
    "shoulderAbd":  ("Shoulder abduction", "Shoulder", "shoulderElev", "front", "Standing, arm at your side, thumb up",
                     90, 10, 120, 0, 2, 8, 30, "Raise your arm out to the side",
                     _rules("standing", "shoulderAbd", "abd", UPRIGHT)),
    "shoulderFlex": ("Active shoulder elevation", "Shoulder", "shoulderElev", "side", "Standing, arm at your side, thumb forward",
                     120, 10, 140, 0, 2, 8, 30, "Raise your straight arm forward and up",
                     _rules("standing", "shoulderFlex", "flex", UPRIGHT)),
    "forwardReach": ("Active forward reach", "Shoulder", "shoulderElev", "side", "Standing, arm at your side",
                     90, 10, 110, 0, 2, 8, 30, "Reach forward to shoulder height, elbow straight",
                     _rules("standing", "shoulderFlex", "flex", UPRIGHT)),
    "supineFlex":   ("Supine shoulder flexion with cane", "Shoulder", "shoulderElev", "side",
                     "Lying on your back, holding a cane with both hands", 100, 10, 140, 0, 2, 8, 30,
                     "Let your good arm help lift the cane up and overhead",
                     _rules("lying", "supineFlex", "flex", NO_CHECKS)),
    "scaption":     ("Full can (scaption)", "Shoulder", "shoulderElev", "front", "Standing, arm slightly forward, thumb up",
                     90, 10, 110, 0, 2, 8, 30, "Raise your arm at a slight angle in front of you, thumb up",
                     _rules("standing", "scaption", "abd", UPRIGHT)),
    "wallSlide":    ("Wall slide (shoulder)", "Shoulder", "shoulderElev", "side", "Facing a wall, forearm resting on it",
                     120, 10, 140, 2, 2, 8, 30, "Slide your hand up the wall",
                     _rules("standing", "shoulderFlex", "flex", UPRIGHT)),
    "shoulderExt":  ("Shoulder extension, straight arm", "Shoulder", "shoulderElev", "side", "Standing, arm at your side",
                     45, 10, 60, 0, 2, 8, 30, "Move your straight arm back behind you",
                     _rules("standing", "shoulderExt", "ext", NO_FORWARD_LEAN)),
    # Elbow
    "elbowFlex":    ("Elbow flexion", "Elbow", "elbowFlex", "side", "Standing, elbow at your side",
                     130, 10, 150, 0, 2, 8, 30, "Bend your elbow and bring your hand up",
                     _rules("standing", "elbowFlex", None, ELBOW_IN)),
    "bicepsCurl":   ("Biceps curl", "Elbow", "elbowFlex", "side", "Standing, elbow at your side, palm up",
                     130, 10, 150, 0, 2, 10, 30, "Curl your hand up toward your shoulder",
                     _rules("standing", "elbowFlex", None, ELBOW_IN)),
    "wallPushUp":   ("Wall push-up", "Elbow", "elbowFlex", "side", "Facing a wall, hands on it at shoulder height",
                     90, 10, 0, 0, 2, 8, 30, "Bend your elbows to bring your chest toward the wall",
                     _rules("standing", "wallPushUp", None, NO_CHECKS)),
    # Hip
    "hipAbd":       ("Standing hip abduction", "Hip", "hipElev", "front", "Standing, holding a chair for balance",
                     25, 5, 40, 0, 2, 8, 30, "Lift your leg out to the side, toes forward",
                     _rules("standing", "hipAbd", "abd", NO_SIDE_LEAN)),
    "sidelyingHipAbd": ("Side-lying hip abduction", "Hip", "hipElev", "front", "Lying on your good side, operated leg on top",
                     25, 5, 40, 0, 2, 8, 30, "Lift your top leg toward the ceiling, toes forward",
                     _rules("sidelying", "hipAbd", "abd", NO_CHECKS)),
    "hipExt":       ("Standing hip extension", "Hip", "hipElev", "side", "Standing, holding a chair for balance",
                     20, 5, 30, 0, 2, 8, 30, "Move your straight leg back without leaning forward",
                     _rules("standing", "hipExt", "ext", NO_FORWARD_LEAN)),
    "slr":          ("Straight leg raise", "Hip", "hipElev", "side", "Lying on your back, other knee bent",
                     45, 5, 60, 0, 2, 8, 30, "Tighten your thigh and lift your straight leg",
                     _rules("lying", "slr", "flex", KNEE_STRAIGHT)),
    "march":        ("Standing march", "Hip", "hipElev", "side", "Standing, holding a chair for balance",
                     70, 10, 100, 0, 2, 8, 30, "Lift your knee up toward your chest",
                     _rules("standing", "march", "flex", NO_BACK_LEAN)),
    # Knee
    "kneeExt":      ("Seated knee extension (LAQ)", "Knee", "kneeExt", "side", "Sitting tall, knee bent at 90°",
                     85, 10, 0, 0, 2, 8, 30, "Straighten your knee slowly, then lower it slowly",
                     _rules("seated", "kneeExt", None, NO_CHECKS)),
    "heelSlide":    ("Heel slide", "Knee", "kneeFlex", "side", "Lying on your back, legs straight",
                     90, 10, 110, 0, 2, 8, 30, "Slide your heel toward you, bending your knee",
                     _rules("lying", "heelSlide", None, NO_CHECKS)),
    "hamstringCurl": ("Standing hamstring curl", "Knee", "kneeFlex", "side", "Standing, holding a chair for balance",
                     90, 10, 120, 0, 2, 8, 30, "Bend your knee to bring your heel toward your buttock",
                     _rules("standing", "hamstringCurl", None, THIGH_DOWN)),
    "miniSquat":    ("Mini squat", "Knee", "kneeFlex", "side", "Standing, holding a chair, feet hip-width",
                     30, 10, 50, 0, 2, 8, 30, "Bend your knees a little, chest up",
                     _rules("standing", "miniSquat", None, CHEST_UP)),
    "miniLunge":    ("Mini lunge", "Knee", "kneeFlex", "side", "Standing, operated leg a step forward, holding a chair",
                     45, 10, 70, 0, 2, 8, 30, "Bend your front knee and lower your body a little",
                     _rules("standing", "miniLunge", None, CHEST_UP)),
    "kneeWallSlide": ("Wall slide to 90° (knee)", "Knee", "kneeFlex", "side", "Back against a wall, feet a step forward",
                     90, 10, 100, 0, 2, 8, 30, "Slide down the wall until your knees bend to 90°",
                     _rules("standing", "miniSquat", None, NO_CHECKS)),
    "sitToStand":   ("Sit to stand", "Knee", "kneeExt", "side", "Sitting on a firm chair, feet flat",
                     85, 10, 0, 0, 2, 8, 45, "Lean forward and stand up tall",
                     _rules("seated", "sitToStand", None, NO_CHECKS)),
    "wallSquatHold": ("Wall squat hold", "Knee", "kneeFlex", "side", "Back flat against wall, feet shoulder-width",
                     60, 10, 85, 5, 2, 8, 30, "Slide down into a squat and hold steady",
                     _rules("standing", "miniSquat", None, CHEST_UP)),
    "quadExtHold":  ("Seated quad extension hold", "Knee", "kneeExt", "side", "Sitting tall, knee bent at 90°",
                     85, 10, 0, 3, 2, 8, 30, "Straighten your knee and hold steady at the top",
                     _rules("seated", "kneeExt", None, NO_CHECKS)),
    "scaptionHold": ("Scaption hold (Full can)", "Shoulder", "shoulderElev", "front", "Standing, arm slightly forward, thumb up",
                     90, 10, 110, 3, 2, 8, 30, "Raise arm to shoulder height in scaption plane and hold",
                     _rules("standing", "scaption", "abd", UPRIGHT)),
    "standingHipFlex": ("Standing hip flexion hold", "Hip", "hipElev", "side", "Standing, holding a chair for balance",
                     70, 10, 95, 3, 2, 8, 30, "Lift your knee high and hold steady for balance",
                     _rules("standing", "march", "flex", NO_BACK_LEAN)),
}

# Normal adult range of motion for each exercise's joint motion (AAOS values as tabulated in
# Norkin & White, Measurement of Joint Motion: A Guide to Goniometry). Shown to the therapist next to the
# prescription, with a warning when a target or safety max goes past it. Check against your edition.
#   code: (joint motion, normal maximum in the tracker's degrees)
NORMAL_ROM = {
    "shoulderAbd": ("Shoulder abduction 0-180°", 180), "shoulderFlex": ("Shoulder flexion 0-180°", 180),
    "forwardReach": ("Shoulder flexion 0-180°", 180), "supineFlex": ("Shoulder flexion 0-180°", 180),
    "scaption": ("Shoulder elevation 0-180°", 180), "scaptionHold": ("Shoulder elevation 0-180°", 180),
    "wallSlide": ("Shoulder flexion 0-180°", 180),
    "shoulderExt": ("Shoulder extension 0-60°", 60),
    "elbowFlex": ("Elbow flexion 0-150°", 150), "bicepsCurl": ("Elbow flexion 0-150°", 150),
    "wallPushUp": ("Elbow flexion 0-150°", 150),
    "hipAbd": ("Hip abduction 0-45°", 45), "sidelyingHipAbd": ("Hip abduction 0-45°", 45),
    "hipExt": ("Hip extension 0-30°", 30), "slr": ("Hip flexion 0-120°", 120),
    "march": ("Hip flexion 0-120°", 120), "standingHipFlex": ("Hip flexion 0-120°", 120),
    "kneeExt": ("Knee extension to 0° (90 on this scale = straight)", 90),
    "quadExtHold": ("Knee extension to 0° (90 on this scale = straight)", 90),
    "sitToStand": ("Knee extension to 0° (90 on this scale = straight)", 90),
    "heelSlide": ("Knee flexion 0-135°", 135), "hamstringCurl": ("Knee flexion 0-135°", 135),
    "miniSquat": ("Knee flexion 0-135°", 135), "miniLunge": ("Knee flexion 0-135°", 135),
    "kneeWallSlide": ("Knee flexion 0-135°", 135), "wallSquatHold": ("Knee flexion 0-135°", 135),
}

# Protocols from the published documents, loaded into the protocol tables.
#   - Phases, goals, precautions, ROM goals and progression rules follow the documents.
#   - Each VR phase holds the protocol's exercises that one webcam can measure; the rest are listed
#     under `other` (done without the camera: isometrics, rotation, bike, manual therapy, ...).
#   - The protocols don't give angles or reps for most exercises; those numbers are starting points
#     (OHSU's "2x8" progression rule is used for sets x reps). Have your physical therapist confirm them.
# Phases with vr=False (immobilization, passive motion, return to sport) have no VR session.
#   protocol: (name, condition, source, [phases])
#   phase:    (name, weeks, vr, goals, precautions, ROM goal, other exercises, max pain increase,
#              check soreness < 2 h, max swelling cm or None,
#              [(code, target, tol, safety max, hold s, sets, reps, rest s)])
PROTOCOL_VERSION = "3"   # 3: seven protocols added (M5.7); unchanged built-ins are kept on reload
OHSU_RULES = "Progress when 2x8 reps are done with pain up by no more than 2 points, swelling up by under 2 cm and soreness gone within 2 hours"
PROTOCOLS = [
    ("Total knee replacement (OHSU)", "Post-op total knee arthroplasty",
     "OHSU Health Total Knee Best Practice Rehab Guideline, HC-REH-400.30.3-ROP-GUD (Nov 2023)", [
        ("Phase I - Immediate post-op", "From hospital discharge (0-90° by week 1)", True,
         "Active quad contraction; passive knee extension to 0°; knee flexion to at least 90°; walking with a device; swelling control",
         "Monitor wound healing and excess swelling; watch for signs of DVT. " + OHSU_RULES,
         "Knee ROM better than 5°-90°",
         "Ankle pumps, passive knee extension stretches, quad sets, stationary bike or recumbent stepper without resistance, "
         "hamstring and calf stretches, gait training, ice and elevation",
         2, True, 2.0,
         [("heelSlide", 90, 10, 100, 0, 2, 8, 30), ("kneeExt", 80, 10, 0, 0, 2, 8, 30),
          ("miniSquat", 30, 10, 45, 0, 2, 8, 30), ("sidelyingHipAbd", 25, 5, 40, 0, 2, 8, 30)]),
        ("Phase II - Motion and mobility", "About weeks 2-6", True,
         "Active ROM 0-110°; quadriceps strengthening; proprioception and endurance; normal gait; gradual return to daily activity",
         OHSU_RULES,
         "Knee ROM better than 5°-110°",
         "Standing calf raises, stationary bike (no or light resistance), single-leg stance, step ups and downs, "
         "stretching (hamstring, quads, calf), walking program 30 min a day",
         2, True, 2.0,
         [("kneeExt", 85, 10, 0, 0, 2, 8, 30), ("slr", 45, 5, 60, 0, 2, 8, 30), ("hamstringCurl", 90, 10, 110, 0, 2, 8, 30),
          ("hipAbd", 25, 5, 40, 0, 2, 8, 30), ("hipExt", 20, 5, 30, 0, 2, 8, 30), ("sitToStand", 85, 10, 0, 0, 2, 8, 45),
          ("march", 70, 10, 100, 0, 2, 8, 30), ("miniLunge", 30, 10, 50, 0, 2, 8, 30), ("heelSlide", 110, 10, 120, 0, 2, 8, 30)]),
        ("Phase III - Intermediate", "About weeks 6-10", True,
         "Active ROM 0-120°; closed-chain exercise; proprioception; normal gait; light recreational activity",
         OHSU_RULES,
         "Knee ROM 0°-120° with good quad control",
         "Leg press, calf press, step ups and side step ups, single-limb stance on foam, star excursion balance, "
         "tilt-board squats, stability-ball hip extension, aquatic therapy, bike (+10% resistance every 2 weeks)",
         2, True, 2.0,
         [("kneeExt", 90, 5, 0, 0, 2, 8, 30), ("hipExt", 25, 5, 30, 0, 2, 8, 30), ("hipAbd", 30, 5, 45, 0, 2, 8, 30),
          ("miniLunge", 60, 10, 80, 0, 2, 8, 30), ("kneeWallSlide", 90, 10, 100, 0, 2, 8, 30), ("heelSlide", 120, 10, 130, 0, 2, 8, 30)]),
        ("Phase IV - Advanced strengthening", "Most patients finish by week 12", True,
         "Maximize ROM; good lower-limb strength; return to desired activities; independent home program",
         OHSU_RULES,
         "Expected ROM achieved (normal pre-op knee: 0-120 to 130°)",
         "Eccentric leg press and calf press, step ups and downs, star excursion reaching, ball bridge with curl, "
         "agility (side shuffle, backward walking, braiding), single-leg stance, 30+ min walking or cycling a day",
         2, True, 2.0,
         [("kneeExt", 90, 5, 0, 0, 2, 8, 30), ("hipExt", 25, 5, 30, 0, 2, 8, 30), ("hipAbd", 30, 5, 45, 0, 2, 8, 30),
          ("miniLunge", 60, 10, 80, 0, 2, 8, 30), ("kneeWallSlide", 90, 10, 100, 5, 2, 8, 30)]),
        ("Phase V - Return to advanced activities", "As needed, 2x a month", False,
         "Full pain-free ROM; minimal swelling; return to recreational activities", "",
         "Full pain-free ROM", "Sports-specific movements; golf, doubles tennis, walking, hiking or biking program",
         2, True, 2.0, []),
    ]),
    ("Rotator cuff repair, large to massive (MGB)", "Post-op arthroscopic rotator cuff repair",
     "Mass General Brigham Sports Medicine - Rehabilitation Protocol for Arthroscopic Rotator Cuff Repair, Large to Massive Tears", [
        ("Phase I - Immediate post-op (immobilization)", "Weeks 1-6", False,
         "Protect the repair and promote tendon-to-bone healing; sling for 6 weeks (abduction pillow 30-45°); reduce pain and inflammation",
         "Do not actively move the surgical arm; no weight bearing through it; no passive or active shoulder ROM; "
         "no reaching overhead or behind the back; no pushing or pulling",
         "Appropriate healing; pain and inflammation controlled",
         "Hand, wrist and elbow AROM (no active elbow ROM for 4 weeks after biceps tenodesis); scapular mobility in the sling",
         0, False, None, []),
        ("Phase II - Passive ROM", "Weeks 6-10", False,
         "Minimize stiffness while protecting the repair; passive ROM with the therapist; home exercise program",
         "No active shoulder ROM; avoid aggressive or painful passive ROM; no internal rotation (behind the back); "
         "no weight bearing on the arm",
         "Passive forward elevation 100-120°, passive ER 25-45° at neutral, passive abduction 90°",
         "Supine passive elevation 0-100° and seated passive ER 0-30° with the PT, table slide, pendulums, "
         "scapular retraction, elevation and depression",
         0, False, None, []),
        ("Phase III - Active-assisted, then active ROM", "Weeks 10-18", True,
         "Active-assisted ROM (weeks 10-14), then active ROM (weeks 14-18); normal daily activities. "
         "Wall slide from week 12; forward reach and active elevation from week 14",
         "No lifting or painful activities; no supporting body weight on the arms; no excessive behind-the-back "
         "movement; no sudden or jerking motions",
         "Active forward elevation over 120° without compensation (passive over 140°)",
         "Supine cane abduction and external rotation, assisted ER, standing and side-lying ER AROM (rotation can't "
         "be measured with one camera), submaximal isometrics, standing rows, manual therapy",
         0, False, None,
         [("supineFlex", 100, 10, 140, 0, 2, 8, 30), ("wallSlide", 120, 10, 140, 0, 2, 8, 30),
          ("forwardReach", 90, 10, 110, 0, 2, 8, 30), ("shoulderFlex", 120, 10, 140, 0, 2, 8, 30)]),
        ("Phase IV - Initial strengthening", "Weeks 18-22", True,
         "Full ROM; gradually restore strength, power and endurance; full daily activities and work",
         "No lifting over 5 lb; no sudden lifting, jerking, pushing or throwing; no straight-arm lateral raise "
         "(long-lever abduction); never raise the arm in the empty-can position",
         "Full ROM in all planes with normal movement",
         "Pec, internal-rotation, doorway ER, cross-body and sleeper stretches; prone W, Y, T, I; supine protraction; "
         "rows; resisted ER and IR; triceps extension; rhythmic stabilization",
         0, False, None,
         [("shoulderExt", 45, 10, 60, 0, 2, 8, 30), ("forwardReach", 90, 10, 110, 0, 2, 8, 30),
          ("bicepsCurl", 130, 10, 150, 0, 2, 10, 30), ("shoulderFlex", 150, 10, 170, 0, 2, 8, 30)]),
        ("Phase V - Advanced strengthening", "Weeks 22-26", True,
         "Restore maximal strength, power and endurance; keep pain-free ROM",
         "No lifting over 10 lb; no overhead lifting; no sudden pushing or lifting; nothing painful",
         "Full, pain-free ROM without compensation",
         "ER at 45° and 90° abduction, IR at 90° abduction, PNF D1/D2 diagonals, dynamic hug, counter and floor push-ups",
         0, False, None,
         [("scaption", 90, 10, 110, 0, 2, 10, 30), ("wallPushUp", 90, 10, 0, 0, 2, 8, 30),
          ("shoulderExt", 45, 10, 60, 0, 2, 10, 30), ("bicepsCurl", 130, 10, 150, 0, 2, 10, 30)]),
        ("Phase VI - Return to sport", "Weeks 26-30", False,
         "Keep ROM; progress strength (85-90% of the other side); return to work, recreation or sport",
         "No forceful or heavy lifting; no sudden pushing or lifting; nothing painful",
         "Full ROM and strength", "Daily home stretching; strengthening 3 days a week; activity-specific progression",
         0, False, None, []),
    ]),
    # ------------------------------------------------------------------ added in protocol version 3 (M5.7)
    ("ACL reconstruction (MGB)", "Post-op anterior cruciate ligament reconstruction",
     "Mass General Brigham Sports Medicine - Rehabilitation Protocol for ACL Reconstruction (revised 8/2024)", [
        ("Phase I - Immediate post-op", "Weeks 0-2", True,
         "Protect the graft; reduce swelling and pain; restore patellar mobility; restore full extension and gradually "
         "improve flexion; re-establish quad control and full active extension",
         "Keep the knee straight and elevated when resting (no towel under the knee); do not actively kick the knee straight; "
         "do not pivot on the surgical leg; WBAT with brace locked and crutches per surgeon (allograft or hamstring autograft: "
         "partial weight bearing with crutches for 6 weeks); no straight leg raise while there is an extension lag; "
         "with a meniscus repair or other injury follow the more conservative protocol",
         "Knee extension 0°; straight leg raise without lag",
         "Ice, compression, elevation, retrograde massage, ankle pumps, patellar mobilizations, prone hang and heel prop, "
         "gastroc, soleus and hamstring stretches, quad sets with NMES, calf raises, multi-angle isometrics at 90° and 60°",
         0, False, None,
         [("heelSlide", 90, 10, 100, 0, 2, 8, 30), ("slr", 45, 5, 60, 0, 2, 8, 30), ("sidelyingHipAbd", 25, 5, 40, 0, 2, 8, 30)]),
        ("Phase II - Intermediate post-op", "Weeks 3-5", True,
         "Continue to protect the graft; maintain full extension and restore full flexion (equal to the other side); normalize gait",
         "Hamstring autograft: no resisted hamstring strengthening until week 12. Progress when swelling is 1+ or less and stable, "
         "flexion is within 10° of the other side and extension is equal",
         "Flexion within 10° of the other knee; extension equal to the other knee",
         "Stationary bike, quad, hamstring and hip flexor stretches, step ups, leg press and hamstring curl machines, bridges, "
         "clamshells, hip hikes, single-leg balance (static to dynamic, firm to unsteady), lateral step-overs, joint position training",
         0, False, None,
         [("heelSlide", 120, 10, 135, 0, 2, 8, 30), ("hamstringCurl", 90, 10, 110, 0, 2, 8, 30),
          ("miniSquat", 45, 10, 60, 0, 2, 8, 30), ("march", 70, 10, 100, 0, 2, 8, 30), ("hipAbd", 25, 5, 40, 0, 2, 8, 30)]),
        ("Phase III - Late post-op", "Weeks 6-8", True,
         "Maintain full ROM; progress strengthening safely; promote proper movement patterns; avoid post-exercise pain and "
         "swelling and pain at the graft donor site",
         "Seated knee extension only between 90° and 45° of knee bend (avoid anterior knee pain). Progress with no swelling or "
         "pain after exercise, normal gait, ROM equal to the other side and joint position sense within 5°",
         "ROM equal to the other knee",
         "Rotational tibial mobilizations if ROM is limited; from week 8 elliptical, stair climber, pool jogging; hip machines, "
         "lateral lunges, lateral band walks, Romanian and single-leg deadlifts, ball bridges, single-leg press, step downs, "
         "single-leg squats, perturbation balance training",
         0, False, None,
         [("kneeExt", 45, 5, 50, 0, 2, 8, 30), ("sitToStand", 85, 10, 0, 0, 2, 8, 45), ("miniLunge", 60, 10, 80, 0, 2, 8, 30),
          ("kneeWallSlide", 90, 10, 100, 0, 2, 8, 30), ("hipExt", 20, 5, 30, 0, 2, 8, 30), ("hipAbd", 30, 5, 45, 0, 2, 8, 30)]),
        ("Phase IV - Transitional", "Weeks 9-12", True,
         "Maintain full ROM; progress strengthening; promote proper movement patterns; begin sub-maximal sport-specific "
         "training in the sagittal plane",
         "Avoid post-exercise pain or swelling and pain at the graft donor site. Progress with no instability, 10 single-leg "
         "squats to at least 60° with good form, a controlled drop vertical jump, KOOS-sports over 70% and quad, hamstring "
         "and glute strength over 80% of the other side",
         "Full ROM; single-leg squat to at least 60° of knee bend",
         "Double-leg plyometrics progressing to full weight bearing (med ball slams, shuttle jumps, hops in place, box jumps, "
         "small drop jumps), sport-specific drills",
         0, False, None,
         [("wallSquatHold", 60, 10, 85, 5, 2, 8, 30), ("miniLunge", 60, 10, 80, 0, 2, 8, 30), ("kneeExt", 45, 5, 50, 0, 2, 8, 30),
          ("hipExt", 25, 5, 30, 0, 2, 8, 30), ("hipAbd", 30, 5, 45, 0, 2, 8, 30)]),
        ("Phase V - Early return to sport", "Months 3-5", False,
         "Progress strengthening; begin single-leg plyometrics and a sport-specific training program",
         "Surgeon clearance and all milestone criteria met before progressing",
         "Full ROM; strength and hop tests 90% of the other side",
         "Return to Running program, agility and plyometric program (with functional brace if prescribed)",
         0, False, None, []),
        ("Phase VI - Return to sport", "6+ months", False,
         "Symmetrical performance in sport-specific drills; safe progression to full sport (cutting and pivoting about 7-9 months, "
         "full play about 9-12 months)",
         "Strength and hop tests 95% of the other side, KOOS-sports over 90%, IKDC over 93, ACL-RSI 90%",
         "Full ROM and strength", "Multi-plane plyometrics and agility, non-contact then full practice", 0, False, None, []),
    ]),
    ("Total knee replacement (MGB)", "Post-op total knee arthroplasty",
     "Mass General Brigham Orthopedics - Rehabilitation Protocol for Total Knee Arthroplasty (06/2025)", [
        ("Phase I - Immediate post-op", "Days 0-7", True,
         "Quiet knee (minimal pain and swelling); protect the incision and watch wound healing; screen for DVT; activate the "
         "quadriceps; begin gentle assisted mobility",
         "Follow the surgeon's weight-bearing orders; do not force painful ROM; no pillow or towel roll under the knee; no "
         "twisting or pivoting; limit prolonged sitting and standing; limit walking to about 700 steps a day",
         "Near full extension and more than 70° of knee flexion; straight leg raise without lag",
         "Heel prop, patellar mobilizations, cryotherapy and elevation, NMES with quad activation, gluteal sets, bed mobility, "
         "transfer, gait and stair training",
         0, False, None,
         [("heelSlide", 70, 10, 90, 0, 2, 8, 30), ("slr", 40, 5, 60, 0, 2, 8, 30)]),
        ("Phase II - Early post-op", "Weeks 1-4", True,
         "Restore full extension early; knee flexion over 90°; begin quadriceps strengthening; reduce reliance on the "
         "walking aid; minimize gait compensations",
         "Avoid deep squats, pivoting and impact activity; watch for increased pain or swelling. Progress with pain 0-3/10 in "
         "daily activities and ten straight leg raises without lag",
         "Near full extension and more than 90° of knee flexion",
         "Tibiofemoral and patellar mobilizations, wall slides, heel prop with weight, stationary bike for ROM, calf and "
         "hamstring stretches, short arc quad, bridging, side-lying adduction, prone hip extension, clamshells, weight shifting, "
         "side stepping at the counter",
         0, False, None,
         [("heelSlide", 95, 10, 110, 0, 2, 8, 30), ("sitToStand", 85, 10, 0, 0, 2, 8, 45), ("miniSquat", 30, 10, 45, 0, 2, 8, 30),
          ("sidelyingHipAbd", 25, 5, 40, 0, 2, 8, 30), ("hamstringCurl", 80, 10, 100, 0, 2, 8, 30)]),
        ("Phase III - Intermediate post-op", "Weeks 4-8", True,
         "Knee flexion over 110° with full extension; improve quadriceps, hip and core strength; normal gait without a walking "
         "aid; begin balance and advanced functional tasks",
         "Avoid high-impact activity; progress load gradually; keep the knee aligned in closed-chain exercises; keep a quiet knee. "
         "Progress with controlled 6-inch step ups and downs and no increase in pain or swelling",
         "About 110° of knee flexion and full extension",
         "Prone knee hangs, retro-walking, calf, hip flexor and hamstring stretches, banded hip flexion, step ups and downs, "
         "lateral step downs, bridges, leg press, single-leg stance, rocker board, lateral step-overs, treadmill or elliptical",
         0, False, None,
         [("kneeExt", 85, 10, 0, 0, 2, 8, 30), ("heelSlide", 110, 10, 125, 0, 2, 8, 30), ("hipAbd", 25, 5, 40, 0, 2, 8, 30),
          ("hipExt", 20, 5, 30, 0, 2, 8, 30), ("wallSquatHold", 45, 10, 60, 5, 2, 8, 30), ("miniLunge", 45, 10, 60, 0, 2, 8, 30)]),
        ("Phase IV - Advanced post-op", "Weeks 8-12", True,
         "Near-normal strength (80% of the other leg); ROM over 120° for daily tasks; proper movement patterns",
         "No uncontrolled pivoting or cutting; no high-impact activity; progress load only without pain or swelling. Progress "
         "with controlled 8-inch step ups and downs and surgeon clearance for low-impact recreation",
         "Full or near-full ROM (more than 120° of knee flexion)",
         "Gait on uneven ground and slopes, prone quad and kneeling hip flexor stretches, banded side steps, monster walks, "
         "hamstring curl and leg extension machines, single-leg stance with perturbation, tandem walking, bike, aquatic program",
         0, False, None,
         [("kneeExt", 90, 5, 0, 0, 2, 8, 30), ("miniSquat", 60, 10, 75, 0, 2, 8, 30), ("miniLunge", 60, 10, 80, 0, 2, 8, 30),
          ("hipAbd", 30, 5, 45, 0, 2, 8, 30), ("hipExt", 25, 5, 30, 0, 2, 8, 30), ("heelSlide", 120, 10, 135, 0, 2, 8, 30)]),
        ("Phase V - Late post-op", "Months 3-6", False,
         "Restore full strength and function; return to low-impact recreation (golf, tennis, hiking) with physician clearance",
         "High-impact sport, plyometrics and running generally discouraged after joint replacement; consult the surgeon first",
         "Strength 95% of the other leg", "Multi-joint, multi-plane strengthening, bike at high resistance, swimming",
         0, False, None, []),
    ]),
    ("Hip fracture fixation (Ferrel)", "Post-op hip fracture fixation",
     "Jason R. Ferrel, MD - Hip Fracture Fixation Rehabilitation Protocol (last updated July 10, 2024)", [
        ("Phase I - Early post-op", "Weeks 0-2", True,
         "Bed to standing and bed to chair transfers; standing practice with a walker in 30-second intervals; walking with "
         "physical therapy 3 times a day; knee and ankle motion",
         "Weight bearing as tolerated; no brace; hip flexion no more than 90°, progressed slowly as pain allows; knee and ankle "
         "ROM unlimited",
         "Hip flexion up to 90° as pain allows",
         "Ice, ankle pumps, thigh and gluteal squeezes, walker gait training",
         2, False, None,
         [("heelSlide", 90, 10, 110, 0, 2, 8, 30), ("kneeExt", 85, 10, 0, 0, 2, 8, 30), ("sitToStand", 85, 10, 0, 0, 2, 5, 60)]),
        ("Phase II - Progressive mobility", "Weeks 2-6", True,
         "Progress transfers, standing time and walking distance with physical therapy 3 times a day",
         "Weight bearing as tolerated; hip flexion no more than 90°, progressed slowly as pain allows",
         "Hip flexion up to 90° as pain allows",
         "Ankle pumps, thigh and gluteal squeezes, longer standing intervals and walks",
         2, False, None,
         [("heelSlide", 100, 10, 120, 0, 2, 8, 30), ("kneeExt", 85, 10, 0, 0, 2, 8, 30), ("sitToStand", 85, 10, 0, 0, 2, 8, 45)]),
        ("Phase III - Gentle strengthening", "Weeks 6-12", True,
         "Continue progressing weight bearing and ROM; gentle strengthening",
         "Progress gently; stop exercises that cause pain",
         "Progressing hip ROM",
         "Calf raises; hip adduction (4-way hip kicks)",
         2, False, None,
         [("hipAbd", 20, 5, 35, 0, 2, 8, 30), ("hipExt", 15, 5, 25, 0, 2, 8, 30), ("march", 60, 10, 90, 0, 2, 8, 30),
          ("hamstringCurl", 80, 10, 100, 0, 2, 8, 30), ("miniSquat", 30, 10, 45, 0, 2, 8, 30)]),
        ("Phase IV - Continued strengthening", "After week 12", True,
         "Continue progressing weight bearing, ROM and gentle strengthening",
         "Progress gently; stop exercises that cause pain",
         "Progressing hip ROM",
         "Calf raises; hip adduction (4-way hip kicks)",
         2, False, None,
         [("hipAbd", 25, 5, 40, 0, 2, 8, 30), ("hipExt", 20, 5, 30, 0, 2, 8, 30), ("march", 70, 10, 100, 0, 2, 8, 30),
          ("hamstringCurl", 90, 10, 110, 0, 2, 8, 30), ("miniSquat", 40, 10, 55, 0, 2, 8, 30)]),
    ]),
    ("Ankle fracture ORIF (MGB)", "Post-op ankle fracture with open reduction and internal fixation",
     "Mass General Brigham Sports Medicine - Rehabilitation Protocol for Ankle Fracture with ORIF (revised 10/2021)", [
        ("Phase I - Immediate post-op", "Weeks 0-6", True,
         "Safe walking within the weight-bearing orders, including transfers and stairs; manage swelling; ankle ROM; keep "
         "core, hip, knee and arm strength",
         "Weight bearing and boot or cast per surgeon; VR exercises lying down only while non-weight bearing; no joint "
         "mobilizations near the fracture; no instrument-assisted soft tissue work over the fracture until week 6. Progress "
         "with pain under 3/10, minimal swelling, more ankle ROM and surgeon clearance for WBAT or full weight bearing",
         "Increasing ankle ROM (measured by the therapist, not the webcam)",
         "Ankle pumps, circles, inversion and eversion, seated heel slides for dorsiflexion, toe stretching, scar mobilization, "
         "arm bike, quad sets, abdominal bracing, clamshells, prone hip extension and hamstring curls, seated heel and toe raises, "
         "arch doming, joint position training",
         0, False, None,
         [("slr", 45, 5, 60, 0, 2, 8, 30), ("sidelyingHipAbd", 25, 5, 40, 0, 2, 8, 30)]),
        ("Phase II - Intermediate post-op", "Weeks 7-12", True,
         "Full ankle and foot ROM; progress strengthening; normal gait on all surfaces, weaning from the boot; return to "
         "regular activities except sport",
         "Full weight bearing and boot weaning per surgeon; standing VR exercises only once full weight bearing is allowed; "
         "no joint mobilizations near the fracture until it is radiographically healed. Progress with no swelling or pain after "
         "exercise, normal gait in a sneaker and ankle AROM equal to the other side",
         "Ankle AROM equal to the other side (measured by the therapist)",
         "Standing dorsiflexion stretch on a step, calf stretches, banded ankle exercises in 4 directions, heel raise progression, "
         "stationary bike, treadmill, hip and leg machines, ball bridges, wobble board and single-leg balance",
         0, False, None,
         [("hipAbd", 25, 5, 40, 0, 2, 8, 30), ("hipExt", 20, 5, 30, 0, 2, 8, 30), ("hamstringCurl", 90, 10, 110, 0, 2, 8, 30),
          ("miniSquat", 30, 10, 45, 0, 2, 8, 30)]),
        ("Phase III - Late post-op", "Weeks 13-16", True,
         "Good balance and control on the injured leg in all planes; progress strengthening; proper movement patterns",
         "Avoid post-exercise pain and swelling",
         "Full ankle ROM",
         "Joint mobilizations as needed, calf machine, single-leg heel raises, hip hikes, single-leg press, slide-board lunges, "
         "lateral step ups, step downs, single-leg squats, single-leg balance on unstable surfaces",
         0, False, None,
         [("miniLunge", 45, 10, 60, 0, 2, 8, 30), ("miniSquat", 45, 10, 60, 0, 2, 8, 30), ("sitToStand", 85, 10, 0, 0, 2, 8, 45),
          ("kneeWallSlide", 60, 10, 75, 0, 2, 8, 30), ("march", 70, 10, 100, 0, 2, 8, 30), ("hipAbd", 30, 5, 45, 0, 2, 8, 30)]),
        ("Phase IV - Transitional", "Weeks 17-20", False,
         "Progress to plyometrics, sport-specific movement and low-impact fitness",
         "Progress with no swelling or pain after exercise, heel rise test over 90% of the other side and 30 minutes of fast "
         "walking without swelling or pain",
         "Full ROM", "Elliptical, stair climber, rebounding heel raises, hopping in place", 0, False, None, []),
        ("Phase V - Return to sport", "5+ months", False,
         "Gradual return to running, jumping, hiking and sport",
         "Surgeon clearance; functional tests 90% of the other side", "Full ROM and strength",
         "Return to Running program, agility and plyometric program", 0, False, None, []),
    ]),
    ("Distal radius fracture ORIF (BWH)", "Post-op distal radius (wrist) fracture with ORIF",
     "Brigham and Women's Hospital Rehabilitation Services - Distal Radius Fracture Post-Operative Hand Therapy Guideline (February 2021)", [
        ("Phase I - Immediate post-op", "Days 1-10", True,
         "Early ROM of the fingers, elbow and shoulder; minimize swelling (arm above the heart when resting; no sling, to "
         "prevent shoulder stiffness)",
         "No weight bearing on the injured arm; no lifting, pushing, pulling or forceful gripping; wrist orthosis as the surgeon "
         "directs",
         "Full elbow and shoulder motion; finger motion as tolerated",
         "Finger and thumb AROM throughout the day, edema management, custom or prefabricated wrist orthosis from day 3-4",
         2, False, None,
         [("elbowFlex", 130, 10, 150, 0, 2, 8, 30), ("forwardReach", 90, 10, 110, 0, 2, 8, 30),
          ("shoulderAbd", 90, 10, 120, 0, 2, 8, 30)]),
        ("Phase II - Protection", "Day 11 to week 5", True,
         "Increase wrist and forearm ROM; light functional use with the orthosis on; start grip strengthening; wean the "
         "orthosis from week 4-5",
         "No weight bearing on the injured arm; orthosis on at all times except hygiene and exercise until weaning starts; "
         "mild discomfort is expected. Progress when wrist and forearm ROM improve with little or no pain",
         "Improving wrist and forearm ROM (measured by the therapist)",
         "Wrist and forearm active and active-assisted ROM, edema control (ice, Coban, compression, Kinesiotape), scar "
         "management, grip and pinch strengthening, light daily tasks",
         2, False, None,
         [("elbowFlex", 140, 10, 150, 0, 2, 8, 30), ("shoulderFlex", 140, 10, 160, 0, 2, 8, 30),
          ("shoulderAbd", 120, 10, 140, 0, 2, 8, 30)]),
        ("Phase III - Intermediate", "Weeks 6-12", True,
         "Regain wrist and forearm ROM and functional strength; return to previous daily activities",
         "Gentle weight bearing only: table or counter first, then wall, then hands and knees; orthosis at night and in crowds "
         "until week 8. Do wall push-ups only once counter-top weight bearing is comfortable",
         "Wrist and forearm ROM regained (measured by the therapist)",
         "Wrist and forearm joint mobilizations, static progressive orthosis if ordered, progressive wrist resistance from "
         "week 6-8, quadruped and modified push-ups",
         2, False, None,
         [("wallPushUp", 90, 10, 0, 0, 2, 8, 30), ("elbowFlex", 140, 10, 150, 0, 2, 8, 30),
          ("shoulderFlex", 150, 10, 170, 0, 2, 8, 30)]),
        ("Phase IV - Advanced strengthening", "Weeks 12-20", False,
         "Return to heavy work or sport; strengthening continues on the patient's own, with a trainer or in work conditioning",
         "Formal therapy usually ends by week 8-12", "Functional strength for work or sport",
         "Progressive strengthening and weight bearing for work or sport", 2, False, None, []),
    ]),
    ("Tibial plateau fracture ORIF (TCO)", "Post-op tibial plateau fracture with ORIF",
     "Twin Cities Orthopedics, Matthew S. Butterfield, MD - Tibial Plateau Fracture ORIF PT Protocol (04/2024)", [
        ("Phase I - Early post-op", "Weeks 0-2", True,
         "Begin passive, assisted and active knee ROM 0-30° when seated; patellar mobilization; pain and swelling control; "
         "quad activation",
         "Hinged knee brace for 8 weeks, locked at 0° for walking and sleeping; unlock only when seated for 0-30°; touch-down "
         "weight bearing with crutches or walker",
         "Knee 0-30°",
         "Patellar mobilization, ankle pumps, quad sets, NMES as needed",
         2, False, None,
         [("heelSlide", 30, 5, 35, 0, 2, 8, 30), ("slr", 45, 5, 60, 0, 2, 8, 30)]),
        ("Phase II - Protected motion", "Weeks 2-6", True,
         "Progress knee ROM to 0-90° (60° by week 4, 90° by week 6); quad isometrics; hip and core strength",
         "Touch-down weight bearing in the brace; brace may be unlocked for walking from week 2; knee no further than 90°",
         "60° knee flexion by week 4; 90° by week 6",
         "Quad isometrics, knee extension stretches, heel raises, NMES or blood flow restriction as needed",
         2, False, None,
         [("heelSlide", 60, 10, 90, 0, 2, 8, 30), ("slr", 45, 5, 60, 0, 2, 8, 30), ("sidelyingHipAbd", 25, 5, 40, 0, 2, 8, 30)]),
        ("Phase III - Loading", "Weeks 6-10", True,
         "Reach full knee ROM; closed-chain exercise; hamstring strength; proprioception and balance",
         "Touch-down weight bearing until week 8, then full weight bearing as tolerated; stop walker, cane or crutches at about "
         "week 9 and the brace at week 10; lunges and other closed-chain work only once full weight bearing is allowed",
         "Full knee ROM",
         "Seated leg press 0-90°, proprioception, core and glute work, daily quad, hamstring and calf stretches, stationary bike "
         "from week 8",
         2, False, None,
         [("heelSlide", 110, 10, 130, 0, 2, 8, 30), ("hamstringCurl", 90, 10, 110, 0, 2, 8, 30), ("hipAbd", 25, 5, 40, 0, 2, 8, 30),
          ("miniLunge", 45, 10, 60, 0, 2, 8, 30)]),
        ("Phase IV - Strengthening", "Weeks 10-16", True,
         "Full ROM; functional strengthening; proprioception; low-intensity plyometrics from week 12",
         "Start gym equipment light with high reps, then progress the load",
         "Full knee ROM",
         "Seated leg press, step up and step down, single-leg squat to chair, low-intensity double then single-leg hopping from "
         "week 12, bike with resistance",
         2, False, None,
         [("sitToStand", 85, 10, 0, 0, 2, 8, 45), ("kneeWallSlide", 90, 10, 100, 0, 2, 8, 30), ("miniSquat", 45, 10, 60, 0, 2, 8, 30),
          ("miniLunge", 60, 10, 80, 0, 2, 8, 30), ("hipAbd", 30, 5, 45, 0, 2, 8, 30)]),
        ("Phase V - Return to activity", "Week 16+", False,
         "Advanced function: running, sprinting, jumping and sport-specific activity; return to sport at 5-6 months",
         "Per surgeon", "Full ROM and strength", "Agility, plyometrics and running progression", 2, False, None, []),
    ]),
    ("Lateral ankle sprain (MGB)", "Lateral ankle sprain, non-operative",
     "Mass General Brigham Sports Medicine - Rehabilitation Protocol for Lateral Ankle Sprain: Non-operative Management (revised 9/2021)", [
        ("Phase I - Protection and optimal loading", "Weeks 1-2", False,
         "Reduce pain and swelling; improve weight bearing; protect healing structures",
         "Brace or tape for weight-bearing activity; immobilization for 10 days for a severe sprain",
         "Pain-free ankle motion as tolerated",
         "Foot and ankle PROM, ankle pumps, circles and alphabet, seated heel and toe raises, towel curls, BAPS board, joint "
         "mobilization for pain, gait training, balance on a firm surface if pain-free; ice, compression, elevation",
         0, False, None, []),
        ("Phase II - Sub-acute", "Weeks 3-6", True,
         "Reduce pain; normalize gait; improve ankle ROM and single-leg stance; keep or improve hip and knee strength",
         "Brace for weight-bearing activity. Progress with a non-antalgic gait, equal single-leg stance, full ankle ROM and 5/5 "
         "ankle strength",
         "Full ankle PROM and AROM (measured by the therapist)",
         "Knee-to-wall dorsiflexion, calf stretches, joint mobilization, banded ankle exercises in 4 directions, double and "
         "single-leg heel raises, toe raises, tandem stance and walking, single-leg stance, wobble board",
         0, False, None,
         [("hipAbd", 25, 5, 40, 0, 2, 8, 30), ("hipExt", 20, 5, 30, 0, 2, 8, 30), ("kneeExt", 85, 10, 0, 0, 2, 8, 30),
          ("hamstringCurl", 90, 10, 110, 0, 2, 8, 30), ("miniSquat", 45, 10, 60, 0, 2, 8, 30)]),
        ("Phase III - Late", "Weeks 7-10", True,
         "Optimize strength and balance; begin plyometrics and return to running",
         "Lace-up brace for functional activity as needed. Progress with 25 single-leg heel raises (or equal to the other side) "
         "and Y-balance at least 80% of the other side",
         "Full ankle ROM",
         "Single-leg reach on firm and unstable surfaces, ball toss balance, double-leg hopping, lateral bounding, agility ladder",
         0, False, None,
         [("miniLunge", 60, 10, 80, 0, 2, 8, 30), ("wallSquatHold", 60, 10, 85, 5, 2, 8, 30), ("sitToStand", 85, 10, 0, 0, 2, 8, 45),
          ("kneeWallSlide", 90, 10, 100, 0, 2, 8, 30), ("hipAbd", 30, 5, 45, 0, 2, 8, 30)]),
        ("Phase IV - Return to sport", "Weeks 11-16", False,
         "Full foot and ankle strength; motor control in higher-level activity; return to normal activities",
         "Y-balance and hop tests at least 90% of the other side; no pain or swelling with plyometrics",
         "Full ROM and strength", "Single-leg agility and hopping, change of direction drills, interval sport training, running",
         0, False, None, []),
    ]),
]

# Columns added after the first version; added to existing databases on startup.
MIGRATIONS = {
    "patient": [("phase_id", "INTEGER"), ("phase_started_at", "TEXT"),
                ("archived_at", "TEXT")],                                   # NULL = active (DEC-014)
    "session": [("pain_before", "INTEGER"), ("pain_after", "INTEGER"),
                ("soreness_over_2h", "INTEGER"), ("swelling_cm", "REAL"),
                ("session_uuid", "TEXT")],                                  # idempotency key from Unity
    "protocol_phase": [("rom_goal", "TEXT"), ("other_exercises", "TEXT"),
                       ("check_soreness", "INTEGER NOT NULL DEFAULT 0"), ("max_swelling_cm", "REAL")],
    "exercise": [("measure", "TEXT"), ("view", "TEXT"), ("position", "TEXT"),
                 ("side", "TEXT NOT NULL DEFAULT ''"), ("safety_max", "REAL NOT NULL DEFAULT 0"),
                 ("hold_seconds", "REAL NOT NULL DEFAULT 0"), ("sets", "INTEGER NOT NULL DEFAULT 1"),
                 ("rest_seconds", "REAL NOT NULL DEFAULT 30"), ("active", "INTEGER NOT NULL DEFAULT 1")],
    "performance_record": [("unsafe_reps", "INTEGER NOT NULL DEFAULT 0"),
                           ("prescribed", "INTEGER NOT NULL DEFAULT 1")],   # 0 = exercise was no longer active
    "protocol": [("builtin", "INTEGER NOT NULL DEFAULT 0")],                # 1 = loaded from PROTOCOLS
    "physical_therapist": [
        ("username", "TEXT"),
        ("password_hash", "TEXT"),
        ("salt", "TEXT"),
        ("role", "TEXT DEFAULT 'Licensed Physical Therapist'"),
    ],
}


def hash_password(password, salt=None):
    if not salt:
        salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000)
    return key.hex(), salt


def verify_password(password, password_hash, salt):
    key, _ = hash_password(password, salt)
    return secrets.compare_digest(key, password_hash)


MIN_PASSWORD_LENGTH = 8
# Passwords that must be changed at the next sign-in (the old seeded development login)
WEAK_PASSWORDS = {"password123"}
LOGIN_MAX_FAILURES, LOGIN_WINDOW_SECONDS = 5, 300

_login_failures = defaultdict(list)     # username (lower case) -> monotonic times of recent failed logins
_login_lock = threading.Lock()


def _token_digest(token):
    """Session tokens are stored hashed, so a copy of the database can't be used to sign in."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_session(con, therapist_id, duration_hours=24):
    now = datetime.now(timezone.utc)
    con.execute("DELETE FROM therapist_session WHERE expires_at <= ?", (now.isoformat(),))
    token = secrets.token_hex(32)
    expires_at = (now + timedelta(hours=duration_hours)).isoformat()
    con.execute("INSERT INTO therapist_session(token, therapist_id, expires_at) VALUES (?,?,?)",
                (_token_digest(token), therapist_id, expires_at))
    con.commit()
    return token, expires_at


def get_session_therapist(con, token):
    if not token:
        return None
    now = datetime.now(timezone.utc).isoformat()
    row = con.execute("""
        SELECT t.therapist_id, t.name, t.license_no, t.email, t.username, t.role
        FROM therapist_session s
        JOIN physical_therapist t ON t.therapist_id = s.therapist_id
        WHERE s.token = ? AND s.expires_at > ?
    """, (_token_digest(token), now)).fetchone()
    return dict(row) if row else None


def delete_session(con, token):
    if token:
        con.execute("DELETE FROM therapist_session WHERE token = ?", (_token_digest(token),))
        con.commit()


def _therapist_json(row):
    return {"id": row["therapist_id"], "username": row["username"], "name": row["name"],
            "license_no": row["license_no"], "role": row["role"] or "Licensed Physical Therapist",
            "email": row["email"]}


def _login_blocked(username):
    now = time.monotonic()
    with _login_lock:
        recent = [t for t in _login_failures[username] if now - t < LOGIN_WINDOW_SECONDS]
        _login_failures[username] = recent
        return len(recent) >= LOGIN_MAX_FAILURES


def _record_login_failure(username):
    with _login_lock:
        _login_failures[username].append(time.monotonic())


def _check_new_password(password):
    if not isinstance(password, str) or len(password) < MIN_PASSWORD_LENGTH:
        raise BadRequest(f"Password must be at least {MIN_PASSWORD_LENGTH} characters")
    if password in WEAK_PASSWORDS:
        raise BadRequest("Choose a password other than the old demo password")


def auth_login(con, body):
    username = (body.get("username") or "").strip()
    password = body.get("password") or ""
    if not username or not password:
        return {"error": "Clinician username and password are required"}, 400
    key = username.lower()
    if _login_blocked(key):
        return {"error": f"Too many failed sign-ins. Try again in {LOGIN_WINDOW_SECONDS // 60} minutes."}, 429
    row = con.execute("SELECT * FROM physical_therapist WHERE username = ? COLLATE NOCASE", (username,)).fetchone()
    if not row or not row["password_hash"] or not row["salt"] \
            or not verify_password(password, row["password_hash"], row["salt"]):
        _record_login_failure(key)
        return {"error": "Invalid clinician username or password"}, 401
    with _login_lock:
        _login_failures.pop(key, None)
    token, expires_at = create_session(con, row["therapist_id"])
    return {"token": token, "expiresAt": expires_at, "therapist": _therapist_json(row),
            "mustChangePassword": password in WEAK_PASSWORDS}, 200


def needs_setup(con):
    """True until some clinician has a password: the first run asks for one instead of seeding a default."""
    return not con.execute("SELECT 1 FROM physical_therapist WHERE password_hash IS NOT NULL LIMIT 1").fetchone()


def auth_setup(con, body):
    """First-run setup: create the first clinician login. Refused once any clinician has a password."""
    if not needs_setup(con):
        raise Conflict("Setup is already done. Sign in instead.")
    username = (body.get("username") or "").strip()
    if not username:
        raise BadRequest("Choose a username")
    password = body.get("password") or ""
    _check_new_password(password)
    name = (body.get("name") or "").strip() or "Physical Therapist"
    h, s = hash_password(password)
    row = con.execute("SELECT therapist_id FROM physical_therapist ORDER BY therapist_id LIMIT 1").fetchone()
    if row:
        con.execute("UPDATE physical_therapist SET username=?, password_hash=?, salt=?, name=? WHERE therapist_id=?",
                    (username, h, s, name, row["therapist_id"]))
        tid = row["therapist_id"]
    else:
        tid = con.execute("INSERT INTO physical_therapist(name, username, password_hash, salt) VALUES (?,?,?,?)",
                          (name, username, h, s)).lastrowid
    con.commit()
    token, expires_at = create_session(con, tid)
    row = con.execute("SELECT * FROM physical_therapist WHERE therapist_id=?", (tid,)).fetchone()
    return {"token": token, "expiresAt": expires_at, "therapist": _therapist_json(row), "mustChangePassword": False}


def change_password(con, therapist_id, body):
    row = con.execute("SELECT * FROM physical_therapist WHERE therapist_id=?", (therapist_id,)).fetchone()
    if not verify_password(body.get("current_password") or "", row["password_hash"], row["salt"]):
        raise BadRequest("Current password is incorrect")
    new = body.get("new_password") or ""
    _check_new_password(new)
    h, s = hash_password(new)
    con.execute("UPDATE physical_therapist SET password_hash=?, salt=? WHERE therapist_id=?", (h, s, therapist_id))
    con.commit()
    return {"success": True}


# ----------------------------------------------------------------- database
def db():
    con = sqlite3.connect(DB_PATH, timeout=15.0)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON;")
    con.execute("PRAGMA journal_mode = WAL;")
    con.execute("PRAGMA synchronous = NORMAL;")
    con.execute("PRAGMA temp_store = MEMORY;")
    con.execute("PRAGMA cache_size = -32000;")
    return con


def init_db():
    os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)
    con = db()
    with open(os.path.join(HERE, "schema.sql"), encoding="utf-8") as f:
        con.executescript(f.read())
    con.execute("""
        CREATE TABLE IF NOT EXISTS therapist_session (
            token TEXT PRIMARY KEY,
            therapist_id INTEGER NOT NULL REFERENCES physical_therapist(therapist_id),
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            expires_at TEXT NOT NULL
        )
    """)
    con.execute("CREATE INDEX IF NOT EXISTS idx_therapist_session_token ON therapist_session(token, expires_at);")
    migrate(con)
    for stmt in POST_MIGRATION_INDEXES:
        con.execute(stmt)
    if con.execute("SELECT COUNT(*) FROM physical_therapist").fetchone()[0] == 0:
        seed(con)
    # No default password: the first clinician login is created through /api/auth/setup.
    version = con.execute("SELECT value FROM app_meta WHERE key='protocol_version'").fetchone()
    if not version or version[0] != PROTOCOL_VERSION:
        replace_protocols(con)
    con.commit()
    con.close()


# Indexes on columns that MIGRATIONS may add; created only after migrate() so old databases can start.
POST_MIGRATION_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_exercise_program_active ON exercise(program_id, active)",
    "CREATE INDEX IF NOT EXISTS idx_patient_phase ON patient(phase_id)",
    "CREATE UNIQUE INDEX IF NOT EXISTS idx_session_uuid ON session(session_uuid)",
    "CREATE UNIQUE INDEX IF NOT EXISTS idx_therapist_username ON physical_therapist(username COLLATE NOCASE)",
]


def _builtin_matches(con, protocol_id, entry):
    """True when a built-in protocol in the database still has exactly the content of its PROTOCOLS entry."""
    name, condition, source, phases = entry
    pr = con.execute("SELECT * FROM protocol WHERE protocol_id=?", (protocol_id,)).fetchone()
    if (pr["condition"], pr["source"]) != (condition, source):
        return False
    rows = con.execute("SELECT * FROM protocol_phase WHERE protocol_id=? ORDER BY phase_no", (protocol_id,)).fetchall()
    if len(rows) != len(phases):
        return False
    for ph, (pname, weeks, vr, goals, precautions, rom_goal, other, pain, soreness, swelling, exs) in zip(rows, phases):
        if (ph["name"], ph["weeks"], bool(ph["vr_allowed"]), ph["goals"], ph["precautions"], ph["rom_goal"],
                ph["other_exercises"], ph["max_pain_increase"], bool(ph["check_soreness"]), ph["max_swelling_cm"]) != \
                (pname, weeks, bool(vr), goals, precautions, rom_goal, other, pain, bool(soreness), swelling):
            return False
        have = [(e["code"], e["target_angle"], e["tolerance"], e["safety_max"], e["hold_seconds"], e["sets"], e["reps"],
                 e["rest_seconds"]) for e in con.execute("SELECT * FROM phase_exercise WHERE phase_id=? ORDER BY sort_order",
                                                         (ph["phase_id"],))]
        if have != [tuple(x) for x in exs]:
            return False
    return True


def replace_protocols(con):
    """
    Brings the built-in protocols in line with PROTOCOLS. Protocols therapists authored are kept.
    A built-in protocol whose content is unchanged is kept as it is, so patients on it keep their phase.
    A changed or withdrawn one is removed: patients on its phases keep their exercises as a custom program,
    and their phase history stays, marked as the old version. New ones are added.
    """
    wanted = {entry[0]: entry for entry in PROTOCOLS}
    old, kept = [], set()
    for r in con.execute("SELECT protocol_id, name FROM protocol WHERE builtin=1 ORDER BY protocol_id").fetchall():
        entry = wanted.get(r[1])
        if entry and r[1] not in kept and _builtin_matches(con, r[0], entry):
            kept.add(r[1])
        else:
            old.append(r[0])
    if old:
        marks = ",".join("?" for _ in old)
        phases = [r[0] for r in con.execute(f"SELECT phase_id FROM protocol_phase WHERE protocol_id IN ({marks})", old)]
        if phases:
            pm = ",".join("?" for _ in phases)
            con.execute(f"UPDATE patient SET phase_id=NULL, phase_started_at=NULL WHERE phase_id IN ({pm})", phases)
            con.execute(f"""UPDATE phase_history SET note = TRIM(COALESCE(note,'') || ' (earlier protocol version)'),
                            phase_id=NULL WHERE phase_id IN ({pm})""", phases)
            con.execute(f"DELETE FROM phase_exercise WHERE phase_id IN ({pm})", phases)
            con.execute(f"DELETE FROM protocol_phase WHERE phase_id IN ({pm})", phases)
        con.execute(f"DELETE FROM protocol WHERE protocol_id IN ({marks})", old)
    seed_protocols(con, [e for e in PROTOCOLS if e[0] not in kept])
    con.execute("INSERT OR REPLACE INTO app_meta(key, value) VALUES ('protocol_version', ?)", (PROTOCOL_VERSION,))


def migrate(con):
    for table, cols in MIGRATIONS.items():
        have = {r[1] for r in con.execute(f"PRAGMA table_info({table})")}
        for name, decl in cols:
            if name not in have:
                con.execute(f"ALTER TABLE {table} ADD COLUMN {name} {decl}")
                if (table, name) == ("protocol", "builtin"):
                    # Databases from before the flag: protocols named like a shipped one are the built-in ones
                    names = [p[0] for p in PROTOCOLS]
                    con.execute(f"UPDATE protocol SET builtin=1 WHERE name IN ({','.join('?' for _ in names)})", names)
    # Exercises created before the library existed: fill in its details
    for code, lib in LIBRARY.items():
        con.execute("UPDATE exercise SET measure=?, view=?, position=?, safety_max=? WHERE code=? AND measure IS NULL",
                    (lib[2], lib[3], lib[4], lib[7], code))


def add_exercise(con, program_id, code, rx=None):
    """Add a library exercise to a program. `rx` overrides the library's prescription numbers."""
    if code not in LIBRARY:
        raise BadRequest(f"Unknown exercise '{code}'")
    name, joint, measure, view, position, tgt, tol, smax, hold, sets, reps, rest, cue, _ = LIBRARY[code]
    v = dict(target_angle=tgt, tolerance=tol, safety_max=smax, hold_seconds=hold, sets=sets, reps=reps, rest_seconds=rest)
    v.update({k: x for k, x in (rx or {}).items() if k in v and x is not None})
    v = clamp_rx_columns(v)
    order = con.execute("SELECT COALESCE(MAX(sort_order), -1) + 1 FROM exercise WHERE program_id=?", (program_id,)).fetchone()[0]
    con.execute("""INSERT INTO exercise(program_id, code, name, joint, measure, view, position, target_angle, tolerance,
                   safety_max, hold_seconds, sets, reps, rest_seconds, cue, sort_order)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (program_id, code, name, joint, measure, view, position, v["target_angle"], v["tolerance"],
                 v["safety_max"], v["hold_seconds"], v["sets"], v["reps"], v["rest_seconds"], cue, order))


def seed_protocols(con, entries=PROTOCOLS):
    for name, condition, source, phases in entries:
        prid = con.execute("INSERT INTO protocol(name, condition, source, builtin) VALUES (?,?,?,1)",
                           (name, condition, source)).lastrowid
        for no, (pname, weeks, vr, goals, precautions, rom_goal, other, pain, soreness, swelling, exs) in enumerate(phases, 1):
            phid = con.execute("""INSERT INTO protocol_phase(protocol_id, phase_no, name, weeks, vr_allowed, goals, precautions,
                                  rom_goal, other_exercises, max_pain_increase, check_soreness, max_swelling_cm)
                                  VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                               (prid, no, pname, weeks, int(vr), goals, precautions, rom_goal, other,
                                pain, int(soreness), swelling)).lastrowid
            for i, (code, tgt, tol, smax, hold, sets, reps, rest) in enumerate(exs):
                con.execute("""INSERT INTO phase_exercise(phase_id, code, target_angle, tolerance, safety_max,
                               hold_seconds, sets, reps, rest_seconds, sort_order) VALUES (?,?,?,?,?,?,?,?,?,?)""",
                            (phid, code, tgt, tol, smax, hold, sets, reps, rest, i))


def seed(con):
    """Starter data so the system works on first run. Replace with your real test setup."""
    tid = con.execute("INSERT INTO physical_therapist(name, license_no, email) VALUES (?,?,?)",
                      ("Test Therapist", "PT-0000", "therapist@example.com")).lastrowid
    pid = con.execute("""INSERT INTO rehabilitation_program(therapist_id, name, description, schedule_days, max_reps)
                         VALUES (?,?,?,?,?)""",
                      (tid, "Post-op shoulder & knee", "Orthopedic ROM program", "1,3,5", 14)).lastrowid
    for code in ("shoulderAbd", "elbowFlex", "kneeExt"):
        add_exercise(con, pid, code)
    con.execute("INSERT INTO patient(therapist_id, program_id, code, name, condition) VALUES (?,?,?,?,?)",
                (tid, pid, "P-001", "Test Patient", "Post-op shoulder"))


# ------------------------------------------------------------ game helpers
def level_from_xp(xp):
    """Same curve as Unity's GamificationManager: 100 XP for level 2, +60 per level after."""
    lv, need, acc = 1, 100, 0
    while xp >= acc + need:
        acc += need
        lv += 1
        need = 100 + (lv - 1) * 60
    return {"level": lv, "xp_into_level": xp - acc, "xp_for_next": need}


def effective_reps(ex, max_reps):
    return min(max_reps, ex["reps"] + 2 * (ex["stage"] - 1))


def schedule(program_row):
    return [int(d) for d in program_row["schedule_days"].split(",") if d.strip() != ""]


def py_dow(d):
    """Python weekday (Mon=0) -> our convention (Sun=0)."""
    return (d.weekday() + 1) % 7


# ----------------------------------------------------- adherence analytics
def day_statuses(con, patient_id, program, days=14, today=None, created_at=None):
    today = today or date.today()
    sched = schedule(program)
    start = today - timedelta(days=days - 1)
    rows = con.execute("""SELECT session_date, status FROM adherence_record
                          WHERE patient_id=? AND session_date>=?""", (patient_id, start.isoformat())).fetchall()
    if not created_at:
        row = con.execute("SELECT created_at FROM patient WHERE patient_id=?", (patient_id,)).fetchone()
        created = row[0][:10] if row else "1970-01-01"
    else:
        created = created_at[:10]
    by_day = {}
    for r in rows:
        prev = by_day.get(r["session_date"])
        if prev != "complete":
            by_day[r["session_date"]] = r["status"]
    out = []
    for i in range(days):
        d = start + timedelta(days=i)
        k = d.isoformat()
        scheduled = py_dow(d) in sched and k >= created   # no "missed" before the patient was enrolled
        if k in by_day:
            st = by_day[k]
        elif not scheduled:
            st = "rest"
        else:
            st = "pending" if d == today else "missed"
        out.append({"date": k, "dow": py_dow(d), "status": st, "scheduled": scheduled})
    return out


def streak(con, patient_id, program, created_at=None):
    n = 0
    for d in reversed(day_statuses(con, patient_id, program, days=60, created_at=created_at)):
        if d["status"] in ("pending", "rest"):
            continue
        if d["status"] == "complete":
            n += 1
        else:
            break
    return n



def adherence_rate(statuses):
    sched = [d for d in statuses if d["scheduled"] and d["status"] != "pending"]
    done = sum(1 for d in sched if d["status"] == "complete")
    return {"rate": round(100 * done / len(sched)) if sched else 0, "done": done, "scheduled": len(sched)}


# ------------------------------------------------------- protocol phases
def phase_info(con, p):
    """The patient's current protocol phase (empty fields = custom program without a protocol)."""
    ph = p["phase_id"] and con.execute("""SELECT ph.*, pr.name AS protocol FROM protocol_phase ph
                                          JOIN protocol pr ON pr.protocol_id = ph.protocol_id
                                          WHERE ph.phase_id=?""", (p["phase_id"],)).fetchone()
    if not ph:
        return {"id": 0, "protocolId": 0, "protocol": "", "name": "", "phaseNo": 0, "weeks": "", "vrAllowed": True,
                "goals": "", "precautions": "", "romGoal": "", "other": "", "startedAt": ""}
    return {"id": ph["phase_id"], "protocolId": ph["protocol_id"], "protocol": ph["protocol"], "name": ph["name"],
            "phaseNo": ph["phase_no"], "weeks": ph["weeks"], "vrAllowed": bool(ph["vr_allowed"]),
            "goals": ph["goals"], "precautions": ph["precautions"], "romGoal": ph["rom_goal"] or "",
            "other": ph["other_exercises"] or "", "startedAt": p["phase_started_at"] or ""}


def set_phase(con, patient_id, body):
    """
    Therapist assigns a protocol phase (or phase_id null = keep the exercises as a custom program).
    The phase's exercises replace the patient's program; the therapist can still adjust any value.
    """
    p = con.execute("SELECT * FROM patient WHERE patient_id=?", (patient_id,)).fetchone()
    if not p:
        raise NotFound("Unknown patient")
    phase_id = body.get("phase_id")
    now = datetime.now().isoformat(timespec="seconds")
    if phase_id:
        phase_id = int(phase_id)
        if not con.execute("SELECT 1 FROM protocol_phase WHERE phase_id=?", (phase_id,)).fetchone():
            raise BadRequest("Unknown phase")
        con.execute("UPDATE exercise SET active=0 WHERE program_id=? AND active=1", (p["program_id"],))
        for r in con.execute("SELECT * FROM phase_exercise WHERE phase_id=? ORDER BY sort_order", (phase_id,)).fetchall():
            add_exercise(con, p["program_id"], r["code"], dict(r))
    con.execute("UPDATE patient SET phase_id=?, phase_started_at=? WHERE patient_id=?",
                (phase_id or None, now if phase_id else None, patient_id))
    con.execute("INSERT INTO phase_history(patient_id, phase_id, changed_at, note) VALUES (?,?,?,?)",
                (patient_id, phase_id or None, now, body.get("note", "")))
    con.commit()
    return get_program(con, patient_id)


def readiness(con, p):
    """
    Progression suggestion for the current phase. The system only suggests; the therapist approves.
    Criteria, checked on the most recent `min_sessions` complete sessions in this phase:
      - enough complete sessions (every exercise reached all its sets and reps)
      - ROM goal: every exercise at or above `min_accuracy`
      - pain after minus pain before at most `max_pain_increase` (recorded by the therapist)
      - when the phase uses them: soreness gone within 2 hours, swelling increase under `max_swelling_cm`
      - no reps past the safety limit
    """
    if not p["phase_id"]:
        return None
    ph = con.execute("SELECT * FROM protocol_phase WHERE phase_id=?", (p["phase_id"],)).fetchone()
    nxt = con.execute("SELECT * FROM protocol_phase WHERE protocol_id=? AND phase_no>? ORDER BY phase_no LIMIT 1",
                      (ph["protocol_id"], ph["phase_no"])).fetchone()
    out = {"next": {"id": nxt["phase_id"], "name": nxt["name"], "weeks": nxt["weeks"]} if nxt else None,
           "ready": False, "criteria": [], "note": ""}
    if not ph["vr_allowed"]:
        out["note"] = "This phase is done with the therapist, so TheraQuest has no session data to judge it."
        return out

    n, acc, pain = ph["min_sessions"], ph["min_accuracy"], ph["max_pain_increase"]
    rows = con.execute("""
        SELECT s.started_at, s.pain_before, s.pain_after, s.soreness_over_2h, s.swelling_cm, MIN(r.avg_accuracy) AS min_acc,
               COALESCE(SUM(r.unsafe_reps),0) AS unsafe
        FROM session s LEFT JOIN performance_record r ON r.session_id = s.session_id
        WHERE s.patient_id=? AND s.status='complete' AND s.started_at>=?
        GROUP BY s.session_id ORDER BY s.started_at DESC LIMIT ?""", (p["patient_id"], p["phase_started_at"], n)).fetchall()
    enough = len(rows) >= n

    def pain_ok(r):
        return r["pain_before"] is not None and r["pain_after"] is not None and r["pain_after"] - r["pain_before"] <= pain

    def crit(label, ok, detail):
        out["criteria"].append({"label": label, "met": bool(enough and ok), "detail": detail if rows else "no complete sessions yet"})

    out["criteria"].append({"label": f"{n} complete sessions in this phase (all sets and reps done)", "met": enough,
                            "detail": f"{len(rows)} of {n}"})
    goal = f" ({ph['rom_goal']})" if ph["rom_goal"] else ""
    crit(f"ROM goal{goal}: every exercise at {acc:.0f}% accuracy or more", all((r["min_acc"] or 0) >= acc for r in rows),
         ", ".join(f"{r['min_acc'] or 0:.0f}%" for r in rows))
    crit("No increase in pain" if pain == 0 else f"Pain went up by {pain} points or less", all(pain_ok(r) for r in rows),
         ", ".join("not recorded yet" if r["pain_before"] is None or r["pain_after"] is None
                   else f"{r['pain_before']}→{r['pain_after']}" for r in rows))
    if ph["check_soreness"]:
        crit("Soreness gone within 2 hours", all(r["soreness_over_2h"] == 0 for r in rows),
             ", ".join({None: "not recorded yet", 0: "under 2 h", 1: "over 2 h"}[r["soreness_over_2h"]] for r in rows))
    if ph["max_swelling_cm"] is not None:
        lim = ph["max_swelling_cm"]
        crit(f"Swelling up by less than {lim:g} cm", all(r["swelling_cm"] is not None and r["swelling_cm"] < lim for r in rows),
             ", ".join("not recorded yet" if r["swelling_cm"] is None else f"{r['swelling_cm']:g} cm" for r in rows))
    crit("No reps past the safety limit", all(r["unsafe"] == 0 for r in rows),
         ", ".join(str(r["unsafe"]) for r in rows) + " unsafe reps")
    out["ready"] = nxt is not None and all(c["met"] for c in out["criteria"])
    return out


def _phase_exercise_json(e):
    code = e["code"]
    return {
        "code": code,
        "name": LIBRARY[code][0] if code in LIBRARY else code,
        "targetAngle": e["target_angle"],
        "tolerance": e["tolerance"],
        "safetyMax": e["safety_max"],
        "holdSeconds": e["hold_seconds"],
        "sets": e["sets"],
        "reps": e["reps"],
        "restSeconds": e["rest_seconds"]
    }


def _phase_json(ph, ex_list):
    return {
        "id": ph["phase_id"], "phaseNo": ph["phase_no"], "name": ph["name"], "weeks": ph["weeks"],
        "vrAllowed": bool(ph["vr_allowed"]), "goals": ph["goals"], "precautions": ph["precautions"],
        "romGoal": ph["rom_goal"] or "", "other": ph["other_exercises"] or "",
        "minSessions": ph["min_sessions"], "minAccuracy": ph["min_accuracy"],
        "maxPainIncrease": ph["max_pain_increase"], "checkSoreness": bool(ph["check_soreness"]),
        "maxSwellingCm": ph["max_swelling_cm"],
        "exercises": [e["name"] for e in ex_list if e["code"] in LIBRARY], "exerciseDetails": ex_list
    }


def _protocols_json(con, protocols):
    ids = [pr["protocol_id"] for pr in protocols]
    if not ids:
        return []
    marks = ",".join("?" for _ in ids)
    phases = con.execute(f"SELECT * FROM protocol_phase WHERE protocol_id IN ({marks}) ORDER BY protocol_id, phase_no", ids).fetchall()
    ex_by_phase = defaultdict(list)
    phase_ids = [ph["phase_id"] for ph in phases]
    if phase_ids:
        pm = ",".join("?" for _ in phase_ids)
        for e in con.execute(f"SELECT * FROM phase_exercise WHERE phase_id IN ({pm}) ORDER BY phase_id, sort_order", phase_ids):
            ex_by_phase[e["phase_id"]].append(_phase_exercise_json(e))
    phases_by_protocol = defaultdict(list)
    for ph in phases:
        phases_by_protocol[ph["protocol_id"]].append(_phase_json(ph, ex_by_phase.get(ph["phase_id"], [])))
    return [{
        "id": pr["protocol_id"], "name": pr["name"], "condition": pr["condition"], "source": pr["source"],
        "builtin": bool(pr["builtin"]),          # shipped protocols are read-only (DEC-014)
        "phases": phases_by_protocol.get(pr["protocol_id"], [])
    } for pr in protocols]


def list_protocols(con):
    return _protocols_json(con, con.execute("SELECT * FROM protocol ORDER BY protocol_id").fetchall())


def get_protocol(con, protocol_id):
    pr = con.execute("SELECT * FROM protocol WHERE protocol_id=?", (protocol_id,)).fetchall()
    return _protocols_json(con, pr)[0] if pr else None


# Bounds for phase progression criteria (same idea as the prescription bounds): json key -> column, type, min, max, default
PHASE_CRITERIA = {
    "minSessions": ("min_sessions", int, 1, 50, 3),
    "minAccuracy": ("min_accuracy", float, 0, 100, 85.0),
    "maxPainIncrease": ("max_pain_increase", int, 0, 10, 2),
}
TEXT_MAX = 500


def _text(d, key, default="", max_len=TEXT_MAX):
    v = d.get(key)
    v = default if v is None else str(v).strip()
    if len(v) > max_len:
        raise BadRequest(f"{key} is too long (at most {max_len} characters)")
    return v


def _phase_values(ph, idx, current=None):
    """Column values for a protocol phase from the dashboard's JSON. `current` (a row) fills fields left out."""
    cur = dict(current) if current else {}

    def text(key, col):
        return _text(ph, key, cur.get(col) or "")

    v = {
        "name": text("name", "name") or f"Phase {idx}",
        "weeks": text("weeks", "weeks"),
        "vr_allowed": (1 if ph["vrAllowed"] else 0) if "vrAllowed" in ph else cur.get("vr_allowed", 1),
        "goals": text("goals", "goals"),
        "precautions": text("precautions", "precautions"),
        "rom_goal": text("romGoal", "rom_goal"),
        "other_exercises": _text(ph, "other", _text(ph, "otherExercises", cur.get("other_exercises") or "")),
        "check_soreness": (1 if ph["checkSoreness"] else 0) if "checkSoreness" in ph else cur.get("check_soreness", 0),
    }
    for key, (col, cast, lo, hi, default) in PHASE_CRITERIA.items():
        raw = ph.get(key)
        v[col] = max(lo, min(hi, cast(raw))) if raw not in (None, "") else cur.get(col, default)
    if "maxSwellingCm" in ph:
        raw = ph.get("maxSwellingCm")
        v["max_swelling_cm"] = None if raw in (None, "") else max(0.0, min(20.0, float(raw)))
    else:
        v["max_swelling_cm"] = cur.get("max_swelling_cm")
    return v


def _write_phase_exercises(con, phase_id, ex_list):
    """Replace a phase's exercises. Unknown codes are skipped; values get the prescription bounds."""
    con.execute("DELETE FROM phase_exercise WHERE phase_id=?", (phase_id,))
    for s_idx, ex in enumerate(ex_list or []):
        if isinstance(ex, str):
            code, rx = ex, {}
        elif isinstance(ex, dict):
            code, rx = ex.get("code"), ex
        else:
            continue
        if not code or code not in LIBRARY:
            continue
        lib_def = LIBRARY[code]
        v = clamp_rx_columns({
            "target_angle": rx.get("target_angle", rx.get("targetAngle", lib_def[5])),
            "tolerance": rx.get("tolerance", lib_def[6]),
            "safety_max": rx.get("safety_max", rx.get("safetyMax", lib_def[7])),
            "hold_seconds": rx.get("hold_seconds", rx.get("holdSeconds", lib_def[8])),
            "sets": rx.get("sets", lib_def[9]),
            "reps": rx.get("reps", lib_def[10]),
            "rest_seconds": rx.get("rest_seconds", rx.get("restSeconds", lib_def[11])),
        })
        con.execute("""INSERT INTO phase_exercise(phase_id, code, target_angle, tolerance, safety_max,
                                             hold_seconds, sets, reps, rest_seconds, sort_order)
                       VALUES (?,?,?,?,?,?,?,?,?,?)""",
                    (phase_id, code, v["target_angle"], v["tolerance"], v["safety_max"], v["hold_seconds"],
                     v["sets"], v["reps"], v["rest_seconds"], s_idx))


def _insert_phase(con, protocol_id, phase_no, v):
    return con.execute("""INSERT INTO protocol_phase(protocol_id, phase_no, name, weeks, vr_allowed, goals, precautions,
                                                     rom_goal, other_exercises, min_sessions, min_accuracy,
                                                     max_pain_increase, check_soreness, max_swelling_cm)
                          VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                       (protocol_id, phase_no, v["name"], v["weeks"], v["vr_allowed"], v["goals"], v["precautions"],
                        v["rom_goal"], v["other_exercises"], v["min_sessions"], v["min_accuracy"],
                        v["max_pain_increase"], v["check_soreness"], v["max_swelling_cm"])).lastrowid


def _authored_protocol(con, protocol_id):
    """A protocol the therapist may change. Built-in ones are reloaded from PROTOCOLS on upgrade, so they stay read-only."""
    pr = con.execute("SELECT * FROM protocol WHERE protocol_id=?", (protocol_id,)).fetchone()
    if not pr:
        raise NotFound(f"Protocol with id {protocol_id} not found")
    if pr["builtin"]:
        raise Forbidden("Built-in protocols are read-only. Create your own protocol to change phases.")
    return pr


def add_phase(con, protocol_id, body):
    """Append a phase to a therapist-authored protocol."""
    _authored_protocol(con, protocol_id)
    if not _text(body, "name"):
        raise BadRequest("Phase name is required")
    nxt = con.execute("SELECT COALESCE(MAX(phase_no), 0) + 1 FROM protocol_phase WHERE protocol_id=?", (protocol_id,)).fetchone()[0]
    phase_id = _insert_phase(con, protocol_id, nxt, _phase_values(body, nxt))
    _write_phase_exercises(con, phase_id, body.get("exercises"))
    con.commit()
    return get_protocol(con, protocol_id)


def update_phase(con, protocol_id, phase_id, body):
    """
    Edit a phase of a therapist-authored protocol. Fields left out keep their value; "exercises", when sent,
    replaces the phase's exercise list. Patients already on the phase keep their current prescription
    (a phase's exercises are copied to the patient when it is assigned).
    """
    _authored_protocol(con, protocol_id)
    row = con.execute("SELECT * FROM protocol_phase WHERE phase_id=? AND protocol_id=?", (phase_id, protocol_id)).fetchone()
    if not row:
        raise NotFound("Unknown phase for this protocol")
    if "name" in body and not _text(body, "name"):
        raise BadRequest("Phase name is required")
    v = _phase_values(body, row["phase_no"], current=row)
    con.execute("""UPDATE protocol_phase SET name=?, weeks=?, vr_allowed=?, goals=?, precautions=?, rom_goal=?,
                   other_exercises=?, min_sessions=?, min_accuracy=?, max_pain_increase=?, check_soreness=?,
                   max_swelling_cm=? WHERE phase_id=?""",
                (v["name"], v["weeks"], v["vr_allowed"], v["goals"], v["precautions"], v["rom_goal"],
                 v["other_exercises"], v["min_sessions"], v["min_accuracy"], v["max_pain_increase"],
                 v["check_soreness"], v["max_swelling_cm"], phase_id))
    if "exercises" in body:
        _write_phase_exercises(con, phase_id, body.get("exercises"))
    con.commit()
    return get_protocol(con, protocol_id)


def add_protocol(con, body):
    name = _text(body, "name", max_len=200)
    condition = _text(body, "condition", max_len=200)
    source = _text(body, "source")
    if not name:
        raise BadRequest("Protocol name is required")

    cur = con.execute("INSERT INTO protocol (name, condition, source) VALUES (?,?,?)",
                      (name, condition or "General Physical Therapy", source or "Clinical Protocol"))
    protocol_id = cur.lastrowid

    phases = body.get("phases") or []
    if not phases:
        phases = [{
            "name": "Phase I - Initial Rehabilitation",
            "phaseNo": 1,
            "weeks": "Weeks 1-4",
            "vrAllowed": True,
            "goals": "Early mobility and range of motion",
            "precautions": "Avoid symptom exacerbation",
            "romGoal": "Achieve functional baseline",
            "other": "",
            "minSessions": 3,
            "minAccuracy": 85,
            "maxPainIncrease": 2,
            "exercises": []
        }]

    for idx, ph in enumerate(phases, start=1):
        pno = int(ph.get("phaseNo") or idx)
        phase_id = _insert_phase(con, protocol_id, pno, _phase_values(ph, idx))
        _write_phase_exercises(con, phase_id, ph.get("exercises"))

    con.commit()
    prot = get_protocol(con, protocol_id)
    return prot if prot else {"id": protocol_id, "name": name, "condition": condition}


def delete_protocol(con, protocol_id):
    prot = con.execute("SELECT * FROM protocol WHERE protocol_id=?", (protocol_id,)).fetchone()
    if not prot:
        raise NotFound(f"Protocol with id {protocol_id} not found")

    phase_rows = con.execute("SELECT phase_id FROM protocol_phase WHERE protocol_id=?", (protocol_id,)).fetchall()
    phase_ids = [r["phase_id"] for r in phase_rows]

    if phase_ids:
        placeholders = ",".join("?" for _ in phase_ids)
        con.execute(f"UPDATE patient SET phase_id=NULL, phase_started_at=NULL WHERE phase_id IN ({placeholders})", phase_ids)
        note_suffix = f' (Protocol "{prot["name"]}" deleted)'
        con.execute(f"UPDATE phase_history SET phase_id=NULL, note=TRIM(COALESCE(note,'') || ?) WHERE phase_id IN ({placeholders})", [note_suffix] + phase_ids)
        con.execute(f"DELETE FROM phase_exercise WHERE phase_id IN ({placeholders})", phase_ids)
        con.execute("DELETE FROM protocol_phase WHERE protocol_id=?", (protocol_id,))

    con.execute("DELETE FROM protocol WHERE protocol_id=?", (protocol_id,))
    con.commit()
    return {"success": True, "protocol_id": protocol_id, "name": prot["name"]}


def remove_patient_protocol(con, patient_id, note="Protocol removed by clinician"):
    p = con.execute("SELECT * FROM patient WHERE patient_id=?", (patient_id,)).fetchone()
    if not p:
        raise NotFound("Unknown patient")
    now = datetime.now().isoformat(timespec="seconds")
    con.execute("UPDATE patient SET phase_id=NULL, phase_started_at=NULL WHERE patient_id=?", (patient_id,))
    con.execute("INSERT INTO phase_history(patient_id, phase_id, changed_at, note) VALUES (?,NULL,?,?)",
                (patient_id, now, note))
    con.commit()
    return get_program(con, patient_id)



def add_patient(con, body, therapist_id):
    code = (body.get("code") or "").strip().upper()
    name = (body.get("name") or "").strip()
    condition = (body.get("condition") or "").strip()
    if not code:
        raise BadRequest("Patient code is required (e.g. P-002)")
    existing = con.execute("SELECT patient_id FROM patient WHERE code=?", (code,)).fetchone()
    if existing:
        raise Conflict(f"Patient with code {code} already exists")

    prog_id = con.execute("INSERT INTO rehabilitation_program (therapist_id, name, schedule_days, max_reps) VALUES (?, ?, '1,3,5', 14)",
                          (therapist_id, f"Rehabilitation Program for {code}")).lastrowid
    pid = con.execute("INSERT INTO patient (therapist_id, program_id, code, name, condition) VALUES (?, ?, ?, ?, ?)",
                      (therapist_id, prog_id, code, name or f"Patient {code}", condition or "Orthopedic Physical Therapy")).lastrowid
    
    add_exercise(con, prog_id, "shoulderAbd")
    con.commit()
    return {"id": pid, "code": code, "name": name, "condition": condition}


def update_patient(con, patient_id, body):
    """Edit a patient's name or condition. The code can't change: the VR app on the patient's PC is set up with it."""
    p = con.execute("SELECT * FROM patient WHERE patient_id=?", (patient_id,)).fetchone()
    if not p:
        raise NotFound("Unknown patient")
    if "code" in body and str(body["code"]).strip().upper() != p["code"]:
        raise BadRequest("The patient code can't be changed; the VR app is set up with it")
    name = _text(body, "name", p["name"] or "", max_len=200) or f"Patient {p['code']}"
    condition = _text(body, "condition", p["condition"] or "", max_len=200) or "Orthopedic Physical Therapy"
    con.execute("UPDATE patient SET name=?, condition=? WHERE patient_id=?", (name, condition, patient_id))
    con.commit()
    return {"id": patient_id, "code": p["code"], "name": name, "condition": condition}


def set_patient_archived(con, patient_id, body):
    """
    DEC-014: archive instead of delete. An archived patient keeps every record, is hidden from the caseload
    by default, and the VR app can't start new sessions for them (uploads of sessions already recorded still work).
    """
    p = con.execute("SELECT * FROM patient WHERE patient_id=?", (patient_id,)).fetchone()
    if not p:
        raise NotFound("Unknown patient")
    if not isinstance(body.get("archived"), bool):
        raise BadRequest("archived must be true or false")
    archived_at = None
    if body["archived"]:
        archived_at = p["archived_at"] or datetime.now().isoformat(timespec="seconds")   # archiving twice keeps the first date
    con.execute("UPDATE patient SET archived_at=? WHERE patient_id=?", (archived_at, patient_id))
    con.commit()
    return {"id": patient_id, "code": p["code"], "archivedAt": archived_at}


# ------------------------------------------------------------- API logic
def get_program(con, patient_id, patient=None, program=None):
    p = patient or con.execute("SELECT * FROM patient WHERE patient_id=?", (patient_id,)).fetchone()
    if not p:
        return None
    prog = program or con.execute("SELECT * FROM rehabilitation_program WHERE program_id=?", (p["program_id"],)).fetchone()
    exs = con.execute("SELECT * FROM exercise WHERE program_id=? AND active=1 ORDER BY sort_order", (prog["program_id"],)).fetchall()
    badges = [r["badge_code"] for r in con.execute("SELECT badge_code FROM patient_badge WHERE patient_id=?", (patient_id,))]
    lvl = level_from_xp(p["xp"])
    return {
        "patient": {"id": p["patient_id"], "code": p["code"], "name": p["name"], "condition": p["condition"], "xp": p["xp"],
                    "level": lvl["level"], "xpIntoLevel": lvl["xp_into_level"], "xpForNext": lvl["xp_for_next"],
                    "badges": badges, "streak": streak(con, patient_id, prog, created_at=p["created_at"])},
        "program": {"id": prog["program_id"], "name": prog["name"], "days": schedule(prog), "maxReps": prog["max_reps"]},
        "phase": phase_info(con, p),
        "exercises": [{
            "id": e["exercise_id"], "code": e["code"], "name": e["name"], "joint": e["joint"],
            "measure": e["measure"], "view": e["view"], "position": e["position"], "side": e["side"],
            "targetAngle": e["target_angle"], "tolerance": e["tolerance"], "safetyMax": e["safety_max"],
            "holdSeconds": e["hold_seconds"], "sets": e["sets"], "restSeconds": e["rest_seconds"],
            "baseReps": e["reps"], "reps": effective_reps(e, prog["max_reps"]), "stage": e["stage"], "cue": e["cue"],
            "normalRom": NORMAL_ROM.get(e["code"], ("", 0))[0], "normalMax": NORMAL_ROM.get(e["code"], ("", 0))[1],
            **exercise_rules(e["code"], e["measure"], e["view"]),
        } for e in exs],
    }


def exercise_rules(code, measure, view):
    """DEC-012 rules for the VR program. Codes no longer in LIBRARY get a generic pose from the measured angle."""
    if code in LIBRARY:
        r = LIBRARY[code][13]
        return {"posture": r["posture"], "pose": r["pose"], "direction": r["direction"] or "", "checks": r["checks"]}
    front = view == "front"
    pose = {"elbowFlex": "elbowFlex", "hipElev": "hipAbd" if front else "slr", "kneeFlex": "heelSlide",
            "kneeExt": "kneeExt"}.get(measure, "shoulderAbd" if front else "shoulderFlex")
    return {"posture": "seated" if pose == "kneeExt" else "lying" if pose in ("slr", "heelSlide") else "standing",
            "pose": pose, "direction": "", "checks": []}


def record_clinical(con, session_id, body):
    """Therapist records pain before/after (0-10), soreness over 2 hours (yes/no) and swelling (cm) for a session."""
    if not con.execute("SELECT 1 FROM session WHERE session_id=?", (session_id,)).fetchone():
        raise NotFound("Unknown session")

    def num(key, cast, lo, hi):
        v = body.get(key)
        return None if v is None or v == "" else max(lo, min(hi, cast(v)))

    con.execute("UPDATE session SET pain_before=?, pain_after=?, soreness_over_2h=?, swelling_cm=? WHERE session_id=?",
                (num("pain_before", int, 0, 10), num("pain_after", int, 0, 10), num("soreness_over_2h", int, 0, 1),
                 num("swelling_cm", float, 0, 20), session_id))
    con.commit()
    return {"ok": True}


INPUT_SOURCES = ("webcam", "keyboard", "simulated")
MAX_REP_EVENTS = 2000      # per session upload


def _iso_time(value, field):
    """Session times from Unity: ISO 8601 local time. Anything else is rejected (it is shown on the dashboard)."""
    if value in (None, ""):
        return datetime.now().isoformat(timespec="seconds")
    if not isinstance(value, str):
        raise BadRequest(f"{field} must be an ISO date-time")
    try:
        return datetime.fromisoformat(value).isoformat(timespec="seconds")
    except ValueError:
        raise BadRequest(f"{field} must be an ISO date-time")


def _int_field(r, key, lo=0, hi=100000, default=0):
    v = r.get(key, default)
    try:
        return max(lo, min(hi, int(v)))
    except (TypeError, ValueError):
        raise BadRequest(f"{key} must be a number")


def _float_field(r, key, lo=0.0, hi=1000.0, default=0.0):
    v = r.get(key, default)
    try:
        return max(lo, min(hi, float(v)))
    except (TypeError, ValueError):
        raise BadRequest(f"{key} must be a number")


def _rep_events(raw):
    """Per-rep log from Unity (M4.5). Optional, so uploads from older clients still work."""
    if raw is None:
        return []
    if not isinstance(raw, list) or not all(isinstance(r, dict) for r in raw):
        raise BadRequest("rep_events must be a list of objects")
    if len(raw) > MAX_REP_EVENTS:
        raise BadRequest(f"rep_events has more than {MAX_REP_EVENTS} entries")
    events = []
    for r in raw:
        try:
            eid = int(r["exercise_id"])
        except (KeyError, TypeError, ValueError):
            raise BadRequest("every rep event needs an exercise_id")
        side = str(r.get("side") or "").upper()[:1]
        events.append({
            "exercise_id": eid,
            "attempt": _int_field(r, "attempt", 1, 100000, 1),
            "set_no": _int_field(r, "set", 1, 1000, 1),
            "side": side if side in ("L", "R") else "",
            "t_seconds": _float_field(r, "t", 0, 86400),
            "peak_angle": _float_field(r, "peak", -360, 360),
            "angle_error": _float_field(r, "error", 0, 360),
            "accuracy": _float_field(r, "accuracy", 0, 100),
            "valid": 1 if r.get("valid") else 0,
            "fault": str(r.get("fault") or "")[:200] or None,
            "unsafe": 1 if r.get("past_safety_max") else 0,
            "too_fast": 1 if r.get("too_fast") else 0,
            "held": 0 if r.get("held") is False else 1,
        })
    return events


def save_session(con, body):
    """
    Adherence Monitoring Module: Completion Checker -> Status Classifier -> Adherence Record Writer.
    Also applies gamification results (XP, badges) and the Progression Controller.
    Completion is judged against the server's prescription, not the client's own targets.
    A repeated upload with the same session_uuid returns the stored session instead of saving it twice.
    """
    try:
        pid = int(body["patient_id"])
    except (KeyError, TypeError, ValueError):
        raise BadRequest("patient_id is required")
    p = con.execute("SELECT * FROM patient WHERE patient_id=?", (pid,)).fetchone()
    if not p:
        raise BadRequest("Unknown patient_id")

    session_uuid = body.get("session_uuid") or None
    if session_uuid is not None:
        session_uuid = str(session_uuid)[:64]
        prev = con.execute("SELECT session_id, patient_id, status FROM session WHERE session_uuid=?", (session_uuid,)).fetchone()
        if prev:
            if prev["patient_id"] != pid:
                raise Conflict("session_uuid already used by another patient")
            return {"session_id": prev["session_id"], "status": prev["status"], "notes": [], "new_badges": [],
                    "patient": get_program(con, pid)["patient"], "duplicate": True}

    prog = con.execute("SELECT * FROM rehabilitation_program WHERE program_id=?", (p["program_id"],)).fetchone()
    in_program = {e["exercise_id"]: e for e in con.execute("SELECT * FROM exercise WHERE program_id=?", (prog["program_id"],))}
    active = {eid: e for eid, e in in_program.items() if e["active"]}

    raw = body.get("exercises") or []
    if not isinstance(raw, list) or not all(isinstance(r, dict) for r in raw):
        raise BadRequest("exercises must be a list of objects")
    results, ignored = {}, 0
    for r in raw:
        try:
            eid = int(r["exercise_id"])
        except (KeyError, TypeError, ValueError):
            raise BadRequest("every exercise result needs an exercise_id")
        if eid not in in_program:
            ignored += 1           # not this patient's exercise (e.g. an old offline default program)
        elif eid not in results:   # a repeated id is counted once
            results[eid] = r

    def required_reps(e):
        return effective_reps(e, prog["max_reps"]) * max(1, e["sets"])

    # Completion Checker: every active prescribed exercise reached its prescribed valid reps
    ended_early = bool(body.get("ended_early"))
    complete = (not ended_early and bool(active)
                and all(eid in results and _int_field(results[eid], "valid_reps") >= required_reps(e)
                        for eid, e in active.items()))
    status = "complete" if complete else "incomplete"

    started = _iso_time(body.get("started_at"), "started_at")
    ended = _iso_time(body.get("ended_at"), "ended_at")
    source = body.get("input_source") or ""
    if source not in INPUT_SOURCES + ("",):
        raise BadRequest(f"input_source must be one of {', '.join(INPUT_SOURCES)}")
    source = source or "unknown"     # uploads from clients older than M4.3; never counted as webcam data
    rep_events = _rep_events(body.get("rep_events"))
    points = _int_field(body, "points", 0, 100000)
    stars = _int_field(body, "stars", 0, 3)

    def pain(key):   # 0-10, or None when the check-in was skipped (Unity sends -1)
        v = body.get(key)
        if v is None:
            return None
        v = _int_field(body, key, -1, 10)
        return v if v >= 0 else None

    sid = con.execute("""INSERT INTO session(patient_id, program_id, started_at, ended_at, input_source, points, stars, status,
                         pain_before, pain_after, session_uuid) VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                      (pid, prog["program_id"], started, ended, source, points, stars, status,
                       pain("pain_before"), pain("pain_after"), session_uuid)).lastrowid

    notes = []
    if ignored:
        notes.append(f"{ignored} result(s) ignored: not part of this patient's program")
    for eid, r in results.items():
        e = in_program[eid]
        prescribed = eid in active
        unsafe = _int_field(r, "unsafe_reps")
        accuracy = _float_field(r, "avg_accuracy", 0, 100)
        feedback = r.get("feedback") or []
        feedback = [str(f)[:200] for f in feedback][:50] if isinstance(feedback, list) else []
        con.execute("""INSERT INTO performance_record(session_id, exercise_id, target_reps, valid_reps, attempts,
                       avg_accuracy, mean_angle_error, unsafe_reps, feedback_log, prescribed) VALUES (?,?,?,?,?,?,?,?,?,?)""",
                    (sid, eid, required_reps(e) if prescribed else _int_field(r, "target_reps"),
                     _int_field(r, "valid_reps"), _int_field(r, "attempts"), accuracy,
                     _float_field(r, "mean_angle_error", 0, 360), unsafe, json.dumps(feedback), int(prescribed)))
        # Progression Controller: >=85% accuracy and no unsafe reps on a completed session
        # -> next stage (+2 reps per set, capped)
        if prescribed and complete and unsafe == 0 and accuracy >= 85:
            nxt = min(prog["max_reps"], e["reps"] + 2 * e["stage"])
            if nxt > effective_reps(e, prog["max_reps"]):
                con.execute("UPDATE exercise SET stage = stage + 1 WHERE exercise_id=?", (eid,))
                notes.append(f"{e['name']}: next session goes to {nxt} reps")

    skipped = 0
    for ev in rep_events:
        if ev["exercise_id"] not in in_program:
            skipped += 1
            continue
        con.execute("""INSERT INTO rep_event(session_id, exercise_id, attempt, set_no, side, t_seconds, peak_angle,
                       angle_error, accuracy, valid, fault, unsafe, too_fast, held) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (sid, ev["exercise_id"], ev["attempt"], ev["set_no"], ev["side"], ev["t_seconds"], ev["peak_angle"],
                     ev["angle_error"], ev["accuracy"], ev["valid"], ev["fault"], ev["unsafe"], ev["too_fast"], ev["held"]))
    if skipped:
        notes.append(f"{skipped} rep event(s) ignored: not part of this patient's program")

    session_day = started[:10]
    con.execute("""INSERT INTO adherence_record(patient_id, session_id, session_date, status, completion_flag)
                   VALUES (?,?,?,?,?)""", (pid, sid, session_day, status, 1 if complete else 0))

    # Gamification persistence (one atomic update, so two uploads at once can't lose XP)
    old_level = level_from_xp(p["xp"])["level"]
    con.execute("UPDATE patient SET xp = xp + ? WHERE patient_id=?", (points, pid))
    new_xp = con.execute("SELECT xp FROM patient WHERE patient_id=?", (pid,)).fetchone()[0]
    new_level = level_from_xp(new_xp)["level"]
    if new_level > old_level:
        notes.append(f"Level up! Reached level {new_level}")

    earned = [b for b in (body.get("badges_earned") or []) if isinstance(b, str)]
    if complete:
        earned.append("first")
    if streak(con, pid, prog) >= 3:
        earned.append("streak3")
    adh = adherence_rate(day_statuses(con, pid, prog))
    if adh["rate"] >= 80 and adh["scheduled"] >= 4:
        earned.append("adh80")
    if new_level >= 5:
        earned.append("lv5")
    new_badges = []
    for b in earned:
        if b in BADGES:
            cur = con.execute("INSERT OR IGNORE INTO patient_badge(patient_id, badge_code) VALUES (?,?)", (pid, b))
            if cur.rowcount:
                new_badges.append(b)
                notes.append(f"Badge unlocked: {BADGES[b]}")
    con.commit()
    return {"session_id": sid, "status": status, "notes": notes, "new_badges": new_badges,
            "patient": get_program(con, pid)["patient"]}


def update_program(con, patient_id, body):
    p = con.execute("SELECT * FROM patient WHERE patient_id=?", (patient_id,)).fetchone()
    if not p:
        raise NotFound("Unknown patient")
    if "days" in body:
        days = sorted({int(d) for d in body["days"] if 0 <= int(d) <= 6})
        con.execute("UPDATE rehabilitation_program SET schedule_days=? WHERE program_id=?",
                    (",".join(map(str, days)), p["program_id"]))
    if "maxReps" in body:
        con.execute("UPDATE rehabilitation_program SET max_reps=? WHERE program_id=?",
                    (max(1, min(50, int(body["maxReps"]))), p["program_id"]))
    for e in body.get("exercises", []):
        updates = []
        params = []
        for key, (col, cast, lo, hi) in RX_FIELDS.items():
            if key in e:
                updates.append(f"{col}=?")
                params.append(max(lo, min(hi, cast(e[key]))))
        if "side" in e:
            updates.append("side=?")
            params.append(e["side"] if e["side"] in ("L", "R") else "")
        if updates:
            params.extend([int(e["id"]), p["program_id"]])
            con.execute(f"UPDATE exercise SET {', '.join(updates)} WHERE exercise_id=? AND program_id=?", params)
    con.commit()
    return get_program(con, patient_id, patient=p)


# Prescription fields the therapist can edit: json key -> (column, type, min, max)
RX_FIELDS = {
    "reps": ("reps", int, 1, 50), "targetAngle": ("target_angle", float, 5, 175),
    "tolerance": ("tolerance", float, 1, 30), "safetyMax": ("safety_max", float, 0, 180),
    "holdSeconds": ("hold_seconds", float, 0, 30), "sets": ("sets", int, 1, 10),
    "restSeconds": ("rest_seconds", float, 0, 300),
}
_RX_BY_COLUMN = {col: (cast, lo, hi) for col, cast, lo, hi in RX_FIELDS.values()}


def clamp_rx_columns(values):
    """Apply the therapist-edit bounds to prescription values keyed by column name (every write path uses this)."""
    out = dict(values)
    for col, (cast, lo, hi) in _RX_BY_COLUMN.items():
        if out.get(col) is not None:
            out[col] = max(lo, min(hi, cast(out[col])))
    return out


def change_exercises(con, patient_id, method, body, exercise_id=None):
    """Therapist adds an exercise from the library (POST) or removes one (DELETE; its history is kept)."""
    p = con.execute("SELECT * FROM patient WHERE patient_id=?", (patient_id,)).fetchone()
    if not p:
        raise NotFound("Unknown patient")
    if method == "POST":
        rx = body.get("rx") or {}
        rx_clean = {
            "target_angle": rx.get("targetAngle", rx.get("target_angle")),
            "tolerance": rx.get("tolerance"),
            "safety_max": rx.get("safetyMax", rx.get("safety_max")),
            "hold_seconds": rx.get("holdSeconds", rx.get("hold_seconds")),
            "sets": rx.get("sets"),
            "reps": rx.get("reps"),
            "rest_seconds": rx.get("restSeconds", rx.get("rest_seconds")),
        }
        rx_filtered = {k: v for k, v in rx_clean.items() if v is not None}
        add_exercise(con, p["program_id"], body.get("code"), rx=rx_filtered)
        if body.get("side"):
            con.execute("UPDATE exercise SET side=? WHERE exercise_id = (SELECT MAX(exercise_id) FROM exercise WHERE program_id=?)",
                        (body.get("side") if body.get("side") in ("L", "R") else "", p["program_id"]))
    else:
        con.execute("UPDATE exercise SET active=0 WHERE exercise_id=? AND program_id=?", (exercise_id, p["program_id"]))
    con.commit()
    return get_program(con, patient_id, patient=p)


SESSION_PAGE = 50          # dashboard session rows per page ("Show older sessions" asks for more)
SESSION_LIMIT_MAX = 1000


def dashboard(con, patient_id, session_limit=SESSION_PAGE):
    p = con.execute("SELECT * FROM patient WHERE patient_id=?", (patient_id,)).fetchone()
    if not p:
        return None
    prog = con.execute("SELECT * FROM rehabilitation_program WHERE program_id=?", (p["program_id"],)).fetchone()
    if not prog:
        return None
    info = get_program(con, patient_id, patient=p, program=prog)
    statuses = day_statuses(con, patient_id, prog, created_at=p["created_at"])
    since = (date.today() - timedelta(days=13)).isoformat()
    sessions = con.execute("""
        SELECT s.session_id, s.started_at, s.input_source, s.points, s.stars, s.status, s.pain_before, s.pain_after,
               s.soreness_over_2h, s.swelling_cm,
               COALESCE(SUM(r.valid_reps),0) AS valid, COALESCE(SUM(r.attempts),0) AS attempts,
               CASE WHEN SUM(r.attempts)>0 THEN SUM(r.avg_accuracy*r.attempts)/SUM(r.attempts) ELSE 0 END AS accuracy,
               CASE WHEN SUM(r.attempts)>0 THEN SUM(r.mean_angle_error*r.attempts)/SUM(r.attempts) ELSE 0 END AS mean_err
        FROM session s LEFT JOIN performance_record r ON r.session_id = s.session_id
        WHERE s.patient_id=? GROUP BY s.session_id ORDER BY s.started_at DESC, s.session_id DESC LIMIT ?""", (patient_id, session_limit)).fetchall()
    sessions = [dict(r) for r in sessions]
    recent = [s for s in sessions if s["started_at"][:10] >= since]
    att = sum(s["attempts"] for s in recent)
    per_ex = con.execute("""
        SELECT e.name, COUNT(r.record_id) AS n, COALESCE(SUM(r.unsafe_reps),0) AS unsafe,
               CASE WHEN SUM(r.attempts)>0 THEN SUM(r.avg_accuracy*r.attempts)/SUM(r.attempts) ELSE 0 END AS accuracy,
               CASE WHEN SUM(r.attempts)>0 THEN SUM(r.mean_angle_error*r.attempts)/SUM(r.attempts) ELSE 0 END AS mean_err
        FROM exercise e LEFT JOIN performance_record r ON r.exercise_id = e.exercise_id
        WHERE e.program_id=? AND e.active=1 GROUP BY e.exercise_id ORDER BY e.sort_order""", (prog["program_id"],)).fetchall()
    return {
        **info,
        "kpis": {
            "adherence": adherence_rate(statuses),
            "accuracy": round(sum(s["accuracy"] * s["attempts"] for s in recent) / att) if att else 0,
            "attempts": att,
            "validReps": sum(s["valid"] for s in recent),
            "streak": info["patient"]["streak"],
        },
        "archivedAt": p["archived_at"],
        "calendar": statuses,
        "readiness": readiness(con, p),
        "phaseHistory": [dict(r) for r in con.execute("""
            SELECT h.changed_at, h.note, ph.name AS phase, pr.name AS protocol FROM phase_history h
            LEFT JOIN protocol_phase ph ON ph.phase_id = h.phase_id LEFT JOIN protocol pr ON pr.protocol_id = ph.protocol_id
            WHERE h.patient_id=? ORDER BY h.history_id DESC LIMIT 10""", (patient_id,))],
        "sessionsTotal": con.execute("SELECT COUNT(*) FROM session WHERE patient_id=?", (patient_id,)).fetchone()[0],
        "sessions": [{**s, "accuracy": round(s["accuracy"], 1), "mean_err": round(s["mean_err"], 1)} for s in sessions],
        "byExercise": [{**dict(r), "accuracy": round(r["accuracy"], 1), "mean_err": round(r["mean_err"], 1)} for r in per_ex],
    }


def _csv_safe(v):
    """Stop spreadsheet apps from running text cells as formulas (CSV injection)."""
    if isinstance(v, str) and v[:1] in ("=", "+", "-", "@", "\t", "\r"):
        return "'" + v
    return v


def _export(rows, fields, fmt):
    data = [dict(r) for r in rows]
    if fmt == "json":
        return data, "application/json"
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=fields)
    writer.writeheader()
    for row in data:
        writer.writerow({k: _csv_safe(v) for k, v in row.items()})
    return out.getvalue().encode("utf-8"), "text/csv; charset=utf-8"


REP_EXPORT_FIELDS = [
    "patient_code", "session_id", "session_uuid", "started_at", "input_source", "exercise_code", "exercise_name",
    "joint", "target_angle", "tolerance", "safety_max", "attempt", "set_no", "side", "t_seconds", "peak_angle",
    "angle_error", "accuracy", "valid", "fault", "unsafe", "too_fast", "held",
]


def export_rep_events(con, patient_id=None, fmt="csv"):
    """One row per rep attempt (M4.5): the input for therapist rep labels and goniometer comparison."""
    query = """
        SELECT p.code AS patient_code, s.session_id, s.session_uuid, s.started_at, s.input_source,
               e.code AS exercise_code, e.name AS exercise_name, e.joint, e.target_angle, e.tolerance, e.safety_max,
               v.attempt, v.set_no, v.side, v.t_seconds, v.peak_angle, v.angle_error, v.accuracy, v.valid,
               v.fault, v.unsafe, v.too_fast, v.held
        FROM rep_event v
        JOIN session s ON s.session_id = v.session_id
        JOIN patient p ON p.patient_id = s.patient_id
        JOIN exercise e ON e.exercise_id = v.exercise_id
    """
    params = ()
    if patient_id is not None:
        query += " WHERE p.patient_id = ? "
        params = (patient_id,)
    query += " ORDER BY s.session_id, v.exercise_id, v.attempt"
    return _export(con.execute(query, params).fetchall(), REP_EXPORT_FIELDS, fmt)


def export_telemetry(con, patient_id=None, fmt="csv"):
    query = """
        SELECT 
            p.code AS patient_code,
            p.name AS patient_name,
            p.condition AS patient_condition,
            s.session_id,
            s.session_uuid,
            s.started_at,
            s.ended_at,
            s.input_source,
            s.status AS session_status,
            s.points AS session_points,
            s.stars AS session_stars,
            s.pain_before,
            s.pain_after,
            s.soreness_over_2h,
            s.swelling_cm,
            e.code AS exercise_code,
            e.name AS exercise_name,
            e.joint,
            e.target_angle,
            e.tolerance,
            e.hold_seconds,
            r.target_reps,
            r.valid_reps,
            r.attempts,
            r.avg_accuracy,
            r.mean_angle_error,
            r.unsafe_reps,
            r.feedback_log
        FROM performance_record r
        JOIN session s ON s.session_id = r.session_id
        JOIN patient p ON p.patient_id = s.patient_id
        JOIN exercise e ON e.exercise_id = r.exercise_id
    """
    params = ()
    if patient_id is not None:
        query += " WHERE p.patient_id = ? "
        params = (patient_id,)
    query += " ORDER BY s.session_id ASC, r.record_id ASC"

    fields = [
        "patient_code", "patient_name", "patient_condition", "session_id", "session_uuid", "started_at", "ended_at",
        "input_source", "session_status", "session_points", "session_stars", "pain_before", "pain_after",
        "soreness_over_2h", "swelling_cm", "exercise_code", "exercise_name", "joint", "target_angle",
        "tolerance", "hold_seconds", "target_reps", "valid_reps", "attempts", "avg_accuracy",
        "mean_angle_error", "unsafe_reps", "feedback_log"
    ]
    return _export(con.execute(query, params).fetchall(), fields, fmt)


# ---------------------------------------------------------------- HTTP
class Handler(BaseHTTPRequestHandler):
    """
    No CORS headers on purpose: the dashboard is served from this same origin and Unity is not a browser,
    so other web pages open on the clinic PC can't call the API (M4.2).
    """
    server_version = "TheraQuest/1.0"
    STATIC_ROOT = os.path.realpath(os.path.join(HERE, "static"))
    MIMES = {".js": "application/javascript; charset=utf-8", ".css": "text/css; charset=utf-8",
             ".svg": "image/svg+xml", ".png": "image/png", ".json": "application/json"}

    def _send(self, code, payload, ctype="application/json"):
        data = payload if isinstance(payload, bytes) else json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(data)

    def _send_file(self, data, ctype, filename):
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _body(self):
        try:
            n = int(self.headers.get("Content-Length") or 0)
            body = json.loads(self.rfile.read(n) or b"{}")
        except (ValueError, UnicodeDecodeError):
            raise BadRequest("Request body must be JSON")
        if not isinstance(body, dict):
            raise BadRequest("Request body must be a JSON object")
        return body

    @staticmethod
    def _id(part):
        try:
            return int(part)
        except ValueError:
            raise BadRequest(f"'{part}' is not a valid id")

    def _get_auth_token(self):
        auth_hdr = self.headers.get("Authorization", "")
        if auth_hdr.startswith("Bearer "):
            return auth_hdr[7:].strip()
        # ?token= is accepted only on export downloads (plain <a href> links can't send headers)
        parsed = urlparse(self.path)
        if not parsed.path.rstrip("/").endswith("/export"):
            return ""
        return parse_qs(parsed.query).get("token", [""])[0]

    def _client_is_loopback(self):
        host = self.client_address[0]
        return host in ("127.0.0.1", "::1") or host.startswith("127.") or host.startswith("::ffff:127.")

    def _vr_patient(self, con):
        """
        DEC-009: the VR client authenticates with its synthetic patient code, from this machine only.
        Browsers always send an Origin header on API calls; Unity doesn't, so a web page can't pose as the VR client.
        Returns (patient_row, None) or (None, (status, error)).
        """
        if not self._client_is_loopback() or self.headers.get("Origin"):
            return None, (403, "Forbidden: VR routes accept requests from the VR app on this machine only")
        code = (self.headers.get("X-Patient-Code") or "").strip().upper()
        if not code:
            return None, (401, "Unauthorized: X-Patient-Code header required")
        p = con.execute("SELECT * FROM patient WHERE code=?", (code,)).fetchone()
        if not p:
            return None, (401, "Unauthorized: Unknown patient code")
        return p, None

    def _static(self, parts):
        """Serve a file under static/ only; anything resolving outside it (.., other drives) is refused."""
        try:
            full = os.path.realpath(os.path.join(HERE, *parts))
            inside = os.path.commonpath([self.STATIC_ROOT, full]) == self.STATIC_ROOT
        except ValueError:   # different drive on Windows
            inside = False
        if not inside:
            return self._send(403, {"error": "Forbidden"})
        if not os.path.isfile(full):
            return self._send(404, {"error": "Static file not found"})
        with open(full, "rb") as f:
            data = f.read()
        self.send_response(200)
        self.send_header("Content-Type", self.MIMES.get(os.path.splitext(full)[1].lower(), "application/octet-stream"))
        self.send_header("Content-Length", str(len(data)))
        self.send_header("X-Content-Type-Options", "nosniff")
        if "vendor" in parts:
            self.send_header("Cache-Control", "public, max-age=86400")
        self.end_headers()
        self.wfile.write(data)

    def _route(self, method):
        parsed = urlparse(self.path)
        parts = [p for p in parsed.path.split("/") if p]
        qs = parse_qs(parsed.query)
        fmt = qs.get("format", ["csv"])[0].lower()
        try:
            if method == "GET" and parts in ([], ["dashboard"]):
                with open(os.path.join(HERE, "dashboard.html"), "rb") as f:
                    return self._send(200, f.read(), "text/html; charset=utf-8")
            if method == "GET" and parts[:1] == ["static"]:
                return self._static(parts)
            if parts[:1] != ["api"]:
                return self._send(404, {"error": "Not found"})
            con = db()
            try:
                return self._api(con, method, parts, fmt)
            finally:
                con.close()
        except ApiError as e:
            return self._send(e.status, {"error": str(e)})
        except (ValueError, TypeError, KeyError) as e:
            # Values that don't convert (e.g. "abc" for reps) or required fields that are missing
            sys.stderr.write(f"  bad request: {e!r}\n")
            return self._send(400, {"error": "Invalid request data"})
        except Exception:
            import traceback
            traceback.print_exc()
            return self._send(500, {"error": "Internal server error. Details are in the server window."})

    def _api(self, con, method, parts, fmt):
        # Clinician Authentication endpoints
        if method == "GET" and parts == ["api", "auth", "setup"]:
            return self._send(200, {"needsSetup": needs_setup(con)})
        if method == "POST" and parts == ["api", "auth", "setup"]:
            if not self._client_is_loopback():
                return self._send(403, {"error": "First-run setup must be done on the clinic computer itself"})
            return self._send(201, auth_setup(con, self._body()))
        if method == "POST" and parts == ["api", "auth", "login"]:
            res, code = auth_login(con, self._body())
            return self._send(code, res)
        if method == "POST" and parts == ["api", "auth", "logout"]:
            delete_session(con, self._get_auth_token())
            return self._send(200, {"success": True})

        # Patient-scoped VR routes (Unity client, patient code + loopback only)
        if parts[:2] == ["api", "vr"]:
            p, err = self._vr_patient(con)
            if err:
                return self._send(err[0], {"error": err[1]})
            if method == "GET" and parts == ["api", "vr", "program"]:
                if p["archived_at"]:
                    return self._send(403, {"error": "This patient is archived. Ask the therapist to reactivate them."})
                return self._send(200, get_program(con, p["patient_id"], patient=p))
            if method == "POST" and parts == ["api", "vr", "sessions"]:
                body = self._body()
                try:
                    claimed = int(body.get("patient_id") or 0)   # 0 = recorded offline, unknown id
                except (TypeError, ValueError):
                    raise BadRequest("patient_id must be a number")
                if claimed and claimed != p["patient_id"]:
                    return self._send(403, {"error": "Forbidden: session belongs to a different patient"})
                body["patient_id"] = p["patient_id"]
                return self._send(201, save_session(con, body))
            return self._send(404, {"error": "Not found"})

        # Everything below is therapist-only
        therapist = get_session_therapist(con, self._get_auth_token())
        if not therapist:
            return self._send(401, {"error": "Unauthorized: Session invalid or expired"})

        if method == "GET" and parts == ["api", "auth", "me"]:
            return self._send(200, {"therapist": therapist})
        if method == "POST" and parts == ["api", "auth", "password"]:
            return self._send(200, change_password(con, therapist["therapist_id"], self._body()))
        if method == "GET" and (parts == ["api", "export"] or
                                (len(parts) == 4 and parts[1] == "patients" and parts[3] == "export")):
            pid = self._id(parts[2]) if len(parts) == 4 else None
            reps = parse_qs(urlparse(self.path).query).get("kind", [""])[0].lower() == "reps"
            payload, ctype = (export_rep_events if reps else export_telemetry)(con, pid, fmt)
            if fmt == "csv":
                who = "all" if pid is None else f"patient_{pid}"
                return self._send_file(payload, ctype, f"theraquest_{'reps' if reps else 'telemetry'}_{who}.csv")
            return self._send(200, payload)
        if method == "GET" and parts == ["api", "patients"]:
            rows = con.execute("""
                SELECT
                    p.patient_id AS id,
                    p.code,
                    p.name,
                    p.condition,
                    COALESCE(pr.name, 'Custom Prescription') AS protocol_name,
                    COALESCE(ph.name, 'Phase 1') AS phase_name,
                    COUNT(s.session_id) AS total_sessions,
                    MAX(s.started_at) AS last_session_at,
                    p.archived_at
                FROM patient p
                LEFT JOIN protocol_phase ph ON ph.phase_id = p.phase_id
                LEFT JOIN protocol pr ON pr.protocol_id = ph.protocol_id
                LEFT JOIN session s ON s.patient_id = p.patient_id
                WHERE p.archived_at IS NULL OR ?
                GROUP BY p.patient_id
                ORDER BY p.code
            """, (parse_qs(urlparse(self.path).query).get("include_archived", ["0"])[0] == "1",)).fetchall()
            return self._send(200, [dict(r) for r in rows])
        if method == "POST" and parts == ["api", "patients"]:
            return self._send(201, add_patient(con, self._body(), therapist["therapist_id"]))
        if method == "GET" and parts == ["api", "protocols"]:
            return self._send(200, list_protocols(con))
        if method == "POST" and parts == ["api", "protocols"]:
            return self._send(201, add_protocol(con, self._body()))
        if method == "DELETE" and len(parts) == 3 and parts[:2] == ["api", "protocols"]:
            return self._send(200, delete_protocol(con, self._id(parts[2])))
        if method == "POST" and len(parts) == 4 and parts[1] == "protocols" and parts[3] == "phases":
            return self._send(201, add_phase(con, self._id(parts[2]), self._body()))
        if method == "PUT" and len(parts) == 5 and parts[1] == "protocols" and parts[3] == "phases":
            return self._send(200, update_phase(con, self._id(parts[2]), self._id(parts[4]), self._body()))
        if method == "PUT" and len(parts) == 3 and parts[1] == "patients":
            return self._send(200, update_patient(con, self._id(parts[2]), self._body()))
        if method == "POST" and len(parts) == 4 and parts[1] == "patients" and parts[3] == "archive":
            return self._send(200, set_patient_archived(con, self._id(parts[2]), self._body()))
        if len(parts) == 4 and parts[1] == "patients" and parts[3] == "protocol" and method == "DELETE":
            return self._send(200, remove_patient_protocol(con, self._id(parts[2])))
        if len(parts) == 4 and parts[1] == "patients" and parts[3] == "phase" and method == "POST":
            return self._send(200, set_phase(con, self._id(parts[2]), self._body()))
        if method == "GET" and parts == ["api", "library"]:
            return self._send(200, [{
                "code": c, "name": v[0], "joint": v[1], "measure": v[2], "view": v[3], "position": v[4],
                "targetAngle": v[5], "tolerance": v[6], "safetyMax": v[7], "holdSeconds": v[8],
                "sets": v[9], "reps": v[10], "restSeconds": v[11], "cue": v[12],
                "normalRom": NORMAL_ROM.get(c, ("", 0))[0], "pose": v[13]["pose"], "posture": v[13]["posture"]
            } for c, v in LIBRARY.items()])
        if len(parts) == 4 and parts[1] == "sessions" and parts[3] == "clinical" and method == "PUT":
            return self._send(200, record_clinical(con, self._id(parts[2]), self._body()))
        if len(parts) == 4 and parts[1] == "patients" and parts[3] == "exercises" and method == "POST":
            return self._send(201, change_exercises(con, self._id(parts[2]), method, self._body()))
        if len(parts) == 5 and parts[1] == "patients" and parts[3] == "exercises" and method == "DELETE":
            return self._send(200, change_exercises(con, self._id(parts[2]), method, {}, self._id(parts[4])))
        if len(parts) == 4 and parts[1] == "patients" and parts[3] in ("program", "dashboard"):
            pid = self._id(parts[2])
            if method == "GET":
                if parts[3] == "program":
                    data = get_program(con, pid)
                else:
                    # Never fewer than one page: the 14-day KPIs are computed from these rows
                    limit = int(parse_qs(urlparse(self.path).query).get("sessions", [SESSION_PAGE])[0])
                    data = dashboard(con, pid, min(max(limit, SESSION_PAGE), SESSION_LIMIT_MAX))
                return self._send(200, data) if data else self._send(404, {"error": "Patient not found"})
            if method == "PUT" and parts[3] == "program":
                return self._send(200, update_program(con, pid, self._body()))
        return self._send(404, {"error": "Not found"})

    def do_GET(self):
        self._route("GET")

    def do_POST(self):
        self._route("POST")

    def do_PUT(self):
        self._route("PUT")

    def do_DELETE(self):
        self._route("DELETE")

    def log_message(self, fmt, *args):
        path = self.path.split("token=")[0] + "token=***" if "token=" in self.path else self.path
        sys.stderr.write("  %s %s\n" % (self.command, path))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--host", default="127.0.0.1",
                    help="address to listen on; 0.0.0.0 also exposes the dashboard to the clinic network")
    ap.add_argument("--reset", action="store_true", help="delete the database first")
    args = ap.parse_args()
    if args.reset:
        delete_db_files(DB_PATH)
    else:
        migrate_legacy_db()
    init_db()
    print(f"TheraQuest server running.  Dashboard: http://localhost:{args.port}   (Ctrl+C to stop)")
    print(f"Database: {DB_PATH}")
    try:
        ThreadingHTTPServer((args.host, args.port), Handler).serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
