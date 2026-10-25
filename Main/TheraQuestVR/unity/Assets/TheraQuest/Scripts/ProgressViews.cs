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

        /// <summary>Rich text for the Progress page on the main menu.</summary>
        public static string ProgressPage(ProgramResponse p, bool online)
        {
            var sb = new StringBuilder();
            if (p == null || p.patient == null) return "Loading…";
            var prog = p.progress ?? new ProgressInfo();
            var xp = Xp(p.patient.xp, p.patient.xp);
            sb.Append($"<b>Level {xp.toLevel}</b> · {Mathf.RoundToInt(xp.toFrac * 100)}% of the way to level {xp.toLevel + 1}");
            sb.Append($"   ·   <b>{p.patient.streak}</b> day streak");
            sb.Append($"   ·   <b>{prog.completeSessions}</b> of {prog.totalSessions} sessions completed\n");

            var gallery = Gallery(prog, p.patient.badges);
            int earned = 0;
            foreach (var b in gallery) if (b.earned) earned++;
            sb.Append($"\n<b>Badges</b>  {earned} of {gallery.Count}\n");
            for (int i = 0; i < gallery.Count; i++)
            {
                var b = gallery[i];
                if (i > 0 && i % 4 == 0) sb.Append("\n");   // whole names per line, never "On a / roll"
                sb.Append(b.earned ? $"<color={UIKit.HexGold}>★</color> {b.name}    " : $"<color=#C9C3B6>★</color> <color={UIKit.HexMuted}>{b.name}</color>    ");
            }
            sb.Append("\n");

            sb.Append("\n<b>Recent sessions</b>\n");
            if (prog.recent == null || prog.recent.Length == 0) sb.Append($"<color={UIKit.HexMuted}>No sessions yet. Start today's quest!</color>\n");
            else
                foreach (var r in prog.recent)
                {
                    string day = !string.IsNullOrEmpty(r.started_at) && r.started_at.Length >= 10 ? r.started_at.Substring(0, 10) : "";
                    string stars = $"<color={UIKit.HexGold}>{new string('★', Mathf.Clamp(r.stars, 0, 3))}</color>" + $"<color=#C9C3B6>{new string('★', 3 - Mathf.Clamp(r.stars, 0, 3))}</color>";
                    string status = r.status == "complete" ? $"<color={UIKit.HexGood}>done</color>" : $"<color={UIKit.HexWarn}>partly done</color>";
                    sb.Append($"{day}   {stars}   {status}   {r.valid} good reps   {r.points} points\n");
                }
            if (!online) sb.Append($"\n<color={UIKit.HexWarn}>Offline: this is your progress from the last time the app was connected.</color>");
            return sb.ToString().TrimEnd('\n');
        }
    }
}
