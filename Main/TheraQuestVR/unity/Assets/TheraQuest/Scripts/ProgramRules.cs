using System.Collections.Generic;
using UnityEngine;

namespace TheraQuest
{
    /// <summary>
    /// Checks a program from the server (or the offline cache) before a session uses it (M4.3).
    /// An exercise the evaluator can't score is dropped with a warning; out-of-range numbers are clamped,
    /// so a bad prescription can't freeze a session (target 0), divide by zero (tolerance 0) or finish
    /// without any reps (reps 0).
    /// </summary>
    public static class ProgramRules
    {
        public static void Clean(ProgramResponse p)
        {
            if (p.patient == null) p.patient = new PatientInfo();
            if (p.program == null) p.program = new ProgramInfo();
            if (p.phase == null) p.phase = new PhaseInfo();
            var kept = new List<ExerciseDef>();
            foreach (var e in p.exercises ?? new ExerciseDef[0])
            {
                string why = Problem(e);
                if (why != null)
                {
                    Debug.LogWarning($"[TheraQuest] Skipping exercise '{e?.name}': {why}. Ask the therapist to fix it on the dashboard.");
                    continue;
                }
                Normalize(e);
                kept.Add(e);
            }
            p.exercises = kept.ToArray();
        }

        /// <summary>Why an exercise can't be used, or null when it can.</summary>
        public static string Problem(ExerciseDef e)
        {
            if (e == null) return "missing";
            if (!(e.targetAngle > 0f)) return "target angle must be above 0°";
            return null;
        }

        public static void Normalize(ExerciseDef e)
        {
            e.tolerance = Mathf.Max(1f, e.tolerance);
            e.reps = Mathf.Max(1, e.reps);
            e.sets = Mathf.Max(1, e.sets);
            e.holdSeconds = Mathf.Max(0f, e.holdSeconds);
            e.restSeconds = Mathf.Max(0f, e.restSeconds);
            e.safetyMax = Mathf.Max(0f, e.safetyMax);
            string side = (e.side ?? "").Trim().ToUpperInvariant();
            e.side = side == "L" || side == "R" ? side : "";
        }
    }
}
