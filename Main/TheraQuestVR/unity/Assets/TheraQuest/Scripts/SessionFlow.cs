using UnityEngine;
using UnityEngine.XR;

namespace TheraQuest
{
    /// <summary>
    /// The 3-2-1 countdown before each exercise (M5.4). Driven by the game's delta time, so it freezes while paused.
    /// <see cref="Number"/> is 3, 2, 1, then 0 ("Go!") for a short moment before <see cref="Finished"/>.
    /// </summary>
    public sealed class Countdown
    {
        readonly int from;
        readonly float goSeconds;
        float remaining = -1f;
        int shown = -1;

        public Countdown(int from = 3, float goSeconds = 0.6f)
        {
            this.from = Mathf.Max(1, from);
            this.goSeconds = Mathf.Max(0f, goSeconds);
        }

        public bool Active => remaining > 0f;
        public bool Finished { get; private set; }
        public int Number => Mathf.Clamp(Mathf.CeilToInt(remaining - goSeconds), 0, from);

        public void Begin()
        {
            remaining = from + goSeconds;
            shown = -1;
            Finished = false;
        }

        public void Cancel()
        {
            remaining = -1f;
            Finished = false;
        }

        /// <returns>true when <see cref="Number"/> changed (play a beep, show the new number)</returns>
        public bool Tick(float dt)
        {
            if (!Active) return false;
            remaining -= dt;
            if (remaining <= 0f) { remaining = -1f; Finished = true; }
            int n = Finished ? 0 : Number;
            if (n == shown) return false;
            shown = n;
            return true;
        }
    }

    /// <summary>
    /// Control names for the hints on screen (M5.4): keyboard words on the laptop, controller buttons in the headset.
    /// The actual bindings live in <see cref="InputHelper"/>; keep the two in step.
    /// </summary>
    public sealed class ControlHints
    {
        public string Start, Back, Recenter, Quest, Walk, Turn, Navigate, Change, Angle;

        public static readonly ControlHints Keyboard = new ControlHints
        {
            Start = "Space", Back = "Esc", Recenter = "R", Quest = "M", Walk = "W A S D", Turn = "Q / E",
            Navigate = "↑ ↓", Change = "‹ ›", Angle = "the Up / Down keys",
        };

        public static readonly ControlHints Controller = new ControlHints
        {
            Start = "A", Back = "B", Recenter = "Y", Quest = "left stick click", Walk = "left stick", Turn = "right stick",
            Navigate = "stick up / down", Change = "stick left / right", Angle = "the right stick",
        };

        public static ControlHints For(bool headset) => headset ? Controller : Keyboard;

        /// <summary>Hints for whatever the patient is using right now.</summary>
        public static ControlHints Current => For(XRSettings.isDeviceActive);

        public string MenuFooter => this == Keyboard
            ? $"{Navigate} navigate   ·   {Change} or Click to change   ·   {Start} select   ·   {Back} back"
            : $"{Navigate} navigate   ·   {Change} change   ·   {Start} select   ·   {Back} back";
    }
}
