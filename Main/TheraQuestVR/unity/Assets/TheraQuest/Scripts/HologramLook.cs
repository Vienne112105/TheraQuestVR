using UnityEngine;

namespace TheraQuest
{
    /// <summary>
    /// Colours and glow of the first-person hologram limbs (M8.4). Pure, unit tested.
    /// Target and live limb take palette colours; inside tolerance both turn green and glow. The glow eases in over
    /// <see cref="GlowFadeIn"/> and drops to zero at once when the limb leaves tolerance, so it never shows outside it
    /// and never pulses (comfort: no flicker, no flashes).
    /// </summary>
    public static class HologramLook
    {
        /// <summary>The prescribed angle: palette blue, see-through.</summary>
        public static readonly Color Target = WithAlpha(UIKit.Blue, 0.32f);
        /// <summary>The patient's own limb (the real one can't be seen in a headset): palette white, a little more solid.</summary>
        public static readonly Color Live = WithAlpha(UIKit.White, 0.5f);
        public const float GoodTargetAlpha = 0.45f, ToneLiveAlpha = 0.65f;
        /// <summary>Seconds the glow takes to reach full strength after the limb enters tolerance.</summary>
        public const float GlowFadeIn = 0.2f;
        public static readonly int GlowId = Shader.PropertyToID("_Glow");

        /// <summary>The evaluator states that mean the angle is inside target ± tolerance with good posture.</summary>
        public static bool InTolerance(LiveState s) => s == LiveState.OnTarget || s == LiveState.Holding;

        /// <summary>The guide's tone for an evaluator state: green only inside tolerance, red past it or on a fault.</summary>
        public static Tone StateTone(LiveState s) =>
            InTolerance(s) ? Tone.Good :
            s == LiveState.TooFar || s == LiveState.Fault || s == LiveState.Unsafe ? Tone.Bad : Tone.Neutral;

        /// <summary>The glow one frame later: eases up inside tolerance, zero outside it. dt 0 (paused) holds it.</summary>
        public static float NextGlow(float glow, bool inTolerance, float dt) =>
            inTolerance ? Mathf.MoveTowards(glow, 1f, Mathf.Max(0f, dt) / GlowFadeIn) : 0f;

        /// <summary>Sets both limb materials for a tone; the glow is written only for the in-tolerance (Good) tone.</summary>
        public static void Apply(Material target, Material live, Tone tone, float glow)
        {
            var c = FeedbackManager.ToneColor(tone);
            target.color = tone == Tone.Good ? WithAlpha(c, GoodTargetAlpha) : Target;
            live.color = tone == Tone.Neutral ? Live : WithAlpha(c, ToneLiveAlpha);
            float g = tone == Tone.Good ? Mathf.Clamp01(glow) : 0f;
            target.SetFloat(GlowId, g);
            live.SetFloat(GlowId, g);
        }

        static Color WithAlpha(Color c, float a) => new Color(c.r, c.g, c.b, a);
    }
}
