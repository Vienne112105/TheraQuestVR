using UnityEngine;

namespace TheraQuest
{
    /// <summary>
    /// The default body every patient exercises in (M5.8, DEC-021). All numbers are metres in the body's frame, measured
    /// from the eyes: +X the patient's right, +Y up, +Z forward. Pure math, unit tested.
    /// The eye height depends only on the posture, never on the patient, so everyone gets the same view (see
    /// <see cref="HeadTracking.SetEyeHeight"/>). Limb angles follow the tracker's values, as the coach's poses do.
    /// </summary>
    public static class FirstPersonMath
    {
        public const float StandingEye = 1.55f, SeatedEye = 1.15f, LyingEye = 0.25f, SideLyingEye = 0.30f;
        public const float UpperArm = 0.30f, Forearm = 0.27f, Hand = 0.09f, Thigh = 0.42f, Shin = 0.40f, Foot = 0.20f;

        /// <summary>One limb, from its top joint to the fingertips or toes.</summary>
        public struct Chain { public Vector3 root, mid, end, tip; public bool leg; }

        public static float EyeHeight(string posture)
        {
            switch (posture)
            {
                case "seated": return SeatedEye;
                case "lying": return LyingEye;
                case "sidelying": return SideLyingEye;
                default: return StandingEye;
            }
        }

        /// <summary>
        /// How far the view sits above the body's eye line. Lying down a view at eye level runs straight along the
        /// limbs, so it is lifted as if the head were raised to look at them.
        /// </summary>
        public static float ViewLift(string posture) => posture == "lying" ? 0.40f : posture == "sidelying" ? 0.25f : 0f;

        /// <summary>What to add to the tracked head height so the view sits at the default height.</summary>
        public static float HeightOffset(float wantedEye, float trackedEye) => wantedEye - trackedEye;

        /// <summary>The exercise's posture, or the one its pose implies when the server sent none.</summary>
        public static string PostureOf(ExerciseDef ex)
        {
            if (!string.IsNullOrEmpty(ex.posture)) return ex.posture;
            string pose = FigureVisualizer.PoseOf(ex);
            return pose == "kneeExt" || pose == "sitToStand" || pose == "seatedHeelRaise" ? "seated"
                 : pose == "slr" || pose == "heelSlide" || pose == "supineFlex" || pose == "anklePump" ? "lying" : "standing";
        }

        /// <summary>Exercises that move the ankle (M6.4): the view frames the foot.</summary>
        public static bool AnklePose(string pose) => pose == "anklePump" || pose == "heelRaise" || pose == "seatedHeelRaise";

        // ---- Out-of-plane live limb (M6.4, DEC-023). The webcam's angle lies in the exercise's plane; the tracker's 3D
        // limb directions show how far the limb leans out of it. Display only: the target limb and scoring never use it.
        public const float ArmDeadZone = 20f, LegDeadZone = 12f, MaxTilt = 35f;   // M6.5: 90th percentile of a resting limb

        /// <summary>
        /// The normal of the exercise's plane, pointing the way a positive lean goes (out to the side for forward and back
        /// movements, forward for sideways ones), or zero for poses whose live limb never leans.
        /// </summary>
        public static Vector3 PlaneNormal(string pose, int s)
        {
            switch (pose)
            {
                case "shoulderFlex": case "shoulderExt": case "slr": case "hipExt": case "march": return new Vector3(s, 0f, 0f);
                case "shoulderAbd": case "hipAbd": return Vector3.forward;
                case "scaption": return new Vector3(-0.5f * s, 0f, 0.866f);
                default: return Vector3.zero;
            }
        }

        public static bool MovesLeg(string pose) => pose == "slr" || pose == "hipExt" || pose == "march" || pose == "hipAbd";

        /// <summary>
        /// Degrees the limb (dir, body frame) leans out of the exercise's plane, after a dead zone (arms hang a little
        /// outside the hips, and the camera's depth is noisy) and capped at MaxTilt.
        /// </summary>
        public static float OutOfPlane(string pose, int s, Vector3 dir)
        {
            var n = PlaneNormal(pose, s);
            if (n == Vector3.zero || dir.sqrMagnitude < 1e-6f) return 0f;
            float deg = Mathf.Asin(Mathf.Clamp(Vector3.Dot(dir.normalized, n), -1f, 1f)) * Mathf.Rad2Deg;
            float lean = Mathf.Max(0f, Mathf.Abs(deg) - (MovesLeg(pose) ? LegDeadZone : ArmDeadZone));
            return Mathf.Sign(deg) * Mathf.Min(lean, MaxTilt);
        }

        /// <summary>The chain leaned deg out of the exercise's plane, turning about its top joint.</summary>
        public static Chain Tilt(Chain c, string pose, int s, float deg)
        {
            var n = PlaneNormal(pose, s);
            var v = c.mid - c.root;
            if (n == Vector3.zero || Mathf.Abs(deg) < 0.01f || v.sqrMagnitude < 1e-8f) return c;
            var inPlane = Vector3.ProjectOnPlane(v, n).normalized;
            var q = Quaternion.FromToRotation(inPlane, inPlane * Cos(deg) + n * Sin(deg));
            c.mid = c.root + q * (c.mid - c.root);
            c.end = c.root + q * (c.end - c.root);
            c.tip = c.root + q * (c.tip - c.root);
            return c;
        }

        public static bool IsLying(string posture) => posture == "lying" || posture == "sidelying";

        /// <summary>The limb ends behind the patient, out of first-person view: these exercises get the side mirror.</summary>
        public static bool BehindBody(string pose) => pose == "shoulderExt" || pose == "hipExt" || pose == "hamstringCurl";

        /// <summary>Turns the body frame into the room: lying down the feet point along +Z, with the moving side on top side-lying.</summary>
        public static Quaternion BodyFrame(string posture, int s)
        {
            if (posture == "lying") return Quaternion.Euler(-90f, 0f, 0f);
            if (posture == "sidelying") return Quaternion.LookRotation(new Vector3(-s, 0f, 0f), Vector3.back);
            return Quaternion.identity;
        }

        /// <summary>
        /// Which way the body points on the floor, from the head's own axes (degrees). Lying down the face points at the
        /// ceiling, so the top of the head gives it: the feet are opposite. Also used when looking straight down.
        /// </summary>
        public static float FlatYaw(Vector3 forward, Vector3 up, bool lying)
        {
            var dir = lying ? -up : forward;
            dir.y = 0f;
            if (dir.sqrMagnitude < 0.01f) { dir = lying ? forward : up; dir.y = 0f; }
            return dir.sqrMagnitude < 1e-6f ? 0f : Mathf.Atan2(dir.x, dir.z) * Mathf.Rad2Deg;
        }

        /// <summary>
        /// A view (yaw, pitch: positive looks down) mostly on the target, with the start toward the edge. The turn is
        /// limited: looking right along a limb that points sideways would only show its end.
        /// </summary>
        public static void Aim(Vector3 toStart, Vector3 toTarget, out float yaw, out float pitch)
        {
            var dir = (toStart.normalized * 0.35f + toTarget.normalized * 0.65f).normalized;
            yaw = Mathf.Clamp(Mathf.Atan2(dir.x, dir.z) * Mathf.Rad2Deg, -60f, 60f);
            pitch = Mathf.Clamp(-Mathf.Asin(Mathf.Clamp(dir.y, -1f, 1f)) * Mathf.Rad2Deg, -60f, 75f);
        }

        /// <summary>A few words for the coach window's arrow.</summary>
        public static string Word(string pose)
        {
            switch (pose)
            {
                case "shoulderAbd": case "hipAbd": return "Out to the side";
                case "scaption": return "Up and out";
                case "shoulderExt": case "hipExt": return "Move back";
                case "elbowFlex": return "Bend";
                case "wallPushUp": return "Lean in";
                case "slr": case "march": return "Lift";
                case "heelSlide": return "Slide in";
                case "hamstringCurl": return "Heel up";
                case "miniSquat": return "Bend knees";
                case "miniLunge": return "Lower";
                case "kneeExt": return "Straighten";
                case "sitToStand": return "Stand up";
                case "anklePump": return "Toes up";
                case "heelRaise": case "seatedHeelRaise": return "Heels up";
                default: return "Raise up";
            }
        }

        static float Sin(float deg) => Mathf.Sin(deg * Mathf.Deg2Rad);
        static float Cos(float deg) => Mathf.Cos(deg * Mathf.Deg2Rad);
        static Vector3 Sag(float a) => new Vector3(0f, -Cos(a), Sin(a));                     // swing forward and up
        static Vector3 Out(int s, float a) => new Vector3(s * Sin(a), -Cos(a), 0f);          // out to the side
        static Vector3 Scap(int s, float a) => new Vector3(s * Sin(a) * 0.866f, -Cos(a), Sin(a) * 0.5f); // 30° forward of the side

        static Chain Arm(int s, Vector3 upper, Vector3 fore)
        {
            var c = new Chain { root = new Vector3(s * 0.19f, -0.24f, -0.06f) };
            c.mid = c.root + upper * UpperArm;
            c.end = c.mid + fore * Forearm;
            c.tip = c.end + fore * Hand;
            return c;
        }

        /// <param name="ankle">foot angle from a right angle to the shin: + toes down (plantarflexion), - toes up</param>
        static Chain Leg(int s, Vector3 thigh, Vector3 shin, Vector3 shift = default, float ankle = 0f)
        {
            var c = new Chain { leg = true, root = new Vector3(s * 0.10f, -0.72f, -0.06f) + shift };
            c.mid = c.root + thigh * Thigh;
            c.end = c.mid + shin * Shin;
            // Toes forward at a right angle to the shin, or up when the shin itself points forward
            var toes = Vector3.ProjectOnPlane(Vector3.forward, shin);
            // M6.5: a shin swung behind the knee (hamstring curl) keeps the foot at a right angle to it, toes toward
            // the floor; projecting "forward" there shrinks to nothing at 90 degrees and flipped the toes up.
            if (shin.z < 0f) toes = Vector3.Cross(shin.normalized, Vector3.right);
            else if (toes.sqrMagnitude < 0.04f) toes = Vector3.ProjectOnPlane(Vector3.up, shin);
            toes = toes.normalized * Cos(ankle) + shin.normalized * Sin(ankle);
            c.tip = c.end + toes.normalized * Foot;
            return c;
        }

        /// <summary>The limbs an exercise moves at angle a: the first is the operated side (s = +1 right, -1 left).</summary>
        public static Chain[] Limbs(string pose, int s, float a)
        {
            a = Mathf.Clamp(a, 0f, 180f);
            int o = -s;
            switch (pose)
            {
                case "shoulderAbd": return new[] { Arm(s, Out(s, Mathf.Max(a, 8f)), Out(s, Mathf.Max(a, 8f))) };
                case "scaption": return new[] { Arm(s, Scap(s, Mathf.Max(a, 8f)), Scap(s, Mathf.Max(a, 8f))) };
                case "supineFlex": return new[] { Arm(s, Sag(a), Sag(a)), Arm(o, Sag(a), Sag(a)) };   // both hands on the cane
                case "shoulderExt": return new[] { Arm(s, Sag(-a), Sag(-a)) };
                case "elbowFlex": return new[] { Arm(s, Sag(0f), Sag(a)) };
                case "wallPushUp":                                                                    // hands stay on the wall
                {
                    Vector3 up = Sag(90f - a / 2f), fore = Sag(90f + a / 2f);
                    return new[] { Arm(s, up, fore), Arm(o, up, fore) };
                }
                case "hipAbd": return new[] { Leg(s, Out(s, a), Out(s, a)) };
                case "hipExt": return new[] { Leg(s, Sag(-a), Sag(-a)) };
                case "slr": return new[] { Leg(s, Sag(a), Sag(a)) };
                case "march": return new[] { Leg(s, Sag(a), Sag(0f)) };                               // shin stays vertical
                case "heelSlide": return new[] { Leg(s, Sag(a / 2f), Sag(-a / 2f)) };                 // heel stays on the mat
                case "hamstringCurl": return new[] { Leg(s, Sag(0f), Sag(-a)) };
                case "miniSquat":                                                                     // feet stay on the floor
                {
                    var drop = Vector3.up * (Thigh + Shin) * (Cos(a / 2f) - 1f);
                    return new[] { Leg(s, Sag(a / 2f), Sag(-a / 2f), drop), Leg(o, Sag(a / 2f), Sag(-a / 2f), drop) };
                }
                case "miniLunge":
                    return new[] { Leg(s, Sag(a * 0.55f), Sag(-a * 0.45f), Vector3.up * (Thigh + Shin) * (Cos(a / 2f) - 1f) * 0.8f) };
                case "kneeExt": return new[] { Leg(s, Sag(90f), Sag(Mathf.Min(a, 90f))) };            // seated, 0 = knee at 90°
                case "sitToStand":                                                                    // 0 = seated, 90 = standing
                {
                    float f = 90f - Mathf.Min(a, 90f);
                    var rise = new Vector3(0f, Thigh * Cos(f), Thigh * (1f - Sin(f)));
                    return new[] { Leg(s, Sag(f), Sag(0f), rise), Leg(o, Sag(f), Sag(0f), rise) };
                }
                // Ankles (M6.4): the leg holds still and the foot turns. The angle is from a right angle to the shin
                case "anklePump": return new[] { Leg(s, Sag(0f), Sag(0f), default, -Mathf.Min(a, 60f)) };          // lying, toes up
                case "seatedHeelRaise": return new[] { Leg(s, Sag(90f), Sag(0f), default, Mathf.Min(a, 80f)) };   // toes stay down
                case "heelRaise":                                                                                // both heels up
                {
                    float f = Mathf.Min(a, 80f);
                    return new[] { Leg(s, Sag(0f), Sag(0f), default, f), Leg(o, Sag(0f), Sag(0f), default, f) };
                }
                default: return new[] { Arm(s, Sag(a), Sag(a)) };                                     // shoulderFlex
            }
        }
    }

    /// <summary>
    /// First-person exercise guide (M5.8, DEC-021). Two see-through limbs extend from the patient's default body:
    ///   target - stays at the prescribed angle, and is the exercise's threshold (it replaces the old gold marker)
    ///   live   - follows the tracker's angle, because the real arm can't be seen in a headset
    /// The patient moves the live limb into the target; both turn green there. The webcam gives one angle in the
    /// exercise's plane; for one limb swinging from the shoulder or hip the live limb also leans out of that plane, from
    /// the tracker's 3D limb direction (M6.4, display only). Limbs that end behind the patient also show in a side mirror, drawn by
    /// a small camera that alone sees a plain head and body (the mirror layer). Added at runtime by SessionManager.
    /// </summary>
    public class FirstPersonGuide : MonoBehaviour
    {
        public const int HologramLayer = 30, MirrorOnlyLayer = 29;

        static readonly Color TargetColor = new Color(0.35f, 0.8f, 1f, 0.3f);
        static readonly Color LiveColor = new Color(0.97f, 0.98f, 1f, 0.55f);

        sealed class LimbView
        {
            public Transform upper, lower, end;
            public GameObject[] parts;
        }

        Transform root, mirrorBody;
        Material targetMat, liveMat, bodyMat;
        readonly LimbView[] target = new LimbView[2], live = new LimbView[2];
        Camera mirrorCam;
        RenderTexture mirrorTex;
        string pose = "";
        int side = 1;
        bool behind, shown;
        float liveAngle, liveVel, liveTilt, tiltVel;

        /// <summary>The side view while it is needed, else null.</summary>
        public Texture MirrorTexture => shown && behind ? mirrorTex : null;

        /// <summary>The see-through material, or a plain transparent one when the shader is missing.</summary>
        public static Material HologramMaterial(Color c, float rim = 1.5f, float lines = 30f, bool alwaysOnTop = false)
        {
            var shader = Resources.Load<Shader>("Shaders/Hologram");
            if (shader == null) return FigureVisualizer.MakeMat(c, true);
            var m = new Material(shader) { color = c };
            m.SetFloat("_Rim", rim);
            m.SetFloat("_Lines", lines);
            m.SetFloat("_ZTest", (float)(alwaysOnTop ? UnityEngine.Rendering.CompareFunction.Always : UnityEngine.Rendering.CompareFunction.LessEqual));
            return m;
        }

        void Awake()
        {
            root = new GameObject("First-person body").transform;
            targetMat = HologramMaterial(TargetColor);
            liveMat = HologramMaterial(LiveColor);
            bodyMat = HologramMaterial(new Color(0.75f, 0.85f, 0.95f, 0.18f), 1f, 0f);
            for (int i = 0; i < 2; i++)
            {
                target[i] = MakeLimb(targetMat, "Target limb " + i);
                live[i] = MakeLimb(liveMat, "Live limb " + i);
            }
            BuildMirror();
            root.gameObject.SetActive(false);
        }

        void OnDestroy()
        {
            if (root != null) Destroy(root.gameObject);
            if (mirrorTex != null) mirrorTex.Release();
        }

        LimbView MakeLimb(Material mat, string name)
        {
            var holder = new GameObject(name).transform;
            holder.SetParent(root, false);
            var v = new LimbView
            {
                upper = Part(PrimitiveType.Capsule, holder, mat, HologramLayer),
                lower = Part(PrimitiveType.Capsule, holder, mat, HologramLayer),
                end = Part(PrimitiveType.Capsule, holder, mat, HologramLayer),
            };
            v.parts = new[] { v.upper.gameObject, v.lower.gameObject, v.end.gameObject };
            return v;
        }

        static Transform Part(PrimitiveType type, Transform parent, Material mat, int layer)
        {
            var go = GameObject.CreatePrimitive(type);
            Destroy(go.GetComponent<Collider>());
            go.layer = layer;
            go.transform.SetParent(parent, false);
            var r = go.GetComponent<Renderer>();
            r.sharedMaterial = mat;
            r.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            r.receiveShadows = false;
            return go.transform;
        }

        void BuildMirror()
        {
            mirrorBody = new GameObject("Mirror body").transform;
            mirrorBody.SetParent(root, false);
            var head = Part(PrimitiveType.Sphere, mirrorBody, bodyMat, MirrorOnlyLayer);
            head.localPosition = new Vector3(0f, 0.02f, -0.08f);
            head.localScale = Vector3.one * 0.22f;
            var torso = Part(PrimitiveType.Capsule, mirrorBody, bodyMat, MirrorOnlyLayer);
            torso.localPosition = new Vector3(0f, -0.48f, -0.06f);
            torso.localScale = new Vector3(0.3f, 0.35f, 0.2f);
            foreach (int s in new[] { -1, 1 })
            {
                var leg = Part(PrimitiveType.Capsule, mirrorBody, bodyMat, MirrorOnlyLayer);
                leg.localPosition = new Vector3(s * 0.1f, -1.13f, -0.06f);
                leg.localScale = new Vector3(0.13f, 0.41f, 0.13f);
            }

            mirrorTex = new RenderTexture(512, 512, 16) { antiAliasing = 4, name = "Side mirror" };
            mirrorCam = new GameObject("Side mirror camera").AddComponent<Camera>();
            mirrorCam.transform.SetParent(root, false);
            mirrorCam.targetTexture = mirrorTex;
            mirrorCam.cullingMask = (1 << HologramLayer) | (1 << MirrorOnlyLayer);
            mirrorCam.clearFlags = CameraClearFlags.SolidColor;
            mirrorCam.backgroundColor = UIKit.Navy;
            mirrorCam.orthographic = true;
            mirrorCam.orthographicSize = 0.95f;
            mirrorCam.nearClipPlane = 0.05f;
            mirrorCam.farClipPlane = 6f;
            if (UnityEngine.Rendering.GraphicsSettings.currentRenderPipeline == null) mirrorCam.stereoTargetEye = StereoTargetEyeMask.None;   // URP ignores it (and warns)
            mirrorCam.enabled = false;
        }

        /// <summary>Puts the body where the patient is now (eyes at eye, feet toward yaw) and picks the exercise's limbs.</summary>
        public void Anchor(ExerciseDef ex, Vector3 eye, float yaw)
        {
            pose = FigureVisualizer.PoseOf(ex);
            side = ex.side == "L" ? -1 : 1;   // "" = right; first person is never mirrored
            behind = FirstPersonMath.BehindBody(pose);
            string posture = FirstPersonMath.PostureOf(ex);
            root.SetPositionAndRotation(eye, Quaternion.Euler(0f, yaw, 0f) * FirstPersonMath.BodyFrame(posture, side));
            var chains = FirstPersonMath.Limbs(pose, side, ex.targetAngle);
            for (int i = 0; i < 2; i++)
            {
                Place(target[i], chains, i);
                foreach (var p in live[i].parts) p.SetActive(i < chains.Length);
            }
            // Looking from the operated side at the body's middle (the mirror only appears for standing exercises)
            var cam = mirrorCam.transform;
            cam.localPosition = new Vector3(side * 2.5f, -0.72f, 0f);
            cam.localRotation = Quaternion.LookRotation(new Vector3(-side, 0f, 0f), Vector3.up);
            liveAngle = 0f;
            liveVel = 0f;
            liveTilt = 0f;
            tiltVel = 0f;
        }

        /// <summary>Room points the view should frame, from the start of the movement to the target.</summary>
        public void AimPoints(ExerciseDef ex, out Vector3 start, out Vector3 goal)
        {
            start = AimPoint(0f);
            goal = AimPoint(ex.targetAngle);
        }

        Vector3 AimPoint(float angle)
        {
            var c = FirstPersonMath.Limbs(pose, side, angle)[0];
            // Ankles: the foot; other legs: between knee and ankle (a squat's feet barely move); arms: the hand
            if (FirstPersonMath.AnklePose(pose)) return root.TransformPoint((c.end + c.tip) / 2f);
            return root.TransformPoint(c.leg ? (c.mid + c.end) / 2f : c.tip);
        }

        /// <param name="tilt">degrees the live limb leans out of the exercise's plane (display only, M6.4)</param>
        public void Show(ExerciseDef ex, float angle, Tone tone, float tilt = 0f)
        {
            if (!shown) { shown = true; root.gameObject.SetActive(true); liveAngle = angle; liveTilt = tilt; }
            mirrorCam.enabled = behind;
            float dt = Time.deltaTime;   // 0 while paused: everything holds still
            liveAngle = Mathf.SmoothDamp(liveAngle, angle, ref liveVel, 0.06f, Mathf.Infinity, Mathf.Max(dt, 1e-5f));   // M6.5: the tracker smooths now
            liveTilt = Mathf.SmoothDamp(liveTilt, tilt, ref tiltVel, 0.2f, Mathf.Infinity, Mathf.Max(dt, 1e-5f));
            var chains = FirstPersonMath.Limbs(pose, side, liveAngle);
            chains[0] = FirstPersonMath.Tilt(chains[0], pose, side, liveTilt);
            for (int i = 0; i < chains.Length; i++) Place(live[i], chains, i);
            var c = FeedbackManager.ToneColor(tone);
            targetMat.color = tone == Tone.Good ? new Color(c.r, c.g, c.b, 0.45f) : TargetColor;
            liveMat.color = tone == Tone.Neutral ? LiveColor : new Color(c.r, c.g, c.b, 0.65f);
        }

        public void Hide()
        {
            if (!shown) return;
            shown = false;
            mirrorCam.enabled = false;
            root.gameObject.SetActive(false);
        }

        static void Place(LimbView v, FirstPersonMath.Chain[] chains, int i)
        {
            bool on = i < chains.Length;
            foreach (var p in v.parts) p.SetActive(on);
            if (!on) return;
            var c = chains[i];
            Segment(v.upper, c.root, c.mid, c.leg ? 0.13f : 0.085f);
            Segment(v.lower, c.mid, c.end, c.leg ? 0.10f : 0.07f);
            Segment(v.end, c.end, c.tip, c.leg ? 0.08f : 0.065f);
        }

        /// <summary>A capsule (2 units tall, 1 wide) between two points of the body frame.</summary>
        static void Segment(Transform t, Vector3 a, Vector3 b, float width)
        {
            var d = b - a;
            t.localPosition = (a + b) / 2f;
            t.localRotation = Quaternion.FromToRotation(Vector3.up, d);
            t.localScale = new Vector3(width, Mathf.Max(width, d.magnitude + width * 0.5f) / 2f, width);
        }
    }
}
