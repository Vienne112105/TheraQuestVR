using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

namespace TheraQuest.EditorTools
{
    /// <summary>
    /// Menu: TheraQuest > Create Scene
    /// Builds the whole TheraQuest scene in one click and wires every reference,
    /// so you don't have to drag components around by hand.
    /// Coach: select a Humanoid character (model or prefab) in the Project window before running it,
    /// or add them to Humanoid Coach > Characters afterwards. With nothing selected it lists every
    /// model in a Coaches folder (the patient picks one on the start screen); with none the
    /// primitive figure is used. A looping idle (e.g. Mixamo "Breathing Idle") in a CoachAnimations folder
    /// becomes the coach's resting animation.
    /// </summary>
    public static class TheraQuestSceneBuilder
    {
        const string Folder = "Assets/TheraQuest";
        const string ScenePath = Folder + "/TheraQuest.unity";

        [MenuItem("TheraQuest/Create Scene")]
        public static void CreateScene()
        {
            if (!Application.isBatchMode && !EditorSceneManager.SaveCurrentModifiedScenesIfUserWantsTo()) return;
            var selected = Selection.activeGameObject;   // read before the new scene clears the selection
            var characters = selected != null && EditorUtility.IsPersistent(selected) && IsHumanoid(selected)
                ? new[] { new TheraQuest.HumanoidCoach.Option { name = selected.name, model = selected } }
                : FindCoachAvatars();
            var scene = EditorSceneManager.NewScene(NewSceneSetup.DefaultGameObjects, NewSceneMode.Single);

            // Camera rig ---------------------------------------------------------
            var cam = Camera.main;
            var rig = new GameObject("Rig");
            cam.transform.SetParent(rig.transform, false);
            cam.transform.localPosition = new Vector3(0, 1.55f, 0);
            cam.nearClipPlane = 0.05f;
            cam.clearFlags = CameraClearFlags.SolidColor;
            cam.backgroundColor = new Color(0.05f, 0.10f, 0.11f);
            var head = cam.gameObject.AddComponent<TheraQuest.HeadTracking>();

            // Room -----------------------------------------------------------------
            var floorMat = SaveMat("Floor", new Color(0.16f, 0.22f, 0.23f));
            var wallMat = SaveMat("Wall", new Color(0.82f, 0.88f, 0.86f));
            var matMat = SaveMat("Exercise Mat", new Color(0.04f, 0.54f, 0.49f));
            Block("Floor", new Vector3(0, -0.05f, 2), new Vector3(10, 0.1f, 10), floorMat);
            Block("Back wall", new Vector3(0, 1.75f, 5.5f), new Vector3(10, 3.5f, 0.1f), wallMat);
            Block("Exercise mat", new Vector3(0, 0.005f, 2.6f), new Vector3(1.6f, 0.01f, 1.2f), matMat);
            var light = Object.FindAnyObjectByType<Light>();
            if (light != null) light.transform.rotation = Quaternion.Euler(45, -20, 0);

            // Systems -----------------------------------------------------------------
            var root = new GameObject("TheraQuest");
            var receiver = root.AddComponent<TheraQuest.MotionReceiver>();
            var motion = root.AddComponent<TheraQuest.MotionInput>();
            motion.receiver = receiver;
            var api = root.AddComponent<TheraQuest.ApiClient>();
            var fb = root.AddComponent<TheraQuest.FeedbackManager>();

            var hudGo = new GameObject("HUD");
            hudGo.transform.SetParent(root.transform, false);
            var hud = hudGo.AddComponent<TheraQuest.HUDController>();

            var figGo = new GameObject("Primitive Figure (fallback)");
            figGo.transform.position = new Vector3(0, 0, 2.6f);
            var figure = figGo.AddComponent<TheraQuest.FigureVisualizer>();

            var coachGo = new GameObject("Humanoid Coach");
            coachGo.transform.SetPositionAndRotation(new Vector3(0, 0, 2f), Quaternion.Euler(0, 180, 0));   // 2 m ahead, facing the player
            var coach = coachGo.AddComponent<TheraQuest.HumanoidCoach>();
            coach.characters = characters;
            foreach (var opt in characters)
            {
                if (opt.name.Contains("Female") && coach.femaleModel == null) coach.femaleModel = opt.model;
                else if (opt.name.Contains("Male") && coach.maleModel == null) coach.maleModel = opt.model;
            }
            coach.fallback = figure;
            coach.idleClip = FindIdleClip();

            var session = root.AddComponent<TheraQuest.SessionManager>();
            session.api = api;
            session.motion = motion;
            session.receiver = receiver;
            session.feedback = fb;
            session.hud = hud;
            session.figure = figure;
            session.coach = coach;
            session.head = head;

            // Project settings this app needs ---------------------------------------------
            PlayerSettings.insecureHttpOption = InsecureHttpOption.AlwaysAllowed; // server runs on http://localhost
            PlayerSettings.runInBackground = true;                                // keep running when the tracker window has focus

            EditorSceneManager.SaveScene(scene, ScenePath);
            EditorBuildSettings.scenes = new[] { new EditorBuildSettingsScene(ScenePath, true) };
            Selection.activeGameObject = characters.Length > 0 ? root : coachGo;
            Debug.Log("[TheraQuest] Scene created at " + ScenePath + (characters.Length > 0
                ? $". Coaches: {string.Join(", ", System.Array.ConvertAll(characters, c => c.name))}. Press Play."
                : ". Add a Humanoid character to Humanoid Coach > Characters, or press Play to use the primitive figure."));
        }

        /// <summary>Every Humanoid model under a Coaches folder, categorized into Female Coach and Male Coach.</summary>
        static TheraQuest.HumanoidCoach.Option[] FindCoachAvatars()
        {
            var list = new System.Collections.Generic.List<TheraQuest.HumanoidCoach.Option>();
            var femaleModels = new System.Collections.Generic.List<GameObject>();
            var maleModels = new System.Collections.Generic.List<GameObject>();
            var otherModels = new System.Collections.Generic.List<GameObject>();

            foreach (var guid in AssetDatabase.FindAssets("t:Model"))
            {
                string path = AssetDatabase.GUIDToAssetPath(guid).Replace('\\', '/');
                if (path.IndexOf(CoachModelImporter.Folder, System.StringComparison.OrdinalIgnoreCase) < 0) continue;
                var go = AssetDatabase.LoadAssetAtPath<GameObject>(path);
                if (go == null || !IsHumanoid(go)) continue;

                string lower = path.ToLowerInvariant();
                string goName = go.name.ToLowerInvariant();

                if (lower.Contains("female") || goName.Contains("female"))
                    femaleModels.Add(go);
                else if (lower.Contains("male") || goName.Contains("male"))
                    maleModels.Add(go);
                else
                    otherModels.Add(go);
            }

            GameObject pickPreferred(System.Collections.Generic.List<GameObject> candidates)
            {
                foreach (var c in candidates)
                    if (c.name.Contains("Casual") && !c.name.StartsWith("Smooth_")) return c;
                foreach (var c in candidates)
                    if (c.name.Contains("Casual")) return c;
                return candidates.Count > 0 ? candidates[0] : null;
            }

            var femalePrimary = pickPreferred(femaleModels);
            if (femalePrimary != null)
                list.Add(new TheraQuest.HumanoidCoach.Option { name = "Female Coach", model = femalePrimary });

            var malePrimary = pickPreferred(maleModels);
            if (malePrimary != null)
                list.Add(new TheraQuest.HumanoidCoach.Option { name = "Male Coach", model = malePrimary });

            foreach (var o in otherModels)
                list.Add(new TheraQuest.HumanoidCoach.Option { name = ObjectNames.NicifyVariableName(o.name.Replace('_', ' ')), model = o });

            return list.ToArray();
        }

        /// <summary>First looping clip with "idle" in its name under a CoachAnimations folder (e.g. Mixamo "Breathing Idle").</summary>
        static AnimationClip FindIdleClip()
        {
            AnimationClip any = null;
            foreach (var guid in AssetDatabase.FindAssets("t:AnimationClip"))
            {
                string path = AssetDatabase.GUIDToAssetPath(guid);
                if (!path.Contains(CoachModelImporter.AnimationFolder)) continue;
                foreach (var asset in AssetDatabase.LoadAllAssetsAtPath(path))
                {
                    if (!(asset is AnimationClip clip) || clip.name.StartsWith("__preview__")) continue;
                    if (clip.name.ToLowerInvariant().Contains("idle") || path.ToLowerInvariant().Contains("idle")) return clip;
                    if (any == null) any = clip;
                }
            }
            return any;
        }

        static bool IsHumanoid(GameObject go)
        {
            if (go == null) return false;
            var anim = go.GetComponentInChildren<Animator>(true);
            if (anim != null && anim.avatar != null && (anim.avatar.isHuman || anim.avatar.isValid)) return true;
            string path = AssetDatabase.GetAssetPath(go);
            if (!string.IsNullOrEmpty(path))
            {
                foreach (var asset in AssetDatabase.LoadAllAssetsAtPath(path))
                    if (asset is Avatar av && (av.isHuman || av.isValid)) return true;
            }
            // Check if it has a rigged skeleton with arms and legs
            var transforms = go.GetComponentsInChildren<Transform>(true);
            bool hasArm = false, hasLeg = false;
            foreach (var t in transforms)
            {
                string n = t.name.ToLowerInvariant();
                if (n.Contains("upperarm") || n.Contains("arm")) hasArm = true;
                if (n.Contains("upperleg") || n.Contains("leg") || n.Contains("thigh")) hasLeg = true;
            }
            return hasArm && hasLeg;
        }

        static GameObject Block(string name, Vector3 pos, Vector3 scale, Material mat)
        {
            var go = GameObject.CreatePrimitive(PrimitiveType.Cube);
            go.name = name;
            go.transform.position = pos;
            go.transform.localScale = scale;
            go.GetComponent<Renderer>().sharedMaterial = mat;
            return go;
        }

        static Material SaveMat(string name, Color color)
        {
            string path = $"{Folder}/Materials/{name}.mat";
            var existing = AssetDatabase.LoadAssetAtPath<Material>(path);
            if (existing != null) return existing;
            if (!AssetDatabase.IsValidFolder(Folder + "/Materials")) AssetDatabase.CreateFolder(Folder, "Materials");
            var tmp = GameObject.CreatePrimitive(PrimitiveType.Cube);
            var mat = new Material(tmp.GetComponent<Renderer>().sharedMaterial) { color = color };
            Object.DestroyImmediate(tmp);
            AssetDatabase.CreateAsset(mat, path);
            return mat;
        }
    }
}
