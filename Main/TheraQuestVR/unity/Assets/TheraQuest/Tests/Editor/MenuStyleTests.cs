using NUnit.Framework;
using UnityEngine;

namespace TheraQuest.Tests
{
    /// <summary>M8.5: one type scale, one button style with distinct states, pages that never shrink, comfortable distances.</summary>
    public class MenuStyleTests
    {
        GameObject root;

        [SetUp] public void SetUp() { root = new GameObject("Menu style test", typeof(RectTransform)); }
        [TearDown] public void TearDown() { Object.DestroyImmediate(root); }

        static readonly UIKit.ButtonState[] Shown =
            { UIKit.ButtonState.Normal, UIKit.ButtonState.Highlighted, UIKit.ButtonState.Selected, UIKit.ButtonState.Pressed };

        /// <summary>A translucent fill as seen on the cream menu card.</summary>
        static Color OnCard(Color c) { var m = Color.Lerp(UIKit.Cream, c, c.a); m.a = 1f; return m; }

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

        [Test]
        public void ButtonStates_HaveDistinctFills()
        {
            for (int i = 0; i < Shown.Length; i++)
                for (int j = i + 1; j < Shown.Length; j++)
                {
                    Color a = OnCard(UIKit.Buttons.Fill(Shown[i])), b = OnCard(UIKit.Buttons.Fill(Shown[j]));
                    float diff = Mathf.Abs(a.r - b.r) + Mathf.Abs(a.g - b.g) + Mathf.Abs(a.b - b.b);
                    Assert.Greater(diff, 0.15f, $"{Shown[i]} and {Shown[j]} look alike");
                }
        }

        [Test]
        public void ButtonStates_TextIsReadableOnItsFill()
        {
            foreach (var s in Shown)
                Assert.GreaterOrEqual(Contrast(OnCard(UIKit.Buttons.Fill(s)), UIKit.Buttons.Text(s)), 4.5f, s.ToString());
        }

        [Test]
        public void ButtonState_Precedence_DisabledThenPressedThenSelectedThenHighlighted()
        {
            Assert.AreEqual(UIKit.ButtonState.Disabled, UIKit.StateOf(false, true, true, true));
            Assert.AreEqual(UIKit.ButtonState.Pressed, UIKit.StateOf(true, true, true, true));
            Assert.AreEqual(UIKit.ButtonState.Selected, UIKit.StateOf(true, false, true, true));
            Assert.AreEqual(UIKit.ButtonState.Highlighted, UIKit.StateOf(true, false, false, true));
            Assert.AreEqual(UIKit.ButtonState.Normal, UIKit.StateOf(true, false, false, false));
        }

        [Test]
        public void ButtonLook_FollowsPointerAndSelection()
        {
            var bg = UIKit.Box(root.transform, Vector2.zero, new Vector2(400, 70), UIKit.Row, "Row", true);
            var label = UIKit.Label(bg.transform, Vector2.zero, new Vector2(400, 70), UIKit.TypeSize.Item, UIKit.Ink);
            var look = UIKit.Look(bg, label);
            Assert.AreEqual(UIKit.Buttons.normal, bg.color);
            look.OnPointerEnter(null);
            Assert.AreEqual(UIKit.Buttons.highlighted, bg.color);
            look.OnPointerDown(null);
            Assert.AreEqual(UIKit.Buttons.pressed, bg.color);
            look.OnPointerUp(null);
            look.OnPointerExit(null);
            look.selected = true; look.Apply();
            Assert.AreEqual(UIKit.Buttons.selected, bg.color);
            Assert.AreEqual(UIKit.Buttons.selectedText, label.color);
        }

        [Test]
        public void TypeScale_IsOrdered_AndHeadingUsesTheDisplayFont()
        {
            Assert.Greater(UIKit.TypeSize.Hero, UIKit.TypeSize.Title);
            Assert.Greater(UIKit.TypeSize.Title, UIKit.TypeSize.Heading);
            Assert.Greater(UIKit.TypeSize.Heading, UIKit.TypeSize.Item);
            Assert.Greater(UIKit.TypeSize.Item, UIKit.TypeSize.Body);
            Assert.Greater(UIKit.TypeSize.Body, UIKit.TypeSize.Label);
            Assert.Greater(UIKit.TypeSize.Label, UIKit.TypeSize.Caption);
            Assert.GreaterOrEqual(UIKit.TypeSize.Heading, UIKit.DisplaySize);
            Assert.Less(UIKit.TypeSize.Item, UIKit.DisplaySize, "row text stays in the body font");
        }

        /// <summary>Height a Body-size text block takes for the given text, as the menu measures it.</summary>
        float BodyHeight(string text, int size = UIKit.TypeSize.Body)
        {
            var t = UIKit.Label(root.transform, Vector2.zero, new Vector2(MenuController.ContentWidth, 40), size, UIKit.Ink);
            t.text = text;
            t.ForceMeshUpdate();
            return t.preferredHeight;
        }

        [Test]
        public void EveryMenuPage_FitsWithoutShrinking_SoNoTextIsSmallerThanCaption()
        {
            float oneLine = BodyHeight("P-001 · Knee rehab");
            float twoLines = BodyHeight("P-001 · Total knee replacement, early protocol · Phase 2: strength and range of motion · level 12");
            Assert.Greater(twoLines, oneLine * 1.5f, "the long subtitle wraps (worst case)");
            float threeLines = BodyHeight("Today: 6 exercises · about 14 minutes\nOffline: your results are saved and sent to your therapist later.\n2 saved sessions are waiting to be sent to your therapist.");
            float therapistInfo = BodyHeight("Codes like P-001. For other codes, start the app with -patient CODE.");
            float headline = BodyHeight("<size=" + UIKit.TypeSize.Heading + ">Level 12</size>   45% of the way to level 13\n<b>3</b> day streak\n<b>9</b> of 12 sessions completed\n<b>4</b> of 7 badges earned\n\nOffline: this is your progress from the last time the app was connected.");
            float badgesLine = BodyHeight("<size=" + UIKit.TypeSize.Heading + ">7</size> of 8 badges earned");

            var pages = new (string name, float h)[]
            {
                ("Main (7 rows, wrapped subtitle, 3 info lines)", MenuController.PageHeight(twoLines, threeLines, 7, 0f, false)),
                ("Pause", MenuController.PageHeight(oneLine, oneLine, 5, 0f, false)),
                ("Settings", MenuController.PageHeight(oneLine, 0f, 7, 0f, false)),
                ("Therapist PIN", MenuController.PageHeight(oneLine, oneLine, 6, 0f, false)),
                ("Therapist", MenuController.PageHeight(oneLine, therapistInfo, 8, 0f, false)),
                ("Progress: Profile", MenuController.PageHeight(oneLine, headline, 1, 0f, true)),
                ("Progress: Badges (8 badges)", MenuController.PageHeight(oneLine, badgesLine, 1, MenuController.BadgeGridHeight(8), true)),
            };
            foreach (var (name, h) in pages)
                Assert.LessOrEqual(h, MenuController.MaxHeight, $"{name} is {h:0} tall and would shrink its text below the scale");
        }

        [Test]
        public void LongestRowLabels_FitTheirRow()
        {
            foreach (var text in new[] { "▶  Show numbers (therapist)", "▶  Back to the exercise spot", "▶  Patient code digit 3", "▶  Coach (Female / Male)" })
            {
                var t = UIKit.Label(root.transform, Vector2.zero, new Vector2(MenuController.RowLabelWidth, 40), UIKit.TypeSize.Item, UIKit.Ink, TextAnchor.MiddleLeft, FontStyle.Bold);
                t.textWrappingMode = TMPro.TextWrappingModes.NoWrap;
                t.text = text;
                t.ForceMeshUpdate();
                Assert.LessOrEqual(t.preferredWidth, MenuController.RowLabelWidth, text);
            }
        }

        static float Deg(float opposite, float adjacent) => Mathf.Atan2(opposite, adjacent) * Mathf.Rad2Deg;

        const float HalfWidthDeg = 30f, UpDeg = 20f, DownDeg = 40f;

        [Test]
        public void TallestMenu_StaysInsideTheComfortableView()
        {
            float w = MenuController.Width * MenuController.BaseScale, h = MenuController.MaxHeight * MenuController.BaseScale;
            float d = MenuController.Distance, y = -MenuController.DropBelowEye;
            Assert.LessOrEqual(Deg(w / 2f, d), HalfWidthDeg);
            Assert.LessOrEqual(Deg(y + h / 2f, d), UpDeg);
            Assert.LessOrEqual(Deg(-(y - h / 2f), d), DownDeg);
        }

        [Test]
        public void TallestSummary_StaysInsideTheComfortableView()
        {
            float scale = HUDController.DefaultHudScale * HUDController.SummaryScale;
            float d = HUDController.HeadsetDistance * HUDController.SummaryDepth, y = HUDController.SummaryHeadsetLift;
            // Worst case: three detail lines and a badge row
            float h = HUDController.SummaryHeight(3 * 42f, true) * scale, w = HUDController.SummaryWidth * scale;
            Assert.LessOrEqual(Deg(w / 2f, d), HalfWidthDeg);
            Assert.LessOrEqual(Deg(y + h / 2f, d), UpDeg);
            Assert.LessOrEqual(Deg(-(y - h / 2f), d), DownDeg);
        }
    }
}
