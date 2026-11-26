using NUnit.Framework;
using UnityEngine;
using UnityEngine.UI;

namespace TheraQuest.Tests
{
    /// <summary>M8.3: panel transitions stay short and end in their final state; reward effects only for counted, safe events.</summary>
    public class FeedbackMotionTests
    {
        GameObject root;

        [TearDown]
        public void TearDown()
        {
            if (root != null) Object.DestroyImmediate(root);
        }

        RectTransform Panel(Vector2 pos, Vector2 size)
        {
            root = new GameObject("Canvas", typeof(RectTransform), typeof(Canvas));
            var go = new GameObject("Panel", typeof(RectTransform), typeof(Image));
            go.transform.SetParent(root.transform, false);
            var rt = (RectTransform)go.transform;
            rt.anchorMin = rt.anchorMax = rt.pivot = new Vector2(0, 1);   // top-left, like the game's panels
            rt.anchoredPosition = pos;
            rt.sizeDelta = size;
            return rt;
        }

        // ------------------------------------------------------------------ transitions

        [Test]
        public void TransitionLength_IsKeptBetweenPoint15AndPoint25Seconds()
        {
            Assert.AreEqual(0.15f, UIKit.TransitionSeconds(0f), 1e-6f);
            Assert.AreEqual(0.15f, UIKit.TransitionSeconds(0.05f), 1e-6f);
            Assert.AreEqual(0.2f, UIKit.TransitionSeconds(0.2f), 1e-6f);
            Assert.AreEqual(0.25f, UIKit.TransitionSeconds(2f), 1e-6f);
            Assert.LessOrEqual(UIKit.TransitionDefault, UIKit.TransitionMax);
            Assert.LessOrEqual(UIKit.TransitionMax, 0.25f, "VR comfort: UI transitions 0.25 s or shorter");
        }

        [Test]
        public void Show_AskedForALongFade_StillTakesAtMostPoint25Seconds()
        {
            var p = Panel(new Vector2(10, -20), new Vector2(400, 200));
            UIKit.Show(p, false, animate: false);
            var f = UIKit.Show(p, true, true, 3f);
            Assert.AreEqual(UIKit.TransitionMax, f.Duration, 1e-6f);
            f.Step(0.25f);
            Assert.IsFalse(f.Running);
            Assert.AreEqual(1f, f.Group.alpha);
        }

        [Test]
        public void FadeIn_StartsFaintAndSmall_AndEndsFullyShownInPlace()
        {
            var p = Panel(new Vector2(10, -20), new Vector2(400, 200));
            UIKit.Show(p, false, animate: false);
            Assert.IsFalse(p.gameObject.activeSelf);

            var f = UIKit.Show(p, true);
            Assert.IsTrue(p.gameObject.activeSelf);
            Assert.IsTrue(f.Running);
            Assert.Less(f.Group.alpha, 0.01f);
            Assert.Less(p.localScale.x, 1f);
            // Scaled about its centre: the centre stays where it is at full size
            Vector2 centre = p.anchoredPosition + new Vector2(200, -100) * p.localScale.x;
            Assert.AreEqual(10f + 200f, centre.x, 0.01f);
            Assert.AreEqual(-20f - 100f, centre.y, 0.01f);

            f.Step(0.1f);
            Assert.Greater(f.Group.alpha, 0f);
            Assert.Less(f.Group.alpha, 1f);

            f.Step(1f);
            Assert.IsFalse(f.Running);
            Assert.AreEqual(1f, f.Group.alpha);
            Assert.AreEqual(Vector3.one, p.localScale);
            Assert.AreEqual(new Vector2(10, -20), p.anchoredPosition);
            Assert.IsTrue(f.Group.interactable && f.Group.blocksRaycasts);
        }

        [Test]
        public void FadeOut_EndsInactive_WithItsFullLookKeptForAPlainSetActive()
        {
            var p = Panel(new Vector2(10, -20), new Vector2(400, 200));
            var f = UIKit.Show(p, false);
            Assert.IsTrue(p.gameObject.activeSelf, "still visible while it fades out");
            Assert.IsFalse(f.Group.interactable, "no clicks while fading out");
            f.Step(0.3f);
            Assert.IsFalse(p.gameObject.activeSelf);
            Assert.AreEqual(1f, f.Group.alpha);
            Assert.AreEqual(Vector3.one, p.localScale);
            Assert.AreEqual(new Vector2(10, -20), p.anchoredPosition);
        }

        [Test]
        public void SkipToEnd_MidFade_JumpsToTheFinalState()
        {
            var p = Panel(Vector2.zero, new Vector2(300, 300));
            UIKit.Show(p, false, animate: false);
            var f = UIKit.Show(p, true);
            f.Step(0.05f);
            f.SkipToEnd();
            Assert.IsFalse(f.Running);
            Assert.IsTrue(p.gameObject.activeSelf);
            Assert.AreEqual(1f, f.Group.alpha);
            Assert.AreEqual(Vector3.one, p.localScale);

            UIKit.Show(p, false).SkipToEnd();
            Assert.IsFalse(p.gameObject.activeSelf);
        }

        [Test]
        public void WithoutAnimation_ShowAndHideSnap()
        {
            var p = Panel(Vector2.zero, new Vector2(300, 300));
            var f = UIKit.Show(p, false, animate: false);
            Assert.IsFalse(f.Running);
            Assert.IsFalse(p.gameObject.activeSelf);
            UIKit.Show(p, true, animate: false);
            Assert.IsFalse(f.Running);
            Assert.AreEqual(1f, f.Group.alpha);
        }

        [Test]
        public void Reversing_MidFade_ContinuesFromTheCurrentLook()
        {
            var p = Panel(Vector2.zero, new Vector2(300, 300));
            UIKit.Show(p, false, animate: false);
            var f = UIKit.Show(p, true);
            f.Step(0.1f);
            float a = f.Group.alpha;
            UIKit.Show(p, false);
            Assert.AreEqual(a, f.Group.alpha, 0.02f, "no jump when reversing");
            f.Step(1f);
            Assert.IsFalse(p.gameObject.activeSelf);
        }

        [Test]
        public void RootCanvas_OnlyFades_ItsScaleBelongsToItsLayout()
        {
            var c = new GameObject("World canvas", typeof(RectTransform), typeof(Canvas));
            root = c;
            c.transform.localScale = Vector3.one * 0.001f;
            UIKit.Show(c, false, animate: false);
            var f = UIKit.Show(c, true);
            f.Step(0.05f);
            Assert.AreEqual(Vector3.one * 0.001f, c.transform.localScale);
            f.Step(1f);
            Assert.AreEqual(Vector3.one * 0.001f, c.transform.localScale);
        }

        [Test]
        public void Replay_FadesAShownPanelInAgain()
        {
            var p = Panel(Vector2.zero, new Vector2(300, 300));
            var f = UIKit.Show(p, true);
            f.SkipToEnd();
            f.Replay();
            Assert.IsTrue(f.Running);
            Assert.Less(f.Group.alpha, 0.01f);
            f.Step(1f);
            Assert.AreEqual(1f, f.Group.alpha);
            Assert.IsTrue(p.gameObject.activeSelf);
        }

        // ------------------------------------------------------------------ reward rules

        static RepResult Good() => new RepResult { valid = true, accuracy = 92, error = 3f, held = 1f, heldLongEnough = true };

        [Test]
        public void GoodRep_GetsTheRewardEffect()
        {
            Assert.IsTrue(FeedbackMotion.ForRep(Good(), LiveState.Lowering, 0, 1).reward);
            Assert.IsTrue(FeedbackMotion.ForRep(Good(), LiveState.Idle, 0, 1).reward);
        }

        [Test]
        public void StopOrUnsafeRep_NeverGetsARewardEffect()
        {
            var r = Good(); r.valid = false; r.pastSafetyMax = true;
            var fx = FeedbackMotion.ForRep(r, LiveState.Unsafe, 3, 0);
            Assert.IsFalse(fx.reward);
            Assert.IsFalse(fx.comboPulse);

            // Even a rep marked valid gets nothing while STOP, a fault or too far is showing
            foreach (var s in new[] { LiveState.Unsafe, LiveState.Fault, LiveState.TooFar })
            {
                Assert.IsFalse(FeedbackMotion.RewardAllowed(s), s.ToString());
                Assert.IsFalse(FeedbackMotion.ForRep(Good(), s, 1, 2).reward, s.ToString());
                Assert.IsFalse(FeedbackMotion.ForRep(Good(), s, 1, 2).comboPulse, s.ToString());
                Assert.IsFalse(FeedbackMotion.HoldComplete(s), s.ToString());
            }
            var past = Good(); past.pastSafetyMax = true;
            Assert.IsFalse(FeedbackMotion.GoodRep(past), "past the STOP line is never good");
        }

        [Test]
        public void FaultyTooFarOrInvalidRep_GetsNoRewardEffect()
        {
            var fault = Good(); fault.valid = false; fault.fault = "Keep your back straight";
            var over = Good(); over.overshoot = true;
            var fast = Good(); fast.valid = false; fast.tooFast = true;
            var miss = Good(); miss.valid = false; miss.error = 20f;
            foreach (var r in new[] { fault, over, fast, miss })
                Assert.IsFalse(FeedbackMotion.ForRep(r, LiveState.Idle, 0, 0).reward);
        }

        [Test]
        public void ComboPulse_OnlyWhenACountedRepGrowsTheStreak()
        {
            Assert.IsFalse(FeedbackMotion.ComboPulse(0, 1), "a first rep is not a streak");
            Assert.IsTrue(FeedbackMotion.ComboPulse(1, 2));
            Assert.IsFalse(FeedbackMotion.ComboPulse(5, 0), "a reset never pulses");
            Assert.IsFalse(FeedbackMotion.ComboPulse(3, 3));
            Assert.IsTrue(FeedbackMotion.ForRep(Good(), LiveState.Idle, 4, 5).comboPulse);

            // Through the real scorer: a missed rep resets the combo and gets nothing
            var game = new GamificationManager(null);
            int before = game.Combo; game.ScoreRep(Good());
            before = game.Combo; game.ScoreRep(Good());
            Assert.IsTrue(FeedbackMotion.ForRep(Good(), LiveState.Idle, before, game.Combo).comboPulse);
            var miss = Good(); miss.valid = false;
            before = game.Combo; game.ScoreRep(miss);
            Assert.IsFalse(FeedbackMotion.ForRep(miss, LiveState.Idle, before, game.Combo).comboPulse);
        }

        [Test]
        public void HoldRing_FillsOnlyWhileHoldingInTheBand()
        {
            Assert.AreEqual(0.5f, FeedbackMotion.HoldFill(LiveState.Holding, 1f, 2f), 1e-6f);
            Assert.AreEqual(1f, FeedbackMotion.HoldFill(LiveState.Holding, 5f, 2f), 1e-6f);
            foreach (var s in new[] { LiveState.Idle, LiveState.Rising, LiveState.OnTarget, LiveState.TooFar,
                                      LiveState.Unsafe, LiveState.Fault, LiveState.Resting, LiveState.Lowering })
                Assert.AreEqual(0f, FeedbackMotion.HoldFill(s, 1f, 2f), s.ToString());
            Assert.AreEqual(0f, FeedbackMotion.HoldFill(LiveState.Holding, 1f, 0f), "no hold in this exercise");
            Assert.IsTrue(FeedbackMotion.HoldComplete(LiveState.Holding));
        }

        [Test]
        public void LevelUpAndBadgeReveal_OnlyForRealRewards()
        {
            Assert.IsTrue(FeedbackMotion.LevelUpReveal(new ProgressViews.XpSpan { fromLevel = 2, toLevel = 3 }));
            Assert.IsFalse(FeedbackMotion.LevelUpReveal(new ProgressViews.XpSpan { fromLevel = 3, toLevel = 3 }));
            Assert.IsFalse(FeedbackMotion.BadgeReveal(0, 0));
            Assert.IsFalse(FeedbackMotion.BadgeReveal(1, 0), "no new badges, no reveal");
            Assert.IsTrue(FeedbackMotion.BadgeReveal(1, 2));
            Assert.IsTrue(FeedbackMotion.BadgeReveal(2, 2));
            // A session that does not count (keyboard practice) gets no XP and no badges on the server (M7.1),
            // so the summary has no level-up or badge to reveal
            Assert.IsFalse(ProgressViews.IsCounted("keyboard"));
        }

        // ------------------------------------------------------------------ effects

        [Test]
        public void Effect_IsShort_AndRemovesItselfAtTheEnd()
        {
            var p = Panel(Vector2.zero, new Vector2(100, 100));
            var img = p.GetComponent<Image>();
            var e = EffectSprite.Attach(img, p.gameObject, 5f, 0.5f, 1.2f);
            Assert.LessOrEqual(e.Life, FeedbackMotion.MaxEffectSeconds);
            Assert.LessOrEqual(FeedbackMotion.BurstSeconds, FeedbackMotion.MaxEffectSeconds);
            Assert.LessOrEqual(FeedbackMotion.SparkleSeconds, FeedbackMotion.MaxEffectSeconds);
            e.Step(0.1f);
            Assert.IsFalse(e.Finished);
            e.Step(1f);
            Assert.IsTrue(e.Finished);
            Assert.IsTrue(p == null, "the effect's object is gone");
        }

        [Test]
        public void MissingEffectSprite_KeepsTheStaticLook()
        {
            Assert.IsNull(FeedbackMotion.Sprite("no-such-effect"));
            var p = Panel(Vector2.zero, new Vector2(100, 100));
            if (FeedbackMotion.Sprite(FeedbackMotion.SparkleName) == null)
                Assert.IsNull(FeedbackMotion.UiSparkle(p, 200f, Color.white));
            if (FeedbackMotion.Sprite(FeedbackMotion.RingName) == null)
                Assert.IsNull(FeedbackMotion.HoldRing(p, new Vector2(100, 100)));
            if (FeedbackMotion.Sprite(FeedbackMotion.BurstName) == null)
                Assert.IsNull(FeedbackMotion.WorldBurst(Vector3.zero, p, Color.white));
        }
    }
}
