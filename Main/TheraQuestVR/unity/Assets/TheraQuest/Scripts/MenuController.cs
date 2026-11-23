using System;
using System.Collections.Generic;
using TMPro;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.UI;
#if ENABLE_INPUT_SYSTEM
using UnityEngine.InputSystem.UI;
#endif

namespace TheraQuest
{
    /// <summary>
    /// Main menu, pause menu and settings, as a world-space panel that opens in front of the player
    /// (works on the laptop screen and in the headset).
    ///   Up / Down (arrows or thumbstick) choose, Left / Right change a value,
    ///   Space / Enter / A select, Esc / B go back. On the laptop the mouse can click too.
    /// SessionManager calls <see cref="HandleInput"/> every frame while the menu is open.
    /// The therapist page (patient code, motion input, therapist numbers) sits behind a 4-digit PIN and is
    /// only reachable from the main menu, never mid-session (M4.3). The first visit sets the PIN.
    /// </summary>
    public class MenuController : MonoBehaviour
    {
        public enum Page { Main, Pause, Settings, TherapistPin, Therapist, Progress }

        public SessionManager session;

        public bool IsOpen => canvas != null && canvas.gameObject.activeSelf;
        public Page Current { get; private set; }

        sealed class Item
        {
            public Func<string> label;
            public Func<string> value;          // shown as ‹ value › when the item can be changed
            public Action select;
            public Action<int> adjust;          // -1 / +1
            public Func<bool> enabled = () => true;
        }

        sealed class Row { public Image bg; public ButtonLook look; public TextMeshProUGUI label, value; }

        // Sizes and gaps come from the UIKit scale (M8.5); these are the page's own measures in canvas units
        public const float Width = 1000f, ContentWidth = Width - 2f * UIKit.Gap.Margin;
        const float RowH = 68f, RowGap = UIKit.Gap.Small, HeaderH = 124f, FooterH = 76f;
        public const float RowLabelWidth = 560f;
        /// <summary>Taller pages shrink to stay in view, so every page is kept within this (M8.5 EditMode test).</summary>
        public const float BaseScale = 0.00115f, MaxHeight = 1000f;
        /// <summary>The menu opens this far in front of the eyes and this far below them, in metres.</summary>
        public const float Distance = 1.35f, DropBelowEye = 0.10f;

        Canvas canvas;
        UIKit.CardRef card;
        TextMeshProUGUI title, subtitle, info, footer;
        Image logoMark;                         // the logo's mark (main page only)
        TextMeshProUGUI logoName;               // the logo's name beside it

        public const string LogoMarkResource = "Logo/TheraQuestMark";
        public const int LogoNameSize = 66;      // at or above UIKit.DisplaySize: the cartoon display font

        /// <summary>Sticker-style title (human request 2026-11-19, "flat and obscure"): white outline, a navy outer
        /// edge and drop shadow so it stands off the cream card, and letters lit from above (darker toward the base).</summary>
        public static void StyleLogoName(TMPro.TextMeshProUGUI t)
        {
            // Values tuned in the editor: heavier ones merge LuckiestGuy's letters into one blob
            t.outlineColor = UIKit.White;
            t.outlineWidth = 0.22f;
            var m = t.fontMaterial;
            m.SetFloat(TMPro.ShaderUtilities.ID_FaceDilate, 0.1f);
            m.EnableKeyword(TMPro.ShaderUtilities.Keyword_Underlay);
            m.SetColor(TMPro.ShaderUtilities.ID_UnderlayColor, UIKit.Ink);
            m.SetFloat(TMPro.ShaderUtilities.ID_UnderlayOffsetX, 0.2f);
            m.SetFloat(TMPro.ShaderUtilities.ID_UnderlayOffsetY, -0.3f);
            m.SetFloat(TMPro.ShaderUtilities.ID_UnderlayDilate, 0.25f);
            m.SetFloat(TMPro.ShaderUtilities.ID_UnderlaySoftness, 0f);
            t.enableVertexGradient = true;
            t.colorGradient = new TMPro.VertexGradient(Color.white, Color.white,
                new Color(0.78f, 0.78f, 0.78f), new Color(0.78f, 0.78f, 0.78f));
            t.extraPadding = true;
            t.UpdateMeshPadding();
        }
        public const string LogoText ="Thera<color=" + UIKit.HexTeal + ">Quest</color>";
        const float LogoMarkSize = 80f;
        public const float LogoGap = 36f;          // space between the mark and the name (human request: ample spacing)
        RectTransform tabBar;                   // Progress page tabs
        RectTransform badgeGrid;                // Progress page, Badges tab: one card per badge
        const int BadgeCols = 4;
        Vector3 placedAt;                       // where PlaceInFront put the menu's centre
        const float BadgeCardH = 226f, BadgeGap = UIKit.Gap.Medium;
        readonly List<ButtonLook> tabs = new List<ButtonLook>();
        ProgressViews.ProgressTab progressTab;
        const float TitleX = 50f, TabsY = 172f, TabH = 56f;
        readonly List<Item> items = new List<Item>();
        readonly List<Row> rows = new List<Row>();
        Transform rowRoot;
        int sel, lastSel = -1;
        Page back;                              // where Settings returns to
        readonly int[] pin = new int[4];
        readonly int[] codeDigits = new int[3];
        string pinMessage = "";
        int pinFailures;
        bool changingPin;                       // "Change PIN" chosen: the PIN page sets a new one
        float pinLockedUntil;
        const int MaxPinFailures = 5;
        const float PinLockSeconds = 60f;

        void Awake()
        {
            canvas = UIKit.Canvas(transform, "Menu", Vector3.zero, 0f, new Vector2(Width, 900));
            canvas.sortingOrder = 40;
            ((RectTransform)canvas.transform).pivot = new Vector2(0.5f, 0.5f);
            canvas.gameObject.AddComponent<GraphicRaycaster>();
            canvas.gameObject.AddComponent<UnityEngine.XR.Interaction.Toolkit.UI.TrackedDeviceGraphicRaycaster>();   // controller rays (M10.2)
            var t = canvas.transform;
            card = UIKit.Window(t, new Vector2(Width, 900), 0.97f, "Card");   // same frame as the HUD cards, nearly solid
            title = UIKit.Stroke(UIKit.Label(t, new Vector2(TitleX, -52), new Vector2(ContentWidth, 80), UIKit.TypeSize.Title, UIKit.Orange, TextAnchor.UpperLeft, FontStyle.Bold), 3f);
            // Logo (human choice "B Joint Angle", 2026-11-19): the mark, then the name in Nunito ExtraBold, "Thera" navy
            // and "Quest" blue. It replaces the cartoon title and the tilted headset icon on the main page.
            var markTex = Resources.Load<Texture2D>(LogoMarkResource);
            float nameX = TitleX;
            if (markTex != null)
            {
                logoMark = UIKit.Box(t, new Vector2(TitleX, -40), new Vector2(LogoMarkSize, LogoMarkSize), Color.white, "Logo mark");
                logoMark.sprite = Sprite.Create(markTex, new Rect(0, 0, markTex.width, markTex.height), new Vector2(0.5f, 0.5f), 100f);
                logoMark.preserveAspect = true;
                nameX += LogoMarkSize + LogoGap;
            }
            // The cartoon display face (LuckiestGuy, with its outline), like the old title (human request 2026-11-19)
            logoName = UIKit.Label(t, new Vector2(nameX, -40), new Vector2(Width - 50 - nameX, LogoMarkSize), LogoNameSize, UIKit.Ink, TextAnchor.MiddleLeft, FontStyle.Bold);
            logoName.textWrappingMode = TMPro.TextWrappingModes.NoWrap;
            logoName.enableAutoSizing = true; logoName.fontSizeMin = UIKit.DisplaySize; logoName.fontSizeMax = LogoNameSize;
            StyleLogoName(logoName);
            // Centre on the letters themselves, not the font line box (LuckiestGuy sits off-centre in its line)
            logoName.verticalAlignment = TMPro.VerticalAlignmentOptions.Geometry;
            logoName.text = LogoText;
            badgeGrid = (RectTransform)new GameObject("Badge cards", typeof(RectTransform)).transform;
            badgeGrid.SetParent(t, false);
            badgeGrid.anchorMin = badgeGrid.anchorMax = badgeGrid.pivot = new Vector2(0, 1);
            tabBar = (RectTransform)new GameObject("Tabs", typeof(RectTransform)).transform;
            tabBar.SetParent(t, false);
            tabBar.anchorMin = tabBar.anchorMax = tabBar.pivot = new Vector2(0, 1);
            tabBar.anchoredPosition = new Vector2(TitleX, -TabsY);
            float tx = 0f;
            for (int i = 0; i < ProgressViews.ProgressTabNames.Length; i++)
            {
                int index = i;
                float w = ProgressViews.ProgressTabNames[i].Length * 16f + 70f;
                var bg = UIKit.Box(tabBar, new Vector2(tx, 0), new Vector2(w, TabH), UIKit.Row, "Tab " + i, true);
                var button = bg.gameObject.AddComponent<Button>();
                button.transition = Selectable.Transition.None;
                button.navigation = new Navigation { mode = Navigation.Mode.None };
                button.onClick.AddListener(() => ShowTab((ProgressViews.ProgressTab)index));
                var label = UIKit.Label(bg.transform, Vector2.zero, new Vector2(w, TabH), UIKit.TypeSize.Label, UIKit.Ink, TextAnchor.MiddleCenter, FontStyle.Bold);
                label.text = ProgressViews.ProgressTabNames[i];
                tabs.Add(UIKit.Look(bg, label));
                tx += w + UIKit.Gap.Small;
            }
            subtitle = UIKit.Label(t, new Vector2(52, -HeaderH), new Vector2(ContentWidth, 40), UIKit.TypeSize.Body, UIKit.Muted);
            info = UIKit.Label(t, new Vector2(52, -170), new Vector2(ContentWidth, 120), UIKit.TypeSize.Body, UIKit.Ink);
            rowRoot = new GameObject("Rows", typeof(RectTransform)).transform;
            rowRoot.SetParent(t, false);
            var rr = (RectTransform)rowRoot;
            rr.anchorMin = rr.anchorMax = new Vector2(0, 1);
            rr.pivot = new Vector2(0, 1);
            footer = UIKit.Label(t, Vector2.zero, new Vector2(ContentWidth, 40), UIKit.TypeSize.Caption, UIKit.Muted, TextAnchor.MiddleCenter);
            UIKit.MakeOnTop(canvas, 40);
            canvas.gameObject.SetActive(false);
            EnsureEventSystem();
        }

        static void EnsureEventSystem()
        {
            if (EventSystem.current != null || FindAnyObjectByType<EventSystem>() != null) return;
            var go = new GameObject("EventSystem", typeof(EventSystem));
#if ENABLE_INPUT_SYSTEM
            // The XR Interaction Toolkit's module takes both the controller rays and the mouse (M10.2)
            var module = go.AddComponent<UnityEngine.XR.Interaction.Toolkit.UI.XRUIInputModule>();
            module.enableXRInput = true;
            module.enableMouseInput = true;
#else
            go.AddComponent<StandaloneInputModule>();
#endif
        }

        // ------------------------------------------------------------------ pages
        public void Open(Page page)
        {
            if (page == Page.Settings && Current != Page.Settings) back = IsOpen ? Current : Page.Main;
            if (page == Page.Progress && Current != Page.Progress) progressTab = ProgressViews.ProgressTab.Profile;
            Current = page;
            items.Clear();
            switch (page)
            {
                case Page.Main: BuildMain(); break;
                case Page.Pause: BuildPause(); break;
                case Page.TherapistPin: BuildTherapistPin(); break;
                case Page.Therapist: BuildTherapist(); break;
                case Page.Progress: BuildProgress(); break;
                default: BuildSettings(); break;
            }
            footer.text = page == Page.Progress ? ProgressFooter : ControlHints.Current.MenuFooter;
            // The main page shows the logo in place of the page title
            bool logo = page == Page.Main;
            title.gameObject.SetActive(!logo);
            logoName.gameObject.SetActive(logo);
            if (logoMark != null) logoMark.gameObject.SetActive(logo);
            title.rectTransform.anchoredPosition = new Vector2(TitleX, -52);
            tabBar.gameObject.SetActive(page == Page.Progress);
            Layout();
            if (!IsOpen) PlaceInFront();
            canvas.gameObject.SetActive(true);
            canvas.worldCamera = Camera.main;
            sel = FirstEnabled(0, 1);
            Refresh();
        }

        public void Close() => canvas.gameObject.SetActive(false);

        void BuildMain()
        {
            title.text = "TheraQuest";
            subtitle.text = session.MenuSubtitle;
            info.text = session.MenuInfo;
            var coach = session.coach;
            Add(() => "Start today's quest", select: session.StartQuest, enabled: () => session.CanStart);
            Add(() => "Explore the clinic", select: session.FreeRoam);
            Add(() => "Your progress", select: () => Open(Page.Progress));
            if (coach != null && coach.Ready && coach.Count > 1)
                Add(() => coach.Has3DModels ? "Coach (Female / Male)" : "Coach Style", value: () => coach.CoachName, adjust: d => coach.Cycle(d));
            Add(() => "Settings", select: () => Open(Page.Settings));
            Add(() => "Therapist", select: () => { Array.Clear(pin, 0, pin.Length); pinMessage = ""; Open(Page.TherapistPin); },
                enabled: () => !session.SessionRunning);
            Add(() => "Quit", select: session.Quit);
        }

        void BuildPause()
        {
            title.text = "Paused";
            subtitle.text = session.PauseSubtitle;
            info.text = "Take your time. Your reps so far are kept.";
            Add(() => "Resume", select: session.Resume);
            Add(() => "Restart this exercise", select: session.RestartExercise, enabled: () => session.CanRestartExercise);
            Add(() => "Back to the exercise spot", select: () => { session.ReturnToStation(); session.Resume(); });
            Add(() => "Settings", select: () => Open(Page.Settings));
            Add(() => "End session and save", select: session.EndSessionEarly);
        }

        void BuildProgress()
        {
            title.text = "Your progress";
            subtitle.text = session.ProgressSubtitle;
            info.text = session.ProgressInfo(progressTab);
            Add(() => "Back", select: () => Open(Page.Main));
        }

        static string ProgressFooter
        {
            get
            {
                var k = ControlHints.Current;
                return $"{k.Change} switch tab   ·   {k.Start} select   ·   {k.Back} back";
            }
        }

        /// <summary>Shows one tab of the Progress page (Left / Right, or a click on the tab).</summary>
        void ShowTab(ProgressViews.ProgressTab tab)
        {
            if (Current != Page.Progress) return;
            if (tab != progressTab) session.feedback.PlayClick();
            progressTab = tab;
            info.text = session.ProgressInfo(tab);
            // Each tab is only as tall as its content; keep the card's top edge where it was so it doesn't jump
            var corners = new Vector3[4];
            ((RectTransform)canvas.transform).GetWorldCorners(corners);
            Vector3 topBefore = (corners[1] + corners[2]) / 2f;
            Layout();
            ((RectTransform)canvas.transform).GetWorldCorners(corners);
            canvas.transform.position += topBefore - (corners[1] + corners[2]) / 2f;
            // ...unless a taller tab would then hang lower than when the menu opened: centre it as it was placed
            var p = canvas.transform.position;
            if (p.y < placedAt.y) canvas.transform.position = new Vector3(p.x, placedAt.y, p.z);
            Refresh();
            if (EventSystem.current != null) EventSystem.current.SetSelectedGameObject(null);
        }

        void BuildSettings()
        {
            title.text = "Settings";
            subtitle.text = "Saved on this computer";
            info.text = "";
            Add(() => "Music volume", value: () => GameSettings.Percent(GameSettings.Music), adjust: GameSettings.StepMusic);
            Add(() => "Effects volume", value: () => GameSettings.Percent(GameSettings.Effects),
                adjust: d => { GameSettings.StepEffects(d); session.feedback.PlayClick(); });
            Add(() => "Subtitles", value: () => GameSettings.Subtitles ? "On" : "Off", adjust: d =>
            {
                GameSettings.ToggleSubtitles();
                if (GameSettings.Subtitles) Subtitles.Say("Subtitles are on. Sounds are shown in brackets.", 2.5f, "Click");
            });
            Add(() => "Subtitle size", value: () => GameSettings.SubtitleSizes[GameSettings.SubtitleSize], adjust: d =>
            {
                GameSettings.StepSubtitleSize(d);
                Subtitles.Say("This is how big the subtitles look.", 2.5f);
            });
            Add(() => "Turning", value: () => GameSettings.TurnModes[GameSettings.TurnMode], adjust: GameSettings.StepTurnMode);
            Add(() => "Walking speed", value: () => GameSettings.MoveSpeeds[GameSettings.MoveSpeed], adjust: GameSettings.StepMoveSpeed);
            Add(() => "Back", select: GoBack);
        }

        // ------------------------------------------------------------- therapist
        bool PinLocked => Time.unscaledTime < pinLockedUntil;
        string PinText => $"{pin[0]} {pin[1]} {pin[2]} {pin[3]}";
        string PinValue => string.Concat(pin[0], pin[1], pin[2], pin[3]);

        void BuildTherapistPin()
        {
            bool setting = changingPin || !ClientConfig.Current.HasPin;
            title.text = "Therapist";
            subtitle.text = setting ? "Choose a 4-digit PIN for the therapist page" : "Enter the therapist PIN";
            info.text = PinLocked ? $"<color={UIKit.HexWarn}>Too many wrong PINs. Wait a minute.</color>" : pinMessage;
            for (int i = 0; i < pin.Length; i++)
            {
                int d = i;
                Add(() => $"Digit {d + 1}", value: () => pin[d].ToString(), adjust: k => pin[d] = (pin[d] + k + 10) % 10);
            }
            Add(() => setting ? $"Set PIN {PinText}" : "Unlock", select: setting ? (Action)SetPin : TryPin, enabled: () => !PinLocked);
            Add(() => "Back", select: () => { changingPin = false; Open(Page.Main); });
        }

        void SetPin()
        {
            changingPin = false;
            ClientConfig.Current.SetPin(PinValue);
            Open(Page.Therapist);
        }

        void TryPin()
        {
            if (ClientConfig.Current.CheckPin(PinValue))
            {
                pinFailures = 0;
                Open(Page.Therapist);
                return;
            }
            Array.Clear(pin, 0, pin.Length);
            if (++pinFailures >= MaxPinFailures) { pinLockedUntil = Time.unscaledTime + PinLockSeconds; pinFailures = 0; }
            pinMessage = $"<color={UIKit.HexWarn}>Wrong PIN.</color>";
            Open(Page.TherapistPin);
        }

        string CodeFromDigits => $"P-{codeDigits[0]}{codeDigits[1]}{codeDigits[2]}";

        void BuildTherapist()
        {
            title.text = "Therapist";
            subtitle.text = $"This computer is set to patient {session.ActivePatientCode}";
            info.text = "Codes like P-001. For other codes, start the app with -patient CODE.";
            string cur = session.ActivePatientCode;
            if (cur.Length == 5 && cur.StartsWith("P-") && int.TryParse(cur.Substring(2), out int n))
            {
                codeDigits[0] = n / 100; codeDigits[1] = n / 10 % 10; codeDigits[2] = n % 10;
            }
            for (int i = 0; i < codeDigits.Length; i++)
            {
                int d = i;
                Add(() => $"Patient code digit {d + 1}", value: () => codeDigits[d].ToString(),
                    adjust: k => codeDigits[d] = (codeDigits[d] + k + 10) % 10);
            }
            Add(() => $"Use patient {CodeFromDigits}", select: () => session.SwitchPatient(CodeFromDigits),
                enabled: () => CodeFromDigits != session.ActivePatientCode);
            Add(() => "Motion input", value: () => session.motion.SourceLabel, adjust: d =>
            {
                session.motion.NextSource();
                if (d < 0) session.motion.NextSource();   // three modes: twice forward = once back
            });
            Add(() => "Show numbers (therapist)", value: () => GameSettings.ShowDetails ? "On" : "Off", adjust: d => GameSettings.ToggleDetails());
            Add(() => "Change PIN", select: () =>
            {
                changingPin = true;
                Array.Clear(pin, 0, pin.Length);
                pinMessage = "";
                Open(Page.TherapistPin);
            });
            Add(() => "Back", select: () => Open(Page.Main));
        }

        void Add(Func<string> label, Action select = null, Action<int> adjust = null, Func<string> value = null, Func<bool> enabled = null)
        {
            items.Add(new Item { label = label, select = select, adjust = adjust, value = value, enabled = enabled ?? (() => true) });
        }

        void GoBack()
        {
            if (Current == Page.Settings) Open(back);
            else if (Current == Page.TherapistPin || Current == Page.Therapist) { changingPin = false; Open(Page.Main); }
            else if (Current == Page.Progress) Open(Page.Main);
            else if (Current == Page.Pause) session.Resume();
            else session.FreeRoam();   // Esc on the main menu: close it and look around
        }

        // ------------------------------------------------------------------ layout
        void Layout()
        {
            foreach (Transform c in rowRoot) Destroy(c.gameObject);
            rows.Clear();
            bool hasInfo = !string.IsNullOrEmpty(info.text), tabbed = Current == Page.Progress;
            // The info text is as tall as its content (no empty space); rows start right below it
            // A long subtitle (e.g. a protocol name) wraps: the info starts below its real height, never on top of it
            float subH = string.IsNullOrEmpty(subtitle.text) ? 40f : Mathf.Max(40f, subtitle.preferredHeight);
            subtitle.rectTransform.sizeDelta = new Vector2(ContentWidth, subH);
            float infoTop = InfoTop(subH, tabbed);
            float infoH = hasInfo ? info.preferredHeight : 0f;
            info.rectTransform.anchoredPosition = new Vector2(52, -infoTop);
            info.rectTransform.sizeDelta = new Vector2(ContentWidth, infoH);
            foreach (Transform c in badgeGrid) Destroy(c.gameObject);
            float gridH = 0f;
            if (tabbed && progressTab == ProgressViews.ProgressTab.Badges)
            {
                badgeGrid.anchoredPosition = new Vector2(UIKit.Gap.Margin, -(infoTop + infoH + UIKit.Gap.Medium));
                gridH = BuildBadgeCards(session.ProgressBadges);
            }
            float top = RowsTop(infoTop, infoH, gridH, tabbed);
            ((RectTransform)rowRoot).anchoredPosition = new Vector2(UIKit.Gap.Margin, -top);
            for (int i = 0; i < items.Count; i++)
            {
                int index = i;
                var bg = UIKit.Box(rowRoot, new Vector2(0, -i * (RowH + RowGap)), new Vector2(ContentWidth, RowH), UIKit.Row, "Row " + i, true);
                var button = bg.gameObject.AddComponent<Button>();
                button.transition = Selectable.Transition.None;
                button.navigation = new Navigation { mode = Navigation.Mode.None };
                button.onClick.AddListener(() => Click(index));
                // Pointing (mouse or controller ray) highlights a row; it no longer moves the keyboard choice (M8.5)
                var label = UIKit.Label(bg.transform, new Vector2(34, -10), new Vector2(RowLabelWidth, RowH - 20), UIKit.TypeSize.Item, UIKit.Ink, TextAnchor.MiddleLeft, FontStyle.Bold);
                rows.Add(new Row
                {
                    bg = bg,
                    label = label,
                    look = UIKit.Look(bg, label),
                    value = UIKit.Label(bg.transform, new Vector2(500, -10), new Vector2(ContentWidth - 534, RowH - 20), UIKit.TypeSize.Item, UIKit.Orange, TextAnchor.MiddleRight, FontStyle.Bold),
                });
            }
            float h = top + RowsHeight(items.Count) + FooterH;
            ((RectTransform)canvas.transform).sizeDelta = new Vector2(Width, h);
            canvas.transform.localScale = Vector3.one * BaseScale * Mathf.Min(1f, MaxHeight / h);
            card.Resize(new Vector2(Width, h));
            ((RectTransform)footer.transform).anchoredPosition = new Vector2(UIKit.Gap.Margin, -(h - 60f));
        }

        // Page height math, shared by Layout and the EditMode test that keeps every page from shrinking (M8.5)
        static float InfoTop(float subtitleH, bool tabbed) =>
            tabbed ? TabsY + TabH + UIKit.Gap.Medium : HeaderH + subtitleH + UIKit.Gap.Tight;

        static float RowsTop(float infoTop, float infoH, float gridH, bool tabbed) =>
            gridH > 0f ? infoTop + infoH + UIKit.Gap.Medium + gridH + UIKit.Gap.Large
            : infoH > 0f || tabbed ? infoTop + infoH + UIKit.Gap.Large : infoTop + UIKit.Gap.Medium;

        static float RowsHeight(int rows) => rows * (RowH + RowGap);

        /// <summary>How tall a page is for this content (canvas units); see <see cref="MaxHeight"/>.</summary>
        public static float PageHeight(float subtitleH, float infoH, int rows, float badgeGridH, bool tabbed)
        {
            float infoTop = InfoTop(Mathf.Max(40f, subtitleH), tabbed);
            return RowsTop(infoTop, infoH, badgeGridH, tabbed) + RowsHeight(rows) + FooterH;
        }

        /// <summary>Height of the Badges tab's card grid for this many badges.</summary>
        public static float BadgeGridHeight(int badges)
        {
            int rowsN = (badges + BadgeCols - 1) / BadgeCols;
            return rowsN == 0 ? 0f : rowsN * BadgeCardH + (rowsN - 1) * BadgeGap;
        }

        /// <summary>
        /// One card per badge (human request 2026-10-26): icon on a round chip, name, and how to earn it at the bottom.
        /// Earned cards are bright with an orange chip; locked ones are greyed. Returns the grid's height.
        /// </summary>
        float BuildBadgeCards(List<BadgeInfo> badges)
        {
            float w = (ContentWidth - (BadgeCols - 1) * BadgeGap) / BadgeCols;
            const float ChipSize = 76f;
            for (int i = 0; i < badges.Count; i++)
            {
                var b = badges[i];
                var holder = (RectTransform)new GameObject("Badge card " + b.code, typeof(RectTransform)).transform;
                holder.SetParent(badgeGrid, false);
                holder.anchorMin = holder.anchorMax = holder.pivot = new Vector2(0, 1);
                holder.anchoredPosition = new Vector2(i % BadgeCols * (w + BadgeGap), -(i / BadgeCols) * (BadgeCardH + BadgeGap));
                // Plain cards, no coloured bar on top (human request 2026-10-26); greyed while locked
                var card = UIKit.Tile(holder, new Vector2(w, BadgeCardH), b.earned, "Badge card");
                var f = card.fill.transform;
                float inner = w - 16f;

                var chip = UIKit.Box(f, new Vector2((inner - ChipSize) / 2f, -UIKit.Gap.Medium), new Vector2(ChipSize, ChipSize), b.earned ? UIKit.Orange : UIKit.Track, "Chip", true);
                var sprite = UIKit.BadgeIcon(b.code);
                if (sprite != null)
                {
                    var icon = UIKit.Box(chip.transform, new Vector2(13, -13), new Vector2(50, 50), b.earned ? UIKit.White : UIKit.Muted, "Icon", false);
                    icon.sprite = sprite;
                    icon.preserveAspect = true;
                }
                else UIKit.Label(chip.transform, Vector2.zero, new Vector2(ChipSize, ChipSize), UIKit.DisplaySize, b.earned ? UIKit.White : UIKit.Muted,
                                 TextAnchor.MiddleCenter, FontStyle.Bold).text = "★";

                var name = UIKit.Label(f, new Vector2(10, -106), new Vector2(inner - 20f, 34), UIKit.TypeSize.Label, b.earned ? UIKit.Ink : UIKit.Muted,
                                       TextAnchor.UpperCenter, FontStyle.Bold);
                name.text = b.name;
                name.enableAutoSizing = true;
                name.fontSizeMin = UIKit.TypeSize.Caption;
                name.fontSizeMax = UIKit.TypeSize.Label;
                var desc = UIKit.Label(f, new Vector2(10, -144), new Vector2(inner - 20f, 64), UIKit.TypeSize.Caption, UIKit.Muted, TextAnchor.UpperCenter);
                desc.lineSpacing = -8f;
                desc.text = ProgressViews.BadgeHint(b.code);
            }
            return BadgeGridHeight(badges.Count);
        }

        void PlaceInFront()
        {
            var cam = Camera.main != null ? Camera.main.transform : transform;
            var fwd = cam.forward; fwd.y = 0f;
            if (fwd.sqrMagnitude < 1e-4f) fwd = Vector3.forward;
            fwd.Normalize();
            canvas.transform.position = placedAt = cam.position + fwd * Distance + Vector3.down * DropBelowEye;
            canvas.transform.rotation = Quaternion.LookRotation(fwd, Vector3.up);
        }

        void Refresh()
        {
            for (int i = 0; i < tabs.Count; i++)
            {
                tabs[i].selected = (int)progressTab == i;
                tabs[i].Apply();
            }
            for (int i = 0; i < rows.Count; i++)
            {
                var it = items[i];
                bool chosen = i == sel;
                var look = rows[i].look;
                look.selected = chosen;
                look.interactable = it.enabled();
                look.Apply();
                rows[i].label.text = (chosen ? "▶  " : "     ") + it.label();
                var state = look.State;
                rows[i].value.color = state == UIKit.ButtonState.Selected || state == UIKit.ButtonState.Pressed ? UIKit.White
                    : state == UIKit.ButtonState.Disabled ? UIKit.Buttons.disabledText : UIKit.Orange;
                string v = it.value != null ? it.value() : "";
                rows[i].value.text = it.value != null ? (it.adjust != null ? (chosen ? $"◀   {v}   ▶" : $"‹  {v}  ›") : v) : "";
                if (chosen && i != lastSel) UIKit.Bouncy(rows[i].bg).Punch(0.05f);
            }
        }

        // ------------------------------------------------------------------ input
        public void HandleInput()
        {
            if (!IsOpen) return;
            if (InputHelper.UpPressed) Move(-1);
            if (InputHelper.DownPressed) Move(1);
            bool tabbed = Current == Page.Progress;   // Left / Right switch the Progress tabs
            if (InputHelper.LeftPressed) { if (tabbed) ShowTab((ProgressViews.ProgressTab)(((int)progressTab + 2) % 3)); else Adjust(-1); }
            if (InputHelper.RightPressed) { if (tabbed) ShowTab((ProgressViews.ProgressTab)(((int)progressTab + 1) % 3)); else Adjust(1); }
            if (InputHelper.StartPressed) Activate(sel);
            else if (InputHelper.BackPressed) GoBack();
            if (IsOpen) Refresh();
            lastSel = sel;
        }

        void Move(int dir)
        {
            int next = FirstEnabled(sel + dir, dir);
            if (next != sel) { sel = next; session.feedback.PlayClick(); }
        }

        int FirstEnabled(int from, int dir)
        {
            for (int k = 0; k < items.Count; k++)
            {
                int i = ((from + k * dir) % items.Count + items.Count) % items.Count;
                if (items[i].enabled()) return i;
            }
            return 0;
        }

        void Adjust(int dir)
        {
            if (sel < items.Count && items[sel].adjust != null && items[sel].enabled()) items[sel].adjust(dir);
        }

        void Activate(int i)
        {
            if (i >= items.Count || !items[i].enabled()) return;
            if (i < rows.Count) rows[i].look.Flash();   // the pressed colour, for Enter / Space / A too
            session.feedback.PlayClick();
            if (items[i].select != null) items[i].select();
            else items[i].adjust?.Invoke(1);
        }

        void Click(int i)
        {
            sel = i;
            Activate(i);
            if (EventSystem.current != null) EventSystem.current.SetSelectedGameObject(null);   // so Space doesn't click it again
            if (IsOpen) Refresh();
        }
    }
}
