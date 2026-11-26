using System.Collections.Generic;
using System.Text;
using UnityEngine;

namespace TheraQuest
{
    /// <summary>
    /// Text and numbers for the session summary and the Progress page (M5.5). Pure functions, so EditMode tests
    /// cover them; HUDController and MenuController only draw what these return.
    /// </summary>
    public static class ProgressViews
    {
        /// <summary>Where the XP bar starts and ends on the summary (level and share of the level filled).</summary>
        public struct XpSpan
        {
            public int fromLevel, toLevel;
            public float fromFrac, toFrac;
            public bool LevelUp => toLevel > fromLevel;
        }

        /// <summary>Only webcam sessions count on the server (M7.1); XP, badges and progress ignore the rest.</summary>
        public static bool IsCounted(string inputSource) => inputSource == "webcam";

        /// <summary>One short line for the summary of a session that does not count (empty for a webcam session).</summary>
        public static string PracticeLine(string inputSource) => IsCounted(inputSource) ? "" : "Practice: not counted";

        public static XpSpan Xp(int oldXp, int newXp)
        {
            GamificationManager.Level(Mathf.Max(0, oldXp), out int l0, out int i0, out int n0);
            GamificationManager.Level(Mathf.Max(0, newXp), out int l1, out int i1, out int n1);
            return new XpSpan { fromLevel = l0, toLevel = l1, fromFrac = (float)i0 / n0, toFrac = (float)i1 / n1 };
        }

        /// <summary>Display names for badge codes (unknown codes are shown as they are).</summary>
        public static List<string> BadgeNames(IEnumerable<string> codes)
        {
            var names = new List<string>();
            if (codes == null) return names;
            foreach (var c in codes)
                if (!string.IsNullOrEmpty(c) && !names.Contains(Name(c))) names.Add(Name(c));
            return names;
        }

        static string Name(string code) => GamificationManager.BadgeNames.TryGetValue(code, out var n) ? n : code;

        /// <summary>Badge codes without blanks or repeats, in order.</summary>
        public static List<string> BadgeCodes(IEnumerable<string> codes)
        {
            var list = new List<string>();
            if (codes != null)
                foreach (var c in codes)
                    if (!string.IsNullOrEmpty(c) && !list.Contains(c)) list.Add(c);
            return list;
        }

        /// <summary>Summary line for the badges revealed so far, each with its icon: "New badges: [icon] Combo 10, ...".</summary>
        public static string NewBadgesLine(IList<string> shown, int total)
        {
            var parts = new List<string>();
            foreach (var c in shown) parts.Add($"{UIKit.BadgeTag(c, true)} {Name(c)}");
            return $"New badge{(total > 1 ? "s" : "")}: " + string.Join(",  ", parts);
        }

        /// <summary>Every badge, earned or locked. Uses the server's list when there is one, else the game's own.</summary>
        public static List<BadgeInfo> Gallery(ProgressInfo progress, IEnumerable<string> owned)
        {
            var have = new HashSet<string>(owned ?? new string[0]);
            var list = new List<BadgeInfo>();
            if (progress != null && progress.badges != null && progress.badges.Length > 0)
                foreach (var b in progress.badges)
                    list.Add(new BadgeInfo { code = b.code, name = b.name, earned = b.earned || have.Contains(b.code) });
            else
                foreach (var kv in GamificationManager.BadgeNames)
                    list.Add(new BadgeInfo { code = kv.Key, name = kv.Value, earned = have.Contains(kv.Key) });
            return list;
        }

        /// <summary>The Progress page's tabs, in order (human request 2026-10-26).</summary>
        public enum ProgressTab { Profile, Sessions, Badges }
        public static readonly string[] ProgressTabNames = { "Profile", "Recent sessions", "Badges" };

        /// <summary>How each badge is earned, in a few words, for the badge cards on the Badges tab.</summary>
        static readonly Dictionary<string, string> BadgeHints = new Dictionary<string, string>
        {
            { "first", "Finish a whole session" }, { "perfect", "5 reps of 95% or better in a row" },
            { "combo10", "10 good reps in a row" }, { "fullrom", "A rep right on the target" },
            { "streak3", "A 3-day streak" }, { "adh80", "Do 80% of your planned days" }, { "lv5", "Reach level 5" },
        };

        /// <summary>How to earn a badge ("" for an unknown code).</summary>
        public static string BadgeHint(string code) => BadgeHints.TryGetValue(code ?? "", out var h) ? h : "";

        /// <summary>A page's one headline number or word, in the scale's heading size.</summary>
        public static string Headline(string text) => $"<size={UIKit.TypeSize.Heading}><b>{text}</b></size>";

        /// <summary>Rich text for one tab of the Progress page on the main menu.</summary>
        public static string ProgressPage(ProgramResponse p, bool online, ProgressTab tab)
        {
            if (p == null || p.patient == null) return "Loading…";
            var prog = p.progress ?? new ProgressInfo();
            var sb = new StringBuilder();
            switch (tab)
            {
                case ProgressTab.Profile:
                {
                    var xp = Xp(p.patient.xp, p.patient.xp);
                    int earned = 0;
                    var gallery = Gallery(prog, p.patient.badges);
                    foreach (var b in gallery) if (b.earned) earned++;
                    // One headline (the level), then the details (M8.5)
                    sb.Append($"{Headline($"Level {xp.toLevel}")}   {Mathf.RoundToInt(xp.toFrac * 100)}% of the way to level {xp.toLevel + 1}\n");
                    sb.Append($"<b>{p.patient.streak}</b> day streak\n");
                    sb.Append($"<b>{prog.completeSessions}</b> of {prog.totalSessions} sessions completed\n");
                    sb.Append($"<b>{earned}</b> of {gallery.Count} badges earned\n");
                    if (!online) sb.Append($"\n<color={UIKit.HexWarn}>Offline: this is your progress from the last time the app was connected.</color>");
                    break;
                }
                case ProgressTab.Sessions:
                    if (prog.recent == null || prog.recent.Length == 0) sb.Append($"<color={UIKit.HexMuted}>No sessions yet. Start today's quest!</color>");
                    else
                        foreach (var r in prog.recent)
                        {
                            string day = !string.IsNullOrEmpty(r.started_at) && r.started_at.Length >= 10 ? r.started_at.Substring(0, 10) : "";
                            int st = Mathf.Clamp(r.stars, 0, 3);
                            string stars = $"<color={UIKit.HexGold}>{new string('★', st)}</color><color={UIKit.HexLocked}>{new string('★', 3 - st)}</color>";
                            string status = r.status == "complete" ? $"<color={UIKit.HexGood}>done</color>" : $"<color={UIKit.HexWarn}>partly done</color>";
                            sb.Append($"<color={UIKit.HexMuted}>{day}</color>   {stars}   {status}   <b>{r.valid}</b> good reps   <b>{r.points}</b> points\n");
                        }
                    break;
                default:
                {
                    // The badges themselves are cards drawn by the menu (MenuController); this is the line above them
                    int earned = 0;
                    var gallery = Gallery(prog, p.patient.badges);
                    foreach (var b in gallery) if (b.earned) earned++;
                    sb.Append($"{Headline(earned.ToString())} of {gallery.Count} badges earned");
                    break;
                }
            }
            return sb.ToString().TrimEnd('\n');
        }
    }
}
