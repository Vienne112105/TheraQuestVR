using System;
using System.Collections.Generic;

namespace TheraQuest
{
    // ---------------------------------------------------------------
    // Packet sent by tracker.py over UDP (must match the Python field names)
    // ---------------------------------------------------------------
    /// <summary>The angles the tracker measures (see tracker/angles.py). -1 = not visible.</summary>
    [Serializable]
    public class AngleSet
    {
        /// <summary>A signed angle that can't be measured (-1 is a real signed value).</summary>
        public const float SignedInvalid = -999f;

        public float shoulderElev = -1f;
        public float elbowFlex = -1f;
        public float hipElev = -1f;
        public float kneeFlex = -1f;
        public float kneeExt = -1f;
        public float ankleDF = -1f;    // M6.4: toes up from a right angle to the shin
        public float anklePF = -1f;    // M6.4: toes down / heel up
        // Side view only: + = limb in front of the trunk (flexion), - = behind it (extension)
        public float shoulderElevSigned = SignedInvalid;
        public float hipElevSigned = SignedInvalid;

        public static bool SignedValid(float v) => v > SignedInvalid + 1f;

        public float Get(string measure)
        {
            switch (measure)
            {
                case "shoulderElev": return shoulderElev;
                case "elbowFlex": return elbowFlex;
                case "hipElev": return hipElev;
                case "kneeFlex": return kneeFlex;
                case "kneeExt": return kneeExt;
                case "ankleDF": return ankleDF;
                case "anklePF": return anklePF;
                default: return -1f;
            }
        }
    }

    /// <summary>Per measured angle: every landmark it needs is detected and inside the image (M6.3).</summary>
    [Serializable]
    public class FramedSet
    {
        public bool shoulderElev, elbowFlex, hipElev, kneeFlex, kneeExt, ankleDF, anklePF;

        public bool Get(string measure)
        {
            switch (measure)
            {
                case "shoulderElev": return shoulderElev;
                case "elbowFlex": return elbowFlex;
                case "hipElev": return hipElev;
                case "kneeFlex": return kneeFlex;
                case "kneeExt": return kneeExt;
                case "ankleDF": return ankleDF;
                case "anklePF": return anklePF;
                default: return false;
            }
        }
    }

    /// <summary>Camera setup checks from the tracker's raw detection (M6.3). Guidance only, never scored.</summary>
    [Serializable]
    public class SetupInfo
    {
        public bool valid;              // false: the tracker sent no setup checks (nobody detected, or an older tracker)
        public FramedSet framedL = new FramedSet();
        public FramedSet framedR = new FramedSet();
        public string view;             // side | front | "" (turned part way, or can't tell)
        public float size = -1f;        // torso length / image height: bigger = closer
        public float light;             // median landmark confidence 0..1: low in poor light
    }

    /// <summary>
    /// Which way the upper arm (shoulder to elbow) and thigh (hip to knee) point in 3D, as unit vectors in the body's
    /// frame: +x the patient's right, +y up, +z forward (M6.4). Display only: tilts the live limb out of the exercise's
    /// plane, never scored. Empty when the tracker couldn't measure that limb.
    /// </summary>
    [Serializable]
    public class LimbDirs
    {
        public float[] arm;
        public float[] leg;

        /// <summary>The limb's direction, or false when it wasn't sent.</summary>
        public bool TryGet(bool legLimb, out UnityEngine.Vector3 dir)
        {
            var a = legLimb ? leg : arm;
            dir = a != null && a.Length >= 3 ? new UnityEngine.Vector3(a[0], a[1], a[2]) : UnityEngine.Vector3.zero;
            return dir.sqrMagnitude > 0.25f;
        }
    }

    /// <summary>Top-level angles come from whichever side the camera sees best; L and R hold each side.</summary>
    [Serializable]
    public class MotionPacket : AngleSet
    {
        public float ts;
        public bool visible;
        public string side;
        public float trunkLean;
        public float elbowDrift;
        public string trackingState;   // tracking | degraded | reacquiring | lost (DEC-022)
        public string patient;         // Patient Lock (M10.5): locking | ok | away | different; empty from an older tracker
        public int bodies;             // bodies the tracker can see (the patient and anyone else in view)
        public AngleSet estL;          // angles from estimated landmarks: for display only, never scored
        public AngleSet estR;
        public AngleSet L = new AngleSet();
        public AngleSet R = new AngleSet();
        public SetupInfo setup;
        public LimbDirs dirL;          // display only (M6.4)
        public LimbDirs dirR;

        /// <summary>Nobody is in the camera's view (DEC-022 whole-pose state "lost", or no person at all).</summary>
        public bool PersonLost => !visible || trackingState == "lost";

        /// <summary>Another person has taken the patient's place (M10.5): the exercise pauses until the patient is back.</summary>
        public bool DifferentPerson => patient == "different";

        /// <param name="operatedSide">"L", "R", or "" for the best-seen side</param>
        public AngleSet For(string operatedSide) => operatedSide == "L" ? L : operatedSide == "R" ? R : this;
    }

    // ---------------------------------------------------------------
    // GET /api/vr/program
    // ---------------------------------------------------------------
    [Serializable]
    public class PatientInfo
    {
        public int id;
        public string code;      // the name is never sent to the VR client (DEC-027)
        public int xp;
        public int level;
        public int xpIntoLevel;
        public int xpForNext;
        public string[] badges = new string[0];
        public int streak;
    }

    [Serializable]
    public class ProgramInfo
    {
        public int id;
        public string name;
        public int[] days = new int[0];
        public int maxReps;
    }

    [Serializable]
    public class ExerciseDef
    {
        public int id;
        public string code;       // exercise type from the server LIBRARY (shoulderAbd, slr, miniSquat, ...)
        public string name;
        public string joint;
        public string measure;    // tracker angle: shoulderElev | elbowFlex | hipElev | kneeFlex | kneeExt | ankleDF | anklePF
        public string view;       // camera position: front | side
        public string position;   // start position
        public string side;       // operated side: L | R | "" = whichever the camera sees best
        public float targetAngle;
        public float tolerance;
        public float safetyMax;   // hard limit; 0 = none
        public float holdSeconds; // hold within the target band for a rep to count; 0 = none
        public int sets = 1;
        public float restSeconds;
        public int baseReps;
        public int reps;          // per set; effective reps for today (includes progression stage)
        public int stage;
        public string cue;
        public string normalRom;
        public float normalMax;
        // Exercise rules from the server LIBRARY (DEC-012); Unity never switches on `code`
        public string posture;    // standing | seated | lying | sidelying
        public string pose;       // coach / figure animation (several exercises share one)
        public string direction;  // flex | ext | abd | "" (side view: flex / ext use the signed angle)
        public PostureCheck[] checks = new PostureCheck[0];

        public int TotalReps => reps * Math.Max(1, sets);
        public string CameraText => view == "front" ? "in front of you" : "at your side";
    }

    /// <summary>Posture check: the rep is invalid when <see cref="metric"/> goes over <see cref="max"/> degrees.</summary>
    [Serializable]
    public class PostureCheck
    {
        public string metric;     // trunkLean | elbowDrift | a tracker angle of the measured side (kneeFlex, hipElev, ...)
        public float max;
        public string message;
    }

    /// <summary>The patient's protocol phase. Empty name = custom program without a protocol.</summary>
    [Serializable]
    public class PhaseInfo
    {
        public int id;
        public string protocol = "";
        public string name = "";
        public string weeks = "";
        public bool vrAllowed = true;   // false = immobilization / passive phase, done with the therapist
        public string goals = "";
        public string precautions = "";
        public string romGoal = "";
    }

    [Serializable]
    public class ProgramResponse
    {
        public PatientInfo patient;
        public ProgramInfo program;
        public PhaseInfo phase = new PhaseInfo();
        public ExerciseDef[] exercises;
        public ProgressInfo progress = new ProgressInfo();   // patient's own progress page (M5.5); cached with the program
    }

    /// <summary>The patient's progress for the in-game Progress page (M5.5), from GET /api/vr/program.</summary>
    [Serializable]
    public class ProgressInfo
    {
        public RecentSession[] recent = new RecentSession[0];
        public int totalSessions;
        public int completeSessions;
        public BadgeInfo[] badges = new BadgeInfo[0];
    }

    [Serializable]
    public class RecentSession
    {
        public string started_at;
        public string status;       // complete | incomplete
        public int points;
        public int stars;
        public int valid;
        public int attempts;
        public float accuracy;
    }

    [Serializable]
    public class BadgeInfo
    {
        public string code;
        public string name;
        public bool earned;
    }

    // ---------------------------------------------------------------
    // POST /api/vr/sessions
    // ---------------------------------------------------------------
    [Serializable]
    public class ExerciseResult
    {
        public int exercise_id;
        public int target_reps;
        public int valid_reps;
        public int attempts;
        public float avg_accuracy;
        public float mean_angle_error;
        public int unsafe_reps;
        public List<string> feedback = new List<string>();
    }

    [Serializable]
    public class SessionUpload
    {
        public int patient_id;      // 0 = unknown (no program loaded); the server uses patient_code
        public string patient_code;
        public string session_uuid; // set once per session; the server ignores a repeated upload with the same id
        public string started_at;
        public string ended_at;
        public bool ended_early;
        public string input_source;
        public int points;
        public int stars;
        public int other_person_pauses;   // M10.5: times the exercise paused because someone other than the patient took over
        public int other_person_seconds;
        public List<string> badges_earned = new List<string>();
        public List<ExerciseResult> exercises = new List<ExerciseResult>();
        public List<RepEvent> rep_events = new List<RepEvent>();
    }

    /// <summary>
    /// One rep attempt, valid or not (M4.5). Therapist rep labels and goniometer readings are joined to these
    /// by session_uuid + exercise + attempt, so the evaluation uses real per-rep data.
    /// </summary>
    [Serializable]
    public class RepEvent
    {
        public int exercise_id;
        public int attempt;           // 1, 2, 3 ... within this exercise
        public int set;               // 1-based set the attempt belonged to
        public string side;           // operated side: L | R | "" = best-seen side
        public float t;               // seconds since this exercise started
        public float peak;
        public float error;
        public int accuracy;
        public bool valid;
        public string fault;          // posture problem, or ""
        public bool past_safety_max;
        public bool too_fast;
        public bool held = true;      // hold exercises: held long enough
    }

    [Serializable]
    public class SessionResponse
    {
        public int session_id;
        public string status;
        public string[] notes = new string[0];
        public string[] new_badges = new string[0];
        public bool counted = true;  // false for a practice (non-webcam) session, M7.1
        public int xpGained;        // structured rewards for the summary screen (M5.5)
        public int levelBefore;
        public int levelAfter;
        public PatientInfo patient;
    }

    // ---------------------------------------------------------------
    // Result of one repetition (Exercise Evaluation Module output)
    // ---------------------------------------------------------------
    public struct RepResult
    {
        public float peak;        // highest angle reached in this rep
        public float error;       // |target - peak|  (Angle Error, Section 3.9.1)
        public int accuracy;      // 0..100
        public bool valid;
        public bool overshoot;
        public bool pastSafetyMax;
        public float held;        // longest hold inside the target band, seconds
        public bool heldLongEnough;
        public string fault;      // posture error, or null
        public float duration;    // seconds taken for the repetition cycle
        public bool tooFast;      // completed too rapidly (rushed / jerking motion)
    }
}
