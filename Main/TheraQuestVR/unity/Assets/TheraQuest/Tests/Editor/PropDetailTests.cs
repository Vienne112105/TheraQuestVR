using NUnit.Framework;
using UnityEngine;

namespace TheraQuest.Tests
{
    /// <summary>M8.2: the room models get surface detail, keep their colour, and stay URP.</summary>
    public class PropDetailTests
    {
        [TestCase("wood", PropDetail.Kind.Wood)]
        [TestCase("woodDark", PropDetail.Kind.Wood)]
        [TestCase("carpet", PropDetail.Kind.Fabric)]
        [TestCase("metal2", PropDetail.Kind.Metal)]
        [TestCase("pink", PropDetail.Kind.Rubber)]
        [TestCase("plant", PropDetail.Kind.Soft)]
        public void KindOf_MatchesPackMaterialNames(string name, PropDetail.Kind expected) =>
            Assert.AreEqual(expected, PropDetail.KindOf(name));

        [Test]
        public void For_KeepsColourAndName_AndUsesTheDetailShader()
        {
            var src = FigureVisualizer.MakeMat(new Color(0.6f, 0.4f, 0.2f), false);
            src.name = "wood";
            var m = PropDetail.For(src);
            Assert.AreEqual("TheraQuest/PropDetail", m.shader.name);
            Assert.AreEqual("wood", m.name);
            Assert.AreEqual(0.6f, m.GetColor("_BaseColor").r, 0.001f);
            Assert.IsTrue(RenderPipelineCheck.IsAllowed(m.shader));
            Assert.IsNotNull(m.GetTexture("_GrainTex"));
        }

        [Test]
        public void For_Null_ReturnsNull() => Assert.IsNull(PropDetail.For(null));

        [Test]
        public void Shader_IsSupported()
        {
            var s = Shader.Find("TheraQuest/PropDetail");
            Assert.IsNotNull(s);
            Assert.IsTrue(s.isSupported);
        }

        [Test]
        public void Grain_IsTileableAndHasContrast()
        {
            foreach (PropDetail.Kind k in System.Enum.GetValues(typeof(PropDetail.Kind)))
            {
                var t = PropDetail.Grain(k);
                float lo = 1f, hi = 0f;
                foreach (var c in t.GetPixels32()) { lo = Mathf.Min(lo, c.r / 255f); hi = Mathf.Max(hi, c.r / 255f); }
                Assert.Greater(hi - lo, 0.8f, k + " grain is too flat");
                Assert.AreEqual(TextureWrapMode.Repeat, t.wrapMode);
            }
        }
    }
}
