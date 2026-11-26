using NUnit.Framework;
using UnityEngine;

namespace TheraQuest.Tests
{
    /// <summary>M8.2: the coach repaint is found by model name and never touches the pack's material asset.</summary>
    public class CoachReskinTests
    {
        [TestCase("Free Woman Tall", "CoachTextures/coach_woman")]
        [TestCase("Free Woman", "CoachTextures/coach_woman")]
        [TestCase("Free Man Tall", "CoachTextures/coach_man")]
        [TestCase("Free Man", "CoachTextures/coach_man")]
        public void PathFor_PicksTheRightPicture(string model, string expected) => Assert.AreEqual(expected, CoachReskin.PathFor(model));

        [Test]
        public void PathFor_UnknownModel_IsNull() => Assert.IsNull(CoachReskin.PathFor("Robot"));

        [Test]
        public void WomanRepaintExistsAndMatchesThePackSize()
        {
            foreach (var p in new[] { "CoachTextures/coach_woman" })   // the male coach keeps the pack's own look (human request 2026-11-14)
            {
                var t = Resources.Load<Texture2D>(p);
                Assert.IsNotNull(t, p);
                Assert.AreEqual(1024, t.width, p);
            }
        }

        [Test]
        public void MaleCoach_HasNoRepaint_AndKeepsThePacksLook()
        {
            Assert.IsNull(Resources.Load<Texture2D>("CoachTextures/coach_man"));
            var go = new GameObject("x");
            try { Assert.IsFalse(CoachReskin.Apply(go, "Free Man Tall")); }
            finally { Object.DestroyImmediate(go); }
        }

        [Test]
        public void Apply_UnknownModelOrNull_ReturnsFalse()
        {
            Assert.IsFalse(CoachReskin.Apply(null, "Free Woman"));
            var go = new GameObject("x");
            try { Assert.IsFalse(CoachReskin.Apply(go, "Robot")); }
            finally { Object.DestroyImmediate(go); }
        }
    }
}
