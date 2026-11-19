using NUnit.Framework;
using UnityEngine;

namespace TheraQuest.Tests
{
    /// <summary>Every floating window shares one frame, and pill text stays on one line (design consistency, 2026-11-19).</summary>
    public class WindowStyleTests
    {
        GameObject root;

        [SetUp] public void SetUp() { root = new GameObject("Window style test", typeof(RectTransform)); }
        [TearDown] public void TearDown() { Object.DestroyImmediate(root); }

        [Test]
        public void Windows_ShareStripOutlineAndShadow_OnlyFillAlphaDiffers()
        {
            var glass = UIKit.Window(root.transform, new Vector2(600, 400), 0.55f);
            var solid = UIKit.Window(root.transform, new Vector2(600, 400), 0.97f);
            Assert.AreEqual(UIKit.WindowStrip, glass.strip.color);
            Assert.AreEqual(glass.strip.color, solid.strip.color);
            Assert.AreEqual(glass.outline.color, solid.outline.color);
            Assert.AreEqual(glass.shadow.color, solid.shadow.color);
            Assert.AreEqual(0.55f, glass.fill.color.a, 0.001f);
            Assert.AreEqual(0.97f, solid.fill.color.a, 0.001f);
        }

        [Test]
        public void PillText_NeverWraps_AndShrinksToFit()
        {
            var t = UIKit.Pill(root.transform, Vector2.zero, new Vector2(200, 52), UIKit.Blue, "RIGHT SHOULDER", 24, UIKit.White);
            Assert.AreEqual(TMPro.TextWrappingModes.NoWrap, t.textWrappingMode);
            Assert.IsTrue(t.enableAutoSizing);
            Assert.AreEqual(24f, t.fontSizeMax);
        }
    }
}
