using NUnit.Framework;
using UnityEngine;

namespace TheraQuest.Tests
{
    /// <summary>
    /// HUD text must not melt into the room (human request 2026-11-24): near-solid cards, and captions on their own
    /// dark box. Checked against the lightest floor and the cream menu behind them.
    /// </summary>
    public class HudReadabilityTests
    {
        static readonly Color LightFloor = new Color32(232, 196, 150, 255);   // the brightest planks in the room

        static float Luminance(Color c)
        {
            float L(float v) => v <= 0.03928f ? v / 12.92f : Mathf.Pow((v + 0.055f) / 1.055f, 2.4f);
            return 0.2126f * L(c.r) + 0.7152f * L(c.g) + 0.0722f * L(c.b);
        }

        static float Contrast(Color a, Color b)
        {
            float la = Luminance(a), lb = Luminance(b);
            return (Mathf.Max(la, lb) + 0.05f) / (Mathf.Min(la, lb) + 0.05f);
        }

        static Color Over(Color top, Color under) { var m = Color.Lerp(under, top, top.a); m.a = 1f; return m; }

        [Test]
        public void HudCards_AreNearlySolid_SoGreyLabelsReadOverTheFloor()
        {
            Assert.GreaterOrEqual(HUDController.GlassAlpha, 0.85f);
            Assert.GreaterOrEqual(HUDController.BubbleAlpha, HUDController.GlassAlpha);
            var card = UIKit.Cream; card.a = HUDController.GlassAlpha;
            foreach (var under in new[] { LightFloor, UIKit.Navy, Color.black })
                Assert.GreaterOrEqual(Contrast(UIKit.Muted, Over(card, under)), 3f, $"grey label on a card over {under}");
        }

        [Test]
        public void Captions_SitOnADarkBox_ThatKeepsWhiteTextReadableAnywhere()
        {
            Assert.GreaterOrEqual(Subtitles.BoxColor.a, 0.85f);
            foreach (var under in new[] { LightFloor, UIKit.Cream, Color.white })
                Assert.GreaterOrEqual(Contrast(UIKit.White, Over(Subtitles.BoxColor, under)), 4.5f, $"caption over {under}");
        }

        [Test]
        public void Captions_StayOutOfTheWayOfAnOpenMenu_AndComeBackAfter()
        {
            Assert.IsTrue(Subtitles.Visible(2f, true, false));
            Assert.IsFalse(Subtitles.Visible(2f, true, true), "hidden while a menu is open");
            Assert.IsFalse(Subtitles.Visible(2f, false, false), "subtitles off in Settings");
            Assert.IsFalse(Subtitles.Visible(0f, true, false), "the line has run out");
        }
    }
}
