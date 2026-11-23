using UnityEngine;
using UnityEngine.InputSystem;

namespace TheraQuest
{
    /// <summary>
    /// The Quest controllers and headset as the game reads them (M10.2, DEC-030): input actions from
    /// Resources/Input/TheraQuestControls.inputactions, bound to the generic XR controller usages so Quest 2, 3 and Pro
    /// all work. <see cref="InputHelper"/>, <see cref="XrMode"/> and <see cref="HeadTracking"/> read through here;
    /// no script reads <c>UnityEngine.XR.InputDevices</c> any more. Edit the bindings in Unity's input actions editor.
    /// </summary>
    public static class XrControls
    {
        public const string AssetResource = "Input/TheraQuestControls";

        static InputActionAsset asset;
        static InputAction select, rightTrigger, leftTrigger, back, recenter, questToggle;
        static InputAction leftStick, rightStick, leftStickTouch, rightStickTouch;
        static InputAction worn, headTracked, eyePosition;

        /// <summary>The loaded actions (enabled), or null when the file is missing.</summary>
        public static InputActionAsset Asset { get { Ensure(); return asset; } }

        // Play mode without a domain reload keeps statics: load afresh each run
        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
        static void ResetForPlay() { if (asset != null) asset.Disable(); asset = null; }

        static bool Ensure()
        {
            if (asset != null) return true;
            var loaded = Resources.Load<InputActionAsset>(AssetResource);
            if (loaded == null) return false;
            asset = Object.Instantiate(loaded);   // a runtime copy: enabling it never touches the asset file
            select = Find("Controllers/Select"); rightTrigger = Find("Controllers/RightTrigger"); leftTrigger = Find("Controllers/LeftTrigger");
            back = Find("Controllers/Back"); recenter = Find("Controllers/Recenter"); questToggle = Find("Controllers/QuestToggle");
            leftStick = Find("Controllers/LeftStick"); rightStick = Find("Controllers/RightStick");
            leftStickTouch = Find("Controllers/LeftStickTouch"); rightStickTouch = Find("Controllers/RightStickTouch");
            worn = Find("Headset/Worn"); headTracked = Find("Headset/Tracked"); eyePosition = Find("Headset/EyePosition");
            asset.Enable();
            return true;
        }

        static InputAction Find(string path) => asset.FindAction(path, true);

        /// <summary>One of the actions by "Map/Action" name (for the controller rays and pose drivers).</summary>
        public static InputAction Action(string path) => Ensure() ? asset.FindAction(path, true) : null;

        static bool Down(InputAction a) => a != null && a.IsPressed();

        public static bool SelectDown => Ensure() && Down(select);              // A
        public static bool RightTriggerDown => Ensure() && Down(rightTrigger);
        public static bool LeftTriggerDown => Ensure() && Down(leftTrigger);
        public static bool BackDown => Ensure() && Down(back);                  // B or left Menu
        public static bool RecenterDown => Ensure() && Down(recenter);          // Y
        public static bool QuestToggleDown => Ensure() && Down(questToggle);    // left stick click

        /// <summary>A thumbstick after the touch check and dead zone (<see cref="InputHelper.StickValue"/>).</summary>
        public static Vector2 LeftStick => Ensure() ? Stick(leftStick, leftStickTouch) : Vector2.zero;
        public static Vector2 RightStick => Ensure() ? Stick(rightStick, rightStickTouch) : Vector2.zero;

        static Vector2 Stick(InputAction axis, InputAction touch)
        {
            if (axis.controls.Count == 0) return Vector2.zero;
            bool hasTouch = touch.controls.Count > 0;
            return InputHelper.StickValue(axis.ReadValue<Vector2>(), hasTouch, hasTouch && touch.IsPressed());
        }

        /// <summary>Whether the headset is on the patient's head. Headsets without a presence sensor count as worn.</summary>
        public static bool HeadsetWorn => !Ensure() || worn.controls.Count == 0 || worn.IsPressed();

        /// <summary>The headset's eye position from the floor, once it is tracking (false before tracking starts).</summary>
        public static bool TryGetTrackedEyePosition(out Vector3 eye)
        {
            eye = default;
            if (!Ensure() || headTracked.controls.Count == 0 || !headTracked.IsPressed() || eyePosition.controls.Count == 0) return false;
            eye = eyePosition.ReadValue<Vector3>();
            return true;
        }
    }
}
