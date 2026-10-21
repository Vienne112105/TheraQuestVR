using UnityEngine;

namespace TheraQuest
{
    public enum InputSource { Webcam, Keyboard, Simulated }

    /// <summary>
    /// Gives the rest of the system one angle reading per frame, whatever the source:
    ///   Webcam    - live angles from tracker.py (MotionReceiver), for the exercise's operated side
    ///   Keyboard  - arrow keys / thumbstick move the limb (testing without a camera)
    ///   Simulated - an automatic patient with natural variation and occasional form errors
    /// Also hosts the posture checks of the Error Detector.
    /// </summary>
    public class MotionInput : MonoBehaviour
    {
        public MotionReceiver receiver;
        public InputSource source = InputSource.Webcam;

        // Posture limits come with each exercise from the server LIBRARY (ExerciseDef.checks, DEC-012).

        [Header("Smoothing")]
        [Range(0f, 0.95f)] public float smoothing = 0.6f;

        public float Angle { get; private set; }
        public float AngularSpeed { get; private set; }
        public string Fault { get; private set; }
        public bool HasReading { get; private set; }
        /// <summary>Side being measured: the exercise's operated side, or the side the camera sees best.</summary>
        public string MeasuredSide { get; private set; }

        float keyboardAngle;
        float simTime, simPeak = 90f, simPeriod, simPlateau;
        bool simStarted, simFault;

        public void NextSource()
        {
            source = (InputSource)(((int)source + 1) % 3);
            keyboardAngle = 0f;
        }

        /// <summary>Corrective message of the exercise's first posture check (null = no check).</summary>
        public static string FaultText(ExerciseDef ex) =>
            ex != null && ex.checks != null && ex.checks.Length > 0 && ex.checks[0] != null ? ex.checks[0].message : null;

        /// <summary>Message of the first posture check the packet breaks, or null. Not-visible values (-1) never break one.</summary>
        public static string PostureFault(ExerciseDef ex, MotionPacket p, AngleSet s)
        {
            if (ex == null || ex.checks == null || p == null || s == null) return null;
            foreach (var c in ex.checks)
                if (c != null && CheckValue(c.metric, p, s) > c.max) return c.message;
            return null;
        }

        static float CheckValue(string metric, MotionPacket p, AngleSet s)
        {
            switch (metric)
            {
                case "trunkLean": return p.trunkLean;
                // Upper arm away from the trunk; for one chosen side that is the side's shoulder elevation
                case "elbowDrift": return s == p ? p.elbowDrift : s.shoulderElev;
                default: return s.Get(metric);
            }
        }

        /// <summary>
        /// The exercise's angle from one side's tracker reading, or -1 when it can't be measured.
        /// In side view, flexion / extension exercises use the signed elevation (M4.4 / M4.6): an extension
        /// exercise scores only movement behind the trunk, and a flexion exercise scores nothing behind it.
        /// </summary>
        public static float MeasuredAngle(ExerciseDef ex, AngleSet s)
        {
            string measure = ex != null && !string.IsNullOrEmpty(ex.measure) ? ex.measure : "shoulderElev";
            float a = s.Get(measure);
            if (a < 0f || ex == null || ex.view != "side") return a;
            if (ex.direction != "flex" && ex.direction != "ext") return a;
            float signed = measure == "shoulderElev" ? s.shoulderElevSigned
                         : measure == "hipElev" ? s.hipElevSigned : AngleSet.SignedInvalid;
            if (measure != "shoulderElev" && measure != "hipElev") return a;
            if (ex.direction == "ext") return AngleSet.SignedValid(signed) ? Mathf.Max(0f, -signed) : -1f;
            return AngleSet.SignedValid(signed) && signed < 0f ? 0f : a;
        }

        public void Sample(ExerciseDef ex, float dt)
        {
            float raw = 0f;
            Fault = null;
            HasReading = true;
            float target = ex != null ? ex.targetAngle : 90f;

            switch (source)
            {
                case InputSource.Webcam:
                    var p = receiver != null ? receiver.Latest : null;
                    var s = p?.For(ex != null ? ex.side : "");
                    MeasuredSide = ex != null && !string.IsNullOrEmpty(ex.side) ? ex.side : p?.side;
                    float measured = p != null && s != null ? MeasuredAngle(ex, s) : -1f;
                    if (receiver == null || !receiver.IsReceiving || p == null || !p.visible || measured < 0f)
                    {
                        HasReading = false;
                        return;
                    }
                    raw = measured;
                    Fault = PostureFault(ex, p, s);
                    break;

                case InputSource.Keyboard:
                    keyboardAngle = Mathf.Clamp(keyboardAngle + InputHelper.AngleAxis * 70f * dt, 0f, 170f);
                    raw = keyboardAngle;
                    break;

                case InputSource.Simulated:
                    // One rep = rise, hold at the peak, lower. Each rep gets a new peak and maybe a fault,
                    // a short hold, or (rarely) a movement past the safety max.
                    const float rise = 1.2f;
                    simTime += dt;
                    if (!simStarted || simTime >= simPeriod)
                    {
                        simStarted = true;
                        simTime = 0f;
                        float tol = ex != null ? ex.tolerance : 10f;
                        float noise = (Random.value + Random.value + Random.value - 1.5f) * tol * 1.4f;
                        simPeak = Mathf.Clamp(target + noise, 5f, 170f);
                        if (ex != null && ex.safetyMax > 0f && Random.value < 0.04f) simPeak = ex.safetyMax + 5f;
                        simFault = FaultText(ex) != null && Random.value < 0.12f;
                        float hold = ex != null ? ex.holdSeconds : 0f;
                        simPlateau = hold > 0f ? (Random.value < 0.1f ? hold * 0.5f : hold + 0.4f) : 0.15f;
                        simPeriod = rise * 2f + simPlateau;
                    }
                    float k = simTime < rise ? Ease(simTime / rise)
                            : simTime < rise + simPlateau ? 1f
                            : Ease(1f - (simTime - rise - simPlateau) / rise);
                    raw = simPeak * k;
                    if (simFault && simTime > rise * 0.7f && simTime < rise + simPlateau) Fault = FaultText(ex);
                    break;
            }

            float prev = Angle;
            float sm = source == InputSource.Webcam ? smoothing : 0f;
            Angle = Mathf.Lerp(raw, Angle, sm);
            AngularSpeed = dt > 1e-4f ? Mathf.Abs(Angle - prev) / dt : 0f;
        }

        static float Ease(float x) => 0.5f - 0.5f * Mathf.Cos(Mathf.Clamp01(x) * Mathf.PI);

        public string SourceLabel => source == InputSource.Webcam ? "webcam" : source == InputSource.Keyboard ? "keyboard" : "simulated";
    }
}
