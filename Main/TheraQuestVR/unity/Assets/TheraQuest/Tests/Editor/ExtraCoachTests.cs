using NUnit.Framework;
using UnityEditor;
using UnityEngine;

namespace TheraQuest.Tests
{
    /// <summary>Models dropped into Resources/Coaches become extra coaches; they must be valid Humanoids.</summary>
    public class ExtraCoachTests
    {
        [Test]
        public void ExtraCoachModels_FindsMale002()
        {
            var models = HumanoidCoach.ExtraCoachModels();
            Assert.IsTrue(models.Exists(m => m.name == "Male_002"), "Male_002 should be listed");
        }

        [Test]
        public void ExtraCoachName_ReplacesUnderscores()
        {
            var go = new GameObject("Male_002");
            try { Assert.AreEqual("Male 002", HumanoidCoach.ExtraCoachName(go)); }
            finally { Object.DestroyImmediate(go); }
        }

        [Test]
        public void EveryExtraCoach_IsAValidHumanoid()
        {
            foreach (var m in HumanoidCoach.ExtraCoachModels())
            {
                var imp = AssetImporter.GetAtPath(AssetDatabase.GetAssetPath(m)) as ModelImporter;
                Assert.IsNotNull(imp, m.name);
                Assert.AreEqual(ModelImporterAnimationType.Human, imp.animationType, m.name + " must be Humanoid");
                Avatar avatar = null;
                foreach (var o in AssetDatabase.LoadAllAssetsAtPath(AssetDatabase.GetAssetPath(m))) if (o is Avatar a) avatar = a;
                Assert.IsNotNull(avatar, m.name + " has no avatar");
                Assert.IsTrue(avatar.isHuman, m.name + " avatar is not a valid Humanoid");
            }
        }
    }
}
