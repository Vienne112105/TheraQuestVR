using System;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.XR;

namespace TheraQuest
{
    /// <summary>Whether the patient is using the headset (M10.1, DEC-030).</summary>
    public enum XrState { Desktop, Headset, HeadsetOff, LinkLost }

    /// <summary>
    /// The pure state machine behind <see cref="XrMode"/>: fed whether the XR display runs and whether the patient
    /// wears the headset, it says which mode the game is in and what just changed. No Unity calls, so it is unit tested.
    ///   Desktop    : no headset since the start (or the game started with Link off).
    ///   Headset    : display running and the headset is worn.
    ///   HeadsetOff : the headset was taken off (the session pauses). Quest Link may stop the display meanwhile.
    ///   LinkLost   : the display stopped after the headset had been used (Link unplugged): the game carries on on the laptop.
    /// A presence change must last <see cref="PresenceDebounce"/> seconds before it counts, so a brief sensor flicker does nothing.
    /// </summary>
    public sealed class XrModeLogic
    {
        public enum Change { None, HeadsetRemoved, HeadsetBack, FellBackToDesktop, HeadsetConnected }

        public const float PresenceDebounce = 0.5f;
        /// <summary>Said when Link is lost and the game carries on on the laptop.</summary>
        public const string FallbackLine = "Headset disconnected. Carry on with the keyboard, or reconnect the headset.";

        /// <summary>Taking the headset off pauses a running exercise (not when a menu is already open).</summary>
        public static bool PausesSession(Change c, bool exerciseRunning, bool menuOpen) =>
            c == Change.HeadsetRemoved && exerciseRunning && !menuOpen;

        public XrState State { get; private set; } = XrState.Desktop;
        float presenceChangeTime = -1f;

        /// <summary>Feed one frame. <paramref name="now"/> is unscaled time in seconds (the game may be paused).</summary>
        public Change Step(bool displayRunning, bool userPresent, float now)
        {
            if (!displayRunning)
            {
                // Quest Link stops the display as soon as the headset is taken off: if it had just reported "not worn",
                // this is the headset coming off (pause), not Link being lost
                bool takenOff = State == XrState.Headset && presenceChangeTime >= 0f;
                presenceChangeTime = -1f;
                if (takenOff) { State = XrState.HeadsetOff; return Change.HeadsetRemoved; }
                if (State == XrState.HeadsetOff) return Change.None;   // still off; the display comes back when it is worn
                if (State == XrState.Headset) { State = XrState.LinkLost; return Change.FellBackToDesktop; }
                return Change.None;
            }

            if (State == XrState.Desktop || State == XrState.LinkLost)
            {
                presenceChangeTime = -1f;
                State = XrState.Headset;
                return Change.HeadsetConnected;
            }

            bool wornNow = State == XrState.Headset;
            if (userPresent == wornNow) { presenceChangeTime = -1f; return Change.None; }
            if (presenceChangeTime < 0f) { presenceChangeTime = now; return Change.None; }
            if (now - presenceChangeTime < PresenceDebounce) return Change.None;

            presenceChangeTime = -1f;
            State = userPresent ? XrState.Headset : XrState.HeadsetOff;
            return userPresent ? Change.HeadsetBack : Change.HeadsetRemoved;
        }
    }

    /// <summary>
    /// The one place the game asks "is the headset in use?" (M10.1). Reads the XR display subsystem and the headset's
    /// user-presence sensor once per frame. <see cref="InHeadset"/> is true while the headset view is shown (worn or
    /// briefly taken off); false on the laptop, including after Link is lost.
    /// </summary>
    public static class XrMode
    {
        static XrModeLogic logic = new XrModeLogic();
        static readonly List<XRDisplaySubsystem> displays = new List<XRDisplaySubsystem>();
        static int sampledFrame = -1;

        // The project enters Play mode without a domain reload, so statics would keep the last run's state
        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
        static void ResetForPlay()
        {
            logic = new XrModeLogic();
            sampledFrame = -1;
            Changed = null;
            UnityEngine.XR.OpenXR.OpenXRRuntime.wantsToQuit -= KeepRunning;
            UnityEngine.XR.OpenXR.OpenXRRuntime.wantsToQuit += KeepRunning;
        }

        /// <summary>
        /// When Link is unplugged the OpenXR runtime is lost and Unity would quit the game (in the Editor: end Play mode),
        /// losing the session. Refuse: the game carries on on the laptop (M10.1) and the reps are kept.
        /// </summary>
        static bool KeepRunning() => false;

        /// <summary>Raised on the frame a change is seen (HeadsetRemoved, HeadsetBack, FellBackToDesktop, HeadsetConnected).</summary>
        public static event Action<XrModeLogic.Change> Changed;

        public static XrState State { get { Sample(); return logic.State; } }
        public static bool InHeadset { get { var s = State; return s == XrState.Headset || s == XrState.HeadsetOff; } }

        static void Sample()
        {
            if (sampledFrame == Time.frameCount) return;
            sampledFrame = Time.frameCount;
            bool running = DisplayRunning();
            var change = logic.Step(running, running && UserPresent(), Time.unscaledTime);
            if (change != XrModeLogic.Change.None) Changed?.Invoke(change);
        }

        /// <summary>Call once per frame so changes are noticed even when nothing else asks.</summary>
        public static void Tick() => Sample();

        static bool DisplayRunning()
        {
            SubsystemManager.GetSubsystems(displays);
            foreach (var d in displays) if (d.running) return true;
            return false;
        }

        static bool UserPresent()
        {
            var head = InputDevices.GetDeviceAtXRNode(XRNode.Head);
            // Headsets without a presence sensor count as worn
            return !head.isValid || !head.TryGetFeatureValue(CommonUsages.userPresence, out bool present) || present;
        }
    }
}
