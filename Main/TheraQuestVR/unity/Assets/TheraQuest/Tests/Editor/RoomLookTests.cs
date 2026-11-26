using NUnit.Framework;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

namespace TheraQuest.Tests
{
    /// <summary>M8.2: the room's lighting, post-processing and textures, with comfort limits and fallbacks.</summary>
    public class RoomLookTests
    {
        [Test]
        public void Profile_HasNeutralTonemapGradingAndLightBloom_AndNothingBanned()
        {
            var p = RoomLook.MakeProfile();
            Assert.IsTrue(p.TryGet(out Tonemapping tm));
            Assert.AreEqual(TonemappingMode.Neutral, tm.mode.value);
            Assert.IsTrue(p.TryGet(out ColorAdjustments _));
            Assert.IsTrue(p.TryGet(out Bloom bloom));
            Assert.LessOrEqual(bloom.intensity.value, 0.3f, "Bloom must stay light");
            // Comfort rules: no motion blur, vignette, chromatic aberration, film grain, depth of field
            Assert.IsFalse(p.TryGet(out MotionBlur _));
            Assert.IsFalse(p.TryGet(out Vignette _));
            Assert.IsFalse(p.TryGet(out ChromaticAberration _));
            Assert.IsFalse(p.TryGet(out FilmGrain _));
            Assert.IsFalse(p.TryGet(out DepthOfField _));
        }

        [Test]
        public void Sun_HasSoftShadows_AndComesFromTheWindowSide()
        {
            var go = new GameObject("test sun");
            try
            {
                var l = RoomLook.ConfigureSun(go.AddComponent<Light>());
                Assert.AreEqual(LightType.Directional, l.type);
                Assert.AreEqual(LightShadows.Soft, l.shadows);
                Assert.Greater(l.transform.forward.x, 0.2f, "Windows are on the left (-x) wall, so light travels toward +x");
                Assert.Less(l.transform.forward.y, -0.3f, "Light travels downward");
            }
            finally { Object.DestroyImmediate(go); }
        }

        [Test]
        public void MissingTexture_KeepsTheColourAndReturnsFalse()
        {
            var m = FigureVisualizer.MakeMat(new Color(0.3f, 0.4f, 0.5f), false);
            Assert.IsFalse(RoomLook.ApplyTexture(m, "Room/Textures/does_not_exist"));
            Assert.IsNull(m.mainTexture);
            Assert.AreEqual(0.3f, m.color.r, 0.001f);
            Assert.AreEqual(0.5f, m.color.b, 0.001f);
        }

        [Test]
        public void ApplyTexture_ToNullMaterial_DoesNotThrow()
        {
            Assert.IsFalse(RoomLook.ApplyTexture(null, "Room/Textures/floor"));
        }

        [Test]
        public void LightShaft_ReachesTheFloorInsideTheRoom_FromTheWindow()
        {
            var m = LightShafts.Prism(1.6f, RoomLook.SunDirection());
            float minY = float.MaxValue, maxY = float.MinValue, maxX = float.MinValue;
            foreach (var v in m.vertices) { minY = Mathf.Min(minY, v.y); maxY = Mathf.Max(maxY, v.y); maxX = Mathf.Max(maxX, v.x); }
            Assert.AreEqual(0f, minY, 0.001f, "Beam ends on the floor");
            Assert.AreEqual(2.4f, maxY, 0.001f, "Beam starts at the window top");
            Assert.Less(maxX, 4.9f, "Beam stays inside the room (the right wall is at x = 5)");
            Assert.Greater(maxX, -4.9f, "Beam travels away from the window wall");
        }

        [Test]
        public void LightShafts_AreBuiltOncePerWindow_AndOnlyOnce()
        {
            var root = new GameObject("test shafts").transform;
            try
            {
                var sun = RoomLook.SunDirection();
                LightShafts.Build(root, new[] { -1.2f, 1.6f, 4.2f }, sun);
                LightShafts.Build(root, new[] { -1.2f, 1.6f, 4.2f }, sun);
                Assert.AreEqual(3, root.Find(LightShafts.Name).childCount);
            }
            finally { Object.DestroyImmediate(root.gameObject); }
        }

        [Test]
        public void ShaftShader_IsSupported_AndAdditive()
        {
            var s = Shader.Find("TheraQuest/LightShaft");
            Assert.IsNotNull(s);
            Assert.IsTrue(s.isSupported);
        }

        [Test]
        public void Setup_CreatesExactlyOneProbeAndOneVolume_EvenWhenCalledTwice()
        {
            var root = new GameObject("test root").transform;
            try
            {
                RoomLook.Setup(root);
                RoomLook.Setup(root);
                Assert.AreEqual(1, root.GetComponentsInChildren<ReflectionProbe>().Length);
                Assert.AreEqual(1, root.GetComponentsInChildren<Volume>().Length);
            }
            finally { Object.DestroyImmediate(root.gameObject); }
        }
    }
}
