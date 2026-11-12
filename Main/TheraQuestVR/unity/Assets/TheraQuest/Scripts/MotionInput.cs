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
        /// <summary>
        /// The angle to draw the patient's limb at. It follows <see cref="Angle"/>, except that while the tracker can't
        /// verify the joint it may use the tracker's estimate. Display only: scoring reads <see cref="Angle"/> and
        /// <see cref="HasReading"/>, never this (DEC-022).
        /// </summary>
        public float DisplayAngle { get; private set; }
        /// <summary>Degrees the live limb leans out of the exercise's plane (M6.4, webcam only). Display only.</summary>
        public float DisplayTilt { get; private set; }
        /// <summary>Still measuring the patient's resting position for this exercise (M6.5): counting waits.</summary>
        public bool Calibrating { get; private set; }

        readonly RestBaseline rest = new RestBaseline();
        readonly DropoutFilter dropout = new DropoutFilter();
        string restFor;
        /// <summary>Side being measured: the exercise's operated side, or the side the camera sees best.</summary>
        public string MeasuredSide { get; private set; }

        float keyboardAngle;
        float simTime, simPeak = 90f, simPeriod, simPlateau;
        bool simStarted, simFault;
        bool hadReading = true;

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

        /// <summary>True when the exercise moves one limb (the guide draws one limb for it).</summary>
        public static bool OneLimb(ExerciseDef ex) =>
            ex != null && FirstPersonMath.Limbs(FigureVisualizer.PoseOf(ex), 1, 0f).Length == 1;

        /// <summary>
        /// Side-on, which side to measure for an exercise with no operated side (M6.5). With the legs (or arms) one
        /// behind the other the tracker often swaps which is left and which is right, or snaps both onto the near one,
        /// so a side picked once can't be trusted. For an exercise moving one limb, the moving limb is the one reading
        /// the larger angle: the still one stays near its resting angle whatever it is labelled. Null = the tracker's side.
        /// </summary>
        public static string MovingSide(ExerciseDef ex, MotionPacket p)
        {
            if (p == null || !OneLimb(ex)) return null;
            float l = MeasuredAngle(ex, p.L), r = MeasuredAngle(ex, p.R);
            if (l < 0f && r < 0f) return null;
            return l >= r ? "L" : "R";
        }

        /// <summary>The tracker's estimate of the exercise's angle for display, or -1 when it has none.</summary>
        public static float EstimatedAngle(ExerciseDef ex, MotionPacket p)
        {
            if (p == null) return -1f;
            string side = ex != null && !string.IsNullOrEmpty(ex.side) ? ex.side : p.side;
            var est = side == "L" ? p.estL : side == "R" ? p.estR : null;
            return est != null ? MeasuredAngle(ex, est) : -1f;
        }

        /// <summary>The live limb's lean out of the exercise's plane from the packet's 3D limb directions, or NaN without one.</summary>
        public static float TiltFrom(ExerciseDef ex, MotionPacket p, string side)
        {
            if (ex == null || p == null) return float.NaN;
            string pose = FigureVisualizer.PoseOf(ex);
            if (FirstPersonMath.PlaneNormal(pose, 1) == Vector3.zero) return 0f;
            var dirs = side == "L" ? p.dirL : side == "R" ? p.dirR : null;
            if (dirs == null || !dirs.TryGet(FirstPersonMath.MovesLeg(pose), out var dir)) return float.NaN;
            return FirstPersonMath.OutOfPlane(pose, side == "L" ? -1 : 1, dir);
        }

        public void Sample(ExerciseDef ex, float dt)
        {
            float raw = 0f;
            Fault = null;
            HasReading = true;
            float target = ex != null ? ex.targetAngle : 90f;
            if (source != InputSource.Webcam) { DisplayTilt = 0f; Calibrating = false; }

            switch (source)
            {
                case InputSource.Webcam:
                    var p = receiver != null ? receiver.Latest : null;
                    string key = ex != null ? ex.code + "|" + ex.side : "";
                    if (restFor != key) { rest.Reset(ex); dropout.Reset(); restFor = key; }
                    string useSide = ex != null && !string.IsNullOrEmpty(ex.side) ? ex.side
                                   : p != null && p.visible && p.setup != null && p.setup.view == "side" ? MovingSide(ex, p) : null;
                    var s = p?.For(useSide ?? "");
                    MeasuredSide = useSide ?? p?.side;
                    float tilt = TiltFrom(ex, p, MeasuredSide);
                    if (!float.IsNaN(tilt)) DisplayTilt = tilt;   // none sent: the limb keeps its lean
                    float measured = p != null && s != null ? MeasuredAngle(ex, s) : -1f;
                    if (receiver == null || !receiver.IsReceiving || p == null || !p.visible || measured < 0f)
                    {
                        HasReading = false;
                        hadReading = false;
                        dropout.Reset();
                        float estimate = receiver != null && receiver.IsReceiving ? EstimatedAngle(ex, p) : -1f;
                        DisplayAngle = estimate >= 0f ? estimate : Angle;   // no estimate: the limb stays where it was
                        return;
                    }
                    raw = measured;
                    if (RestBaseline.Uses(ex))
                    {
                        raw = rest.Adjust(measured, dt);
                        Calibrating = !rest.Ready;
                        if (Calibrating)
                        {
                            HasReading = false;   // counting waits for the resting position
                            hadReading = false;
                            DisplayAngle = 0f;
                            return;
                        }
                    }
                    else Calibrating = false;
                    raw = dropout.Apply(raw, dt);
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
            // Back from a gap: start from the real reading. Easing from the old angle would make up values in between
            float sm = source == InputSource.Webcam && hadReading ? smoothing : 0f;
            hadReading = true;
            Angle = Mathf.Lerp(raw, Angle, sm);
            DisplayAngle = Angle;
            AngularSpeed = dt > 1e-4f ? Mathf.Abs(Angle - prev) / dt : 0f;
        }

        static float Ease(float x) => 0.5f - 0.5f * Mathf.Cos(Mathf.Clamp01(x) * Mathf.PI);

        public string SourceLabel => source == InputSource.Webcam ? "webcam" : source == InputSource.Keyboard ? "keyboard" : "simulated";
    }
    /// <summary>
    /// The patient's own resting angle in the exercise's start position (M6.5: hip abduction first, then every webcam
    /// exercise). At rest the webcam rarely reads exactly 0, so the exercise first waits for the angle to hold
    /// steady for StillSeconds, takes that as the resting position, and from then on measures the movement above it;
    /// a rep ends when the leg comes back near it. Every later still moment near the resting position refreshes it.
    /// </summary>
    public class RestBaseline
    {
        public const float StillSeconds = 1f, StillSpread = 4f, MaxRest = 25f, RefreshBand = 8f;

        float winTime, winMin, winMax, winSum;
        int winN;

        public bool Ready { get; private set; }
        public float Value { get; private set; }

        /// <summary>Highest angle taken as resting for this baseline (MaxRest unless Reset gave the exercise).</summary>
        public float Limit { get; private set; } = MaxRest;

        public static bool Uses(ExerciseDef ex) => ex != null;

        /// <summary>The highest resting angle for an exercise: never past its start line (60% of the target), never
        /// above MaxRest, and at least 10° so a small target still tolerates the webcam's resting offset.</summary>
        public static float RestLimit(ExerciseDef ex) =>
            ex == null ? MaxRest : Mathf.Min(MaxRest, Mathf.Max(10f, 0.6f * ex.targetAngle));

        public void Reset(ExerciseDef ex = null)
        {
            Limit = RestLimit(ex);
            Ready = false;
            Value = 0f;
            winN = 0;
        }

        /// <summary>Feed one measured angle; returns the angle above the resting position (0 until it is known).</summary>
        public float Adjust(float raw, float dt)
        {
            bool resting = raw <= (Ready ? Mathf.Min(Value + RefreshBand, Limit) : Limit);
            if (!resting) winN = 0;
            else
            {
                if (winN == 0 || Mathf.Max(winMax, raw) - Mathf.Min(winMin, raw) > StillSpread)
                {
                    winN = 0; winTime = 0f; winSum = 0f; winMin = winMax = raw;   // start a new still stretch here
                }
                winMin = Mathf.Min(winMin, raw);
                winMax = Mathf.Max(winMax, raw);
                winSum += raw;
                winN++;
                winTime += dt;
                if (winTime >= StillSeconds)
                {
                    Value = winSum / winN;
                    Ready = true;
                    winN = 0;
                }
            }
            return Ready ? Mathf.Max(0f, raw - Value) : 0f;
        }
    }
    /// <summary>
    /// Holds the reading through a webcam dropout (M6.5): when the legs overlap side-on, the moving leg's landmarks can
    /// snap onto the still leg for a few frames, and the angle falls by tens of degrees in one frame. No limb moves that
    /// fast (over Rate degrees a second), so such a drop keeps the last angle for up to HoldSeconds; one that lasts
    /// longer is real and is let through.
    /// </summary>
    public class DropoutFilter
    {
        public const float Drop = 25f, Rate = 600f, HoldSeconds = 0.3f;
        float last = -1f, held;

        public void Reset()
        {
            last = -1f;
            held = 0f;
        }

        public float Apply(float angle, float dt)
        {
            float fall = last - angle;
            if (last >= 0f && fall > Drop && fall / Mathf.Max(dt, 1e-4f) > Rate && held < HoldSeconds)
            {
                held += dt;
                return last;
            }
            held = 0f;
            last = angle;
            return angle;
        }
    }
}
