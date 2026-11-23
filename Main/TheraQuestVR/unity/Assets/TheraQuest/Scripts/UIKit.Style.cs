using TMPro;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.UI;

namespace TheraQuest
{
    /// <summary>
    /// M8.5: the one type-size and spacing scale, and the one button and card style, for the menus, the Progress page
    /// and the summary. Kept apart from UIKit.cs (palette, fonts, panels) so each file has one concern.
    /// </summary>
    public static partial class UIKit
    {
        /// <summary>Named text sizes in canvas units (1000 = 1 m). Every menu and summary label takes one of these.</summary>
        public static class TypeSize
        {
            /// <summary>The summary's stars.</summary>
            public const int Hero = 120;
            /// <summary>Page and summary titles.</summary>
            public const int Title = 70;
            /// <summary>The one headline number of a page (display font: at least <see cref="DisplaySize"/>).</summary>
            public const int Heading = 52;
            /// <summary>Menu rows and their values.</summary>
            public const int Item = 36;
            /// <summary>Subtitles, info and details.</summary>
            public const int Body = 30;
            /// <summary>Tabs, small labels and badge names.</summary>
            public const int Label = 27;
            /// <summary>Footers and hints: the smallest text on any menu or the summary.</summary>
            public const int Caption = 24;
        }

        /// <summary>Named gaps in canvas units.</summary>
        public static class Gap
        {
            public const float Tight = 6f, Small = 12f, Medium = 20f, Large = 28f;
            /// <summary>Space between a page's edge and its content.</summary>
            public const float Margin = 50f;
        }

        /// <summary>What a button is showing right now (most important first when more than one applies).</summary>
        public enum ButtonState { Normal, Highlighted, Selected, Pressed, Disabled }

        /// <summary>Fill and text colour for each button state.</summary>
        public struct ButtonColors
        {
            public Color normal, highlighted, selected, pressed, disabled;
            public Color normalText, highlightedText, selectedText, pressedText, disabledText;

            public Color Fill(ButtonState s) =>
                s == ButtonState.Highlighted ? highlighted : s == ButtonState.Selected ? selected :
                s == ButtonState.Pressed ? pressed : s == ButtonState.Disabled ? disabled : normal;

            public Color Text(ButtonState s) =>
                s == ButtonState.Highlighted ? highlightedText : s == ButtonState.Selected ? selectedText :
                s == ButtonState.Pressed ? pressedText : s == ButtonState.Disabled ? disabledText : normalText;
        }

        /// <summary>
        /// The one button style (menu rows, Progress tabs): a faint navy row; a light blue tint under the mouse or a
        /// controller ray; solid blue for the keyboard / thumbstick choice; navy while pressed.
        /// </summary>
        // Built on first use: static fields in two partial files have no set start order, so the palette above may
        // not be ready while this file's statics start up
        public static ButtonColors Buttons => buttons ?? (buttons = new ButtonColors
        {
            normal = Row,
            highlighted = new Color32(39, 125, 161, 64),     // blue, 25% over the cream card
            selected = new Color32(33, 106, 137, 255),       // the palette blue, 15% deeper so white text passes 4.5:1
            pressed = Navy,
            disabled = new Color32(29, 53, 87, 8),
            normalText = Ink,
            highlightedText = Ink,
            selectedText = White,
            pressedText = White,
            disabledText = new Color(Muted.r, Muted.g, Muted.b, 0.6f),
        }).Value;
        static ButtonColors? buttons;

        /// <summary>The state to show: disabled, then pressed, then selected, then highlighted.</summary>
        public static ButtonState StateOf(bool enabled, bool pressed, bool selected, bool highlighted) =>
            !enabled ? ButtonState.Disabled : pressed ? ButtonState.Pressed : selected ? ButtonState.Selected :
            highlighted ? ButtonState.Highlighted : ButtonState.Normal;

        /// <summary>
        /// A small content card (the Progress page's badge cards): cream when active, greyed when not, with a soft
        /// outline and shadow and no top strip. Floating panels use <see cref="Window"/> instead.
        /// </summary>
        public static CardRef Tile(Transform parent, Vector2 size, bool active, string name = "Tile")
        {
            var c = Card(parent, size, active ? White : Lighter(Muted, 0.85f), Track, name);
            c.strip.gameObject.SetActive(false);
            if (!active) c.outline.color = new Color(Outline.r, Outline.g, Outline.b, 0.35f);
            c.shadow.color = new Color(0f, 0f, 0f, active ? 0.18f : 0.06f);
            return c;
        }

        /// <summary>Adds the one button style to a box: pointer states plus <see cref="ButtonLook.selected"/>.</summary>
        public static ButtonLook Look(Image bg, TMP_Text text)
        {
            bg.raycastTarget = true;
            var look = bg.gameObject.AddComponent<ButtonLook>();
            look.bg = bg;
            look.text = text;
            look.Apply();
            return look;
        }
    }

    /// <summary>
    /// Colours a button for mouse, keyboard and controller alike: a pointer or ray over it highlights it, holding the
    /// button or trigger presses it, and the menu says which one is the keyboard / thumbstick choice.
    /// </summary>
    public class ButtonLook : MonoBehaviour, IPointerEnterHandler, IPointerExitHandler, IPointerDownHandler, IPointerUpHandler
    {
        public Image bg;
        public TMP_Text text;
        public bool selected, interactable = true;
        public bool Hovered { get; private set; }
        bool held;
        float flashUntil = -1f;

        public const float FlashSeconds = 0.12f;

        public UIKit.ButtonState State => UIKit.StateOf(interactable, held || Time.unscaledTime < flashUntil, selected, Hovered);

        /// <summary>Shows the pressed colour briefly (Enter, Space or A on the selected button).</summary>
        public void Flash() { flashUntil = Time.unscaledTime + FlashSeconds; Apply(); }

        public void Apply()
        {
            var s = State;
            if (bg != null) bg.color = UIKit.Buttons.Fill(s);
            if (text != null) text.color = UIKit.Buttons.Text(s);
        }

        void Update() { if (flashUntil > 0f && Time.unscaledTime >= flashUntil) { flashUntil = -1f; Apply(); } }

        public void OnPointerEnter(PointerEventData e) { Hovered = true; Apply(); }
        public void OnPointerExit(PointerEventData e) { Hovered = false; held = false; Apply(); }
        public void OnPointerDown(PointerEventData e) { held = true; Apply(); }
        public void OnPointerUp(PointerEventData e) { held = false; Apply(); }
    }
}
