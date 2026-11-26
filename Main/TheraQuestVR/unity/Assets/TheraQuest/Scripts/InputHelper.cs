using UnityEngine;
#if ENABLE_INPUT_SYSTEM
using UnityEngine.InputSystem;
#endif

namespace TheraQuest
{
    /// <summary>
    /// One place for all controls: the keyboard and mouse, and the Quest controllers (via Quest Link) read through the
    /// input actions in <see cref="XrControls"/> (M10.2). In a menu in the headset, a controller ray and the trigger
    /// also click the row pointed at (<see cref="ControllerRays"/>).
    ///
    ///   Action              Keyboard / mouse           Quest controller
    ///   Start / select      Space or Enter             A (right) or right trigger
    ///   Pause / back        Esc, P or Backspace        B (right) or Menu (left)
    ///   Menu: choose        Up / Down arrows           either thumbstick up / down
    ///   Menu: change value  Left / Right arrows        either thumbstick left / right
    ///   Walk                W A S D (Shift = faster)   W A S D on the keyboard (sticks do not walk)
    ///   Turn                Q / E, Left / Right, or    right thumbstick left / right
    ///                       move the mouse to look around (no menu open; in a menu, hold the right button)
    ///   Back to the station R                          Y (left)
    ///   Show / hide quest   M                          left thumbstick click
    ///   Angle up / down     Up / Down arrows           right thumbstick up / down (keyboard input mode)
    ///
    /// SessionManager calls <see cref="Tick"/> once at the start of every frame.
    /// </summary>
    public static class InputHelper
    {
        enum B { Start, Back, Recenter, Left, Right, Up, Down, Quest, Count }
        static readonly bool[] now = new bool[(int)B.Count];
        static readonly bool[] before = new bool[(int)B.Count];

        public static bool StartPressed => Pressed(B.Start);
        public static bool BackPressed => Pressed(B.Back);
        public static bool RecenterPressed => Pressed(B.Recenter);
        public static bool QuestTogglePressed => Pressed(B.Quest);
        public static bool LeftPressed => Pressed(B.Left);
        public static bool RightPressed => Pressed(B.Right);
        public static bool UpPressed => Pressed(B.Up);
        public static bool DownPressed => Pressed(B.Down);
        public static float AngleAxis { get; private set; }   // -1..1, keyboard input mode
        public static Vector2 Move { get; private set; }      // -1..1, x = strafe, y = forward
        public static float Turn { get; private set; }        // -1..1
        public static Vector2 Look { get; private set; }      // mouse movement in pixels (free look, or the right button held)
        public static bool Sprint { get; private set; }

        /// <summary>
        /// On the laptop with no menu open, moving the mouse looks around without holding a button, and the cursor is
        /// hidden and kept in the window (M10.1: after Link is lost the patient picks up the mouse). Set by SessionManager.
        /// </summary>
        public static bool FreeLook
        {
            get => freeLook;
            set
            {
                if (freeLook == value) return;
                freeLook = value;
                Cursor.lockState = value ? CursorLockMode.Locked : CursorLockMode.None;
                Cursor.visible = !value;
            }
        }
        static bool freeLook;

        // Play mode without a domain reload keeps statics: start each run with the cursor free
        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
        static void ResetForPlay() => freeLook = false;

        static bool Pressed(B b) => now[(int)b] && !before[(int)b];

        public static void Tick()
        {
            for (int i = 0; i < now.Length; i++) before[i] = now[i];
            // The right trigger selects too, except while a controller ray points at a menu button: then the trigger
            // clicks that button only, so it is not chosen twice (M10.2)
            now[(int)B.Start] = Key(KeyCode.Space) || Key(KeyCode.Return) || XrControls.SelectDown || (XrControls.RightTriggerDown && !RayOnMenu);
            now[(int)B.Back] = Key(KeyCode.Escape) || Key(KeyCode.P) || Key(KeyCode.Backspace) || XrControls.BackDown;
            now[(int)B.Recenter] = Key(KeyCode.R) || XrControls.RecenterDown;
            now[(int)B.Quest] = Key(KeyCode.M) || XrControls.QuestToggleDown;

            Vector2 rs = XrControls.RightStick, ls = XrControls.LeftStick;

            float axis = 0f;
            if (Key(KeyCode.UpArrow)) axis += 1f;
            if (Key(KeyCode.DownArrow)) axis -= 1f;
            if (Mathf.Abs(rs.y) > 0.2f) axis = rs.y;
            AngleAxis = Mathf.Clamp(axis, -1f, 1f);

            now[(int)B.Left] = Key(KeyCode.LeftArrow) || rs.x < -0.6f || ls.x < -0.6f;
            now[(int)B.Right] = Key(KeyCode.RightArrow) || rs.x > 0.6f || ls.x > 0.6f;
            now[(int)B.Up] = Key(KeyCode.UpArrow) || rs.y > 0.6f || ls.y > 0.6f;
            now[(int)B.Down] = Key(KeyCode.DownArrow) || rs.y < -0.6f || ls.y < -0.6f;

            var move = new Vector2((Key(KeyCode.D) ? 1f : 0f) - (Key(KeyCode.A) ? 1f : 0f),
                                   (Key(KeyCode.W) ? 1f : 0f) - (Key(KeyCode.S) ? 1f : 0f));
            // Walking is keyboard only, in the headset too (human request 2026-11-19, after a faulty left stick walked them)
            Move = Vector2.ClampMagnitude(move, 1f);

            float turn = (Key(KeyCode.E) || Key(KeyCode.RightArrow) ? 1f : 0f) - (Key(KeyCode.Q) || Key(KeyCode.LeftArrow) ? 1f : 0f);
            if (Mathf.Abs(rs.x) > 0.2f) turn = rs.x;
            Turn = Mathf.Clamp(turn, -1f, 1f);
            Sprint = Key(KeyCode.LeftShift);
            Look = MouseLook();
        }

        /// <summary>True while a controller ray points at a menu button (set by <see cref="ControllerRays"/>).</summary>
        public static bool RayOnMenu { get; set; }

        /// <summary>
        /// A thumbstick's value as the game uses it. Touch controllers sense the thumb on the stick: with no thumb on it the
        /// stick is ignored, however far it reads, because a faulty stick can read far past the dead zone on its own
        /// (human's left stick read 0.87 untouched and walked them right, 2026-11-19). Controllers without the sensor
        /// keep the dead zone only.
        /// </summary>
        public static Vector2 StickValue(Vector2 raw, bool hasTouchSensor, bool thumbOnStick)
        {
            if (hasTouchSensor && !thumbOnStick) return Vector2.zero;
            return DeadZone(raw);
        }

        /// <summary>How far a thumbstick must be pushed before it counts (0..1). Worn Quest 2 sticks drift on their own (M10.1).</summary>
        public const float StickDeadZone = 0.3f;

        /// <summary>
        /// Ignores a thumbstick pushed less than <see cref="StickDeadZone"/>, so drift does not walk or turn the patient,
        /// and rescales the rest so a push still starts gently from zero and reaches full at the edge.
        /// </summary>
        public static Vector2 DeadZone(Vector2 v, float inner = StickDeadZone)
        {
            float m = v.magnitude;
            if (m <= inner) return Vector2.zero;
            return v / m * Mathf.Clamp01((m - inner) / (1f - inner));
        }

        static Vector2 MouseLook()
        {
#if ENABLE_INPUT_SYSTEM
            var m = Mouse.current;
            return m != null && (freeLook || m.rightButton.isPressed) ? m.delta.ReadValue() : Vector2.zero;
#else
            return freeLook || Input.GetMouseButton(1) ? new Vector2(Input.GetAxis("Mouse X"), Input.GetAxis("Mouse Y")) * 10f : Vector2.zero;
#endif
        }

        static bool Key(KeyCode k)
        {
#if ENABLE_INPUT_SYSTEM
            var kb = Keyboard.current;
            if (kb == null) return false;
            switch (k)
            {
                case KeyCode.Space: return kb.spaceKey.isPressed;
                case KeyCode.Return: return kb.enterKey.isPressed || kb.numpadEnterKey.isPressed;
                case KeyCode.Escape: return kb.escapeKey.isPressed;
                case KeyCode.Backspace: return kb.backspaceKey.isPressed;
                case KeyCode.LeftShift: return kb.leftShiftKey.isPressed || kb.rightShiftKey.isPressed;
                case KeyCode.UpArrow: return kb.upArrowKey.isPressed;
                case KeyCode.DownArrow: return kb.downArrowKey.isPressed;
                case KeyCode.LeftArrow: return kb.leftArrowKey.isPressed;
                case KeyCode.RightArrow: return kb.rightArrowKey.isPressed;
                case KeyCode.W: return kb.wKey.isPressed;
                case KeyCode.A: return kb.aKey.isPressed;
                case KeyCode.S: return kb.sKey.isPressed;
                case KeyCode.D: return kb.dKey.isPressed;
                case KeyCode.Q: return kb.qKey.isPressed;
                case KeyCode.E: return kb.eKey.isPressed;
                case KeyCode.P: return kb.pKey.isPressed;
                case KeyCode.R: return kb.rKey.isPressed;
                case KeyCode.M: return kb.mKey.isPressed;
                default: return false;
            }
#else
            return Input.GetKey(k);
#endif
        }
    }
}
