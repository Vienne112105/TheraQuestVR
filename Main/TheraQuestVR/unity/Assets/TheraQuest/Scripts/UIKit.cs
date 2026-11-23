using System.Collections.Generic;
using TMPro;
using UnityEngine;
using UnityEngine.TextCore.LowLevel;
using UnityEngine.UI;

namespace TheraQuest
{
    /// <summary>
    /// Shared cartoon look for every world-space panel (HUD, menus, posters): bright cream cards with
    /// a thick dark outline and a soft drop shadow, chunky rounded shapes, and a playful palette.
    /// The rounded-corner sprite is generated at runtime (no image assets needed).
    /// World-space canvases use 1000 canvas units = 1 metre.
    /// </summary>
    public static partial class UIKit
    {
        // Palette (human choice 2026-10-26): every panel and text colour is one of these five, or a tint of one.
        //   Navy #1D3557, Blue #277DA1, Orange #F3722C, Green #43AA8B, Off-white #F8F9FA.
        // The older names stay so each role keeps its meaning: Teal = the accent (blue), Yellow = rewards (orange),
        // Pink = the combo tile (green), Purple = the level pill (navy). Red is the one exception: it is kept only for
        // safety warnings (STOP line, unsafe or too-far reps, posture faults), so they never look like normal hints.
        public static readonly Color Navy = new Color32(29, 53, 87, 255);
        public static readonly Color White = new Color32(248, 249, 250, 255);
        public static readonly Color Cream = new Color32(248, 249, 250, 250);
        public static readonly Color Outline = Navy;
        public static readonly Color Ink = Navy;
        public static readonly Color Muted = new Color32(95, 112, 136, 255);     // navy, 70% over off-white
        public static readonly Color Blue = new Color32(39, 125, 161, 255);
        public static readonly Color Teal = Blue;
        public static readonly Color Orange = new Color32(243, 114, 44, 255);
        public static readonly Color Yellow = Orange;
        public static readonly Color Green = new Color32(67, 170, 139, 255);
        public static readonly Color Pink = Green;
        public static readonly Color Purple = Navy;
        public static readonly Color Red = new Color32(229, 72, 77, 255);        // safety warnings only
        public static readonly Color Track = new Color32(29, 53, 87, 28);

        // Names used by the panels
        public static readonly Color Panel = Cream;
        public static readonly Color PanelDeep = Cream;
        public static readonly Color Row = new Color32(29, 53, 87, 16);
        public static readonly Color Accent = Teal;
        public static readonly Color AccentDark = Teal;
        public static readonly Color Gold = Yellow;

        // For rich text: <color=#...>
        public const string HexInk = "#1D3557", HexMuted = "#5F7088", HexGood = "#43AA8B", HexWarn = "#F3722C",
                            HexBad = "#E5484D", HexTeal = "#277DA1", HexGold = "#F3722C", HexPurple = "#1D3557",
                            HexLocked = "#C1C8D1", HexSound = "#A4CBD9";   // locked: navy 25%; sound: light blue

        static Font font, boldFont, displayFont, builtinFont;
        static TMP_FontAsset tmpBody, tmpBold, tmpDisplay, tmpSymbols;
        static Sprite rounded;
        static Material onTop;
        static readonly Dictionary<Material, Material> onTopText = new Dictionary<Material, Material>();

        /// <summary>UI material that ignores depth, so view-attached panels are never hidden by walls or the coach.</summary>
        public static Material OnTopMaterial
        {
            get
            {
                if (onTop == null)
                {
                    onTop = new Material(UnityEngine.Canvas.GetDefaultCanvasMaterial()) { name = "UI (always on top)" };
                    onTop.SetInt("unity_GUIZTestMode", (int)UnityEngine.Rendering.CompareFunction.Always);
                }
                return onTop;
            }
        }

        /// <summary>Makes a canvas draw over the 3D scene (and everything added to it later).</summary>
        public static void MakeOnTop(Canvas c, int sortingOrder)
        {
            c.sortingOrder = sortingOrder;
            if (c.GetComponent<DrawOnTop>() == null) c.gameObject.AddComponent<DrawOnTop>();
            foreach (var g in c.GetComponentsInChildren<Graphic>(true)) SetOnTop(g);
        }

        static void ApplyOnTop(Graphic g, Transform parent)
        {
            if (parent != null && parent.GetComponentInParent<DrawOnTop>(true) != null) SetOnTop(g);
        }

        const int ZTestAlways = (int)UnityEngine.Rendering.CompareFunction.Always;

        static void SetOnTop(Graphic g)
        {
            if (g is TMP_SubMeshUI) return;   // symbol and badge glyphs copy their text's material
            if (!(g is TMP_Text t)) { g.material = OnTopMaterial; return; }
            var m = t.fontSharedMaterial;
            if (m == null || t.font == null) return;
            if (m == t.font.material)
            {
                // Shared per font, so plain labels still batch
                if (!onTopText.TryGetValue(m, out var top) || top == null)
                {
                    top = new Material(m) { name = m.name + " (always on top)" };
                    top.SetInt("unity_GUIZTestMode", ZTestAlways);
                    onTopText[m] = top;
                }
                t.fontSharedMaterial = top;
            }
            else m.SetInt("unity_GUIZTestMode", ZTestAlways);   // the label's own material (outlined text)
        }

        // Fonts (chosen by the human 2026-10-26, option C): Luckiest Guy for big headings, numbers and rewards,
        // Nunito for everything else. Both are open-licensed; see Resources/Fonts and CREDITS.md.
        /// <summary>Text at least this big uses the display font.</summary>
        public const int DisplaySize = 44;

        /// <summary>Body text (Nunito SemiBold).</summary>
        public static Font Font => font != null ? font : (font = LoadFont("Fonts/Nunito-SemiBold"));
        /// <summary>Bold body text (Nunito ExtraBold), so bold isn't faked by stretching the regular weight.</summary>
        public static Font BoldFont => boldFont != null ? boldFont : (boldFont = LoadFont("Fonts/Nunito-ExtraBold"));
        /// <summary>Big headings, numbers and rewards (Luckiest Guy).</summary>
        public static Font DisplayFont => displayFont != null ? displayFont : (displayFont = LoadFont("Fonts/LuckiestGuy-Regular"));

        static Font Builtin => builtinFont != null ? builtinFont : (builtinFont = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf"));

        /// <summary>A font from Resources, or Unity's built-in font when it is missing (text never disappears).</summary>
        static Font LoadFont(string path)
        {
            var f = Resources.Load<Font>(path);
            if (f == null) Debug.LogWarning($"[TheraQuest] Font {path} not found; using the built-in font.");
            return f != null ? f : Builtin;
        }

        /// <summary>The font a label of this size and style uses.</summary>
        public static Font FontFor(int fontSize, FontStyle style) =>
            fontSize >= DisplaySize ? DisplayFont : style == FontStyle.Bold || style == FontStyle.BoldAndItalic ? BoldFont : Font;

        // TextMeshPro (human decision 2026-10-26): labels draw from signed-distance-field atlases made at runtime from
        // the fonts above, so text stays sharp up close and at an angle in a headset. Glyphs the fonts lack (★ ✓ ▶ ↑ …)
        // come from DejaVu Sans Bold. A missing font file falls back to TextMeshPro's default font.
        /// <summary>The TextMeshPro font a label of this size and style uses.</summary>
        public static TMP_FontAsset TmpFontFor(int fontSize, FontStyle style)
        {
            var f = FontFor(fontSize, style);
            if (f == DisplayFont) return tmpDisplay != null ? tmpDisplay : (tmpDisplay = MakeTmpFont(f, true));
            if (f == BoldFont) return tmpBold != null ? tmpBold : (tmpBold = MakeTmpFont(f, true));
            return tmpBody != null ? tmpBody : (tmpBody = MakeTmpFont(f, true));
        }

        /// <summary>Symbols the game fonts don't have (DejaVu Sans Bold).</summary>
        static TMP_FontAsset TmpSymbols
        {
            get
            {
                if (tmpSymbols == null)
                {
                    var f = Resources.Load<Font>("Fonts/DejaVuSans-Bold");
                    if (f == null) Debug.LogWarning("[TheraQuest] Font Fonts/DejaVuSans-Bold not found; symbols may not show.");
                    else tmpSymbols = MakeTmpFont(f, false);
                }
                return tmpSymbols;
            }
        }

        static TMP_FontAsset MakeTmpFont(Font f, bool withSymbols)
        {
            TMP_FontAsset a = null;
            if (f != null && f != Builtin)
                a = TMP_FontAsset.CreateFontAsset(f, 90, 9, GlyphRenderMode.SDFAA, 1024, 1024, AtlasPopulationMode.Dynamic, true);
            if (a == null) return TMP_Settings.defaultFontAsset;
            a.name = f.name + " SDF";
            // The full distance-field shader (outlines, dilate); the default font's material keeps it in builds
            var sdf = TMP_Settings.defaultFontAsset != null ? TMP_Settings.defaultFontAsset.material.shader : Shader.Find("TextMeshPro/Distance Field");
            if (sdf != null) a.material.shader = sdf;
            if (withSymbols && TmpSymbols != null) a.fallbackFontAssetTable = new List<TMP_FontAsset> { TmpSymbols };
            return a;
        }

        static TextAlignmentOptions Align(TextAnchor a)
        {
            switch (a)
            {
                case TextAnchor.UpperCenter: return TextAlignmentOptions.Top;
                case TextAnchor.UpperRight: return TextAlignmentOptions.TopRight;
                case TextAnchor.MiddleLeft: return TextAlignmentOptions.Left;
                case TextAnchor.MiddleCenter: return TextAlignmentOptions.Center;
                case TextAnchor.MiddleRight: return TextAlignmentOptions.Right;
                case TextAnchor.LowerLeft: return TextAlignmentOptions.BottomLeft;
                case TextAnchor.LowerCenter: return TextAlignmentOptions.Bottom;
                case TextAnchor.LowerRight: return TextAlignmentOptions.BottomRight;
                default: return TextAlignmentOptions.TopLeft;
            }
        }

        // Badge icons (M5.6): Kenney CC0 icons in Resources/Badges/BadgeSheet.png, one 128 px cell per badge in this
        // order, and the same cells as a TextMeshPro sprite asset for icons inside text. See CREDITS.md.
        public static readonly string[] BadgeIconCodes = { "first", "perfect", "combo10", "fullrom", "streak3", "adh80", "lv5" };
        static TMP_SpriteAsset badgeSprites;
        static Texture2D badgeSheet;
        static bool badgeSpritesLoaded, badgeSheetLoaded;
        static readonly Dictionary<string, Sprite> badgeIcons = new Dictionary<string, Sprite>();

        /// <summary>Badge icons for &lt;sprite name="code"&gt; in text, or null when the asset is missing.</summary>
        public static TMP_SpriteAsset BadgeSprites
        {
            get
            {
                if (!badgeSpritesLoaded) { badgeSpritesLoaded = true; badgeSprites = Resources.Load<TMP_SpriteAsset>("Badges/BadgeSprites"); }
                return badgeSprites;
            }
        }

        /// <summary>White icon for a badge (tint it), or null for an unknown code or a missing sheet.</summary>
        public static Sprite BadgeIcon(string code)
        {
            if (badgeIcons.TryGetValue(code ?? "", out var s) && s != null) return s;
            if (!badgeSheetLoaded) { badgeSheetLoaded = true; badgeSheet = Resources.Load<Texture2D>("Badges/BadgeSheet"); }
            int i = System.Array.IndexOf(BadgeIconCodes, code);
            if (badgeSheet == null || i < 0) return null;
            int cell = badgeSheet.height;
            s = Sprite.Create(badgeSheet, new Rect(i * cell, 0, cell, cell), new Vector2(0.5f, 0.5f), 100f);
            s.name = "Badge " + code;
            return badgeIcons[code] = s;
        }

        /// <summary>Rich text for a badge's icon: gold when earned, grey when locked; a ★ when it has no icon.</summary>
        public static string BadgeTag(string code, bool earned)
        {
            string hex = earned ? HexGold : HexLocked;
            bool icon = BadgeSprites != null && System.Array.IndexOf(BadgeIconCodes, code) >= 0;
            return icon ? $"<sprite name=\"{code}\" color={hex}>" : $"<color={hex}>★</color>";
        }

        /// <summary>A lighter shade of a colour, e.g. the outline of coloured text.</summary>
        public static Color Lighter(Color c, float amount = 0.55f) =>
            new Color(c.r + (1f - c.r) * amount, c.g + (1f - c.g) * amount, c.b + (1f - c.b) * amount, c.a);

        /// <summary>A darker shade of a colour, e.g. the outline of white text on a coloured pill.</summary>
        public static Color Darker(Color c, float amount = 0.28f) =>
            new Color(c.r * (1f - amount), c.g * (1f - amount), c.b * (1f - amount), c.a);

        static bool IsWhite(Color c) => c.r > 0.95f && c.g > 0.95f && c.b > 0.95f;

        /// <summary>9-sliced rounded rectangle, 36 canvas units corner radius. Small boxes become pills and circles.</summary>
        public static Sprite Rounded => rounded != null ? rounded : (rounded = MakeRounded(96, CornerRadius));
        public const int CornerRadius = 36;

        /// <summary>Sliced-image multiplier that keeps the corners at most half the box's short side (round ends).</summary>
        public static float RoundMultiplier(Vector2 size) =>
            Mathf.Max(1f, CornerRadius / Mathf.Max(1f, Mathf.Min(size.x, size.y) * 0.5f));

        static Sprite MakeRounded(int size, int radius)
        {
            var tex = new Texture2D(size, size, TextureFormat.RGBA32, false) { wrapMode = TextureWrapMode.Clamp, filterMode = FilterMode.Bilinear };
            var px = new Color32[size * size];
            for (int y = 0; y < size; y++)
                for (int x = 0; x < size; x++)
                {
                    // distance outside the inner rectangle, anti-aliased over one pixel
                    float dx = Mathf.Max(radius - x - 0.5f, x + 0.5f - (size - radius), 0f);
                    float dy = Mathf.Max(radius - y - 0.5f, y + 0.5f - (size - radius), 0f);
                    float a = Mathf.Clamp01(radius - Mathf.Sqrt(dx * dx + dy * dy) + 0.5f);
                    px[y * size + x] = new Color32(255, 255, 255, (byte)(a * 255));
                }
            tex.SetPixels32(px);
            tex.Apply();
            return Sprite.Create(tex, new Rect(0, 0, size, size), new Vector2(0.5f, 0.5f), 100f, 0,
                                 SpriteMeshType.FullRect, new Vector4(radius, radius, radius, radius));
        }

        public static Canvas Canvas(Transform parent, string name, Vector3 localPos, float yaw, Vector2 size)
        {
            var go = new GameObject(name, typeof(Canvas));
            go.transform.SetParent(parent, false);
            go.transform.localPosition = localPos;
            go.transform.localRotation = Quaternion.Euler(0, yaw, 0);
            go.transform.localScale = Vector3.one * 0.001f;
            var c = go.GetComponent<Canvas>();
            c.renderMode = RenderMode.WorldSpace;
            ((RectTransform)go.transform).sizeDelta = size;
            return c;
        }

        /// <summary>Box anchored at the parent's top-left; pos is the offset of its top-left corner.</summary>
        public static Image Box(Transform parent, Vector2 pos, Vector2 size, Color color, string name = "Box", bool round = false)
        {
            var go = new GameObject(name, typeof(RectTransform), typeof(Image));
            go.transform.SetParent(parent, false);
            var rt = (RectTransform)go.transform;
            rt.anchorMin = rt.anchorMax = new Vector2(0, 1);
            rt.pivot = new Vector2(0, 1);
            rt.anchoredPosition = pos;
            rt.sizeDelta = size;
            var img = go.GetComponent<Image>();
            img.color = color;
            if (round)
            {
                img.sprite = Rounded;
                img.type = Image.Type.Sliced;
                // Thin boxes (the windows' header strip, pills, bars): shrink the corners to half the short side so
                // the ends are true half circles, not squashed flat ovals (human request 2026-11-19)
                img.pixelsPerUnitMultiplier = RoundMultiplier(size);
            }
            img.raycastTarget = false;
            ApplyOnTop(img, parent);
            return img;
        }

        /// <summary>Cartoon card: soft shadow, thick outline, cream (or coloured) fill and a coloured strip on top.</summary>
        public sealed class CardRef
        {
            public Image shadow, outline, fill, strip;

            /// <summary>See-through card: translucent fill, soft outline, faint shadow (text and colours stay solid).</summary>
            public void Glass(float fillAlpha)
            {
                var f = fill.color; f.a = fillAlpha; fill.color = f;
                outline.color = new Color(Outline.r, Outline.g, Outline.b, 0.35f);
                shadow.color = new Color(0f, 0f, 0f, 0.08f);
            }

            public void Resize(Vector2 size)
            {
                shadow.rectTransform.sizeDelta = outline.rectTransform.sizeDelta = size;
                fill.rectTransform.sizeDelta = size - new Vector2(16, 16);
                strip.rectTransform.sizeDelta = new Vector2(size.x - 64, 14);
            }
        }

        /// <summary>Every floating window's top strip has this one colour (design consistency, human request 2026-11-19).</summary>
        public static Color WindowStrip => Accent;
        /// <summary>The header strip's distance from the window's left edge; content that lines up with it uses this.</summary>
        public const float StripInset = 24f;

        /// <summary>
        /// A floating window: the same strip, soft outline and faint shadow on every one (menu, HUD cards, coach bubble,
        /// coach window, side view, summary); only how see-through the fill is differs.
        /// </summary>
        public static CardRef Window(Transform parent, Vector2 size, float fillAlpha, string name = "Panel")
        {
            var c = Card(parent, size, Cream, WindowStrip, name);
            c.Glass(fillAlpha);
            return c;
        }

        /// <summary>A small grey capitals label over a section of a card ("HOW FAR", "REPS", "BADGES").</summary>
        public const int SectionLabelSize = 24;

        public static CardRef Card(Transform parent, Vector2 size, Color fill, Color strip, string name = "Panel")
        {
            var c = new CardRef
            {
                shadow = Box(parent, new Vector2(12, -16), size, new Color(0f, 0f, 0f, 0.25f), name + " shadow", true),
                outline = Box(parent, Vector2.zero, size, Outline, name + " outline", true),
            };
            c.fill = Box(parent, new Vector2(8, -8), size - new Vector2(16, 16), fill, name, true);
            c.strip = Box(c.fill.transform, new Vector2(StripInset, -14), new Vector2(size.x - 64, 14), strip, "Strip", true);
            return c;
        }

        public static TextMeshProUGUI Label(Transform parent, Vector2 pos, Vector2 size, int fontSize, Color color,
                                            TextAnchor align = TextAnchor.UpperLeft, FontStyle style = FontStyle.Normal)
        {
            var go = new GameObject("Text", typeof(RectTransform), typeof(TextMeshProUGUI));
            go.transform.SetParent(parent, false);
            var rt = (RectTransform)go.transform;
            rt.anchorMin = rt.anchorMax = new Vector2(0, 1);
            rt.pivot = new Vector2(0, 1);
            rt.anchoredPosition = pos;
            rt.sizeDelta = size;
            var t = go.GetComponent<TextMeshProUGUI>();
            t.font = TmpFontFor(fontSize, style);
            t.fontSize = fontSize;
            t.color = color;
            t.alignment = Align(align);
            // The display and bold fonts are already heavy: don't fake-bold them again (the default fallback still needs it)
            bool bold = style == FontStyle.Bold || style == FontStyle.BoldAndItalic;
            bool italic = style == FontStyle.Italic || style == FontStyle.BoldAndItalic;
            t.fontStyle = (bold && t.font == TMP_Settings.defaultFontAsset ? FontStyles.Bold : FontStyles.Normal) | (italic ? FontStyles.Italic : FontStyles.Normal);
            t.textWrappingMode = TextWrappingModes.Normal;
            t.overflowMode = TextOverflowModes.Overflow;
            t.richText = true;
            t.raycastTarget = false;
            if (BadgeSprites != null) t.spriteAsset = BadgeSprites;
            ApplyOnTop(t, parent);
            // Big display text always gets its cartoon outline (a lighter shade of its colour); white text has
            // no lighter shade, so its caller outlines it against what it sits on (see Pill)
            if (fontSize >= DisplaySize && !IsWhite(color)) Stroke(t);
            return t;
        }

        /// <summary>Rounded coloured pill with centred bold text.</summary>
        public static TextMeshProUGUI Pill(Transform parent, Vector2 pos, Vector2 size, Color color, string text, int fontSize, Color textColor)
        {
            var bg = Box(parent, pos, size, color, "Pill", true);
            var t = Label(bg.transform, new Vector2(10, 0), size - new Vector2(20, 0), fontSize, textColor, TextAnchor.MiddleCenter, FontStyle.Bold);
            // One line always: long words shrink instead of wrapping out of the pill ("RIGHT SHOULDER")
            t.textWrappingMode = TextWrappingModes.NoWrap;
            t.enableAutoSizing = true;
            t.fontSizeMin = 14;
            t.fontSizeMax = fontSize;
            t.text = text;
            if (IsWhite(textColor)) Stroke(t, Darker(color), 2f);
            return t;
        }

        /// <summary>Recolours a pill made by <see cref="Pill"/>, keeping its text outline a darker shade of the pill.</summary>
        public static void PillColor(TMP_Text pillText, Color color)
        {
            if (pillText.transform.parent.TryGetComponent<Image>(out var bg)) bg.color = color;
            if (pillText.outlineWidth > 0f) pillText.outlineColor = Darker(color);
        }

        static readonly Dictionary<string, Sprite> icons = new Dictionary<string, Sprite>();

        /// <summary>A white icon from Resources/Icons (tint it), or null when the file is missing.</summary>
        public static Sprite Icon(string name)
        {
            if (icons.TryGetValue(name, out var s)) return s;
            var tex = Resources.Load<Texture2D>("Icons/" + name);
            s = tex != null ? Sprite.Create(tex, new Rect(0, 0, tex.width, tex.height), new Vector2(0.5f, 0.5f), 100f) : null;
            return icons[name] = s;
        }

        /// <summary>
        /// Cartoon stroke in a lighter shade of the text's own colour; dark (navy) text gets a light off-white outline
        /// for contrast instead (human requests 2026-10-26).
        /// </summary>
        public static T Stroke<T>(T graphic, float width = 3f) where T : Graphic =>
            Stroke(graphic, IsDark(graphic.color) ? White : Lighter(graphic.color), width);

        /// <summary>True for dark colours such as the navy text colour.</summary>
        public static bool IsDark(Color c) => 0.2126f * c.r + 0.7152f * c.g + 0.0722f * c.b < 0.35f;

        /// <summary>Cartoon stroke around text (thick outline) in a given colour.</summary>
        public static T Stroke<T>(T graphic, Color color, float width = 3f) where T : Graphic
        {
            if (graphic is TMP_Text t)
            {
                // Distance-field outline: about `width` canvas units outside the letters, the face dilated by the
                // same amount so letters keep their weight (the outline is centred on the glyph edge).
                float w = Mathf.Clamp(width * 9f / Mathf.Max(1f, t.fontSize), 0.05f, 0.6f);
                t.outlineColor = color;
                t.outlineWidth = w;
                t.fontMaterial.SetFloat(ShaderUtilities.ID_FaceDilate, t.fontSize >= DisplaySize ? w : w * 0.5f);
                t.UpdateMeshPadding();
                return graphic;
            }
            var o = graphic.gameObject.AddComponent<UnityEngine.UI.Outline>();
            o.effectColor = color;
            o.effectDistance = new Vector2(width, -width);
            return graphic;
        }

        /// <summary>Adds a springy scale "pop" to a UI element; call Punch() on it.</summary>
        public static Bounce Bouncy(Component c)
        {
            var b = c.gameObject.GetComponent<Bounce>();
            return b != null ? b : c.gameObject.AddComponent<Bounce>();
        }

        // Panel transitions (M8.3): one short fade plus a slight scale, in unscaled time so pause never freezes them.
        // VR comfort: 0.25 s or shorter, only the panel moves (never the view), and a panel is fully usable at its end.
        public const float TransitionMin = 0.15f, TransitionMax = 0.25f, TransitionDefault = 0.2f;

        /// <summary>A transition length kept inside the comfort limits (0.15 to 0.25 s).</summary>
        public static float TransitionSeconds(float seconds) => Mathf.Clamp(seconds, TransitionMin, TransitionMax);

        /// <summary>
        /// Shows or hides a panel with the short fade and scale (hiding deactivates it at the end). Use it instead of
        /// SetActive for menus, HUD cards, pop-ups, the summary and the Progress page. Without animate it snaps.
        /// </summary>
        public static PanelFade Show(Component panel, bool visible, bool animate = true, float seconds = TransitionDefault)
        {
            if (panel == null) return null;
            var f = panel.GetComponent<PanelFade>();
            if (f == null) f = panel.gameObject.AddComponent<PanelFade>();
            f.Play(visible, animate, seconds);
            return f;
        }

        /// <inheritdoc cref="Show(Component, bool, bool, float)"/>
        public static PanelFade Show(GameObject panel, bool visible, bool animate = true, float seconds = TransitionDefault) =>
            panel == null ? null : Show(panel.transform, visible, animate, seconds);
    }

    /// <summary>
    /// Fades a panel in or out through a CanvasGroup and scales it slightly around its centre (see UIKit.Show).
    /// Time is unscaled; Step() advances it so tests can drive it without Play mode.
    /// </summary>
    public class PanelFade : MonoBehaviour
    {
        /// <summary>A hidden panel starts this big and grows to full size as it fades in.</summary>
        public const float StartScale = 0.96f;

        CanvasGroup group;
        Vector3 baseScale = Vector3.one;
        Vector2 lastShift;
        float t, duration = UIKit.TransitionDefault;
        bool showing = true, running;

        public bool Running => running;
        public bool Showing => showing;
        public float Duration => duration;

        public CanvasGroup Group
        {
            get
            {
                if (group == null) group = GetComponent<CanvasGroup>();
                if (group == null) group = gameObject.AddComponent<CanvasGroup>();
                return group;
            }
        }

        /// <summary>0 = hidden look, 1 = fully shown, for a transition <paramref name="elapsed"/> seconds in.</summary>
        public static float Progress(float elapsed, float seconds, bool showing)
        {
            float p = Mathf.Clamp01(elapsed / UIKit.TransitionSeconds(seconds));
            p = 1f - (1f - p) * (1f - p);   // ease out: quick start, gentle stop
            return showing ? p : 1f - p;
        }

        public void Play(bool visible, bool animate, float seconds)
        {
            if (!running) baseScale = transform.localScale;   // the layout may have rescaled it since last time
            bool active = gameObject.activeSelf;
            if (!running && active == visible)
            {
                showing = visible;
                if (visible) Apply(1f);   // already shown: make sure it is at full look
                return;
            }
            // Continue from the current look when reversing mid-way, so the panel never jumps
            float from = running ? Group.alpha : (active ? 1f : 0f);
            showing = visible;
            duration = UIKit.TransitionSeconds(seconds);
            t = (showing ? from : 1f - from) * duration;
            if (visible) gameObject.SetActive(true);
            // Snap when asked, or when nothing would drive it (a parent is hidden, so Update never runs)
            if (!animate || !gameObject.activeInHierarchy) { SkipToEnd(); return; }
            running = true;
            Apply(Progress(t, duration, showing));
        }

        /// <summary>Fades an already shown panel in again from its hidden look (e.g. a new menu page).</summary>
        public void Replay(float seconds = UIKit.TransitionDefault)
        {
            if (running && !showing) return;   // fading out: leave it
            if (!running) baseScale = transform.localScale;
            showing = true;
            duration = UIKit.TransitionSeconds(seconds);
            t = 0f;
            if (!gameObject.activeInHierarchy) { SkipToEnd(); return; }
            running = true;
            Apply(0f);
        }

        /// <summary>Jumps to the end state now: fully shown and clickable, or hidden and inactive.</summary>
        public void SkipToEnd()
        {
            running = false;
            Apply(1f);
            // Hidden panels keep their full look, so a plain SetActive(true) elsewhere still shows them normally
            if (!showing) gameObject.SetActive(false);
        }

        /// <summary>Advances the transition by <paramref name="dt"/> seconds (unscaled).</summary>
        public void Step(float dt)
        {
            if (!running) return;
            t += Mathf.Max(0f, dt);
            if (t >= duration) { SkipToEnd(); return; }
            Apply(Progress(t, duration, showing));
        }

        void Update() => Step(Time.unscaledDeltaTime);

        void OnDisable()
        {
            // Turned off by someone else mid-fade: leave it at its full look for next time
            if (running) { running = false; showing = true; Apply(1f); }
        }

        void Apply(float p)
        {
            var g = Group;
            g.alpha = p;
            // No clicks while it fades out (fading in stays clickable, so buttons never flash their disabled tint)
            g.interactable = g.blocksRaycasts = showing || p >= 1f && !running;
            // Only panels inside a canvas scale: a root canvas's scale belongs to the code that places it (laptop or
            // headset size), so it only fades
            if (transform is RectTransform rt && rt.parent is RectTransform)
            {
                float s = Mathf.Lerp(StartScale, 1f, p);
                transform.localScale = baseScale * s;
                // Scale about the centre whatever the pivot (panels here are anchored top-left). Added as a delta, so
                // a layout that moves the panel during the fade is kept.
                var shift = Vector2.Scale(rt.rect.size * (1f - s), new Vector2(0.5f, 0.5f) - rt.pivot);
                shift = Vector2.Scale(shift, new Vector2(baseScale.x, baseScale.y));
                rt.anchoredPosition += shift - lastShift;
                lastShift = shift;
            }
        }
    }

    /// <summary>Marks a canvas whose UI draws on top of the scene (see UIKit.MakeOnTop).</summary>
    public class DrawOnTop : MonoBehaviour { }

    /// <summary>Springy scale punch around the element's centre, independent of pause (unscaled time).</summary>
    public class Bounce : MonoBehaviour
    {
        float t = 10f, amount;

        void Awake()
        {
            // Scale from the centre: move the pivot to the middle without moving the element
            if (transform is RectTransform rt)
            {
                var shift = Vector2.Scale(rt.sizeDelta, new Vector2(0.5f, 0.5f) - rt.pivot);
                rt.pivot = new Vector2(0.5f, 0.5f);
                rt.anchoredPosition += shift;
            }
        }

        public void Punch(float strength = 0.18f) { amount = strength; t = 0f; }

        void Update()
        {
            if (t > 1.2f) return;
            t += Time.unscaledDeltaTime;
            float s = 1f + amount * Mathf.Exp(-t * 7f) * Mathf.Cos(t * 22f);
            transform.localScale = t > 1.2f ? Vector3.one : new Vector3(s, s, 1f);
        }
    }
}
