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

# Exercise library: every movement the tracker can measure with one webcam (2D, one plane of motion).
# `code` drives the Unity coach figure and posture checks; `measure` is the tracker angle.
# Default numbers are starting points; the protocol phase or the therapist sets the real prescription.
#   code: (name, joint, measure, view, start position, target, tol, safety max, hold s, sets, reps, rest s, cue)
LIBRARY = {
    # Shoulder
    "shoulderAbd":  ("Shoulder abduction", "Shoulder", "shoulderElev", "front", "Standing, arm at your side, thumb up",
                     90, 10, 120, 0, 2, 8, 30, "Raise your arm out to the side"),
    "shoulderFlex": ("Active shoulder elevation", "Shoulder", "shoulderElev", "side", "Standing, arm at your side, thumb forward",
                     120, 10, 140, 0, 2, 8, 30, "Raise your straight arm forward and up"),
    "forwardReach": ("Active forward reach", "Shoulder", "shoulderElev", "side", "Standing, arm at your side",
                     90, 10, 110, 0, 2, 8, 30, "Reach forward to shoulder height, elbow straight"),
    "supineFlex":   ("Supine shoulder flexion with cane", "Shoulder", "shoulderElev", "side",
                     "Lying on your back, holding a cane with both hands", 100, 10, 140, 0, 2, 8, 30,
                     "Let your good arm help lift the cane up and overhead"),
    "scaption":     ("Full can (scaption)", "Shoulder", "shoulderElev", "front", "Standing, arm slightly forward, thumb up",
                     90, 10, 110, 0, 2, 8, 30, "Raise your arm at a slight angle in front of you, thumb up"),
    "wallSlide":    ("Wall slide (shoulder)", "Shoulder", "shoulderElev", "side", "Facing a wall, forearm resting on it",
                     120, 10, 140, 2, 2, 8, 30, "Slide your hand up the wall"),
    "shoulderExt":  ("Shoulder extension, straight arm", "Shoulder", "shoulderElev", "side", "Standing, arm at your side",
                     45, 10, 60, 0, 2, 8, 30, "Move your straight arm back behind you"),
    # Elbow
    "elbowFlex":    ("Elbow flexion", "Elbow", "elbowFlex", "side", "Standing, elbow at your side",
                     130, 10, 150, 0, 2, 8, 30, "Bend your elbow and bring your hand up"),
    "bicepsCurl":   ("Biceps curl", "Elbow", "elbowFlex", "side", "Standing, elbow at your side, palm up",
                     130, 10, 150, 0, 2, 10, 30, "Curl your hand up toward your shoulder"),
    "wallPushUp":   ("Wall push-up", "Elbow", "elbowFlex", "side", "Facing a wall, hands on it at shoulder height",
                     90, 10, 0, 0, 2, 8, 30, "Bend your elbows to bring your chest toward the wall"),
    # Hip
    "hipAbd":       ("Standing hip abduction", "Hip", "hipElev", "front", "Standing, holding a chair for balance",
                     25, 5, 40, 0, 2, 8, 30, "Lift your leg out to the side, toes forward"),
    "sidelyingHipAbd": ("Side-lying hip abduction", "Hip", "hipElev", "front", "Lying on your good side, operated leg on top",
                     25, 5, 40, 0, 2, 8, 30, "Lift your top leg toward the ceiling, toes forward"),
    "hipExt":       ("Standing hip extension", "Hip", "hipElev", "side", "Standing, holding a chair for balance",
                     20, 5, 30, 0, 2, 8, 30, "Move your straight leg back without leaning forward"),
    "slr":          ("Straight leg raise", "Hip", "hipElev", "side", "Lying on your back, other knee bent",
                     45, 5, 60, 0, 2, 8, 30, "Tighten your thigh and lift your straight leg"),
    "march":        ("Standing march", "Hip", "hipElev", "side", "Standing, holding a chair for balance",
                     70, 10, 100, 0, 2, 8, 30, "Lift your knee up toward your chest"),
    # Knee
    "kneeExt":      ("Seated knee extension (LAQ)", "Knee", "kneeExt", "side", "Sitting tall, knee bent at 90°",
                     85, 10, 0, 0, 2, 8, 30, "Straighten your knee slowly, then lower it slowly"),
    "heelSlide":    ("Heel slide", "Knee", "kneeFlex", "side", "Lying on your back, legs straight",
                     90, 10, 110, 0, 2, 8, 30, "Slide your heel toward you, bending your knee"),
    "hamstringCurl": ("Standing hamstring curl", "Knee", "kneeFlex", "side", "Standing, holding a chair for balance",
                     90, 10, 120, 0, 2, 8, 30, "Bend your knee to bring your heel toward your buttock"),
    "miniSquat":    ("Mini squat", "Knee", "kneeFlex", "side", "Standing, holding a chair, feet hip-width",
                     30, 10, 50, 0, 2, 8, 30, "Bend your knees a little, chest up"),
    "miniLunge":    ("Mini lunge", "Knee", "kneeFlex", "side", "Standing, operated leg a step forward, holding a chair",
                     45, 10, 70, 0, 2, 8, 30, "Bend your front knee and lower your body a little"),
    "kneeWallSlide": ("Wall slide to 90° (knee)", "Knee", "kneeFlex", "side", "Back against a wall, feet a step forward",
                     90, 10, 100, 0, 2, 8, 30, "Slide down the wall until your knees bend to 90°"),
    "sitToStand":   ("Sit to stand", "Knee", "kneeExt", "side", "Sitting on a firm chair, feet flat",
                     85, 10, 0, 0, 2, 8, 45, "Lean forward and stand up tall"),
    "wallSquatHold": ("Wall squat hold", "Knee", "kneeFlex", "side", "Back flat against wall, feet shoulder-width",
                     60, 10, 85, 5, 2, 8, 30, "Slide down into a squat and hold steady"),
    "quadExtHold":  ("Seated quad extension hold", "Knee", "kneeExt", "side", "Sitting tall, knee bent at 90°",
                     85, 10, 0, 3, 2, 8, 30, "Straighten your knee and hold steady at the top"),
    "scaptionHold": ("Scaption hold (Full can)", "Shoulder", "shoulderElev", "front", "Standing, arm slightly forward, thumb up",
                     90, 10, 110, 3, 2, 8, 30, "Raise arm to shoulder height in scaption plane and hold"),
    "standingHipFlex": ("Standing hip flexion hold", "Hip", "hipElev", "side", "Standing, holding a chair for balance",
                     70, 10, 95, 3, 2, 8, 30, "Lift your knee high and hold steady for balance"),
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
PROTOCOL_VERSION = "2"
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
]

# Columns added after the first version; added to existing databases on startup.
MIGRATIONS = {
    "patient": [("phase_id", "INTEGER"), ("phase_started_at", "TEXT")],
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


def replace_protocols(con):
    """
    Loads PROTOCOLS, replacing older built-in protocol data. Protocols therapists authored are kept.
    Patients on an old built-in phase keep their exercises as a custom program; their phase history
    stays, marked as the old version.
    """
    old = [r[0] for r in con.execute("SELECT protocol_id FROM protocol WHERE builtin=1")]
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
    seed_protocols(con)
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
    name, joint, measure, view, position, tgt, tol, smax, hold, sets, reps, rest, cue = LIBRARY[code]
    v = dict(target_angle=tgt, tolerance=tol, safety_max=smax, hold_seconds=hold, sets=sets, reps=reps, rest_seconds=rest)
    v.update({k: x for k, x in (rx or {}).items() if k in v and x is not None})
    v = clamp_rx_columns(v)
    order = con.execute("SELECT COALESCE(MAX(sort_order), -1) + 1 FROM exercise WHERE program_id=?", (program_id,)).fetchone()[0]
    con.execute("""INSERT INTO exercise(program_id, code, name, joint, measure, view, position, target_angle, tolerance,
                   safety_max, hold_seconds, sets, reps, rest_seconds, cue, sort_order)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (program_id, code, name, joint, measure, view, position, v["target_angle"], v["tolerance"],
                 v["safety_max"], v["hold_seconds"], v["sets"], v["reps"], v["rest_seconds"], cue, order))


def seed_protocols(con):
    for name, condition, source, phases in PROTOCOLS:
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


def list_protocols(con):
    protocols = con.execute("SELECT * FROM protocol ORDER BY protocol_id").fetchall()
    if not protocols:
        return []

    phases = con.execute("SELECT * FROM protocol_phase ORDER BY protocol_id, phase_no").fetchall()
    exercises = con.execute("SELECT * FROM phase_exercise ORDER BY phase_id, sort_order").fetchall()

    ex_by_phase = defaultdict(list)
    for e in exercises:
        code = e["code"]
        name = LIBRARY[code][0] if code in LIBRARY else code
        ex_by_phase[e["phase_id"]].append({
            "code": code,
            "name": name,
            "targetAngle": e["target_angle"],
            "tolerance": e["tolerance"],
            "safetyMax": e["safety_max"],
            "holdSeconds": e["hold_seconds"],
            "sets": e["sets"],
            "reps": e["reps"],
            "restSeconds": e["rest_seconds"]
        })

    phases_by_protocol = defaultdict(list)
    for ph in phases:
        ex_list = ex_by_phase.get(ph["phase_id"], [])
        ex_names = [e["name"] for e in ex_list if e["code"] in LIBRARY]
        phases_by_protocol[ph["protocol_id"]].append({
            "id": ph["phase_id"], "phaseNo": ph["phase_no"], "name": ph["name"], "weeks": ph["weeks"],
            "vrAllowed": bool(ph["vr_allowed"]), "goals": ph["goals"], "precautions": ph["precautions"],
            "romGoal": ph["rom_goal"] or "", "other": ph["other_exercises"] or "",
            "exercises": ex_names, "exerciseDetails": ex_list
        })

    return [{
        "id": pr["protocol_id"], "name": pr["name"], "condition": pr["condition"], "source": pr["source"],
        "phases": phases_by_protocol.get(pr["protocol_id"], [])
    } for pr in protocols]


def get_protocol(con, protocol_id):
    pr = con.execute("SELECT * FROM protocol WHERE protocol_id=?", (protocol_id,)).fetchone()
    if not pr:
        return None
    phases = con.execute("SELECT * FROM protocol_phase WHERE protocol_id=? ORDER BY phase_no", (protocol_id,)).fetchall()
    phase_ids = [ph["phase_id"] for ph in phases]
    ex_by_phase = defaultdict(list)
    if phase_ids:
        placeholders = ",".join("?" for _ in phase_ids)
        exercises = con.execute(f"SELECT * FROM phase_exercise WHERE phase_id IN ({placeholders}) ORDER BY phase_id, sort_order", phase_ids).fetchall()
        for e in exercises:
            code = e["code"]
            name = LIBRARY[code][0] if code in LIBRARY else code
            ex_by_phase[e["phase_id"]].append({
                "code": code,
                "name": name,
                "targetAngle": e["target_angle"],
                "tolerance": e["tolerance"],
                "safetyMax": e["safety_max"],
                "holdSeconds": e["hold_seconds"],
                "sets": e["sets"],
                "reps": e["reps"],
                "restSeconds": e["rest_seconds"]
            })

    phases_out = []
    for ph in phases:
        ex_list = ex_by_phase.get(ph["phase_id"], [])
        ex_names = [e["name"] for e in ex_list if e["code"] in LIBRARY]
        phases_out.append({
            "id": ph["phase_id"], "phaseNo": ph["phase_no"], "name": ph["name"], "weeks": ph["weeks"],
            "vrAllowed": bool(ph["vr_allowed"]), "goals": ph["goals"], "precautions": ph["precautions"],
            "romGoal": ph["rom_goal"] or "", "other": ph["other_exercises"] or "",
            "exercises": ex_names, "exerciseDetails": ex_list
        })

    return {
        "id": pr["protocol_id"], "name": pr["name"], "condition": pr["condition"], "source": pr["source"],
        "phases": phases_out
    }


def add_protocol(con, body):
    name = (body.get("name") or "").strip()
    condition = (body.get("condition") or "").strip()
    source = (body.get("source") or "").strip()
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
        pname = (ph.get("name") or f"Phase {idx}").strip()
        pno = int(ph.get("phaseNo") or idx)
        weeks = (ph.get("weeks") or "").strip()
        vr_allowed = 1 if ph.get("vrAllowed", True) else 0
        goals = (ph.get("goals") or "").strip()
        precautions = (ph.get("precautions") or "").strip()
        rom_goal = (ph.get("romGoal") or "").strip()
        other_ex = (ph.get("other") or ph.get("otherExercises") or "").strip()
        min_sessions = int(ph.get("minSessions") or 3)
        min_accuracy = float(ph.get("minAccuracy") or 85.0)
        max_pain = int(ph.get("maxPainIncrease") or 2)
        check_soreness = 1 if ph.get("checkSoreness") else 0
        max_swelling = ph.get("maxSwellingCm")
        if max_swelling is not None and max_swelling != "":
            max_swelling = float(max_swelling)
        else:
            max_swelling = None

        ph_cur = con.execute("""INSERT INTO protocol_phase(protocol_id, phase_no, name, weeks, vr_allowed,
                                               goals, precautions, rom_goal, other_exercises,
                                               min_sessions, min_accuracy, max_pain_increase,
                                               check_soreness, max_swelling_cm)
                                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                             (protocol_id, pno, pname, weeks, vr_allowed, goals, precautions,
                              rom_goal, other_ex, min_sessions, min_accuracy, max_pain,
                              check_soreness, max_swelling))
        phase_id = ph_cur.lastrowid

        ex_list = ph.get("exercises") or []
        for s_idx, ex in enumerate(ex_list):
            if isinstance(ex, str):
                code = ex
                rx = {}
            elif isinstance(ex, dict):
                code = ex.get("code")
                rx = ex
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
        "patient": {"id": p["patient_id"], "code": p["code"], "name": p["name"], "xp": p["xp"],
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
        } for e in exs],
    }


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


def dashboard(con, patient_id):
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
        WHERE s.patient_id=? GROUP BY s.session_id ORDER BY s.started_at DESC, s.session_id DESC LIMIT 50""", (patient_id,)).fetchall()
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
        "calendar": statuses,
        "readiness": readiness(con, p),
        "phaseHistory": [dict(r) for r in con.execute("""
            SELECT h.changed_at, h.note, ph.name AS phase, pr.name AS protocol FROM phase_history h
            LEFT JOIN protocol_phase ph ON ph.phase_id = h.phase_id LEFT JOIN protocol pr ON pr.protocol_id = ph.protocol_id
            WHERE h.patient_id=? ORDER BY h.history_id DESC LIMIT 10""", (patient_id,))],
        "sessions": [{**s, "accuracy": round(s["accuracy"], 1), "mean_err": round(s["mean_err"], 1)} for s in sessions],
        "byExercise": [{**dict(r), "accuracy": round(r["accuracy"], 1), "mean_err": round(r["mean_err"], 1)} for r in per_ex],
    }


def _csv_safe(v):
    """Stop spreadsheet apps from running text cells as formulas (CSV injection)."""
    if isinstance(v, str) and v[:1] in ("=", "+", "-", "@", "\t", "\r"):
        return "'" + v
    return v


def export_telemetry(con, patient_id=None, fmt="csv"):
    query = """
        SELECT 
            p.code AS patient_code,
            p.name AS patient_name,
            p.condition AS patient_condition,
            s.session_id,
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

    rows = con.execute(query, params).fetchall()
    data = [dict(r) for r in rows]

    if fmt == "json":
        return data, "application/json"

    out = io.StringIO()
    fields = [
        "patient_code", "patient_name", "patient_condition", "session_id", "started_at", "ended_at",
        "input_source", "session_status", "session_points", "session_stars", "pain_before", "pain_after",
        "soreness_over_2h", "swelling_cm", "exercise_code", "exercise_name", "joint", "target_angle",
        "tolerance", "hold_seconds", "target_reps", "valid_reps", "attempts", "avg_accuracy",
        "mean_angle_error", "unsafe_reps", "feedback_log"
    ]
    writer = csv.DictWriter(out, fieldnames=fields)
    writer.writeheader()
    for row in data:
        writer.writerow({k: _csv_safe(v) for k, v in row.items()})
    return out.getvalue().encode("utf-8"), "text/csv; charset=utf-8"


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
        if method == "GET" and parts == ["api", "export"]:
            payload, ctype = export_telemetry(con, None, fmt)
            if fmt == "csv":
                return self._send_file(payload, ctype, "theraquest_telemetry_all.csv")
            return self._send(200, payload)
        if method == "GET" and len(parts) == 4 and parts[1] == "patients" and parts[3] == "export":
            pid = self._id(parts[2])
            payload, ctype = export_telemetry(con, pid, fmt)
            if fmt == "csv":
                return self._send_file(payload, ctype, f"theraquest_telemetry_patient_{pid}.csv")
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
                    MAX(s.started_at) AS last_session_at
                FROM patient p
                LEFT JOIN protocol_phase ph ON ph.phase_id = p.phase_id
                LEFT JOIN protocol pr ON pr.protocol_id = ph.protocol_id
                LEFT JOIN session s ON s.patient_id = p.patient_id
                GROUP BY p.patient_id
                ORDER BY p.code
            """).fetchall()
            return self._send(200, [dict(r) for r in rows])
        if method == "POST" and parts == ["api", "patients"]:
            return self._send(201, add_patient(con, self._body(), therapist["therapist_id"]))
        if method == "GET" and parts == ["api", "protocols"]:
            return self._send(200, list_protocols(con))
        if method == "POST" and parts == ["api", "protocols"]:
            return self._send(201, add_protocol(con, self._body()))
        if method == "DELETE" and len(parts) == 3 and parts[:2] == ["api", "protocols"]:
            return self._send(200, delete_protocol(con, self._id(parts[2])))
        if len(parts) == 4 and parts[1] == "patients" and parts[3] == "protocol" and method == "DELETE":
            return self._send(200, remove_patient_protocol(con, self._id(parts[2])))
        if len(parts) == 4 and parts[1] == "patients" and parts[3] == "phase" and method == "POST":
            return self._send(200, set_phase(con, self._id(parts[2]), self._body()))
        if method == "GET" and parts == ["api", "library"]:
            return self._send(200, [{
                "code": c, "name": v[0], "joint": v[1], "measure": v[2], "view": v[3], "position": v[4],
                "targetAngle": v[5], "tolerance": v[6], "safetyMax": v[7], "holdSeconds": v[8],
                "sets": v[9], "reps": v[10], "restSeconds": v[11], "cue": v[12],
                "normalRom": NORMAL_ROM.get(c, ("", 0))[0]
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
                data = get_program(con, pid) if parts[3] == "program" else dashboard(con, pid)
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
