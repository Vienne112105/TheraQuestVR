using System.Collections.Generic;
using UnityEditor;
using UnityEngine;

namespace TheraQuest.EditorTools
{
    /// <summary>
    /// Builds a Humanoid avatar for each coach model from a straightened T-pose and saves it to
    /// Resources/CoachAvatars/&lt;model name&gt;, where HumanoidCoach picks it up for its animation clips.
    ///
    /// Why: the Little Guys models (DEC-018) ship avatars made from their own bind pose, which has a curved spine and a
    /// forward neck. Unity retargets clips relative to an avatar's reference pose, so every shared animation (the CC0
    /// idles) played on them with an extra hunch. With an upright T-pose reference the clips stand the coach up straight.
    /// The vendor's prefabs and avatars are left untouched.
    /// </summary>
    public static class CoachAvatarBuilder
    {
        public const string OutputFolder = "Assets/TheraQuest/Resources/CoachAvatars";

        static readonly string[] Models =
        {
            "Assets/LuceedStudio/Character Lab/Little Guys/Little Guys - Free Sample/Woman/Free Woman/Free Woman Tall.prefab",
            "Assets/LuceedStudio/Character Lab/Little Guys/Little Guys - Free Sample/Man/Free Man/Free Man Tall.prefab",
        };

        [MenuItem("TheraQuest/Build Coach T-Pose Avatars")]
        public static void BuildAll()
        {
            foreach (var path in Models)
            {
                var prefab = AssetDatabase.LoadAssetAtPath<GameObject>(path);
                if (prefab == null) { Debug.LogWarning($"[TheraQuest] Coach model not found: {path}"); continue; }
                Build(prefab);
            }
            AssetDatabase.SaveAssets();
        }

        public static Avatar Build(GameObject prefab)
        {
            var src = prefab.GetComponentInChildren<Animator>(true);
            if (src == null || src.avatar == null || !src.avatar.isHuman)
            {
                Debug.LogWarning($"[TheraQuest] {prefab.name} has no Humanoid avatar to start from.");
                return null;
            }
            var go = Object.Instantiate(prefab);
            try
            {
                go.transform.SetPositionAndRotation(Vector3.zero, Quaternion.identity);
                var anim = go.GetComponentInChildren<Animator>(true);
                var desc = src.avatar.humanDescription;
                var bones = new Dictionary<string, Transform>();
                foreach (var t in anim.GetComponentsInChildren<Transform>(true)) bones[t.name] = t;
                Transform B(string human)
                {
                    foreach (var h in desc.human)
                        if (h.humanName == human && bones.TryGetValue(h.boneName, out var t)) return t;
                    return null;
                }

                // Straighten the model in its own frame: it faces +Z, so its left is -X
                var root = anim.transform;
                Vector3 up = root.up, left = -root.right, right = root.right, down = -root.up;
                Point(B("Hips"), B("Spine"), up);
                Point(B("Spine"), B("Chest"), up);
                Point(B("Chest"), B("UpperChest") ?? B("Neck"), up);
                Point(B("UpperChest"), B("Neck"), up);
                Point(B("Neck"), B("Head"), up);
                Point(B("LeftUpperArm"), B("LeftLowerArm"), left);
                Point(B("LeftLowerArm"), B("LeftHand"), left);
                Point(B("RightUpperArm"), B("RightLowerArm"), right);
                Point(B("RightLowerArm"), B("RightHand"), right);
                Point(B("LeftUpperLeg"), B("LeftLowerLeg"), down);
                Point(B("LeftLowerLeg"), B("LeftFoot"), down);
                Point(B("RightUpperLeg"), B("RightLowerLeg"), down);
                Point(B("RightLowerLeg"), B("RightFoot"), down);
                // Fingers straight along the hand too: the pack's bind pose has them curled, so the clips (which carry no
                // finger motion) left the coach making fists
                foreach (var side in new[] { "Left", "Right" })
                {
                    var along = side == "Left" ? left : right;
                    foreach (var finger in new[] { "Index", "Middle", "Ring", "Little" })
                    {
                        Point(B($"{side} {finger} Proximal"), B($"{side} {finger} Intermediate"), along);
                        Point(B($"{side} {finger} Intermediate"), B($"{side} {finger} Distal"), along);
                    }
                }

                var skeleton = new List<SkeletonBone>();
                foreach (var t in anim.GetComponentsInChildren<Transform>(true))
                    skeleton.Add(new SkeletonBone { name = t.name, position = t.localPosition, rotation = t.localRotation, scale = t.localScale });
                desc.skeleton = skeleton.ToArray();

                var avatar = AvatarBuilder.BuildHumanAvatar(anim.gameObject, desc);
                if (!avatar.isValid || !avatar.isHuman)
                {
                    Debug.LogWarning($"[TheraQuest] T-pose avatar for {prefab.name} is not valid.");
                    return null;
                }
                avatar.name = prefab.name + " (T-pose)";
                if (!AssetDatabase.IsValidFolder(OutputFolder))
                    AssetDatabase.CreateFolder("Assets/TheraQuest/Resources", "CoachAvatars");
                string outPath = $"{OutputFolder}/{prefab.name}.asset";
                AssetDatabase.DeleteAsset(outPath);
                AssetDatabase.CreateAsset(avatar, outPath);
                return avatar;
            }
            finally
            {
                Object.DestroyImmediate(go);
            }
        }

        /// <summary>Turns bone so the direction to child becomes dir (world), keeping its twist as close as possible.</summary>
        static void Point(Transform bone, Transform child, Vector3 dir)
        {
            if (bone == null || child == null) return;
            var cur = child.position - bone.position;
            if (cur.sqrMagnitude < 1e-8f) return;
            bone.rotation = Quaternion.FromToRotation(cur, dir) * bone.rotation;
        }
    }
}
