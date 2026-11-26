using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;

namespace TheraQuest
{
    /// <summary>
    /// Feedback motion (M8.3): which important moments get a small effect, and the effects themselves.
    ///   Good rep        -> a burst at the live limb's target point and a punch of the points tile
    ///   Combo up        -> a subtle pulse of the combo tile
    ///   Hold            -> a ring round the target star that fills while holding, and pops on hold complete
    ///   Level up, badge -> a sparkle behind the level pill and the badge row on the summary
    /// STOP (past the safe limit), a posture fault or too far never get a reward effect: they keep their red,
    /// instant, still warning (DEC-016). Effects follow only events the evaluator counted (a valid rep, the evaluator's
    /// own hold complete) or rewards from a counted session; nothing fires from the angle alone.
    /// Sprites come from Resources/Effects (burst, ring, sparkle; chosen by the human, see CREDITS.md). A missing
    /// sprite keeps the static look (punches only). Comfort: small, short (0.45 s at most), near the limb or panel
    /// it belongs to, unscaled time, never a full-view flash.
    /// </summary>
    public static class FeedbackMotion
    {
        public const string BurstName = "burst", RingName = "ring", SparkleName = "sparkle";

        /// <summary>Effect lengths stay short (seconds).</summary>
        public const float BurstSeconds = 0.4f, SparkleSeconds = 0.45f, MaxEffectSeconds = 0.45f;

        /// <summary>Size of the rep burst at the limb (metres).</summary>
        public const float BurstMetres = 0.2f;

        public struct RepEffects
        {
            /// <summary>Burst at the limb, points-tile punch, gold pop text.</summary>
            public bool reward;
            /// <summary>Combo-tile pulse.</summary>
            public bool comboPulse;
        }

        /// <summary>False while a safety warning shows (STOP, posture fault, too far): no celebration then.</summary>
        public static bool RewardAllowed(LiveState state) =>
            state != LiveState.Unsafe && state != LiveState.Fault && state != LiveState.TooFar;

        /// <summary>A rep the evaluator counted as good: valid, no fault, not past the STOP line, not too far.</summary>
        public static bool GoodRep(RepResult r) =>
            r.valid && !r.pastSafetyMax && !r.overshoot && string.IsNullOrEmpty(r.fault);

        /// <summary>The effects for a rep the evaluator just finished.</summary>
        /// <param name="stateNow">the evaluator's state when the rep ended</param>
        /// <param name="comboBefore">the combo before this rep was scored</param>
        /// <param name="comboAfter">the combo after</param>
        public static RepEffects ForRep(RepResult r, LiveState stateNow, int comboBefore, int comboAfter)
        {
            bool reward = GoodRep(r) && RewardAllowed(stateNow);
            return new RepEffects { reward = reward, comboPulse = reward && ComboPulse(comboBefore, comboAfter) };
        }

        /// <summary>The combo tile pulses when the combo grows to 2 or more (a streak), never when it resets.</summary>
        public static bool ComboPulse(int comboBefore, int comboAfter) => comboAfter > comboBefore && comboAfter > 1;

        /// <summary>How full the hold ring is: only while holding inside the band, else empty.</summary>
        public static float HoldFill(LiveState state, float holdTime, float holdSeconds) =>
            holdSeconds > 0f && state == LiveState.Holding ? Mathf.Clamp01(holdTime / holdSeconds) : 0f;

        /// <summary>The hold-complete pop follows the evaluator's HoldCompleted, and never during a warning.</summary>
        public static bool HoldComplete(LiveState state) => RewardAllowed(state);

        /// <summary>The level-up sparkle: only when the summary's XP really crossed a level.</summary>
        public static bool LevelUpReveal(ProgressViews.XpSpan xp) => xp.LevelUp;

        /// <summary>The badge sparkle: only for a badge the summary is revealing now.</summary>
        public static bool BadgeReveal(int revealed, int newBadges) => revealed > 0 && revealed <= newBadges;

        // ------------------------------------------------------------------ sprites
        static readonly Dictionary<string, Sprite> sprites = new Dictionary<string, Sprite>();

        /// <summary>An effect sprite from Resources/Effects, or null when it is missing (static look then).</summary>
        public static Sprite Sprite(string name)
        {
            if (sprites.TryGetValue(name, out var s) && s != null) return s;
            var tex = Resources.Load<Texture2D>("Effects/" + name);
            s = tex != null ? UnityEngine.Sprite.Create(tex, new Rect(0, 0, tex.width, tex.height), new Vector2(0.5f, 0.5f), 100f) : null;
            if (s != null) s.name = "Effect " + name;
            sprites[name] = s;
            return s;
        }

        /// <summary>
        /// A small burst at a room point (the live limb's target point on a good rep), facing the viewer. Null when the
        /// sprite or the view is missing.
        /// </summary>
        public static EffectSprite WorldBurst(Vector3 at, Transform viewer, Color color)
        {
            var sp = Sprite(BurstName);
            if (sp == null || viewer == null) return null;
            const float units = 200f;   // canvas units; the canvas is scaled so this is BurstMetres
            var c = UIKit.Canvas(null, "Rep burst", at, 0f, new Vector2(units, units));
            c.transform.position = at;
            c.transform.rotation = Quaternion.LookRotation(at - viewer.position, Vector3.up);
            c.transform.localScale = Vector3.one * (BurstMetres / units);
            var img = Centred(c.transform, new Vector2(units, units), sp, color);
            return EffectSprite.Attach(img, c.gameObject, BurstSeconds, 0.5f, 1.15f);
        }

        /// <summary>
        /// A sparkle behind a UI element (drawn just before it), centred on it. Null when the sprite is missing.
        /// </summary>
        public static EffectSprite UiSparkle(RectTransform target, float size, Color color)
        {
            var sp = Sprite(SparkleName);
            if (sp == null || target == null || target.parent == null) return null;
            var img = UIKit.Box(target.parent, Vector2.zero, new Vector2(size, size), color, "Sparkle");
            img.sprite = sp;
            img.preserveAspect = true;
            var rt = img.rectTransform;
            rt.anchorMin = target.anchorMin;
            rt.anchorMax = target.anchorMax;
            rt.pivot = new Vector2(0.5f, 0.5f);
            // The target's centre, whatever its pivot
            rt.anchoredPosition = target.anchoredPosition + Vector2.Scale(target.rect.size, new Vector2(0.5f, 0.5f) - target.pivot);
            rt.SetSiblingIndex(target.GetSiblingIndex());
            return EffectSprite.Attach(img, img.gameObject, SparkleSeconds, 0.6f, 1.2f);
        }

        /// <summary>The hold ring round the target star (a radial fill), or null when the ring sprite is missing.</summary>
        public static Image HoldRing(Transform parent, Vector2 size)
        {
            var sp = Sprite(RingName);
            if (sp == null) return null;
            var img = UIKit.Box(parent, Vector2.zero, size, UIKit.Yellow, "Hold ring");
            img.sprite = sp;
            img.type = Image.Type.Filled;
            img.fillMethod = Image.FillMethod.Radial360;
            img.fillOrigin = (int)Image.Origin360.Top;
            img.fillClockwise = true;
            img.fillAmount = 0f;
            img.preserveAspect = true;
            return img;
        }

        static Image Centred(Transform parent, Vector2 size, Sprite sp, Color color)
        {
            var go = new GameObject("Effect", typeof(RectTransform), typeof(Image));
            go.transform.SetParent(parent, false);
            var rt = (RectTransform)go.transform;
            rt.anchorMin = rt.anchorMax = rt.pivot = new Vector2(0.5f, 0.5f);
            rt.sizeDelta = size;
            var img = go.GetComponent<Image>();
            img.sprite = sp;
            img.color = color;
            img.raycastTarget = false;
            img.preserveAspect = true;
            return img;
        }
    }

    /// <summary>
    /// A one-shot effect: the graphic grows and fades out over a short time (unscaled), then its root is destroyed.
    /// Step() advances it so tests can drive it without Play mode.
    /// </summary>
    public class EffectSprite : MonoBehaviour
    {
        Graphic graphic;
        GameObject root;
        float t, life, from, to, alpha;

        public float Life => life;
        public bool Finished { get; private set; }

        public static EffectSprite Attach(Graphic g, GameObject root, float seconds, float fromScale, float toScale)
        {
            var e = g.gameObject.AddComponent<EffectSprite>();
            e.graphic = g;
            e.root = root;
            e.life = Mathf.Min(seconds, FeedbackMotion.MaxEffectSeconds);
            e.from = fromScale;
            e.to = toScale;
            e.alpha = g.color.a;
            e.Apply(0f);
            return e;
        }

        public void Step(float dt)
        {
            if (Finished) return;
            t += Mathf.Max(0f, dt);
            if (t >= life) { Finish(); return; }
            Apply(t / life);
        }

        void Update() => Step(Time.unscaledDeltaTime);

        void Apply(float p)
        {
            float e = 1f - (1f - p) * (1f - p);   // ease out
            transform.localScale = Vector3.one * Mathf.Lerp(from, to, e);
            var c = graphic.color;
            c.a = alpha * (p < 0.35f ? 1f : 1f - (p - 0.35f) / 0.65f);
            graphic.color = c;
        }

        void Finish()
        {
            Finished = true;
            var go = root != null ? root : gameObject;
            if (Application.isPlaying) Destroy(go);
            else DestroyImmediate(go);
        }
    }
}
