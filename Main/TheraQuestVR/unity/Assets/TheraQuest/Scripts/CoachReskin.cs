using UnityEngine;

namespace TheraQuest
{
    /// <summary>
    /// M8.2: the coaches' own colours (white top, teal shorts or trousers, auburn hair) as a repaint of the Little Guys
    /// colour picture. The pack's model, rig and material stay as imported; the new picture is put on a copy of the
    /// material at startup. A missing picture keeps the pack's original look.
    /// </summary>
    public static class CoachReskin
    {
        /// <summary>Resources path of the repaint for a model name ("Free Woman Tall" gives "CoachTextures/coach_woman").</summary>
        public static string PathFor(string modelName)
        {
            string n = (modelName ?? "").ToLowerInvariant();
            if (n.Contains("woman")) return "CoachTextures/coach_woman";
            if (n.Contains("man")) return "CoachTextures/coach_man";
            return null;
        }

        /// <summary>Puts the repaint on every renderer under <paramref name="coach"/>. Returns false when there is none.</summary>
        public static bool Apply(GameObject coach, string modelName)
        {
            string path = PathFor(modelName);
            if (coach == null || path == null) return false;
            var tex = Resources.Load<Texture2D>(path);
            if (tex == null) return false;
            foreach (var r in coach.GetComponentsInChildren<Renderer>(true))
            {
                var ms = r.materials;   // copies; the pack's material asset is never edited
                for (int i = 0; i < ms.Length; i++)
                    if (ms[i] != null && ms[i].HasProperty("_MainTex")) ms[i].mainTexture = tex;
                r.materials = ms;
            }
            return true;
        }
    }
}
