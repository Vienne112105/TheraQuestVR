using System.Collections.Generic;
using System.IO;
using NUnit.Framework;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;

namespace TheraQuest.Tests
{
    /// <summary>M8.1 / DEC-028: the game renders with URP and no material uses a Built-in shader.</summary>
    public class UrpMigrationTests
    {
        [Test]
        public void DefaultPipeline_IsUrpAsset()
        {
            var rp = GraphicsSettings.defaultRenderPipeline;
            Assert.IsNotNull(rp, "No default render pipeline asset in Graphics settings");
            StringAssert.Contains("UniversalRenderPipelineAsset", rp.GetType().Name);
        }

        [Test]
        public void EveryQualityLevel_UsesTheProjectUrpAsset()
        {
            var expected = GraphicsSettings.defaultRenderPipeline;
            Assert.IsNotNull(expected);
            for (int i = 0; i < QualitySettings.names.Length; i++)
                Assert.AreSame(expected, QualitySettings.GetRenderPipelineAssetAt(i), "Quality level " + QualitySettings.names[i]);
        }

        [Test]
        public void ProjectMaterials_UseUrpOrTextMeshProShaders()
        {
            var bad = new List<string>();
            foreach (var guid in AssetDatabase.FindAssets("t:Material", new[] { "Assets/TheraQuest", "Assets/LuceedStudio" }))
            {
                string path = AssetDatabase.GUIDToAssetPath(guid);
                if (!path.EndsWith(".mat")) continue;   // fonts and sprite assets carry their own UI materials
                var m = AssetDatabase.LoadAssetAtPath<Material>(path);
                if (m != null && !RenderPipelineCheck.IsAllowed(m.shader)) bad.Add(path + " (" + (m.shader != null ? m.shader.name : "null") + ")");
            }
            // Materials embedded in imported models (room furniture, gym, coach)
            foreach (var guid in AssetDatabase.FindAssets("t:Model", new[] { "Assets/TheraQuest", "Assets/LuceedStudio" }))
            {
                string path = AssetDatabase.GUIDToAssetPath(guid);
                foreach (var o in AssetDatabase.LoadAllAssetsAtPath(path))
                    if (o is Material m && !RenderPipelineCheck.IsAllowed(m.shader)) bad.Add(path + " :: " + m.name + " (" + (m.shader != null ? m.shader.name : "null") + ")");
            }
            Assert.IsEmpty(bad, "Materials with a non-URP shader:\n" + string.Join("\n", bad));
        }

        [Test]
        public void RuntimeMaterials_UseUrpShaders()
        {
            var opaque = FigureVisualizer.MakeMat(Color.white, false);
            var glass = FigureVisualizer.MakeMat(new Color(1, 1, 1, 0.3f), true);
            var holo = FirstPersonGuide.HologramMaterial(Color.cyan);
            foreach (var m in new[] { opaque, glass, holo })
                Assert.IsTrue(RenderPipelineCheck.IsAllowed(m.shader), m.name + " uses " + m.shader.name);
            Assert.IsTrue(opaque.shader.name.StartsWith("Universal Render Pipeline/"));
        }

        [Test]
        public void HologramShader_CompilesUnderUrp()
        {
            var s = Shader.Find("TheraQuest/Hologram");
            Assert.IsNotNull(s, "Hologram shader not found");
            Assert.IsTrue(s.isSupported, "Hologram shader is not supported");
            StringAssert.DoesNotContain("UnityCG.cginc", File.ReadAllText("Assets/TheraQuest/Resources/Shaders/Hologram.shader"));
        }
    }
}
