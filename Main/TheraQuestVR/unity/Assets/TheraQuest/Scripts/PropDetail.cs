using System.Collections.Generic;
using UnityEngine;

namespace TheraQuest
{
    /// <summary>
    /// M8.2: gives the room's flat-colour models surface detail. Each model material is replaced by a copy that uses the
    /// TheraQuest/PropDetail shader with the same colour, a grain that matches the material (wood streaks, fabric
    /// weave, brushed metal, soft speckle) and a lower, varied shininess. The grain pictures are generated at startup,
    /// so there is no asset to go missing; if the shader is missing the original material is kept.
    /// </summary>
    public static class PropDetail
    {
        public enum Kind { Soft, Wood, Fabric, Metal, Rubber }

        static readonly Dictionary<Material, Material> cache = new Dictionary<Material, Material>();
        static readonly Dictionary<Kind, Texture2D> grains = new Dictionary<Kind, Texture2D>();

        /// <summary>Guesses the material kind from the name used by the model packs ("wood", "carpet", "metal2", "pink" ...).</summary>
        public static Kind KindOf(string materialName)
        {
            string n = (materialName ?? "").ToLowerInvariant();
            if (n.Contains("wood")) return Kind.Wood;
            if (n.Contains("carpet") || n.Contains("white") || n.Contains("towel") || n.Contains("lamp")) return Kind.Fabric;
            if (n.Contains("metal") || n.Contains("dark") || n.Contains("steel")) return Kind.Metal;
            if (n.Contains("pink") || n.Contains("blue") || n.Contains("red") || n.Contains("purple") || n.Contains("green")) return Kind.Rubber;
            return Kind.Soft;
        }

        /// <summary>Detail copy of <paramref name="src"/>, or <paramref name="src"/> itself when it can't be improved.</summary>
        public static Material For(Material src)
        {
            if (src == null) return null;
            if (cache.TryGetValue(src, out var done) && done != null) return done;
            var shader = Shader.Find("TheraQuest/PropDetail");
            if (shader == null || !shader.isSupported || src.shader == shader) return src;

            var kind = KindOf(src.name);
            var m = new Material(shader) { name = src.name };   // same name: ClinicRoom.Glass still finds "metal2"
            Color c = src.HasProperty("_BaseColor") ? src.GetColor("_BaseColor") : src.color;
            m.SetColor("_BaseColor", c);
            m.SetTexture("_GrainTex", Grain(kind));
            switch (kind)
            {
                case Kind.Wood:   Set(m, 5f, 0.28f, 0.12f, 0.30f, 0.10f, 0f); break;
                case Kind.Fabric: Set(m, 14f, 0.22f, 0.10f, 0.08f, 0.04f, 0f); break;
                case Kind.Metal:  Set(m, 10f, 0.18f, 0.08f, 0.50f, 0.18f, 0.55f); break;
                case Kind.Rubber: Set(m, 9f, 0.16f, 0.10f, 0.35f, 0.10f, 0f); break;
                default:          Set(m, 6f, 0.18f, 0.12f, 0.18f, 0.08f, 0f); break;
            }
            cache[src] = m;
            return m;
        }

        /// <summary>Replaces the materials of every renderer under <paramref name="root"/> with detail copies.</summary>
        public static void Apply(Transform root)
        {
            foreach (var r in root.GetComponentsInChildren<Renderer>())
            {
                var ms = r.sharedMaterials;
                for (int i = 0; i < ms.Length; i++) ms[i] = For(ms[i]);
                r.sharedMaterials = ms;
            }
        }

        static void Set(Material m, float scale, float grain, float macro, float smooth, float smoothVar, float metal)
        {
            m.SetFloat("_GrainScale", scale);
            m.SetFloat("_GrainStrength", grain);
            m.SetFloat("_MacroStrength", macro);
            m.SetFloat("_Smoothness", smooth);
            m.SetFloat("_SmoothVar", smoothVar);
            m.SetFloat("_Metallic", metal);
        }

        /// <summary>Tileable grey picture for the kind (periodic sums of cosines, so the edges match).</summary>
        public static Texture2D Grain(Kind kind)
        {
            if (grains.TryGetValue(kind, out var t) && t != null) return t;
            const int S = 128;
            var rng = new System.Random(1000 + (int)kind);
            // (max frequency along x, max frequency along y, number of waves): streaks use high y, low x
            int fxMax, fyMax, waves;
            switch (kind)
            {
                case Kind.Wood: fxMax = 2; fyMax = 40; waves = 40; break;
                case Kind.Metal: fxMax = 3; fyMax = 48; waves = 40; break;
                case Kind.Fabric: fxMax = 32; fyMax = 32; waves = 2; break;
                case Kind.Rubber: fxMax = 24; fyMax = 24; waves = 40; break;
                default: fxMax = 20; fyMax = 20; waves = 36; break;
            }
            var v = new float[S * S];
            float min = float.MaxValue, max = float.MinValue;
            var fx = new int[waves]; var fy = new int[waves]; var px = new float[waves]; var py = new float[waves]; var a = new float[waves];
            for (int k = 0; k < waves; k++)
            {
                fx[k] = rng.Next(1, fxMax + 1); fy[k] = rng.Next(1, fyMax + 1);
                px[k] = (float)rng.NextDouble() * 6.2832f; py[k] = (float)rng.NextDouble() * 6.2832f;
                a[k] = (0.3f + (float)rng.NextDouble() * 0.7f) / (1f + 0.1f * (fx[k] + fy[k]));
            }
            for (int y = 0; y < S; y++)
                for (int x = 0; x < S; x++)
                {
                    float u = x / (float)S * 6.2832f, w = y / (float)S * 6.2832f, s = 0f;
                    if (kind == Kind.Fabric)
                        s = Mathf.Sin(u * fxMax) * 0.5f + Mathf.Sin(w * fyMax) * 0.5f + 0.4f * Mathf.Sin(u * 3 + px[0]) * Mathf.Sin(w * 3 + py[1]);
                    else
                        for (int k = 0; k < waves; k++) s += a[k] * Mathf.Cos(fx[k] * u + px[k]) * Mathf.Cos(fy[k] * w + py[k]);
                    v[y * S + x] = s;
                    if (s < min) min = s; if (s > max) max = s;
                }
            var px32 = new Color32[S * S];
            for (int i = 0; i < v.Length; i++)
            {
                byte g = (byte)Mathf.RoundToInt(Mathf.InverseLerp(min, max, v[i]) * 255f);
                px32[i] = new Color32(g, g, g, 255);
            }
            t = new Texture2D(S, S, TextureFormat.RGBA32, true, true) { name = "Grain " + kind, wrapMode = TextureWrapMode.Repeat, filterMode = FilterMode.Bilinear, anisoLevel = 4 };
            t.SetPixels32(px32);
            t.Apply(true);
            grains[kind] = t;
            return t;
        }
    }
}
