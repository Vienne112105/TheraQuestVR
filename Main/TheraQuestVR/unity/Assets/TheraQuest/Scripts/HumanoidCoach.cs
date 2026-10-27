using System.Collections.Generic;
using System.Linq;
using UnityEngine;
using UnityEngine.Animations;
using UnityEngine.Playables;
using UnityEngine.Rendering;

namespace TheraQuest
{
    /// <summary>
    /// Rigged coach for any Humanoid character (Mixamo, Ready Player Me, VRoid, ...):
    ///   Coach - stands in front of the player and demonstrates the current exercise,
    ///           moving between the start pose and the therapist's target angle.
    ///   Ghost - a translucent copy that follows the patient's live angle, tinted by the feedback tone.
    /// Bones come from Animator.GetBoneTransform (HumanBodyBones), so bone names don't matter.
    /// The Animator is switched off and the pose is written in LateUpdate: every limb is aimed at a
    /// direction in the body's frame (+Z forward, +Y up, +X the character's right), so it works
    /// whatever the rig's rest pose (T-pose or A-pose).
    /// Motions match the tracker angles (tracker/angles.py), picked by the exercise's pose from the server LIBRARY:
    ///   shoulderAbd (+ scaption), shoulderFlex (+ wallSlide, forwardReach), supineFlex (cane, both arms),
    ///   shoulderExt, elbowFlex (+ bicepsCurl), wallPushUp, hipAbd (+ side-lying), hipExt, hipFlex (slr),
    ///   march, kneeFlex (heelSlide, hamstringCurl), miniSquat (+ kneeWallSlide), miniLunge, kneeExt, sitStand.
    /// Several characters can be listed; the patient picks one on the start screen (remembered between sessions).
    /// The patient also picks the guide (remembered too):
    ///   Coach      - the coach demonstrates and the ghost follows the patient
    ///   Silhouette - no coach: only the patient's silhouette, plus a gold marker showing where the
    ///                moving limb has to reach (the target angle)
    /// With no character assigned, or none that is Humanoid, the primitive FigureVisualizer is shown.
    /// Smoothness: the live angle is smoothed (the tracker sends ~8-30 updates a second), every bone eases
    /// toward its new pose instead of snapping, the coach breathes and glances at the player, and a
    /// springy "pop" covers the jump when the exercise, posture or avatar changes.
    /// </summary>
    public class HumanoidCoach : MonoBehaviour
    {
        [System.Serializable]
        public class Option
        {
            public string name = "Coach";
            [Tooltip("A model or prefab whose Rig > Animation Type is Humanoid.")]
            public GameObject model;
        }

        [Header("Gender Coach Models")]
        [Tooltip("Female coach model (from FBX-Female folder or prefab)")]
        public GameObject femaleModel;
        [Tooltip("Male coach model (from FBX-male folder or prefab)")]
        public GameObject maleModel;

        [Tooltip("Coaches the patient can pick from on the start screen. Leave empty to use female/male or the primitive figure.")]
        public Option[] characters = new Option[0];
        [Tooltip("Shown instead when no Humanoid character is assigned.")]
        public FigureVisualizer fallback;
        [Tooltip("Optional looping idle animation (e.g. Mixamo \"Breathing Idle\", put in a CoachAnimations folder; " +
                 "empty uses Resources/CoachAnimations/Idle_Loop). " +
                 "While standing, every limb that isn't exercising plays it, so the coach breathes and shifts naturally.")]
        public AnimationClip idleClip;
        public const string DefaultIdle = "CoachAnimations/Idle_Loop";
        [Tooltip("Optional talking idle: arm and head gestures while the coach speaks. Empty uses Resources/CoachAnimations/Idle_Talking_Loop.")]
        public AnimationClip talkClip;
        public const string DefaultTalk = "CoachAnimations/Idle_Talking_Loop";
        float talkUntil = -1f, talkWeight;

        /// <summary>The coach gestures while it is speaking (lines the subtitles mark as the coach's, or unmarked ones).</summary>
        void OnSaid(string line, float seconds, string sound)
        {
            if (string.IsNullOrEmpty(sound) || sound == "Coach") talkUntil = Time.unscaledTime + Mathf.Clamp(seconds, 1.5f, 5f);
        }

        [Header("Coach demo")]
        [Tooltip("Seconds to move from the start pose to the target, and the same to come back.")]
        public float moveSeconds = 1.6f;
        [Tooltip("Pause in the start pose between demo reps.")]
        public float pauseSeconds = 0.8f;
        [Tooltip("Move the coach's opposite limb so it reads like a mirror (your right arm = its left).")]
        public bool mirror = true;

        [Header("Coach Proportions & Size")]
        [Tooltip("Target physical height of the coach in metres (default 1.72m / 5'8\"). Normalizes models regardless of Blender FBX unit scale.")]
        [SerializeField, Range(1.4f, 2.1f)] public float coachHeight = 1.72f;
        [Tooltip("Vertical foot grounding offset in metres. Adjust if shoes clip floor or float.")]
        [SerializeField, Range(-0.1f, 0.1f)] public float floorOffset = 0f;

        [Header("Ghost (patient's live angle)")]
        [Tooltip("Ghost position relative to the coach. Zero = drawn over the coach, so you match your ghost to it.")]
        public Vector3 ghostOffset = Vector3.zero;
        [Range(0.05f, 1f)] public float ghostAlpha = 0.4f;
        [Tooltip("Opacity of the patient's figure in Silhouette mode, where it is the only figure.")]
        [Range(0.05f, 1f)] public float silhouetteAlpha = 0.65f;

        [Header("Smoothness")]
        [Tooltip("Seconds the live angle takes to catch up (hides tracker jitter and low frame rates).")]
        public float angleSmoothing = 0.12f;
        [Tooltip("How quickly bones ease into each new pose (higher = snappier).")]
        public float poseEasing = 16f;
        [Tooltip("The coach glances toward the player, up to this many degrees.")]
        public float lookAtPlayer = 30f;
        [Tooltip("Metres the overlaid ghost sits behind the coach (along the view), so it only shows where the patient differs.")]
        public float ghostDepthOffset = 0.04f;

        public enum Guide { Coach, Silhouette }

        /// <summary>Show the patient's ghost over the coach (set by SessionManager: only while exercising).</summary>
        [HideInInspector] public bool ghostVisible = true;
        /// <summary>Set by SessionManager: true only while an exercise is actively running, false during menu or rest.</summary>
        [HideInInspector] public bool isSessionActive = false;
        /// <summary>
        /// Set by SessionManager: a session is under way (also during get-ready cards and between exercises). The coach
        /// then waits in the coming exercise's posture (on its chair or the mat); otherwise it stands, without props.
        /// </summary>
        [HideInInspector] public bool sessionRunning = false;

        [Tooltip("Yoga mat the coach exercises on (built at runtime). It turns and grows to fit each posture. " +
                 "The scene's old \"Exercise mat\", if any, is hidden.")]
        public Vector2 yogaMatSize = new Vector2(1.9f, 0.7f);
        [Tooltip("Metres the coach stands further back than where the scene places it (human request 2026-10-27).")]
        public float standBack = 0.6f;

        public bool Ready => built.Count > 0 || fallback != null;
        public int Count => built.Count > 0 ? built.Count : (fallback != null ? FigureVisualizer.StyleCount : 0);
        public string CoachName => built.Count > 0 ? built[selected].name : (fallback != null ? fallback.CurrentStyleName : "");
        public Guide CurrentGuide { get; private set; }
        public string GuideName => CurrentGuide == Guide.Coach ? "Coach to follow" : "Silhouette + target angle";
        public bool Has3DModels => built.Count > 0;

        enum Motion { ShoulderAbd, Scaption, ShoulderFlex, SupineFlex, ShoulderExt, ElbowFlex, WallPushUp, HipAbd, HipExt, HipFlex, March,
                      KneeFlex, MiniSquat, MiniLunge, KneeExt, SitStand }
        enum Posture { Standing, Seated, Lying, SideLying }

        static readonly Color GhostNeutral = new Color(0.18f, 0.76f, 0.68f);
        static readonly Color TargetColor = new Color(0.96f, 0.77f, 0.32f, 0.6f);
        const string PrefKey = "TheraQuest.Coach", GuideKey = "TheraQuest.Guide";
        const float MarkerWidth = 0.07f;

        sealed class Built { public string name; public GameObject root; public Figure coach, ghost; }

        readonly List<Built> built = new List<Built>();
        int selected;
        Material ghostMat, propMat, markerMat;
        Transform marker, markerLimb, markerEnd;
        ExerciseDef current;
        string currentCode, currentSide;
        Motion motion;
        Posture posture;
        int side;               // +1 = drive the character's right limbs, -1 = left
        float liveAngle, liveTarget, liveVel, demoTime, popTime = 10f;
        bool idleLayout;            // standing with no props (menu, summary, free roam)
        bool matDirty = true;       // posture or props changed: fit the mat once the coach has settled
        Transform yogaMat;
        Vector3 matPos;             // where the mat is heading (it glides there)
        Quaternion matRot = Quaternion.identity;
        Vector2 matSizeBuilt;

        void Awake()
        {
#if UNITY_EDITOR
            if (femaleModel == null || maleModel == null)
                OnValidate();
#endif
            transform.position -= transform.forward * standBack;   // the coach faces the player: step away from them
            // The yoga mat replaces the flat teal "Exercise mat" of older scenes
            var oldMat = GameObject.Find("Exercise mat");
            if (oldMat != null && oldMat.TryGetComponent<Renderer>(out var oldR)) oldR.enabled = false;
            matPos = new Vector3(transform.position.x, 0.002f, transform.position.z);
            // Bundled CC0 idles (Quaternius, see CREDITS.md); without them the hand-made breathing and sway are used.
            if (idleClip == null) idleClip = Resources.Load<AnimationClip>(DefaultIdle);
            if (talkClip == null) talkClip = Resources.Load<AnimationClip>(DefaultTalk);
            Subtitles.Said += OnSaid;
            var allOptions = new List<Option>();
            if (femaleModel != null)
                allOptions.Add(new Option { name = "Female Coach", model = femaleModel });
            if (maleModel != null)
                allOptions.Add(new Option { name = "Male Coach", model = maleModel });
            if (characters != null)
            {
                foreach (var option in characters)
                    if (option != null && option.model != null && option.model != femaleModel && option.model != maleModel)
                        allOptions.Add(option);
            }
            foreach (var option in allOptions)
                Build(option);

            if (fallback != null) fallback.gameObject.SetActive(built.Count == 0);
            CurrentGuide = PlayerPrefs.GetInt(GuideKey, 0) == 1 ? Guide.Silhouette : Guide.Coach;
            if (built.Count > 0)
            {
                BuildMarker();
                Select(Mathf.Clamp(PlayerPrefs.GetInt(PrefKey, 0), 0, built.Count - 1));
            }
            else if (fallback != null)
            {
                fallback.SetBodyVisible(CurrentGuide == Guide.Coach);
            }
        }

        /// <summary>Switches between following the coach and silhouette + target, and remembers the choice.</summary>
        public void ToggleGuide()
        {
            if (!Ready) return;
            CurrentGuide = CurrentGuide == Guide.Coach ? Guide.Silhouette : Guide.Coach;
            PlayerPrefs.SetInt(GuideKey, (int)CurrentGuide);
            if (built.Count > 0)
                Select(selected);
            else if (fallback != null)
                fallback.SetBodyVisible(CurrentGuide == Guide.Coach);
        }

        /// <summary>Holographic target area and limb showing where the motion should end.</summary>
        void BuildMarker()
        {
            markerMat = FigureVisualizer.MakeMat(TargetColor, true);
            marker = new GameObject("Holographic Target Guide").transform;
            marker.SetParent(transform, false);
            markerLimb = Figure.Primitive(PrimitiveType.Capsule, marker, markerMat);
            markerEnd = Figure.Primitive(PrimitiveType.Sphere, marker, markerMat);
            markerEnd.localScale = Vector3.one * MarkerWidth * 2.5f;

            // Translucent glowing halo sphere indicating the target tolerance area
            var haloMat = FigureVisualizer.MakeMat(new Color(TargetColor.r, TargetColor.g, TargetColor.b, 0.22f), true);
            var halo = Figure.Primitive(PrimitiveType.Sphere, markerEnd, haloMat);
            halo.name = "Target Tolerance Zone";
            halo.localScale = Vector3.one * 1.8f;

            marker.gameObject.SetActive(false);
        }

        /// <summary>Switches to the next (step 1) or previous (step -1) coach and remembers the choice.</summary>
        public void Cycle(int step)
        {
            if (built.Count > 1)
                Select(((selected + step) % built.Count + built.Count) % built.Count);
            else if (fallback != null)
                fallback.CycleStyle(step);
        }

        void Select(int i)
        {
            selected = i;
            for (int j = 0; j < built.Count; j++) built[j].root.SetActive(j == i);
            built[i].coach.SetBodyVisible(CurrentGuide == Guide.Coach);   // its chair stays
            built[i].ghost.SetBodyVisible(current != null && (ghostVisible || CurrentGuide == Guide.Silhouette));
            currentCode = null;   // re-run Configure on the next Show (ghost size depends on the guide)
            built[i].coach.Snap();
            built[i].ghost.Snap();
            popTime = 0f;
            PlayerPrefs.SetInt(PrefKey, i);
        }

        static Avatar FindAvatar(GameObject go)
        {
            if (go == null) return null;
            // An upright T-pose avatar made for this model (CoachAvatarBuilder) retargets the idle clips without a hunch
            var upright = Resources.Load<Avatar>("CoachAvatars/" + go.name);
            if (upright != null && upright.isHuman) return upright;
            var anim = go.GetComponentInChildren<Animator>(true);
            if (anim != null && anim.avatar != null && (anim.avatar.isHuman || anim.avatar.isValid)) return anim.avatar;
#if UNITY_EDITOR
            string assetPath = UnityEditor.AssetDatabase.GetAssetPath(go);
            if (!string.IsNullOrEmpty(assetPath))
            {
                foreach (var sub in UnityEditor.AssetDatabase.LoadAllAssetsAtPath(assetPath))
                {
                    if (sub is Avatar av && (av.isHuman || av.isValid)) return av;
                }
            }
#endif
            return null;
        }

        void Build(Option option)
        {
            var model = option.model;
            if (model == null) return;
            if (model == gameObject || transform.IsChildOf(model.transform))
            {
                Debug.LogWarning($"[TheraQuest] Put {model.name} on its own object, not on the HumanoidCoach. Skipping it.");
                return;
            }

            var avatar = FindAvatar(model);

            if (ghostMat == null)
            {
                propMat = FigureVisualizer.MakeMat(new Color(0.25f, 0.32f, 0.34f), false);
                ghostMat = FigureVisualizer.MakeMat(new Color(GhostNeutral.r, GhostNeutral.g, GhostNeutral.b, ghostAlpha), true);
            }

            string name = string.IsNullOrEmpty(option.name) ? model.name : option.name;
            var b = new Built { name = name, root = new GameObject(name) };
            b.root.transform.SetParent(transform, false);

            // A prefab or model asset is instantiated; a character already in the scene is used as is.
            var coachGo = model.scene.IsValid() ? model : Instantiate(model);
            var coachAnim = coachGo.GetComponentInChildren<Animator>(true);
            if (coachAnim == null) coachAnim = coachGo.AddComponent<Animator>();
            if (avatar != null && (avatar.isHuman || avatar.isValid))
            {
                coachAnim.avatar = avatar;
                try { coachAnim.Rebind(); } catch {}
            }

            var ghostGo = Instantiate(coachGo);   // copy before the coach's Animator is switched off
            var ghostAnim = ghostGo.GetComponentInChildren<Animator>(true);
            if (ghostAnim == null) ghostAnim = ghostGo.AddComponent<Animator>();
            if (avatar != null && (avatar.isHuman || avatar.isValid))
            {
                ghostAnim.avatar = avatar;
                try { ghostAnim.Rebind(); } catch {}
            }

            coachGo.name = "Coach (" + model.name + ")";
            ghostGo.name = "Ghost (" + model.name + ")";
            b.coach = Figure.Create(b.root.transform, "Coach", coachGo, Vector3.zero, propMat, null, idleClip, coachHeight, floorOffset, talkClip);
            b.ghost = Figure.Create(b.root.transform, "Ghost", ghostGo, ghostOffset, ghostMat, ghostMat, idleClip, coachHeight, floorOffset);
            // Same proportions on both, so the patient's ghost still lines up with the coach; toon shading on the coach only
            if (b.coach != null) UsePlainMaterials(coachGo);
            if (b.coach == null || b.ghost == null)
            {
                Debug.LogWarning($"[TheraQuest] Could not resolve skeleton for {model.name}. Skipping it.");
                Destroy(b.root);
                return;
            }
            b.ghost.showProps = ghostOffset.sqrMagnitude > 0.01f;   // overlaid ghost shares the coach's chair
            b.ghost.SetBodyVisible(false);
            built.Add(b);
        }

        void OnDestroy()
        {
            Subtitles.Said -= OnSaid;
            foreach (var b in built) { b.coach.Dispose(); b.ghost.Dispose(); }
        }

#if UNITY_EDITOR
        // Pick up gender models and idle animation dropped into Coaches folders, so scenes get them automatically.
        void OnValidate()
        {
            if (femaleModel == null || maleModel == null)
            {
                foreach (var guid in UnityEditor.AssetDatabase.FindAssets("t:Model"))
                {
                    string path = UnityEditor.AssetDatabase.GUIDToAssetPath(guid).Replace('\\', '/');
                    if (path.IndexOf("/Coaches/", System.StringComparison.OrdinalIgnoreCase) < 0) continue;
                    var go = UnityEditor.AssetDatabase.LoadAssetAtPath<GameObject>(path);
                    if (go == null) continue;

                    string lower = path.ToLowerInvariant();
                    string goName = go.name.ToLowerInvariant();

                    if (femaleModel == null && (lower.Contains("female") || goName.Contains("female")))
                    {
                        if (goName.Contains("casual") || femaleModel == null) femaleModel = go;
                    }
                    else if (maleModel == null && (lower.Contains("male") || goName.Contains("male")) && !lower.Contains("female") && !goName.Contains("female"))
                    {
                        if (goName.Contains("casual") || maleModel == null) maleModel = go;
                    }
                }
            }

            if (idleClip == null)
            {
                foreach (var guid in UnityEditor.AssetDatabase.FindAssets("t:AnimationClip"))
                {
                    string path = UnityEditor.AssetDatabase.GUIDToAssetPath(guid);
                    if (!path.Replace('\\', '/').Contains("/CoachAnimations/")) continue;
                    foreach (var asset in UnityEditor.AssetDatabase.LoadAllAssetsAtPath(path))
                        if (asset is AnimationClip clip && !clip.name.StartsWith("__preview__")) { idleClip = clip; return; }
                }
            }
        }
#endif

        public void Show(ExerciseDef ex, float angle, Tone tone)
        {
            if (ex == null) return;
            if (built.Count == 0)
            {
                if (fallback != null) fallback.Show(ex, angle, tone);
                return;
            }
            bool exerciseLayout = sessionRunning || isSessionActive;
            faceTone = tone;
            if (exerciseLayout && (idleLayout || ex.code != currentCode || ex.side != currentSide)) Configure(ex);
            else if (!exerciseLayout && !idleLayout) ConfigureIdle();
            current = ex;
            liveTarget = angle;
            var c = tone == Tone.Neutral ? GhostNeutral : FeedbackManager.ToneColor(tone);
            c.a = CurrentGuide == Guide.Coach ? ghostAlpha : silhouetteAlpha;
            ghostMat.color = c;

            if (markerMat != null)
            {
                var mc = tone == Tone.Good ? new Color(0.2f, 0.9f, 0.45f, 0.75f)
                       : tone == Tone.Bad ? new Color(0.95f, 0.45f, 0.2f, 0.75f)
                       : TargetColor;
                markerMat.color = mc;
            }
        }

        /// <summary>Standing, facing the player, no chair (menu, summary, free roam).</summary>
        void ConfigureIdle()
        {
            idleLayout = true;
            matDirty = true;
            foreach (var b in built)
            {
                b.coach.Configure(Posture.Standing, 0f, 1);
                b.ghost.Configure(Posture.Standing, 0f, 1);
                b.coach.Snap();
                b.ghost.Snap();
            }
            popTime = 0f;
        }

        void Configure(ExerciseDef ex)
        {
            idleLayout = false;
            matDirty = true;
            currentCode = ex.code;
            currentSide = ex.side;
            motion = MotionFor(ex);
            posture = PostureFor(ex.posture, motion);
            int patient = ex.side == "L" ? -1 : 1;   // "" = right
            side = mirror ? -patient : patient;

            // Face the player the way the tracker camera sees the patient: front view for movements out to
            // the side, side view (moving limb toward the player) otherwise.
            bool front = ex.view == "front";
            float yaw = front ? 0f : side > 0 ? -90f : 90f;
            foreach (var b in built)
            {
                b.coach.Configure(posture, yaw, side);
                b.ghost.Configure(posture, yaw, side);
                b.coach.Snap();   // new posture: jump straight there, hidden by the pop
                b.ghost.Snap();
            }
            demoTime = 0f;
            liveAngle = liveTarget;
            liveVel = 0f;
            popTime = 0f;
        }

        static Posture PostureFor(string posture, Motion motion)
        {
            switch (posture)
            {
                case "lying": return Posture.Lying;
                case "sidelying": return Posture.SideLying;
                case "seated": return Posture.Seated;
                case "standing": return Posture.Standing;
                default: return motion == Motion.KneeExt || motion == Motion.SitStand ? Posture.Seated : Posture.Standing;
            }
        }

        /// <summary>Animation for the exercise's pose from the server LIBRARY (DEC-012).</summary>
        static Motion MotionFor(ExerciseDef ex)
        {
            switch (ex.pose)
            {
                case "shoulderAbd": return Motion.ShoulderAbd;
                case "scaption": return Motion.Scaption;
                case "shoulderFlex": return Motion.ShoulderFlex;
                case "supineFlex": return Motion.SupineFlex;
                case "shoulderExt": return Motion.ShoulderExt;
                case "elbowFlex": return Motion.ElbowFlex;
                case "wallPushUp": return Motion.WallPushUp;
                case "hipAbd": return Motion.HipAbd;
                case "hipExt": return Motion.HipExt;
                case "slr": return Motion.HipFlex;
                case "march": return Motion.March;
                case "heelSlide": case "hamstringCurl": return Motion.KneeFlex;
                case "miniSquat": return Motion.MiniSquat;
                case "miniLunge": return Motion.MiniLunge;
                case "kneeExt": return Motion.KneeExt;
                case "sitToStand": return Motion.SitStand;
            }
            // Unknown pose: go by the tracker angle and camera view.
            bool front = ex.view == "front";
            switch (ex.measure)
            {
                case "elbowFlex": return Motion.ElbowFlex;
                case "hipElev": return front ? Motion.HipAbd : Motion.HipFlex;
                case "kneeFlex": return Motion.KneeFlex;
                case "kneeExt": return Motion.KneeExt;
                default: return front ? Motion.ShoulderAbd : Motion.ShoulderFlex;
            }
        }

        void LateUpdate()
        {
            if (built.Count == 0) return;
            float dt = Time.deltaTime;   // 0 while paused: everything holds still
            var b = built[selected];

            FitMat(b, dt);
            UpdateFace(b);
            // Gestures while speaking, eased in and out (standing only: the clip drives no other posture)
            float talkTarget = Time.unscaledTime < talkUntil ? 1f : 0f;
            talkWeight = Mathf.MoveTowards(talkWeight, talkTarget, Time.unscaledDeltaTime * 2.5f);
            b.coach.SetTalk(talkWeight);
            if (!isSessionActive || current == null)
            {
                // Before a session begins, while on the menu, or resting between exercises the coach DOES NOT move
                // on its own: it stands in a natural, relaxed idle, or (get-ready card, between exercises) waits in
                // the coming exercise's start position on its chair or the mat.
                float idleBreath = Mathf.Sin(Time.time * 1.6f) * 1.2f;
                float idleSway = Mathf.Sin(Time.time * 0.7f) * 1.5f;
                bool waiting = !idleLayout && current != null;

                if (waiting) b.coach.Pose(motion, posture, 0f, side, idleBreath, idleSway);
                else b.coach.Pose(Motion.ShoulderAbd, Posture.Standing, 0f, 1, idleBreath, idleSway);
                if (Camera.main != null && (!waiting || (posture != Posture.Lying && posture != Posture.SideLying)))
                    b.coach.LookAt(Camera.main.transform.position, lookAtPlayer);
                b.coach.Settle(dt, poseEasing);

                b.ghost.SetBodyVisible(false);
                if (marker != null) marker.gameObject.SetActive(false);

                // Springy pop when switching coaches
                popTime += Time.unscaledDeltaTime;
                float px = Mathf.Clamp01(popTime / 0.35f) - 1f;
                float pscale = 0.6f + 0.4f * (1f + 2.70158f * px * px * px + 1.70158f * px * px);
                b.root.transform.localScale = Vector3.one * pscale;
                return;
            }

            demoTime += dt;
            liveAngle = Mathf.SmoothDamp(liveAngle, liveTarget, ref liveVel, angleSmoothing, Mathf.Infinity, Mathf.Max(dt, 1e-5f));
            bool coachMode = CurrentGuide == Guide.Coach;
            // Gentle breathing and a slow side-to-side weight shift, in degrees (the idle animation does this when there is one)
            float breath = Mathf.Sin(Time.time * 1.6f) * 1.2f;
            float sway = Mathf.Sin(Time.time * 0.7f) * 1.5f;
            if (coachMode)
            {
                b.coach.Pose(motion, posture, current.targetAngle * DemoPhase(), side, breath, sway);
                if (posture != Posture.Lying && posture != Posture.SideLying && Camera.main != null)
                    b.coach.LookAt(Camera.main.transform.position, lookAtPlayer);
                b.coach.Settle(dt, poseEasing);
            }

            // Holographic target area / guide: always compute and show the target position so the user knows where their motion ends!
            b.ghost.Pose(motion, posture, current.targetAngle, side, 0f, 0f);
            var (from, to) = b.ghost.Segment(motion, side);
            PlaceMarker(from, to);
            if (marker != null) marker.gameObject.SetActive(true);

            b.ghost.SetBodyVisible(ghostVisible && (CurrentGuide == Guide.Silhouette || coachMode));
            b.ghost.Pose(motion, posture, liveAngle, side, coachMode ? breath : 0f, coachMode ? sway : 0f);
            if (coachMode && posture != Posture.Lying && posture != Posture.SideLying && Camera.main != null)
                b.ghost.LookAt(Camera.main.transform.position, lookAtPlayer);
            b.ghost.Settle(dt, poseEasing);

            // Over the coach, push the ghost a few centimetres away from the camera: wherever it matches the coach
            // it is hidden behind the coach's body (no flicker, no patches), and the teal only shows where the
            // patient's limb is somewhere else. From the player's point of view the push is invisible.
            bool overlay = coachMode && ghostOffset.sqrMagnitude < 0.01f && Camera.main != null;
            b.ghost.Nudge(overlay ? Camera.main.transform.forward * ghostDepthOffset : Vector3.zero);

            // Springy pop when the exercise, posture or avatar changes (grows from the floor, slight overshoot)
            popTime += Time.unscaledDeltaTime;
            float x = Mathf.Clamp01(popTime / 0.35f) - 1f;
            float scale = 0.6f + 0.4f * (1f + 2.70158f * x * x * x + 1.70158f * x * x);
            b.root.transform.localScale = Vector3.one * scale;
        }

        /// <summary>
        /// Keeps the yoga mat under the coach (and its chair), lengthwise along the body (human requests 2026-10-27).
        /// Measured once per posture change, after the pop-in has finished, then the mat glides and turns there.
        /// </summary>
        void FitMat(Built b, float dt)
        {
            if (matDirty && popTime > 0.45f)
            {
                matDirty = false;
                var area = b.coach.Footprint();
                matPos = new Vector3(area.center.x, 0.002f, area.center.z);
                bool alongX = area.size.x >= area.size.z;
                matRot = Quaternion.Euler(0f, alongX ? 0f : 90f, 0f);
                float along = alongX ? area.size.x : area.size.z, across = alongX ? area.size.z : area.size.x;
                var size = new Vector2(Mathf.Max(yogaMatSize.x, along + 0.3f), Mathf.Max(yogaMatSize.y, across + 0.2f));
                if (yogaMat == null || (size - matSizeBuilt).sqrMagnitude > 0.0004f)
                {
                    var at = yogaMat != null ? yogaMat.position : matPos;
                    var turn = yogaMat != null ? yogaMat.rotation : matRot;
                    if (yogaMat != null) Destroy(yogaMat.gameObject);
                    yogaMat = PropBuilder.YogaMat(null, size.x, size.y);
                    yogaMat.SetPositionAndRotation(at, turn);
                    matSizeBuilt = size;
                }
            }
            if (yogaMat == null) return;
            float k = dt > 0f ? 1f - Mathf.Exp(-8f * Time.unscaledDeltaTime) : 0f;
            yogaMat.position = Vector3.Lerp(yogaMat.position, matPos, k);
            yogaMat.rotation = Quaternion.Slerp(yogaMat.rotation, matRot, k);
        }

        // Plain stand-ins for coach materials this render pipeline can't draw (human request 2026-10-27: no cartoon
        // stylisation, which replaced DEC-017's toon shader)
        static readonly Dictionary<Material, Material> plainMats = new Dictionary<Material, Material>();

        /// <summary>
        /// Keeps the coach's own materials where they work. A material made for another render pipeline (the Little
        /// Guys pack ships URP materials; this project renders with the Built-in pipeline) would draw pink, so it is
        /// swapped for a plain Standard material with the same texture and colour: no outline, no cel shading.
        /// </summary>
        void UsePlainMaterials(GameObject model)
        {
            var standard = Shader.Find("Standard");
            if (standard == null) return;
            foreach (var r in model.GetComponentsInChildren<Renderer>(true))
            {
                var mats = r.sharedMaterials;
                bool changed = false;
                for (int i = 0; i < mats.Length; i++)
                {
                    var src = mats[i];
                    if (src == null || src.shader == null || src.shader.isSupported && !IsForOtherPipeline(src.shader)) continue;
                    if (!plainMats.TryGetValue(src, out var plain) || plain == null)
                    {
                        plain = new Material(standard) { name = src.name + " (plain)" };
                        plain.color = src.HasProperty("_BaseColor") ? src.GetColor("_BaseColor") : src.HasProperty("_Color") ? src.color : Color.white;
                        var tex = src.HasProperty("_BaseMap") ? src.GetTexture("_BaseMap") : src.HasProperty("_MainTex") ? src.GetTexture("_MainTex") : null;
                        if (tex != null) plain.mainTexture = tex;
                        plain.SetFloat("_Glossiness", 0.15f);   // soft cloth and skin, not shiny plastic
                        plainMats[src] = plain;
                    }
                    mats[i] = plain;
                    changed = true;
                }
                if (changed) r.sharedMaterials = mats;
            }
        }

        /// <summary>A URP or HDRP shader while the Built-in pipeline is active (Unity still reports it as supported).</summary>
        static bool IsForOtherPipeline(Shader s) =>
            UnityEngine.Rendering.GraphicsSettings.currentRenderPipeline == null &&
            (s.name.StartsWith("Universal Render Pipeline") || s.name.StartsWith("HDRP") || s.name.Contains("URP"));

        // Face (human request 2026-10-28): blinks every few seconds, a soft smile (the Smile shape also narrows the eyes),
        // a big smile on good reps and a concerned look on a warning; the mouth stays still
        float nextBlink = 2f, blinkStart = -10f, smileNow = 15f, surpriseNow;
        Tone faceTone = Tone.Neutral;

        void UpdateFace(Built b)
        {
            float t = Time.unscaledTime, dt = Time.unscaledDeltaTime;
            if (t >= nextBlink)
            {
                blinkStart = t;
                nextBlink = t + Random.Range(2.2f, 5f);
                if (Random.value < 0.15f) nextBlink = t + 0.35f;   // now and then a double blink
            }
            float bt = (t - blinkStart) / 0.16f;                    // closes and opens in about a sixth of a second
            float blink = bt >= 0f && bt <= 1f ? Mathf.Sin(bt * Mathf.PI) * 100f : 0f;

            bool active = isSessionActive && current != null;
            float smileTarget = !active || faceTone == Tone.Neutral ? 15f : faceTone == Tone.Good ? 60f : faceTone == Tone.Warn ? 10f : 0f;
            float surpriseTarget = active && faceTone == Tone.Bad ? 45f : 0f;
            smileNow = Mathf.MoveTowards(smileNow, smileTarget, dt * 160f);
            surpriseNow = Mathf.MoveTowards(surpriseNow, surpriseTarget, dt * 200f);
            // No talking mouth: the face stays in its idle expression while the coach speaks (human request 2026-10-28)
            b.coach.SetFace(blink, smileNow, 0f, surpriseNow);
        }

        void PlaceMarker(Vector3 from, Vector3 to)
        {
            var d = to - from;
            float len = d.magnitude;
            if (len < 1e-4f) return;
            markerLimb.position = (from + to) / 2f;
            markerLimb.rotation = Quaternion.FromToRotation(Vector3.up, d);
            markerLimb.localScale = new Vector3(MarkerWidth, len / 2f, MarkerWidth);   // capsule is 2 units tall
            markerEnd.position = to;
        }

        /// <summary>0 = start pose, 1 = target. One demo rep: rise, hold, lower, pause.</summary>
        float DemoPhase()
        {
            float move = Mathf.Max(0.2f, moveSeconds), hold = Mathf.Max(0.5f, current.holdSeconds);
            float t = demoTime % (move * 2f + hold + Mathf.Max(0f, pauseSeconds));
            if (t < move) return Ease(t / move);
            if ((t -= move) < hold) return 1f;
            if ((t -= hold) < move) return Ease(1f - t / move);
            return 0f;
        }

        static float Ease(float x) { x = Mathf.Clamp01(x); return x * x * x * (x * (6f * x - 15f) + 10f); }
        static float Sin(float deg) => Mathf.Sin(deg * Mathf.Deg2Rad);
        static float Cos(float deg) => Mathf.Cos(deg * Mathf.Deg2Rad);

        // Limb directions in the body frame (limbs hang along -Y, the body faces +Z, s = +1 right / -1 left).
        static Vector3 Sag(float a) => new Vector3(0f, -Cos(a), Sin(a));                     // swing forward and up
        static Vector3 Out(int s, float a) => new Vector3(s * Sin(a), -Cos(a), 0f);          // out to the side
        static Vector3 Scap(int s, float a) => new Vector3(s * Sin(a) * 0.866f, -Cos(a), Sin(a) * 0.5f); // 30° forward of the side

        /// <summary>One posed copy of the character: slot (view yaw) > pivot (lying) > character.</summary>
        sealed class Figure
        {
            const float MatTop = 0.01f;    // top of the yoga mat: the coach stands, sits and lies on it (no bed)

            public bool showProps = true;
            Vector3 offset;
            Transform slot, pivot, chair, hips, spine, head;
            GameObject body;
            readonly Transform[] upperArm = new Transform[2], lowerArm = new Transform[2], hand = new Transform[2];
            readonly Vector3[] palmLocal = new Vector3[2];   // palm normal in each hand's own space (zero: unknown)
            readonly Transform[] upperLeg = new Transform[2], lowerLeg = new Transform[2], foot = new Transform[2];
            Transform[] posed;
            Quaternion[] rest, last;
            // The model's own torso, neck, head and leg shape (bind pose), kept under the idle clips (human request 2026-10-28:
            // retain the model's original structure; the clips only move the upper arms, forearms and hands. The collarbones
            // stay put so the shoulders sit at the sides of the chest, and the fingers keep their relaxed rest shape)
            Transform[] torso;
            Quaternion[] torsoRest;
            float ankleRest;      // ankle height (pivot space) when the soles rest on the mat
            float backLift = 0.1f, sideLift = 0.2f;   // pivot height above the mat lying on the back / side (measured)
            // Face blend shapes (Little Guys: Blink, Smile, SmileTeeth, Surprise, ...), -1 when the model has none
            SkinnedMeshRenderer face;
            int shapeBlink = -1, shapeSmile = -1, shapeTeeth = -1, shapeSurprise = -1;
            readonly Vector3[] toeLocal = new Vector3[2];
            readonly bool[] legPosed = new bool[2];
            Vector3 hipsRestLocal, hipsRestPivot, hipsLast;
            bool hasLast;
            float thigh, shin;
            float armOut = 10f;   // degrees the resting arms hang out from the body, measured so the hands clear the hips
            bool animated;        // an idle clip drives the limbs the exercise doesn't use (standing only)
            PlayableGraph graph;
            AnimationMixerPlayable mixer;

            public void Dispose() { if (graph.IsValid()) graph.Destroy(); }

            /// <summary>0 = plain idle, 1 = talking gestures (only plays where there is a talking clip).</summary>
            public void SetTalk(float w)
            {
                if (!mixer.IsValid() || mixer.GetInputCount() < 2 || !mixer.GetInput(1).IsValid()) return;
                mixer.SetInputWeight(0, 1f - w);
                mixer.SetInputWeight(1, w);
            }

            static int I(int s) => s > 0 ? 1 : 0;   // array index: 0 = left, 1 = right

            static Transform SafeGetBone(Animator anim, HumanBodyBones bone)
            {
                if (anim == null) return null;
                try { return anim.GetBoneTransform(bone); }
                catch { return null; }
            }

            static Transform FindBone(Transform root, params string[] candidates)
            {
                if (root == null) return null;
                var all = root.GetComponentsInChildren<Transform>(true);
                foreach (var name in candidates)
                {
                    foreach (var t in all)
                        if (string.Equals(t.name, name, System.StringComparison.OrdinalIgnoreCase)) return t;
                }
                foreach (var name in candidates)
                {
                    foreach (var t in all)
                        if (t.name.IndexOf(name, System.StringComparison.OrdinalIgnoreCase) >= 0) return t;
                }
                return null;
            }

            public static Figure Create(Transform owner, string name, GameObject go, Vector3 offset, Material propMat, Material skin, AnimationClip idle, float targetHeight = 1.72f, float groundAdjust = 0f, AnimationClip talk = null)
            {
                var f = new Figure();
                f.slot = new GameObject(name).transform;
                f.slot.SetParent(owner, false);
                f.slot.localPosition = f.offset = offset;
                f.pivot = new GameObject(name + " pose").transform;
                f.pivot.SetParent(f.slot, false);

                var anim = go.GetComponentInChildren<Animator>(true);

                // 1. Resolve hips / pelvis
                f.hips = SafeGetBone(anim, HumanBodyBones.Hips);
                if (f.hips == null)
                {
                    var hipBone = FindBone(go.transform, "Hips", "Pelvis");
                    if (hipBone != null && hipBone.parent != null && hipBone.parent.name.Equals("Body", System.StringComparison.OrdinalIgnoreCase))
                        hipBone = hipBone.parent;
                    f.hips = hipBone ?? FindBone(go.transform, "Body", "Bone", "Root");
                }

                // 2. Resolve spine / torso
                f.spine = SafeGetBone(anim, HumanBodyBones.Spine);
                if (f.spine == null) f.spine = FindBone(go.transform, "Torso", "Spine", "Abdomen", "Chest");

                // 3. Resolve head
                var head = f.head = SafeGetBone(anim, HumanBodyBones.Head);
                if (head == null) head = f.head = FindBone(go.transform, "Head");

                // 4. Resolve arms
                f.upperArm[0] = SafeGetBone(anim, HumanBodyBones.LeftUpperArm) ?? FindBone(go.transform, "UpperArm.L", "UpperArm_L", "LeftUpperArm", "Arm.L", "LeftArm");
                f.upperArm[1] = SafeGetBone(anim, HumanBodyBones.RightUpperArm) ?? FindBone(go.transform, "UpperArm.R", "UpperArm_R", "RightUpperArm", "Arm.R", "RightArm");
                f.lowerArm[0] = SafeGetBone(anim, HumanBodyBones.LeftLowerArm) ?? FindBone(go.transform, "LowerArm.L", "LowerArm_L", "LeftLowerArm", "Forearm.L", "LeftForeArm");
                f.lowerArm[1] = SafeGetBone(anim, HumanBodyBones.RightLowerArm) ?? FindBone(go.transform, "LowerArm.R", "LowerArm_R", "RightLowerArm", "Forearm.R", "RightForeArm");
                f.hand[0] = SafeGetBone(anim, HumanBodyBones.LeftHand) ?? FindBone(go.transform, "Palm.L", "Hand.L", "LeftHand", "MiddleHand.L");
                f.hand[1] = SafeGetBone(anim, HumanBodyBones.RightHand) ?? FindBone(go.transform, "Palm.R", "Hand.R", "RightHand", "MiddleHand.R");

                // 5. Resolve legs
                f.upperLeg[0] = SafeGetBone(anim, HumanBodyBones.LeftUpperLeg) ?? FindBone(go.transform, "UpperLeg.L", "UpperLeg_L", "LeftUpperLeg", "Thigh.L", "LeftUpLeg");
                f.upperLeg[1] = SafeGetBone(anim, HumanBodyBones.RightUpperLeg) ?? FindBone(go.transform, "UpperLeg.R", "UpperLeg_R", "RightUpperLeg", "Thigh.R", "RightUpLeg");
                f.lowerLeg[0] = SafeGetBone(anim, HumanBodyBones.LeftLowerLeg) ?? FindBone(go.transform, "LowerLeg.L", "LowerLeg_L", "LeftLowerLeg", "Shin.L", "LeftLeg");
                f.lowerLeg[1] = SafeGetBone(anim, HumanBodyBones.RightLowerLeg) ?? FindBone(go.transform, "LowerLeg.R", "LowerLeg_R", "RightLowerLeg", "Shin.R", "RightLeg");

                // Reparent foot if model has IK foot parented to root (common in Blender models like Quaternius)
                for (int s = 0; s < 2; s++)
                {
                    string footName = s == 0 ? "Foot.L" : "Foot.R";
                    var ft = FindBone(go.transform, footName, s == 0 ? "Foot_L" : "Foot_R", s == 0 ? "LeftFoot" : "RightFoot");
                    if (ft != null && f.lowerLeg[s] != null && ft.parent != f.lowerLeg[s])
                        ft.SetParent(f.lowerLeg[s], true);
                }

                f.foot[0] = SafeGetBone(anim, HumanBodyBones.LeftFoot) ?? FindBone(go.transform, "Foot.L", "LowerLeg.L_end", "LeftFoot", "Foot_L");
                f.foot[1] = SafeGetBone(anim, HumanBodyBones.RightFoot) ?? FindBone(go.transform, "Foot.R", "LowerLeg.R_end", "RightFoot", "Foot_R");
                // Quaternius rigs map the ankle point (LowerLeg.*_end) as the Humanoid foot (CoachModelImporter): hang the
                // shoe bone from it, so the ankle (animated or posed) turns the shoe
                for (int s = 0; s < 2; s++)
                {
                    var shoe = FindBone(go.transform, s == 0 ? "Foot.L" : "Foot.R");
                    if (shoe != null && f.foot[s] != null && shoe != f.foot[s] && !shoe.IsChildOf(f.foot[s]) && !f.foot[s].IsChildOf(shoe))
                        shoe.SetParent(f.foot[s], true);
                }

                if (f.hips == null || f.head == null || f.upperArm[0] == null || f.upperArm[1] == null ||
                    f.lowerArm[0] == null || f.lowerArm[1] == null || f.upperLeg[0] == null || f.upperLeg[1] == null ||
                    f.lowerLeg[0] == null || f.lowerLeg[1] == null || f.foot[0] == null || f.foot[1] == null)
                {
                    Debug.LogWarning($"[TheraQuest] Model {go.name} is missing essential limbs for coach animation.");
                    Object.Destroy(f.slot.gameObject);
                    return null;
                }

                // Without an idle clip the Animator is off and the whole pose is written by hand in LateUpdate.
                // With one, the Animator plays it (no controller asset needed) and LateUpdate writes the exercise on top.
                f.animated = idle != null && anim != null && anim.avatar != null && anim.avatar.isHuman;
                if (f.animated)
                {
                    anim.applyRootMotion = false;
                    anim.cullingMode = AnimatorCullingMode.AlwaysAnimate;
                    f.graph = PlayableGraph.Create(name + " idle");
                    var output = AnimationPlayableOutput.Create(f.graph, "Idle", anim);
                    // Idle and (when there is one) talking gestures, cross-faded by SetTalk
                    f.mixer = AnimationMixerPlayable.Create(f.graph, 2);
                    f.graph.Connect(AnimationClipPlayable.Create(f.graph, idle), 0, f.mixer, 0);
                    if (talk != null) f.graph.Connect(AnimationClipPlayable.Create(f.graph, talk), 0, f.mixer, 1);
                    f.mixer.SetInputWeight(0, 1f);
                    output.SetSourcePlayable(f.mixer);
                    f.graph.Play();
                }
                else if (anim != null) anim.enabled = false;

                // Turn the model so its body faces +Z with +Y up, whatever its import rotation, hips over the pivot.
                f.body = go;
                var root = go.transform;
                root.SetParent(f.pivot, false);
                root.localPosition = Vector3.zero;
                var right = root.InverseTransformDirection(f.upperArm[1].position - f.upperArm[0].position);
                var up = root.InverseTransformDirection(head.position - f.hips.position);
                root.localRotation = Quaternion.Inverse(Quaternion.LookRotation(Vector3.Cross(right, up), up));

                // 1. Height normalization:
                // FBX models exported from Blender or third-party packages often import at 100x scale (cm units),
                // 10x scale, or inconsistent sizes. We measure the vertical distance from the lowest foot ankle to the head bone
                // in pivot space. On an adult human scaled to targetHeight (default 1.72m / 5'8"), ankle-to-head bone is ~1.48m
                // (with ~0.07m sole thickness to floor and ~0.17m head joint to crown of skull).
                float targetSpan = targetHeight * (1.48f / 1.72f);
                float ankleFloorOffset = targetHeight * (0.07f / 1.72f);

                float footAnkleY = Mathf.Min(f.pivot.InverseTransformPoint(f.foot[0].position).y, f.pivot.InverseTransformPoint(f.foot[1].position).y);
                float headY = f.pivot.InverseTransformPoint(head.position).y;
                float rawSpan = headY - footAnkleY;
                if (rawSpan > 0.01f)
                {
                    float scaleFactor = targetSpan / rawSpan;
                    root.localScale *= scaleFactor;
                }

                // 2. Foot grounding:
                // Re-measure ankle Y and hips in pivot space after scaling so the soles rest firmly at Y = 0 (floor)
                // and the hips are centered horizontally over the pivot.
                float groundAnkleY = Mathf.Min(f.pivot.InverseTransformPoint(f.foot[0].position).y, f.pivot.InverseTransformPoint(f.foot[1].position).y);
                var hipPos = f.pivot.InverseTransformPoint(f.hips.position);
                root.localPosition = new Vector3(-hipPos.x, (ankleFloorOffset - groundAnkleY) + groundAdjust, -hipPos.z);
                // Stand on top of the mat: measure the real bottom of the shoes (the mesh as posed) and lift or lower the
                // model so its soles rest on the mat, whatever its foot and shoe shape (human request 2026-10-28)
                float sole = LowestPoint(go.transform, f.pivot);
                if (!float.IsNaN(sole)) root.localPosition += Vector3.up * (MatTop - sole);

                var torsoBones = new List<Transform>();
                foreach (var hb in new[] { HumanBodyBones.Hips, HumanBodyBones.Spine, HumanBodyBones.Chest, HumanBodyBones.UpperChest, HumanBodyBones.Neck, HumanBodyBones.Head,
                                          HumanBodyBones.LeftUpperLeg, HumanBodyBones.RightUpperLeg, HumanBodyBones.LeftLowerLeg, HumanBodyBones.RightLowerLeg,
                                          HumanBodyBones.LeftFoot, HumanBodyBones.RightFoot, HumanBodyBones.LeftToes, HumanBodyBones.RightToes,
                                          HumanBodyBones.LeftShoulder, HumanBodyBones.RightShoulder, HumanBodyBones.LeftHand, HumanBodyBones.RightHand }.Concat(FingerBones))
                {
                    var t = SafeGetBone(anim, hb);
                    if (t != null && !torsoBones.Contains(t)) torsoBones.Add(t);
                }
                f.torso = torsoBones.ToArray();
                f.torsoRest = new Quaternion[f.torso.Length];
                // Shoulders at the sides of the chest, not behind it (human request 2026-10-28, anatomy): the Little Guys'
                // collarbones set the arm joints well behind the chest's middle, so they turn forward until the joint is
                // level with the chest bone
                var chestBone = SafeGetBone(anim, HumanBodyBones.UpperChest) ?? SafeGetBone(anim, HumanBodyBones.Chest) ?? f.spine;
                for (int side = 0; side < 2 && chestBone != null; side++)
                {
                    var clav = SafeGetBone(anim, side == 0 ? HumanBodyBones.LeftShoulder : HumanBodyBones.RightShoulder);
                    var armJoint = SafeGetBone(anim, side == 0 ? HumanBodyBones.LeftUpperArm : HumanBodyBones.RightUpperArm);
                    if (clav == null || armJoint == null) continue;
                    Vector3 c = f.pivot.InverseTransformPoint(clav.position), d = f.pivot.InverseTransformPoint(armJoint.position) - c;
                    var flat = new Vector3(d.x, 0f, d.z);
                    float reach = flat.magnitude, want = f.pivot.InverseTransformPoint(chestBone.position).z - c.z;
                    if (reach < 0.02f || want <= d.z) continue;
                    want = Mathf.Min(want, reach * 0.5f);   // at most 30 degrees
                    var to = new Vector3(Mathf.Sign(d.x) * Mathf.Sqrt(reach * reach - want * want), 0f, want);
                    var turn = Quaternion.FromToRotation(f.pivot.TransformDirection(flat), f.pivot.TransformDirection(to));
                    clav.rotation = turn * clav.rotation;
                }
                // Semi-relaxed hands (human request 2026-10-28): the fingers curl gently toward the palm, more at the
                // knuckles nearer the tips, the thumb a little; the model's own hand is flat
                for (int side = 0; side < 2; side++)
                {
                    var palm = CurlFingers(anim, side == 0);
                    if (palm != Vector3.zero && f.hand[side] != null) f.palmLocal[side] = f.hand[side].InverseTransformDirection(palm);
                }
                for (int i = 0; i < f.torso.Length; i++) f.torsoRest[i] = f.torso[i].localRotation;

                foreach (var smr in go.GetComponentsInChildren<SkinnedMeshRenderer>(true))
                {
                    var mesh = smr.sharedMesh;
                    if (mesh == null || mesh.GetBlendShapeIndex("Blink") < 0) continue;
                    f.face = smr;
                    f.shapeBlink = mesh.GetBlendShapeIndex("Blink");
                    f.shapeSmile = mesh.GetBlendShapeIndex("Smile");
                    f.shapeTeeth = mesh.GetBlendShapeIndex("SmileTeeth");
                    f.shapeSurprise = mesh.GetBlendShapeIndex("Surprise");
                    break;
                }

                f.posed = new[] { f.hips, f.spine, f.upperArm[0], f.upperArm[1], f.lowerArm[0], f.lowerArm[1],
                                  f.upperLeg[0], f.upperLeg[1], f.lowerLeg[0], f.lowerLeg[1], f.head, f.foot[0], f.foot[1] };
                f.rest = new Quaternion[f.posed.Length];
                f.last = new Quaternion[f.posed.Length];
                for (int i = 0; i < f.posed.Length; i++) f.rest[i] = f.posed[i].localRotation;
                // Which way the toes point, in each foot's own space (the rest pose faces +Z)
                for (int i = 0; i < 2; i++) f.toeLocal[i] = f.foot[i].InverseTransformDirection(f.pivot.forward);
                f.hipsRestLocal = f.hips.localPosition;
                f.ankleRest = Mathf.Min(f.pivot.InverseTransformPoint(f.foot[0].position).y, f.pivot.InverseTransformPoint(f.foot[1].position).y);
                f.hipsRestPivot = f.pivot.InverseTransformPoint(f.hips.position);
                f.thigh = (f.Length(f.upperLeg[0], f.lowerLeg[0]) + f.Length(f.upperLeg[1], f.lowerLeg[1])) / 2f;
                f.shin = (f.Length(f.lowerLeg[0], f.foot[0]) + f.Length(f.lowerLeg[1], f.foot[1])) / 2f;

                // Resting arm angle for this character: the hands must hang clear of the hips and thighs.
                // shoulder x, hip-joint x and arm length are read from the rig, so any body shape works.
                float shoulderX = (Mathf.Abs(f.pivot.InverseTransformPoint(f.upperArm[0].position).x) +
                                   Mathf.Abs(f.pivot.InverseTransformPoint(f.upperArm[1].position).x)) / 2f;
                float hipX = (Mathf.Abs(f.pivot.InverseTransformPoint(f.upperLeg[0].position).x) +
                              Mathf.Abs(f.pivot.InverseTransformPoint(f.upperLeg[1].position).x)) / 2f;
                float arm = (f.Length(f.upperArm[0], f.lowerArm[0]) + f.Length(f.lowerArm[0], f.hand[0]) +
                             f.Length(f.upperArm[1], f.lowerArm[1]) + f.Length(f.lowerArm[1], f.hand[1])) / 2f;
                float clearX = hipX + 0.16f;   // thigh and hip flesh plus the hand's own thickness
                f.armOut = Mathf.Clamp(Mathf.Asin(Mathf.Clamp((clearX - shoulderX) / Mathf.Max(0.3f, arm), -1f, 1f)) * Mathf.Rad2Deg, 9f, 26f);

                foreach (var r in go.GetComponentsInChildren<Renderer>(true))
                {
                    if (skin != null)
                    {
                        var mats = new Material[r.sharedMaterials.Length];
                        for (int i = 0; i < mats.Length; i++) mats[i] = skin;
                        r.sharedMaterials = mats;
                        r.shadowCastingMode = ShadowCastingMode.Off;
                    }
                    if (r is SkinnedMeshRenderer smr) smr.updateWhenOffscreen = true;   // bones move far from the bind pose
                }

                // Chair sized to the character: hips on the seat, thighs level, feet on the floor.
                f.chair = new GameObject("Chair").transform;
                f.chair.SetParent(f.slot, false);
                float seatTop = Mathf.Max(0.2f, f.hipsRestPivot.y - f.thigh - 0.08f);
                PropBuilder.Chair(f.chair, seatTop, -f.thigh - 0.17f, -0.02f);
                f.chair.gameObject.SetActive(false);

                // Calibrate the standing pose (soft knees, flat feet), not the bind pose: the shoe soles must touch the
                // top of the mat, so the ankle height the standing pose keeps is set from the posed mesh
                f.Pose(Motion.ShoulderAbd, Posture.Standing, 0f, 1, 0f, 0f);
                float standingSole = LowestPoint(go.transform, f.pivot);
                if (!float.IsNaN(standingSole)) f.ankleRest += MatTop - standingSole;
                // Same for lying on the back and on the side: the lowest point (hair, hips, shoulder) rests on the mat
                f.Configure(Posture.Lying, 0f, 1);
                f.Pose(Motion.SupineFlex, Posture.Lying, 0f, 1, 0f, 0f);
                float back = LowestPoint(go.transform, f.slot);
                if (!float.IsNaN(back)) f.backLift += MatTop - back;
                f.Configure(Posture.SideLying, 0f, 1);
                f.Pose(Motion.HipAbd, Posture.SideLying, 0f, 1, 0f, 0f);
                float flank = LowestPoint(go.transform, f.slot);
                if (!float.IsNaN(flank)) f.sideLift += MatTop - flank;
                f.Configure(Posture.Standing, 0f, 1);
                return f;
            }

            static Vector3 CurlFingers(Animator anim, bool left)
            {
                HumanBodyBones B(string name) => (HumanBodyBones)System.Enum.Parse(typeof(HumanBodyBones), (left ? "Left" : "Right") + name);
                var hand = SafeGetBone(anim, B("Hand"));
                var index = SafeGetBone(anim, B("IndexProximal"));
                var middle = SafeGetBone(anim, B("MiddleProximal"));
                var little = SafeGetBone(anim, B("LittleProximal"));
                if (hand == null || index == null || middle == null || little == null) return Vector3.zero;
                // Palm normal from the hand's shape: fingers' direction crossed with the knuckle line
                var palm = Vector3.Cross(middle.position - hand.position, index.position - little.position).normalized * (left ? -1f : 1f);
                foreach (var (finger, curl) in new[] { ("Index", 1f), ("Middle", 1.05f), ("Ring", 1.1f), ("Little", 1.15f), ("Thumb", 0.4f) })
                {
                    float[] angles = { 14f, 20f, 12f };
                    string[] joints = { "Proximal", "Intermediate", "Distal" };
                    for (int j = 0; j < 3; j++)
                    {
                        var bone = SafeGetBone(anim, B(finger + joints[j]));
                        if (bone == null) continue;
                        var tip = j < 2 ? SafeGetBone(anim, B(finger + joints[j + 1])) : (bone.childCount > 0 ? bone.GetChild(0) : null);
                        var along = tip != null ? tip.position - bone.position : bone.position - bone.parent.position;
                        var axis = Vector3.Cross(along, palm);   // turns the bone toward the palm
                        if (axis.sqrMagnitude < 1e-10f) continue;
                        bone.rotation = Quaternion.AngleAxis(angles[j] * curl, axis.normalized) * bone.rotation;
                    }
                }
                return palm;
            }

            static IEnumerable<HumanBodyBones> FingerBones =>
                Enumerable.Range((int)HumanBodyBones.LeftThumbProximal, (int)HumanBodyBones.RightLittleDistal - (int)HumanBodyBones.LeftThumbProximal + 1)
                          .Select(i => (HumanBodyBones)i);

            /// <summary>Lowest point of the model's meshes as currently posed, in the given space (NaN without meshes).</summary>
            static float LowestPoint(Transform model, Transform space)
            {
                float low = float.PositiveInfinity;
                var baked = new Mesh();
                foreach (var r in model.GetComponentsInChildren<Renderer>(true))
                {
                    Vector3[] verts;
                    if (r is SkinnedMeshRenderer smr) { smr.BakeMesh(baked, true); verts = baked.vertices; }
                    else if (r.TryGetComponent<MeshFilter>(out var mf) && mf.sharedMesh != null) verts = mf.sharedMesh.vertices;
                    else continue;
                    foreach (var v in verts) low = Mathf.Min(low, space.InverseTransformPoint(r.transform.TransformPoint(v)).y);
                }
                Object.Destroy(baked);
                return float.IsPositiveInfinity(low) ? float.NaN : low;
            }

            /// <summary>Face blend shapes, 0-100 each; does nothing on a model without them.</summary>
            public void SetFace(float blink, float smile, float teeth, float surprise)
            {
                if (face == null) return;
                Shape(shapeBlink, blink);
                Shape(shapeSmile, smile);
                Shape(shapeTeeth, teeth);
                Shape(shapeSurprise, surprise);
            }

            // Shapes reach full strength at their last frame's weight: 1 on the Little Guys (made in Blender), 100 on
            // others. Unity extrapolates past it, so 0-100 is scaled to that weight (100 on a 0-1 shape blew the face apart)
            void Shape(int index, float percent)
            {
                if (index < 0) return;
                var mesh = face.sharedMesh;
                float full = mesh.GetBlendShapeFrameWeight(index, mesh.GetBlendShapeFrameCount(index) - 1);
                face.SetBlendShapeWeight(index, Mathf.Clamp(percent, 0f, 100f) / 100f * full);
            }

            float Length(Transform a, Transform b) => pivot.InverseTransformVector(b.position - a.position).magnitude;

            public void SetBodyVisible(bool visible) => body.SetActive(visible);

            /// <summary>World start and end of the limb segment that the exercise moves (as currently posed).</summary>
            public (Vector3 from, Vector3 to) Segment(Motion m, int s)
            {
                int i = I(s);
                switch (m)
                {
                    case Motion.ShoulderAbd: case Motion.Scaption: case Motion.ShoulderFlex: case Motion.SupineFlex: case Motion.ShoulderExt:
                        return (upperArm[i].position, hand[i].position);
                    case Motion.ElbowFlex: case Motion.WallPushUp: return (lowerArm[i].position, hand[i].position);
                    case Motion.HipAbd: case Motion.HipFlex: case Motion.HipExt: return (upperLeg[i].position, foot[i].position);
                    case Motion.KneeFlex: case Motion.KneeExt: return (lowerLeg[i].position, foot[i].position);
                    default: return (upperLeg[i].position, lowerLeg[i].position);   // march, mini squat, sit to stand: thigh
                }
            }

            public static Transform Primitive(PrimitiveType type, Transform parent, Material mat)
            {
                var go = GameObject.CreatePrimitive(type);
                Object.Destroy(go.GetComponent<Collider>());
                go.transform.SetParent(parent, false);
                var r = go.GetComponent<Renderer>();
                r.sharedMaterial = mat;
                r.shadowCastingMode = ShadowCastingMode.Off;
                return go.transform;
            }

            public void Configure(Posture p, float yaw, int s)
            {
                bool lying = p == Posture.Lying, sideLying = p == Posture.SideLying;
                slot.localRotation = Quaternion.Euler(0f, yaw, 0f);
                // Lying on the back on the mat: face up, head toward -Z, hips just above the floor.
                // Side-lying: rolled onto the other side so the moving leg (s) is on top.
                pivot.localRotation = lying ? Quaternion.Euler(-90f, 0f, 0f) : sideLying ? Quaternion.Euler(0f, 0f, 90f * s) : Quaternion.identity;
                pivot.localPosition = lying ? new Vector3(0f, MatTop + backLift, hipsRestPivot.y)
                                    : sideLying ? new Vector3(s * hipsRestPivot.y, MatTop + sideLift, 0f) : Vector3.zero;
                chair.gameObject.SetActive(showProps && p == Posture.Seated);

                slot.localPosition = offset;
            }

            /// <summary>World box around the figure's body (head, hands, feet) and the chair it is using.</summary>
            public Bounds Footprint()
            {
                var area = new Bounds(hips.position, Vector3.zero);
                foreach (var t in new[] { head, hand[0], hand[1], lowerLeg[0], lowerLeg[1], foot[0], foot[1] })
                    if (t != null) area.Encapsulate(t.position);
                // Lying down the whole body, big head and hair included, must fit on the mat (the bones stop short of it)
                if (pivot.localRotation != Quaternion.identity)
                    foreach (var r in pivot.GetComponentsInChildren<SkinnedMeshRenderer>()) area.Encapsulate(r.bounds);
                foreach (var prop in new[] { chair })
                    if (prop != null && prop.gameObject.activeInHierarchy)
                        foreach (var r in prop.GetComponentsInChildren<Renderer>()) area.Encapsulate(r.bounds);
                return area;
            }

            /// <summary>Moves the figure by a world-space offset from its place (used to sit the ghost behind the coach).</summary>
            public void Nudge(Vector3 world) => slot.localPosition = offset + slot.parent.InverseTransformVector(world);

            /// <summary>Next pose is applied as is (after a posture change), not eased from the old one.</summary>
            public void Snap() => hasLast = false;

            /// <summary>Eases every bone from last frame's pose toward the pose just written (removes snapping).</summary>
            public void Settle(float dt, float rate)
            {
                float k = hasLast ? 1f - Mathf.Exp(-rate * dt) : 1f;
                for (int i = 0; i < posed.Length; i++)
                {
                    if (hasLast) posed[i].localRotation = Quaternion.Slerp(last[i], posed[i].localRotation, k);
                    last[i] = posed[i].localRotation;
                }
                if (hasLast) hips.localPosition = Vector3.Lerp(hipsLast, hips.localPosition, k);
                hipsLast = hips.localPosition;
                hasLast = true;
            }

            /// <summary>Turns the head toward a point (the player), limited to maxDeg from straight ahead.</summary>
            public void LookAt(Vector3 target, float maxDeg)
            {
                if (head == null || maxDeg <= 0f) return;
                var face = pivot.TransformDirection(Vector3.forward);
                var want = target - head.position;
                if (want.sqrMagnitude < 1e-4f) return;
                var dir = Vector3.RotateTowards(face, want.normalized, maxDeg * Mathf.Deg2Rad, 0f);
                head.rotation = Quaternion.FromToRotation(face, dir) * head.rotation;
            }

            /// <summary>
            /// Poses the character at angle a (the tracker's ROM value) for the exercise. breath and sway add
            /// small idle movements (degrees); the limbs that don't exercise relax naturally.
            /// </summary>
            public void Pose(Motion m, Posture p, float a, int s, float breath, float sway)
            {
                // Standing with an idle clip: start from the animated pose (natural breathing, weight shift, arms).
                // Otherwise start from the rest pose and add the small hand-made idle movements.
                // Every frame starts from the model's own rest shape (human requests 2026-10-28: keep the model's
                // structure). The idle clips no longer show: their arm twist turned the palms forward and the chest
                // and neck lifted the head off the mat. Breathing and sway are added by hand below.
                for (int i = 0; i < torso.Length; i++) torso[i].localRotation = torsoRest[i];
                for (int i = 0; i < posed.Length; i++) posed[i].localRotation = rest[i];
                hips.localPosition = hipsRestLocal;
                legPosed[0] = legPosed[1] = false;
                a = Mathf.Clamp(a, 0f, 180f);
                int o = -s;
                bool lying = p == Posture.Lying || p == Posture.SideLying;
                if (!lying)
                {
                    if (breath != 0f) Lean(breath);
                    if (sway != 0f) spine.rotation = Quaternion.AngleAxis(sway, pivot.forward) * spine.rotation;
                }

                switch (m)
                {
                    case Motion.MiniSquat:                                               // feet stay on the floor
                    {
                        float f = a / 2f;
                        Shift((thigh + shin) * (Cos(f) - 1f), (shin - thigh) * Sin(f));
                        Lean(f * 0.6f);
                        Leg(s, f, a);
                        Leg(o, f, a);
                        break;
                    }
                    case Motion.SitStand:                                                // 0 = seated, 90 = standing
                    {
                        float f = 90f - Mathf.Min(a, 90f);
                        Shift(thigh * (Cos(f) - 1f), -thigh * Sin(f));
                        Lean(30f * Sin(2f * f));                                         // lean forward mid-rise
                        Leg(s, f, f);
                        Leg(o, f, f);
                        break;
                    }
                    case Motion.KneeExt:                                                 // seated, 0 = knee at 90°
                        Shift(-thigh, -thigh);
                        Leg(s, 90f, 90f - Mathf.Min(a, 90f));
                        Leg(o, 90f, 90f);
                        break;
                    case Motion.HipAbd: LegDir(s, Out(s, a), Out(s, a)); break;
                    case Motion.HipFlex:                                                 // straight leg
                        Leg(s, a, 0f);
                        if (p == Posture.Lying) Leg(o, 45f, 90f);                        // other knee bent, foot flat
                        break;
                    case Motion.March: Leg(s, a, a); break;                              // shin stays vertical
                    case Motion.HipExt: Leg(s, -a, 0f); break;                           // straight leg back
                    case Motion.MiniLunge:                                               // operated leg in front
                    {
                        Shift((thigh + shin) * (Cos(a / 2f) - 1f) * 0.8f, 0f);
                        Lean(a * 0.15f);
                        Leg(s, a * 0.55f, a);
                        Leg(o, -15f - a * 0.2f, a * 0.6f);
                        break;
                    }
                    case Motion.KneeFlex:
                        if (p == Posture.Lying) Leg(s, a / 2f, a);                       // heel stays on the mat
                        else Leg(s, 0f, a);
                        break;
                }

                // Standing legs that the exercise doesn't move: soft knees instead of locked straight. Also with the idle
                // clip, which drives the trunk, head and arms: retargeted onto the coach rigs its legs take a stride
                // and crease the thigh, so the feet stay planted side by side
                if (p == Posture.Standing)
                    for (int side = -1; side <= 1; side += 2)
                        if (!legPosed[I(side)]) Leg(side, 3f, 7f);
                // Lying down they lie straight along the mat (the rig's rest pose bends the knees, which pushed the
                // shins down through the mattress and left the shoes floating)
                if (lying)
                    for (int side = -1; side <= 1; side += 2)
                        if (!legPosed[I(side)]) Leg(side, 0f, 0f);

                // Standing: keep the supporting foot's sole on top of the mat whatever the knees do
                if (p == Posture.Standing)
                {
                    float ankle = Mathf.Min(pivot.InverseTransformPoint(foot[0].position).y, pivot.InverseTransformPoint(foot[1].position).y);
                    hips.position += pivot.up * (ankleRest - ankle);
                }

                // Arms last, so they hang down even when the trunk leans. Resting arms keep a soft elbow
                // (straight along the body when lying down); some exercises move the other arm naturally.
                Vector3 upper = RestUpper(s, p, sway), fore = RestFore(s, p, sway);
                Vector3 oUpper = RestUpper(o, p, -sway), oFore = RestFore(o, p, -sway);
                switch (m)
                {
                    // Low angles keep the resting arm's gap from the hip, so the hand never sinks into the waist
                    // and over the first 15 degrees the arm moves out of the relaxed resting pose (soft elbow), so the
                    // idle and the start position look like the other arm
                    case Motion.ShoulderAbd: Raise(ref upper, ref fore, Out(s, Mathf.Max(a, armOut)), a); break;
                    case Motion.Scaption: Raise(ref upper, ref fore, Scap(s, Mathf.Max(a, armOut)), a); break;
                    case Motion.ShoulderFlex: Raise(ref upper, ref fore, Clear(s, Sag(a)), a); break;
                    case Motion.ShoulderExt: Raise(ref upper, ref fore, Clear(s, Sag(-a)), a); break;
                    case Motion.ElbowFlex: fore = Sag(a); break;
                    case Motion.March:                                                   // opposite arm swings forward
                        oUpper = Sag(a * 0.4f); oFore = Sag(a * 0.4f + 30f);
                        upper = Sag(-a * 0.25f); fore = Sag(-a * 0.25f + 15f);
                        break;
                    case Motion.MiniSquat: case Motion.MiniLunge:                        // arms forward for balance
                    {
                        float r = Mathf.Min(70f, a * 1.2f);
                        upper = oUpper = Sag(r);
                        fore = oFore = Sag(r + 12f);
                        break;
                    }
                    case Motion.SitStand:                                                // reach forward while rising
                    {
                        float r = 50f * Sin(2f * (90f - Mathf.Min(a, 90f)));
                        upper = oUpper = Sag(r);
                        fore = oFore = Sag(r + 20f);
                        break;
                    }
                    case Motion.SupineFlex:                                              // both hands on the cane
                        Arm(s, Sag(a), Sag(a));
                        Arm(o, Sag(a), Sag(a));
                        return;
                    case Motion.WallPushUp:                                              // hands stay on the wall
                        Lean(15f + a * 0.1f);
                        Arm(s, Sag(90f - a / 2f), Sag(90f + a / 2f));
                        Arm(o, Sag(90f - a / 2f), Sag(90f + a / 2f));
                        return;
                }
                // Always hand-posed: the idle clips' arm angles assume their own rig's collarbones (human request
                // 2026-10-28: keep the model's structure, arms hang relaxed at the sides)
                Arm(s, upper, fore);
                Arm(o, oUpper, oFore);
            }

            /// <summary>
            /// Resting upper arm: hangs out just enough to clear the hips (armOut), drifting slightly with the idle sway.
            /// Seated, the arm comes forward so the hands rest on the thighs.
            /// </summary>
            static void Raise(ref Vector3 upper, ref Vector3 fore, Vector3 to, float a)
            {
                float t = Mathf.Clamp01(a / 15f);
                upper = Vector3.Slerp(upper, to, t);
                fore = Vector3.Slerp(fore, to, t);
            }

            /// <summary>A hanging arm direction moved out to the resting angle, less as the arm rises.</summary>
            Vector3 Clear(int s, Vector3 dir)
            {
                dir.x += s * Sin(armOut) * Mathf.Clamp01(-dir.y);
                return dir.normalized;
            }

            Vector3 RestUpper(int s, Posture p, float sway)
            {
                if (p == Posture.Seated) return (Out(s, armOut * 0.6f) + Vector3.forward * 0.18f).normalized;   // elbow by the hip
                return Out(s, armOut + sway * 0.4f);
            }

            /// <summary>Resting forearm: a soft elbow (slightly forward) standing, on the thigh seated, straight lying down.</summary>
            Vector3 RestFore(int s, Posture p, float sway)
            {
                if (p == Posture.Lying || p == Posture.SideLying) return Out(s, armOut + 2f);
                if (p == Posture.Seated) return (Sag(48f) + new Vector3(s * 0.1f, 0f, 0f)).normalized;   // forearm down onto the thigh
                return (Out(s, armOut + 3f + sway * 0.4f) + Vector3.forward * 0.24f).normalized;
            }

            void Shift(float dy, float dz) => hips.position = pivot.TransformPoint(hipsRestPivot + new Vector3(0f, dy, dz));
            void Lean(float deg) => spine.rotation = Quaternion.AngleAxis(deg, pivot.right) * spine.rotation;

            /// <summary>Leg in the sagittal plane: hip flexion and knee bend in degrees.</summary>
            void Leg(int s, float hipFlex, float kneeBend) => LegDir(s, Sag(hipFlex), Sag(hipFlex - kneeBend));
            void LegDir(int s, Vector3 thighDir, Vector3 shinDir)
            {
                Aim(upperLeg[I(s)], lowerLeg[I(s)], thighDir);
                Aim(lowerLeg[I(s)], foot[I(s)], shinDir);
                AimFoot(s, shinDir);
                legPosed[I(s)] = true;
            }

            /// <summary>
            /// Natural ankle: toes point forward (body +Z) at a right angle to the shin, and up (body +Y)
            /// when the shin itself points forward, blending smoothly in between. Lying down, that means toes up.
            /// </summary>
            void AimFoot(int s, Vector3 shinDir)
            {
                var shin = shinDir.normalized;
                var fwd = Vector3.forward - Vector3.Dot(Vector3.forward, shin) * shin;
                var up = Vector3.up - Vector3.Dot(Vector3.up, shin) * shin;
                var toes = (fwd + up * Mathf.Clamp01(0.6f - fwd.magnitude)).normalized;
                // A foot under its knee carries weight: flat on the mat, so the toes don't dip into it
                toes = Vector3.Slerp(toes, Vector3.forward, Mathf.InverseLerp(-0.8f, -0.95f, shin.y));
                var f = foot[I(s)];
                var cur = f.TransformDirection(toeLocal[I(s)]);
                if (toes.sqrMagnitude > 1e-6f && cur.sqrMagnitude > 1e-6f)
                    f.rotation = Quaternion.FromToRotation(cur, pivot.TransformDirection(toes)) * f.rotation;
            }
            void Arm(int s, Vector3 upperDir, Vector3 foreDir)
            {
                Aim(upperArm[I(s)], lowerArm[I(s)], upperDir);
                Aim(lowerArm[I(s)], hand[I(s)], foreDir);
                // Palm toward the body (human request 2026-10-28: palm parallel to the waist): turn the forearm about its
                // own axis. Fades out as the forearm points sideways, where "toward the body" runs along it.
                var palmHere = palmLocal[I(s)];
                if (palmHere == Vector3.zero) return;
                var axis = (hand[I(s)].position - lowerArm[I(s)].position).normalized;
                var inward = Vector3.ProjectOnPlane(pivot.right * -s, axis);
                var now = Vector3.ProjectOnPlane(hand[I(s)].TransformDirection(palmHere), axis);
                if (now.sqrMagnitude < 1e-6f) return;
                float turn = Vector3.SignedAngle(now, inward, axis) * Mathf.Clamp01((inward.magnitude - 0.3f) / 0.4f);
                lowerArm[I(s)].rotation = Quaternion.AngleAxis(turn, axis) * lowerArm[I(s)].rotation;
            }

            /// <summary>Rotates bone so the segment to its child points along dir (body frame).</summary>
            void Aim(Transform bone, Transform child, Vector3 dir)
            {
                var cur = child.position - bone.position;
                if (cur.sqrMagnitude > 1e-8f)
                    bone.rotation = Quaternion.FromToRotation(cur, pivot.TransformDirection(dir)) * bone.rotation;
            }
        }
    }
}
