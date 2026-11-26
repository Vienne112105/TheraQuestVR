using UnityEngine;

namespace TheraQuest
{
    /// <summary>
    /// A mirror "coach" figure built from primitives (no 3D assets needed).
    /// It copies the patient's measured angle in real time and shows a translucent
    /// ghost limb at the therapist's target angle, coloured by the live feedback tone.
    /// Each exercise's pose, posture (standing, seated on a chair, lying on the mat) and camera
    /// view come from the server LIBRARY (DEC-012); several exercises share one pose. The figure
    /// is mirrored when the operated side is the left.
    /// HumanoidCoach drives a rigged avatar instead and falls back to this figure when
    /// no Humanoid character is assigned.
    /// </summary>
    public class FigureVisualizer : MonoBehaviour
    {
        const float UpperArm = 0.30f, Forearm = 0.28f, Thigh = 0.42f, Shin = 0.42f;
        const float MatTop = 0.008f;   // lying exercises happen on the yoga mat on the floor (no bed)

        enum Posture { Standing, Seated, Lying, SideLying }

        Material skin, active, ghost;
        Transform body, chair, yogaMat;
        Transform rUpperArm, rForearm, rThigh, rShin, lUpperArm, lThigh, lShin;
        public enum CoachStyle { Clinical, Athletic, ZenSage, HighContrast }
        public const int StyleCount = 4;
        public CoachStyle CurrentStyle { get; private set; }
        public string CurrentStyleName => StyleName(CurrentStyle);

        public static string StyleName(CoachStyle s)
        {
            switch (s)
            {
                case CoachStyle.Athletic: return "Coach Jordan (Athletic)";
                case CoachStyle.ZenSage: return "Zen Guide (Sage)";
                case CoachStyle.HighContrast: return "High-Contrast Guide";
                default: return "Therapist Maya (Clinical)";
            }
        }

        public void CycleStyle(int step)
        {
            int n = StyleCount;
            CurrentStyle = (CoachStyle)(((int)CurrentStyle + step % n + n) % n);
            PlayerPrefs.SetInt("TheraQuest.FigureStyle", (int)CurrentStyle);
            ApplyStyle(CurrentStyle);
        }

        public void ApplyStyle(CoachStyle s)
        {
            Color skinCol, actCol, ghCol;
            switch (s)
            {
                case CoachStyle.Athletic:
                    skinCol = new Color(0.24f, 0.35f, 0.50f);
                    actCol = new Color(0.98f, 0.45f, 0.22f);
                    ghCol = new Color(0.95f, 0.80f, 0.28f, 0.40f);
                    break;
                case CoachStyle.ZenSage:
                    skinCol = new Color(0.52f, 0.66f, 0.56f);
                    actCol = new Color(0.85f, 0.56f, 0.32f);
                    ghCol = new Color(0.26f, 0.78f, 0.58f, 0.35f);
                    break;
                case CoachStyle.HighContrast:
                    skinCol = new Color(0.92f, 0.92f, 0.94f);
                    actCol = new Color(1.00f, 0.92f, 0.10f);
                    ghCol = new Color(0.00f, 0.90f, 1.00f, 0.45f);
                    break;
                default: // Clinical
                    skinCol = new Color(0.62f, 0.76f, 0.74f);
                    actCol = new Color(0.94f, 0.71f, 0.24f);
                    ghCol = new Color(0.18f, 0.76f, 0.68f, 0.35f);
                    break;
            }
            if (skin != null) skin.color = skinCol;
            if (active != null) active.color = actCol;
            if (ghost != null) ghost.color = ghCol;
            foreach (var p in new[] { body, chair })
            {
                if (p == null) continue;
                foreach (var r in p.GetComponentsInChildren<Renderer>())
                    if (ghostPivot == null || !r.transform.IsChildOf(ghostPivot)) r.sharedMaterial = skin;
            }
        }

        Transform ghostPivot, ghostSeg;
        Renderer[] activeRenderers = new Renderer[0];
        string currentCode, currentSide, currentPose;
        Posture posture;
        float shown, shownVel, popTime = 10f, mirror = 1f;   // smoothed angle, springy pop on changes

        void Awake()
        {
            CurrentStyle = (CoachStyle)PlayerPrefs.GetInt("TheraQuest.FigureStyle", 0);
            skin = MakeMat(new Color(0.62f, 0.76f, 0.74f), false);
            active = MakeMat(new Color(0.94f, 0.71f, 0.24f), false);
            ghost = MakeMat(new Color(0.18f, 0.76f, 0.68f, 0.35f), true);
            Build();
            ApplyStyle(CurrentStyle);
        }

        /// <summary>Also used by HumanoidCoach for its ghost and props.</summary>
        public static Material MakeMat(Color c, bool transparent)
        {
            // Copy the default material of a primitive, so this works in URP and Built-in projects.
            var tmp = GameObject.CreatePrimitive(PrimitiveType.Cube);
            var m = new Material(tmp.GetComponent<Renderer>().sharedMaterial) { color = c };
            if (Application.isPlaying) Destroy(tmp); else DestroyImmediate(tmp);   // edit-mode tests call this too
            if (transparent)
            {
                if (m.HasProperty("_Surface")) // URP
                {
                    m.SetFloat("_Surface", 1f);
                    m.SetFloat("_Blend", 0f);
                    m.SetOverrideTag("RenderType", "Transparent");
                    m.SetInt("_SrcBlend", (int)UnityEngine.Rendering.BlendMode.SrcAlpha);
                    m.SetInt("_DstBlend", (int)UnityEngine.Rendering.BlendMode.OneMinusSrcAlpha);
                    m.SetInt("_ZWrite", 0);
                    m.EnableKeyword("_SURFACE_TYPE_TRANSPARENT");
                    m.renderQueue = (int)UnityEngine.Rendering.RenderQueue.Transparent;
                }
                else // Standard shader
                {
                    m.SetFloat("_Mode", 3f);
                    m.SetInt("_SrcBlend", (int)UnityEngine.Rendering.BlendMode.SrcAlpha);
                    m.SetInt("_DstBlend", (int)UnityEngine.Rendering.BlendMode.OneMinusSrcAlpha);
                    m.SetInt("_ZWrite", 0);
                    m.EnableKeyword("_ALPHABLEND_ON");
                    m.renderQueue = 3000;
                }
            }
            return m;
        }

        Transform Part(PrimitiveType type, Transform parent, Vector3 localPos, Vector3 scale, Material mat, string name)
        {
            var go = GameObject.CreatePrimitive(type);
            go.name = name;
            Destroy(go.GetComponent<Collider>());
            go.transform.SetParent(parent, false);
            go.transform.localPosition = localPos;
            go.transform.localScale = scale;
            go.GetComponent<Renderer>().sharedMaterial = mat;
            return go.transform;
        }

        // A pivot with a capsule hanging "down" from it (local -Y), so rotating the pivot swings the limb.
        Transform Limb(Transform parent, Vector3 pivotPos, float length, float thickness, string name, out Transform segment)
        {
            var pivot = new GameObject(name).transform;
            pivot.SetParent(parent, false);
            pivot.localPosition = pivotPos;
            segment = Part(PrimitiveType.Capsule, pivot, new Vector3(0, -length / 2f, 0),
                           new Vector3(thickness, length / 2f, thickness), skin, name + " mesh");
            return pivot;
        }

        void Build()
        {
            body = new GameObject("Body").transform;
            body.SetParent(transform, false);
            Part(PrimitiveType.Sphere, body, new Vector3(0, 1.62f, 0), Vector3.one * 0.22f, skin, "Head");
            Part(PrimitiveType.Capsule, body, new Vector3(0, 1.25f, 0), new Vector3(0.30f, 0.30f, 0.18f), skin, "Torso");

            // Patient's right side is local -X (the figure faces the viewer, so it appears on the viewer's right).
            rUpperArm = Limb(body, new Vector3(-0.19f, 1.45f, 0), UpperArm, 0.08f, "R upper arm", out _);
            rForearm = Limb(rUpperArm, new Vector3(0, -UpperArm, 0), Forearm, 0.07f, "R forearm", out _);
            lUpperArm = Limb(body, new Vector3(0.19f, 1.45f, 0), UpperArm + Forearm, 0.08f, "L arm", out _);
            rThigh = Limb(body, new Vector3(-0.09f, 0.92f, 0), Thigh, 0.11f, "R thigh", out _);
            rShin = Limb(rThigh, new Vector3(0, -Thigh, 0), Shin, 0.09f, "R shin", out _);
            lThigh = Limb(body, new Vector3(0.09f, 0.92f, 0), Thigh, 0.11f, "L thigh", out _);
            lShin = Limb(lThigh, new Vector3(0, -Thigh, 0), Shin, 0.09f, "L shin", out _);

            chair = new GameObject("Chair").transform;
            chair.SetParent(transform, false);
            PropBuilder.Chair(chair, 0.5f, -0.2f, 0.3f);

            yogaMat = PropBuilder.YogaMat(transform, 1.9f, 0.7f);   // the figure exercises on a yoga mat

            ghostPivot = new GameObject("Target ghost").transform;
            ghostPivot.SetParent(body, false);
            ghostSeg = Part(PrimitiveType.Capsule, ghostPivot, Vector3.zero, Vector3.one, ghost, "Ghost mesh");
        }

        void SetActiveLimb(params Transform[] pivots)
        {
            foreach (var r in activeRenderers) r.sharedMaterial = skin;
            var list = new System.Collections.Generic.List<Renderer>();
            foreach (var p in pivots)
                foreach (var r in p.GetComponentsInChildren<Renderer>())
                    if (!r.transform.IsChildOf(ghostPivot)) list.Add(r);
            activeRenderers = list.ToArray();
            ApplyVisibility();
        }

        bool coachBodyVisible = true;
        public void SetBodyVisible(bool visible)
        {
            coachBodyVisible = visible;
            ApplyVisibility();
        }

        void ApplyVisibility()
        {
            if (body == null) return;
            foreach (var r in body.GetComponentsInChildren<Renderer>())
            {
                if (ghostPivot != null && r.transform.IsChildOf(ghostPivot)) continue;
                bool isActive = false;
                foreach (var ar in activeRenderers)
                {
                    if (ar == r) { isActive = true; break; }
                }
                r.enabled = coachBodyVisible || isActive;
            }
        }

        /// <summary>The exercise's pose, or one picked from the tracker angle and camera view when the server sent none.</summary>
        public static string PoseOf(ExerciseDef ex)
        {
            if (!string.IsNullOrEmpty(ex.pose)) return ex.pose;
            bool front = ex.view == "front";
            switch (ex.measure)
            {
                case "elbowFlex": return "elbowFlex";
                case "hipElev": return front ? "hipAbd" : "slr";
                case "kneeFlex": return "heelSlide";
                case "kneeExt": return "kneeExt";
                default: return front ? "shoulderAbd" : "shoulderFlex";
            }
        }

        static Posture PostureOf(ExerciseDef ex, string pose)
        {
            switch (ex.posture)
            {
                case "seated": return Posture.Seated;
                case "lying": return Posture.Lying;
                case "sidelying": return Posture.SideLying;
                case "standing": return Posture.Standing;
                default: return pose == "kneeExt" || pose == "sitToStand" || pose == "seatedHeelRaise" ? Posture.Seated
                              : pose == "slr" || pose == "heelSlide" || pose == "supineFlex" || pose == "anklePump" ? Posture.Lying : Posture.Standing;
            }
        }

        void Configure(ExerciseDef ex)
        {
            currentCode = ex.code;
            currentSide = ex.side;
            string pose = currentPose = PoseOf(ex);
            posture = PostureOf(ex, pose);
            chair.gameObject.SetActive(posture == Posture.Seated);

            // Front view for movements out to the side, side view for forward/backward ones,
            // matching where the camera should be. Left side = mirrored figure.
            bool left = ex.side == "L";
            mirror = left ? -1f : 1f;
            transform.localScale = new Vector3(mirror, 1f, 1f);
            popTime = 0f;
            transform.localRotation = Quaternion.Euler(0, ex.view == "front" ? 0f : left ? 90f : -90f, 0);

            // Lying on the back on the mat: head away from the feet, face up.
            // Side-lying: rolled onto the left side, so the right (moving) leg is on top.
            body.localRotation = posture == Posture.Lying ? Quaternion.Euler(-90, 0, 0)
                               : posture == Posture.SideLying ? Quaternion.Euler(0, 0, -90) : Quaternion.identity;
            body.localPosition = posture == Posture.Lying ? new Vector3(0, MatTop + 0.1f, 0.8f)
                               : posture == Posture.SideLying ? new Vector3(-0.92f, MatTop + 0.18f, 0f) : Vector3.zero;
            // The mat runs along the body: across the view lying down sideways, along it lying on the back
            yogaMat.localRotation = Quaternion.Euler(0f, posture == Posture.Lying ? 90f : 0f, 0f);
            yogaMat.localPosition = posture == Posture.Lying ? new Vector3(0f, 0f, 0.1f) : posture == Posture.SideLying ? new Vector3(-0.2f, 0f, 0f) : Vector3.zero;

            rUpperArm.localRotation = rForearm.localRotation = lUpperArm.localRotation = Quaternion.identity;
            rThigh.localRotation = rShin.localRotation = lThigh.localRotation = lShin.localRotation = Quaternion.identity;
            if (pose == "slr") { lThigh.localRotation = Flex(45); lShin.localRotation = Bend(90); } // other knee bent, foot flat

            if (ex.joint == "Elbow") Ghost(rUpperArm, rForearm.localPosition, Forearm);
            else if (ex.joint == "Shoulder") Ghost(body, rUpperArm.localPosition, UpperArm + Forearm);
            else if (pose == "hipAbd" || pose == "slr" || pose == "hipExt") Ghost(body, rThigh.localPosition, Thigh + Shin);
            else if (pose == "march") Ghost(body, rThigh.localPosition, Thigh);
            else if (FirstPersonMath.AnklePose(pose)) Ghost(rShin, new Vector3(0f, -Shin, 0f), 0.16f);   // the foot (M6.4)
            else Ghost(rThigh, rShin.localPosition, Shin);   // knee exercises: target knee angle

            // Colour the moving limb (done after the ghost is re-parented; SetActiveLimb skips it).
            if (ex.joint == "Elbow") SetActiveLimb(rForearm);
            else if (pose == "kneeExt" || pose == "hamstringCurl" || FirstPersonMath.AnklePose(pose)) SetActiveLimb(rShin);
            else if (ex.joint == "Hip" || ex.joint == "Knee") SetActiveLimb(rThigh);
            else SetActiveLimb(rUpperArm);
        }

        void Ghost(Transform parent, Vector3 pos, float len)
        {
            ghostPivot.SetParent(parent, false);
            ghostPivot.localPosition = pos;
            ghostSeg.localPosition = new Vector3(0, -len / 2f, 0);
            ghostSeg.localScale = new Vector3(0.05f, len / 2f, 0.05f);
        }

        // Limb rotations, in the body's frame (limbs hang along -Y, the figure faces +Z).
        static Quaternion Flex(float a) => Quaternion.Euler(-a, 0, 0);      // swing forward and up
        static Quaternion Bend(float a) => Quaternion.Euler(a, 0, 0);       // knee bend (shin swings back)
        static Quaternion Abduct(float a) => Quaternion.Euler(0, 0, -a);    // out to the side
        static Quaternion Scaption(float a) => Quaternion.AngleAxis(-a, Quaternion.Euler(0, 30, 0) * Vector3.forward);

        /// <summary>Rotation of the ghost limb at the target angle.</summary>
        static Quaternion GhostPose(string pose, float target)
        {
            switch (pose)
            {
                case "shoulderAbd": case "hipAbd": return Abduct(target);
                case "scaption": return Scaption(target);
                case "shoulderExt": case "hipExt": return Flex(-target);
                case "heelSlide": case "miniSquat": case "miniLunge": case "hamstringCurl": return Bend(target);
                case "kneeExt": case "sitToStand": return Bend(90f - target);
                case "anklePump": return Flex(90f + target);                              // the foot, from the shin
                case "heelRaise": case "seatedHeelRaise": return Flex(90f - target);
                default: return Flex(target);   // shoulderFlex, supineFlex, elbowFlex, wallPushUp, march, slr
            }
        }

        /// <summary>Moves the figure to the patient's measured angle.</summary>
        void Pose(string pose, float a)
        {
            switch (pose)
            {
                case "shoulderAbd": rUpperArm.localRotation = Abduct(a); break;
                case "scaption": rUpperArm.localRotation = Scaption(a); break;
                case "shoulderFlex": rUpperArm.localRotation = Flex(a); break;
                case "supineFlex": rUpperArm.localRotation = lUpperArm.localRotation = Flex(a); break;   // both hands on the cane
                case "shoulderExt": rUpperArm.localRotation = Flex(-a); break;
                case "elbowFlex": rForearm.localRotation = Flex(a); break;
                case "wallPushUp":                                                                   // hands stay on the wall
                    rUpperArm.localRotation = Flex(90f - a / 2f); rForearm.localRotation = Flex(a);
                    lUpperArm.localRotation = Flex(90f - a / 4f);
                    break;
                case "hipAbd": rThigh.localRotation = Abduct(a); break;
                case "hipExt": rThigh.localRotation = Flex(-a); break;
                case "hamstringCurl": rShin.localRotation = Bend(a); break;
                case "miniLunge":                                                                    // right leg in front
                    rThigh.localRotation = Flex(a * 0.55f); rShin.localRotation = Bend(a);
                    lThigh.localRotation = Flex(-15f - a * 0.2f); lShin.localRotation = Bend(a * 0.6f);
                    body.localPosition = new Vector3(0, -(Thigh + Shin) * (1f - Mathf.Cos(a / 2f * Mathf.Deg2Rad)) * 0.8f, 0);
                    break;
                case "slr": rThigh.localRotation = Flex(a); break;
                case "march": rThigh.localRotation = Flex(a); rShin.localRotation = Bend(a); break;   // shin stays vertical
                case "heelSlide":                                                                    // heel stays on the mat
                    rThigh.localRotation = Flex(a / 2f); rShin.localRotation = Bend(a); break;
                case "miniSquat":                                                                    // feet stay on the floor
                    rThigh.localRotation = lThigh.localRotation = Flex(a / 2f);
                    rShin.localRotation = lShin.localRotation = Bend(a);
                    body.localPosition = new Vector3(0, -(Thigh + Shin) * (1f - Mathf.Cos(a / 2f * Mathf.Deg2Rad)), 0);
                    break;
                case "anklePump": case "heelRaise": break;                                           // the figure has no feet: still
                case "seatedHeelRaise":
                    rThigh.localRotation = lThigh.localRotation = Flex(90);
                    rShin.localRotation = lShin.localRotation = Bend(90);
                    body.localPosition = new Vector3(0, -0.40f, 0.05f);
                    break;
                case "sitToStand":                                                                   // 0 = seated, 90 = standing
                    float hip = 90f - Mathf.Clamp(a, 0f, 90f), r = hip * Mathf.Deg2Rad;
                    rThigh.localRotation = lThigh.localRotation = Flex(hip);
                    rShin.localRotation = lShin.localRotation = Bend(hip);
                    body.localPosition = new Vector3(0, Thigh * (Mathf.Cos(r) - 1f) + 0.02f * hip / 90f, 0.47f - Thigh * Mathf.Sin(r));
                    break;
                default:                                                                             // kneeExt, seated
                    rThigh.localRotation = lThigh.localRotation = Flex(90);
                    lShin.localRotation = Bend(90);
                    rShin.localRotation = Bend(90f - a);
                    body.localPosition = new Vector3(0, -0.40f, 0.05f);
                    break;
            }
        }

        public void Show(ExerciseDef ex, float angle, Tone tone)
        {
            if (ex == null) return;
            if (ex.code != currentCode || ex.side != currentSide) { Configure(ex); shown = angle; shownVel = 0f; }
            // Smooth the live angle so tracker jitter and low frame rates don't make the figure twitch
            float dt = Time.deltaTime;
            shown = Mathf.SmoothDamp(shown, angle, ref shownVel, 0.12f, Mathf.Infinity, Mathf.Max(dt, 1e-5f));
            Pose(currentPose, shown);

            // Springy pop when the exercise changes (grows from the floor with a slight overshoot)
            popTime += Time.unscaledDeltaTime;
            float x = Mathf.Clamp01(popTime / 0.35f) - 1f;
            float k = 0.6f + 0.4f * (1f + 2.70158f * x * x * x + 1.70158f * x * x);
            transform.localScale = new Vector3(mirror * k, k, k);
            ghostPivot.localRotation = GhostPose(currentPose, ex.targetAngle);

            active.color = tone == Tone.Neutral ? new Color(0.94f, 0.71f, 0.24f) : FeedbackManager.ToneColor(tone);
            foreach (var r in activeRenderers) r.sharedMaterial = active;
        }
    }
}
