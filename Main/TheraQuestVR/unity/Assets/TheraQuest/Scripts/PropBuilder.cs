using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Rendering;

namespace TheraQuest
{
    /// <summary>
    /// Exercise furniture: the seated-exercise chair (a Kenney model, primitives as a fallback) and the yoga mat,
    /// plus loading of the room's decoration models. Colours stand out from the floor so the
    /// patient can see what the coach is sitting or lying on. No colliders (the player walks through the coach area).
    /// </summary>
    public static class PropBuilder
    {
        static readonly Color Wood = new Color(0.62f, 0.44f, 0.28f);
        static readonly Color Cushion = new Color(0.18f, 0.72f, 0.66f);
        static readonly Dictionary<Color, Material> mats = new Dictionary<Color, Material>();

        static Material Mat(Color c)
        {
            if (!mats.TryGetValue(c, out var m) || m == null) mats[c] = m = FigureVisualizer.MakeMat(c, false);
            return m;
        }

        static Transform Part(PrimitiveType type, Transform parent, Vector3 pos, Vector3 scale, Color c, string name, Quaternion? rot = null)
        {
            var go = GameObject.CreatePrimitive(type);
            go.name = name;
            Object.Destroy(go.GetComponent<Collider>());
            go.transform.SetParent(parent, false);
            go.transform.localPosition = pos;
            go.transform.localRotation = rot ?? Quaternion.identity;
            go.transform.localScale = scale;
            var r = go.GetComponent<Renderer>();
            r.sharedMaterial = Mat(c);
            r.shadowCastingMode = ShadowCastingMode.On;
            return go.transform;
        }

        /// <summary>
        /// A 3D model from Resources (room decoration or exercise prop, see CREDITS.md), turned by yaw, scaled, and
        /// moved so the middle of its base sits on floorPos (in parent space). Returns null when the model is missing.
        /// </summary>
        public static Transform Model(string resource, Transform parent, Vector3 floorPos, float yaw, Vector3 scale, bool solid = false)
        {
            var prefab = Resources.Load<GameObject>(resource);
            if (prefab == null) return null;
            var holder = new GameObject(prefab.name).transform;
            holder.SetParent(parent, false);
            var go = Object.Instantiate(prefab, holder, false);
            go.transform.localRotation = Quaternion.Euler(0f, yaw, 0f) * go.transform.localRotation;
            go.transform.localScale = Vector3.Scale(go.transform.localScale, scale);
            var rs = go.GetComponentsInChildren<Renderer>();
            if (rs.Length > 0)
            {
                var b = rs[0].bounds;
                foreach (var r in rs) { b.Encapsulate(r.bounds); r.shadowCastingMode = ShadowCastingMode.On; }
                go.transform.position += holder.position - new Vector3(b.center.x, b.min.y, b.center.z);
                if (solid)
                {
                    var box = holder.gameObject.AddComponent<BoxCollider>();   // the player walks around it
                    box.center = new Vector3(0f, b.size.y / 2f, 0f);
                    box.size = b.size;
                }
            }
            holder.localPosition = floorPos;
            return holder;
        }

        /// <summary>Kenney Furniture Kit models are about five times life size.</summary>
        public const float KenneyScale = 0.2f;

        /// <summary>
        /// The seated-exercise chair: Kenney's cushioned wooden chair (CC0), seat top at seatTop, seat spanning
        /// zBack..zFront (backrest at zBack), centred on x = 0. Falls back to a chair made of primitives.
        /// </summary>
        public static void Chair(Transform parent, float seatTop, float zBack, float zFront)
        {
            // Measured on the model: the seat top is at 52% of its height and the backrest fills the last tenth of its
            // depth on +Z (the chair faces -Z), so it is turned to face +Z like the coach and stretched to fit
            const float seatFraction = 0.52f, modelUnits = 2f, modelHeight = 4.6f;
            float sy = seatTop / (seatFraction * modelHeight);
            float sz = (zFront - zBack) / (0.9f * modelUnits);
            var chair = Model("Room/Furniture/chairCushion", parent, new Vector3(0f, 0f, (zBack + zFront) / 2f - 0.05f * (zFront - zBack)), 180f,
                              new Vector3(0.5f / modelUnits, sy, sz));
            if (chair != null) return;
            PrimitiveChair(parent, seatTop, zBack, zFront);
        }

        static void PrimitiveChair(Transform parent, float seatTop, float zBack, float zFront)
        {
            float depth = zFront - zBack, mid = (zBack + zFront) / 2f, w = 0.52f;
            Part(PrimitiveType.Cube, parent, new Vector3(0, seatTop - 0.11f, mid), new Vector3(w, 0.04f, depth), Wood, "Seat board");
            Part(PrimitiveType.Cube, parent, new Vector3(0, seatTop - 0.045f, mid), new Vector3(w - 0.02f, 0.09f, depth - 0.02f), Cushion, "Seat cushion");
            float legH = Mathf.Max(0.05f, seatTop - 0.13f);
            foreach (var x in new[] { -w / 2f + 0.04f, w / 2f - 0.04f })
                foreach (var z in new[] { zBack + 0.04f, zFront - 0.04f })
                    Part(PrimitiveType.Cylinder, parent, new Vector3(x, legH / 2f, z), new Vector3(0.05f, legH / 2f, 0.05f), Wood, "Leg");
            // Backrest: two posts and a rounded pad
            foreach (var x in new[] { -w / 2f + 0.04f, w / 2f - 0.04f })
                Part(PrimitiveType.Cylinder, parent, new Vector3(x, seatTop + 0.2f, zBack + 0.03f), new Vector3(0.045f, 0.3f, 0.045f), Wood, "Back post");
            Part(PrimitiveType.Capsule, parent, new Vector3(0, seatTop + 0.36f, zBack + 0.03f), new Vector3(0.22f, w / 2f, 0.07f), Cushion,
                 "Back pad", Quaternion.Euler(0, 0, 90));
        }

        /// <summary>
        /// Yoga mat lying on the floor, centred on the parent, long side along X: a rounded slab (6 mm thick) in the
        /// palette blue with a slightly lighter inset panel, like a real mat's textured top.
        /// </summary>
        public static Transform YogaMat(Transform parent, float length, float width)
        {
            var mat = new GameObject("Yoga mat").transform;
            mat.SetParent(parent, false);
            Slab(mat, "Mat", length, width, 0.006f, Mathf.Min(0.08f, width * 0.15f), 0f, UIKit.Blue);
            Slab(mat, "Mat top", length - 0.07f, width - 0.07f, 0.0012f, Mathf.Min(0.06f, width * 0.12f), 0.006f,
                 UIKit.Lighter(UIKit.Blue, 0.12f));
            return mat;
        }

        /// <summary>Flat rounded rectangle of the given size and thickness, its bottom at y.</summary>
        static void Slab(Transform parent, string name, float length, float width, float thick, float radius, float y, Color c)
        {
            var go = new GameObject(name, typeof(MeshFilter), typeof(MeshRenderer));
            go.transform.SetParent(parent, false);
            go.transform.localPosition = new Vector3(0f, y, 0f);
            go.GetComponent<MeshFilter>().sharedMesh = RoundedSlab(length, width, thick, radius);
            var r = go.GetComponent<MeshRenderer>();
            r.sharedMaterial = Mat(c);
            r.shadowCastingMode = ShadowCastingMode.Off;
        }

        static Mesh RoundedSlab(float length, float width, float thick, float radius, int seg = 6)
        {
            // Outline of the rounded rectangle, counter-clockwise seen from above
            var ring = new List<Vector2>();
            float hx = length / 2f - radius, hz = width / 2f - radius;
            var corners = new[] { new Vector2(hx, hz), new Vector2(-hx, hz), new Vector2(-hx, -hz), new Vector2(hx, -hz) };
            for (int c = 0; c < 4; c++)
                for (int i = 0; i <= seg; i++)
                {
                    float a = (c * 90f + i * 90f / seg) * Mathf.Deg2Rad;
                    ring.Add(corners[c] + new Vector2(Mathf.Cos(a), Mathf.Sin(a)) * radius);
                }
            int n = ring.Count;
            var verts = new List<Vector3>();
            var tris = new List<int>();
            // Top and bottom caps (fans from the centre)
            foreach (var (yy, up) in new[] { (thick, true), (0f, false) })
            {
                int centre = verts.Count;
                verts.Add(new Vector3(0f, yy, 0f));
                foreach (var p in ring) verts.Add(new Vector3(p.x, yy, p.y));
                for (int i = 0; i < n; i++)
                {
                    int a = centre + 1 + i, b = centre + 1 + (i + 1) % n;
                    if (up) { tris.Add(centre); tris.Add(b); tris.Add(a); }
                    else { tris.Add(centre); tris.Add(a); tris.Add(b); }
                }
            }
            // Side wall
            int side = verts.Count;
            foreach (var p in ring) { verts.Add(new Vector3(p.x, 0f, p.y)); verts.Add(new Vector3(p.x, thick, p.y)); }
            for (int i = 0; i < n; i++)
            {
                int a = side + 2 * i, b = side + 2 * ((i + 1) % n);
                tris.Add(a); tris.Add(a + 1); tris.Add(b);
                tris.Add(b); tris.Add(a + 1); tris.Add(b + 1);
            }
            var mesh = new Mesh { name = "Rounded slab" };
            mesh.SetVertices(verts);
            mesh.SetTriangles(tris, 0);
            mesh.RecalculateNormals();
            mesh.RecalculateBounds();
            return mesh;
        }
    }
}
