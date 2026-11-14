using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Rendering;

namespace TheraQuest
{
    /// <summary>
    /// M8.2: faint sunbeams from the windows to the floor, along the sun's direction. A beam is a four-sided prism
    /// drawn with the additive TheraQuest/LightShaft shader (brightest at the window, fading toward the floor and
    /// sides). Static, so nothing flickers or moves in the headset. If the shader is missing, no beams are made.
    /// </summary>
    public static class LightShafts
    {
        public const string Name = "Light shafts";
        const float WindowX = -4.92f, WindowBottom = 1.1f, WindowTop = 2.4f, WindowHalfWidth = 0.75f;

        /// <summary>Makes one beam for each window (given by its z centre) under <paramref name="root"/>. Safe to call twice.</summary>
        public static Transform Build(Transform root, float[] windowZ, Vector3 sunDir)
        {
            var existing = root.Find(Name);
            if (existing != null) return existing;
            var shader = Shader.Find("TheraQuest/LightShaft");
            if (shader == null || !shader.isSupported || sunDir.y > -0.05f) return null;

            var holder = new GameObject(Name).transform;
            holder.SetParent(root, false);
            var mat = new Material(shader) { name = "Light shaft" };
            foreach (float z in windowZ)
            {
                var go = new GameObject("Shaft");
                go.transform.SetParent(holder, false);
                go.AddComponent<MeshFilter>().sharedMesh = Prism(z, sunDir);
                var r = go.AddComponent<MeshRenderer>();
                r.sharedMaterial = mat;
                r.shadowCastingMode = ShadowCastingMode.Off;
                r.receiveShadows = false;
            }
            return holder;
        }

        /// <summary>Beam from the window opening to the floor, as 4 sides; uv.y is 0 at the window and 1 at the floor.</summary>
        public static Mesh Prism(float zCentre, Vector3 sunDir)
        {
            // Carry a point along the sun's direction down to the floor
            Vector3 Floor(Vector3 p) => p + sunDir * (p.y / -sunDir.y);
            var wTL = new Vector3(WindowX, WindowTop, zCentre - WindowHalfWidth);
            var wTR = new Vector3(WindowX, WindowTop, zCentre + WindowHalfWidth);
            var wBL = new Vector3(WindowX, WindowBottom, zCentre - WindowHalfWidth);
            var wBR = new Vector3(WindowX, WindowBottom, zCentre + WindowHalfWidth);
            Vector3 fTL = Floor(wTL), fTR = Floor(wTR), fBL = Floor(wBL), fBR = Floor(wBR);

            var v = new List<Vector3>();
            var uv = new List<Vector2>();
            var t = new List<int>();
            void Quad(Vector3 a0, Vector3 a1, Vector3 b0, Vector3 b1)   // a = window side, b = floor side
            {
                int i = v.Count;
                v.Add(a0); v.Add(a1); v.Add(b0); v.Add(b1);
                uv.Add(new Vector2(0, 0)); uv.Add(new Vector2(1, 0)); uv.Add(new Vector2(0, 1)); uv.Add(new Vector2(1, 1));
                t.AddRange(new[] { i, i + 2, i + 1, i + 1, i + 2, i + 3 });
            }
            Quad(wTL, wTR, fTL, fTR);   // upper face
            Quad(wBL, wBR, fBL, fBR);   // lower face
            Quad(wTL, wBL, fTL, fBL);   // side toward -z
            Quad(wTR, wBR, fTR, fBR);   // side toward +z
            var m = new Mesh { name = "Light shaft" };
            m.SetVertices(v);
            m.SetUVs(0, uv);
            m.SetTriangles(t, 0);
            m.RecalculateNormals();
            m.RecalculateBounds();
            return m;
        }
    }
}
