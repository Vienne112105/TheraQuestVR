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
    ///   HeadsetOff : display running but the headset was taken off (the session pauses).
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
                presenceChangeTime = -1f;
                if (State == XrState.Headset || State == XrState.HeadsetOff) { State = XrState.LinkLost; return Change.FellBackToDesktop; }
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
        static readonly XrModeLogic logic = new XrModeLogic();
        static readonly List<XRDisplaySubsystem> displays = new List<XRDisplaySubsystem>();
        static int sampledFrame = -1;

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
