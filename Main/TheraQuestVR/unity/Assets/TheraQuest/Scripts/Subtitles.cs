using TMPro;
using UnityEngine;
using UnityEngine.UI;

namespace TheraQuest
{
    /// <summary>
    /// Closed captions at the bottom of the view: the coach's instructions and every sound cue
    /// ("[Perfect chime] Perfect! 97%"). They follow the head, so they stay readable while walking
    /// around the clinic. On/off and size come from Settings.
    /// Call <see cref="Say"/> from anywhere.
    /// </summary>
    public class Subtitles : MonoBehaviour
    {
        static Subtitles instance;
        static readonly int[] FontSizes = { 34, 44, 56 };

        Canvas canvas;
        Image bg;
        TextMeshProUGUI text;
        float timer;

        /// <param name="sound">sound cue shown in brackets before the line, or null</param>
        /// <summary>Every line shown (also when subtitles are off): line, seconds, sound cue. The coach gestures as it speaks.</summary>
        public static event System.Action<string, float, string> Said;

        /// <summary>
        /// True while captions must stay out of the way (a menu is open): the menu owns the middle of the view and
        /// already says everything in its own text. A line still running shows again when the menu closes.
        /// </summary>
        public static System.Func<bool> Hidden;

        /// <summary>Whether the caption shows now: a line still running, subtitles on and nothing covering it.</summary>
        public static bool Visible(float timeLeft, bool subtitlesOn, bool hidden) => timeLeft > 0f && subtitlesOn && !hidden;

        public static void Say(string line, float seconds = 3f, string sound = null)
        {
            Said?.Invoke(line, seconds, sound);
            if (instance == null) return;
            string s = string.IsNullOrEmpty(sound) ? "" : $"<color={UIKit.HexSound}><i>[{sound}]</i></color> ";
            instance.Show(s + StripTags(line), seconds);
        }

        void Awake()
        {
            instance = this;
            var cam = Camera.main != null ? Camera.main.transform : transform;
            canvas = UIKit.Canvas(cam, "Subtitles", Offset, 0f, new Vector2(1200, 160));
            canvas.sortingOrder = 50;
            // A rounded navy caption box fitted to the line: white text on its own dark box never blends into the
            // light floor, the cream panels or the menu behind it (human request 2026-11-24)
            bg = UIKit.Box(canvas.transform, Vector2.zero, new Vector2(1200, 160), BoxColor, "Caption box", true);
            var area = bg.rectTransform;
            area.anchorMin = area.anchorMax = area.pivot = new Vector2(0.5f, 0.5f);
            area.anchoredPosition = Vector2.zero;
            text = UIKit.Label(bg.transform, Vector2.zero, new Vector2(MaxTextW, 132), 38, UIKit.White, TextAnchor.MiddleCenter, FontStyle.Bold);
            var tr = text.rectTransform;
            tr.anchorMin = tr.anchorMax = tr.pivot = new Vector2(0.5f, 0.5f);
            tr.anchoredPosition = Vector2.zero;
            UIKit.MakeOnTop(canvas, 50);
            canvas.gameObject.SetActive(false);
            GameSettings.Changed += Apply;
            Apply();
        }

        void OnDestroy() { GameSettings.Changed -= Apply; if (instance == this) instance = null; }

        void Apply()
        {
            text.fontSize = FontSizes[Mathf.Clamp(GameSettings.SubtitleSize, 0, FontSizes.Length - 1)];
            if (!GameSettings.Subtitles) canvas.gameObject.SetActive(false);
        }

        void Show(string line, float seconds)
        {
            timer = Mathf.Max(1.5f, seconds);
            if (!GameSettings.Subtitles) return;
            text.text = line;
            // Fit the box to the line (one or two lines), with even padding all round
            var size = text.GetPreferredValues(line, MaxTextW, 0f);
            float w = Mathf.Min(MaxTextW, size.x), h = Mathf.Min(MaxTextH, size.y);
            text.rectTransform.sizeDelta = new Vector2(w + 2f, h);
            var box = new Vector2(w + 2f * PadX, h + 2f * PadY);
            bg.rectTransform.sizeDelta = box;
            bg.pixelsPerUnitMultiplier = UIKit.RoundMultiplier(box);
            canvas.gameObject.SetActive(Visible(timer, true, Hidden != null && Hidden()));
        }

        void Update()
        {
            if (timer > 0f) timer -= Time.unscaledDeltaTime;   // keeps counting while the game is paused
            bool on = Visible(timer, GameSettings.Subtitles, Hidden != null && Hidden());
            if (canvas.gameObject.activeSelf != on) canvas.gameObject.SetActive(on);
        }

        /// <summary>On the laptop the line is fixed to the screen; in the headset it stays put in the room with the HUD panels (M10.1).</summary>
        void LateUpdate()
        {
            var cam = Camera.main != null ? Camera.main.transform : null;
            Transform want = XrMode.InHeadset && HUDController.View != null ? HUDController.View : cam;
            if (want == null || canvas.transform.parent == want) return;
            canvas.transform.SetParent(want, false);
            canvas.transform.localPosition = Offset;
            canvas.transform.localRotation = Quaternion.identity;
        }

        static readonly Vector3 Offset = new Vector3(0f, -0.32f, 1.25f);

        /// <summary>The caption box: navy, nearly solid, so white text keeps its contrast on any background.</summary>
        public static readonly Color BoxColor = new Color(UIKit.Navy.r, UIKit.Navy.g, UIKit.Navy.b, 0.9f);
        const float MaxTextW = 1080f, MaxTextH = 200f, PadX = 36f, PadY = 18f;

        static string StripTags(string s) => System.Text.RegularExpressions.Regex.Replace(s ?? "", "<.*?>", "").Replace("\n", " ");
    }
}
