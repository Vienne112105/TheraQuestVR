using UnityEditor;
using UnityEngine;

namespace TheraQuest.EditorTools
{
    /// <summary>
    /// Import settings for coach characters and their animations, so they work with no manual setup:
    ///   .../Coaches/...          characters (e.g. Assets/ThirdParty/Coaches: Quaternius Ultimate Modular
    ///                            Men / Women (CC0), or Mixamo characters downloaded as "FBX for Unity", T-pose):
    ///                            Humanoid rig, no animations, and smooth normals so low-poly models don't
    ///                            look faceted. TheraQuest > Create Scene picks them up.
    ///   .../CoachAnimations/...  Mixamo animations such as "Breathing Idle" (download "Without Skin"):
    ///                            Humanoid, looping, root motion baked in place. Create Scene uses the first
    ///                            clip with "idle" in its name for the coach's resting limbs.
    /// </summary>
    public class CoachModelImporter : AssetPostprocessor
    {
        public const string Folder = "/Coaches/";
        public const string AnimationFolder = "/CoachAnimations/";

        public override uint GetVersion() => 5;

        static bool In(string path, string folder) => path.Replace('\\', '/').IndexOf(folder, System.StringComparison.OrdinalIgnoreCase) >= 0;

        void OnPreprocessModel()
        {
            var importer = (ModelImporter)assetImporter;
            if (In(assetPath, Folder))
            {
                importer.animationType = ModelImporterAnimationType.Human;
                importer.avatarSetup = ModelImporterAvatarSetup.CreateFromThisModel;
                MapQuaterniusRig(importer);
                importer.importAnimation = false;
                // Smooth shading: blend facets that meet at less than 80°, keep sharper creases crisp
                importer.importNormals = ModelImporterNormals.Calculate;
                importer.normalCalculationMode = ModelImporterNormalCalculationMode.AreaAndAngleWeighted;
                importer.normalSmoothingAngle = 80f;
                importer.importTangents = ModelImporterTangents.CalculateMikk;
            }
            else if (In(assetPath, AnimationFolder))
            {
                importer.animationType = ModelImporterAnimationType.Human;
                importer.avatarSetup = ModelImporterAvatarSetup.CreateFromThisModel;
                importer.importAnimation = true;
            }
        }

        // Quaternius Ultimate Modular rigs keep the feet as IK bones under the root ("Bone/Foot.L"), so Unity's automatic
        // mapping finds no feet and the avatar is not Humanoid: idle clips then don't play on the coach. Map the rig by
        // hand, with the ankle points (LowerLeg.*_end, children of the lower legs) as the feet; HumanoidCoach re-attaches
        // the Foot.* bones (the shoes) to the lower legs at runtime. Bone names come from the skeleton Unity recorded on
        // the previous import, so a brand-new model of this kind becomes Humanoid on its first reimport.
        static readonly string[,] QuaterniusMap =
        {
            { "Hips", "Body" }, { "Spine", "Hips" }, { "Chest", "Abdomen" }, { "UpperChest", "Torso" }, { "Neck", "Neck" }, { "Head", "Head" },
            { "LeftShoulder", "Shoulder.L" }, { "LeftUpperArm", "UpperArm.L" }, { "LeftLowerArm", "LowerArm.L" }, { "LeftHand", "Palm.L" },
            { "RightShoulder", "Shoulder.R" }, { "RightUpperArm", "UpperArm.R" }, { "RightLowerArm", "LowerArm.R" }, { "RightHand", "Palm.R" },
            { "LeftUpperLeg", "UpperLeg.L" }, { "LeftLowerLeg", "LowerLeg.L" }, { "LeftFoot", "LowerLeg.L_end" },
            { "RightUpperLeg", "UpperLeg.R" }, { "RightLowerLeg", "LowerLeg.R" }, { "RightFoot", "LowerLeg.R_end" },
        };

        static void MapQuaterniusRig(ModelImporter importer)
        {
            var desc = importer.humanDescription;
            var bones = new System.Collections.Generic.HashSet<string>();
            if (desc.skeleton != null) foreach (var s in desc.skeleton) bones.Add(s.name);
            for (int i = 0; i < QuaterniusMap.GetLength(0); i++)
                if (!bones.Contains(QuaterniusMap[i, 1])) return;   // not this rig (e.g. Mixamo): keep Unity's own mapping
            var human = new HumanBone[QuaterniusMap.GetLength(0)];
            for (int i = 0; i < human.Length; i++)
            {
                human[i] = new HumanBone { humanName = QuaterniusMap[i, 0], boneName = QuaterniusMap[i, 1] };
                human[i].limit.useDefaultValues = true;
            }
            desc.human = human;
            importer.humanDescription = desc;
        }

        void OnPreprocessAnimation()
        {
            if (!In(assetPath, AnimationFolder)) return;
            var importer = (ModelImporter)assetImporter;
            var clips = importer.defaultClipAnimations;
            foreach (var c in clips)
            {
                c.loopTime = true;              // idles loop forever
                c.lockRootRotation = true;      // "Bake into pose": the coach stays where it was placed
                c.lockRootHeightY = true;
                c.lockRootPositionXZ = true;
                c.keepOriginalOrientation = true;
                c.keepOriginalPositionY = true;
                c.keepOriginalPositionXZ = true;
            }
            importer.clipAnimations = clips;
        }
    }
}
