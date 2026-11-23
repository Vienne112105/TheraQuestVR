using System;
using NUnit.Framework;
using UnityEngine;

namespace TheraQuest.Tests
{
    /// <summary>M8.4: the hologram glows only while the evaluator reports the angle inside tolerance, steadily.</summary>
    public class HologramGlowTests
    {
        Material target, live;

        [SetUp]
        public void SetUp()
        {
            target = FirstPersonGuide.HologramMaterial(HologramLook.Target);
            live = FirstPersonGuide.HologramMaterial(HologramLook.Live);
        }

        [TearDown]
        public void TearDown()
        {
            UnityEngine.Object.DestroyImmediate(target);
            UnityEngine.Object.DestroyImmediate(live);
        }

        /// <summary>What the guide does each frame: tone from the evaluator state, glow eased, materials set.</summary>
        float Run(LiveState state, float seconds, float glow = 0f)
        {
            var tone = HologramLook.StateTone(state);
            for (float t = 0f; t < seconds; t += 1f / 60f)
            {
                glow = HologramLook.NextGlow(glow, tone == Tone.Good, 1f / 60f);
                HologramLook.Apply(target, live, tone, glow);
            }
            return glow;
        }

        [Test]
        public void Glow_OnlyForInToleranceStates()
        {
            foreach (LiveState s in Enum.GetValues(typeof(LiveState)))
            {
                Run(s, 1f);
                bool inside = s == LiveState.OnTarget || s == LiveState.Holding;
                Assert.AreEqual(inside, target.GetFloat("_Glow") > 0f, "target glow for " + s);
                Assert.AreEqual(inside, live.GetFloat("_Glow") > 0f, "live glow for " + s);
            }
        }

        [Test]
        public void Glow_NeverForWarningsOrFaults()
        {
            foreach (var tone in new[] { Tone.Neutral, Tone.Warn, Tone.Bad })
            {
                HologramLook.Apply(target, live, tone, 1f);
                Assert.AreEqual(0f, target.GetFloat("_Glow"), "target glow for " + tone);
                Assert.AreEqual(0f, live.GetFloat("_Glow"), "live glow for " + tone);
            }
        }

        [Test]
        public void Glow_EasesIn_ThenHoldsSteady()
        {
            float first = HologramLook.NextGlow(0f, true, 1f / 60f);
            Assert.That(first, Is.GreaterThan(0f).And.LessThan(0.5f), "no pop on entering tolerance");
            float g = Run(LiveState.Holding, HologramLook.GlowFadeIn + 0.05f);
            Assert.AreEqual(1f, g, 1e-4f);
            // Holding inside tolerance: constant from frame to frame (no pulse)
            for (int i = 0; i < 120; i++) Assert.AreEqual(1f, HologramLook.NextGlow(g, true, 1f / 60f), 1e-6f);
        }

        [Test]
        public void Glow_DropsAtOnce_WhenTheLimbLeavesTolerance()
        {
            float g = Run(LiveState.OnTarget, 1f);
            Assert.AreEqual(1f, g, 1e-4f);
            Run(LiveState.TooFar, 1f / 60f, g);
            Assert.AreEqual(0f, target.GetFloat("_Glow"));
            Assert.AreEqual(0f, HologramLook.NextGlow(g, false, 1f / 60f));
        }

        [Test]
        public void Glow_HoldsWhilePaused()
        {
            Assert.AreEqual(0.4f, HologramLook.NextGlow(0.4f, true, 0f), 1e-6f);
        }

        [Test]
        public void LimbColours_ComeFromThePalette()
        {
            HologramLook.Apply(target, live, Tone.Neutral, 0f);
            AssertRgb(UIKit.Blue, target.color, "target");
            AssertRgb(UIKit.White, live.color, "live");
            HologramLook.Apply(target, live, Tone.Good, 1f);
            AssertRgb(UIKit.Green, target.color, "target in tolerance");
            AssertRgb(UIKit.Green, live.color, "live in tolerance");
            HologramLook.Apply(target, live, Tone.Bad, 0f);
            AssertRgb(UIKit.Red, live.color, "live past the target");
            AssertRgb(UIKit.Blue, target.color, "target stays blue on a warning");
        }

        [Test]
        public void Shader_DocumentsAndExposesEveryParameter()
        {
            var shader = Resources.Load<Shader>("Shaders/Hologram");
            Assert.IsNotNull(shader);
            Assert.IsTrue(shader.isSupported, "hologram shader compiles under URP");
            string source = System.IO.File.ReadAllText(UnityEditor.AssetDatabase.GetAssetPath(shader));
            string header = source.Substring(0, source.IndexOf("Shader \"", StringComparison.Ordinal));
            for (int i = 0; i < shader.GetPropertyCount(); i++)
            {
                string name = shader.GetPropertyName(i);
                StringAssert.Contains(name, header, name + " is documented in the shader's header");
            }
            foreach (var p in new[] { "_Rim", "_RimPower", "_Glow", "_Cutoff" }) Assert.IsTrue(target.HasProperty(p), p);
        }

        [Test]
        public void Arrow_IsSolid_LimbsStayBlended()
        {
            var arrow = FirstPersonGuide.HologramMaterial(UIKit.Orange, 0f, 0f, alwaysOnTop: true, solid: true);
            try
            {
                Assert.AreEqual((float)UnityEngine.Rendering.BlendMode.One, arrow.GetFloat("_SrcBlend"));
                Assert.AreEqual((float)UnityEngine.Rendering.BlendMode.Zero, arrow.GetFloat("_DstBlend"));
                Assert.AreEqual(1f, arrow.GetFloat("_ZWrite"));
                Assert.AreEqual((float)UnityEngine.Rendering.BlendMode.SrcAlpha, target.GetFloat("_SrcBlend"));
                Assert.AreEqual(0f, target.GetFloat("_ZWrite"));
            }
            finally { UnityEngine.Object.DestroyImmediate(arrow); }
        }

        static void AssertRgb(Color want, Color got, string what)
        {
            Assert.AreEqual(want.r, got.r, 0.01f, what + " red");
            Assert.AreEqual(want.g, got.g, 0.01f, what + " green");
            Assert.AreEqual(want.b, got.b, 0.01f, what + " blue");
        }
    }
}
