using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

namespace TheraQuest
{
    /// <summary>
    /// M8.2 clinic look, built at runtime because the room is built at runtime (nothing is baked): a soft sun through
    /// the windows, gradient ambient, one reflection probe rendered once, and one URP Volume with neutral tonemapping,
    /// gentle colour grading and light bloom. SSAO is a renderer feature on the URP renderer asset.
    /// Comfort rules (xr-interface-architect): no motion blur, vignette, chromatic aberration, film grain or depth of field.
    /// Textures are optional files under Resources/Room/Textures; a missing file keeps the material's current colour.
    /// </summary>
    public static class RoomLook
    {
        public const string ProbeName = "Room reflection probe";
        public const string VolumeName = "Room look volume";

        /// <summary>Builds the lighting, probe and volume under <paramref name="root"/>. Safe to call twice.</summary>
        public static void Setup(Transform root)
        {
            if (root.Find(VolumeName) != null) return;

            // Sun: reuse the scene's directional light while playing; otherwise (edit-mode tests) make our own.
            Light sun = Application.isPlaying ? FindDirectional(root) : null;
            if (sun == null) sun = new GameObject("Room sun").AddComponent<Light>();
            if (sun.transform.parent == null && sun.gameObject.name == "Room sun") sun.transform.SetParent(root, false);
            ConfigureSun(sun);

            // Ambient: sky, horizon, ground gradient
            RenderSettings.ambientMode = AmbientMode.Trilight;
            RenderSettings.ambientSkyColor = new Color(0.70f, 0.80f, 0.90f);
            RenderSettings.ambientEquatorColor = new Color(0.78f, 0.78f, 0.74f);
            RenderSettings.ambientGroundColor = new Color(0.45f, 0.42f, 0.38f);

            // Reflection probe: rendered once, after the room exists (one frame later, so every prop is in place)
            var probeGo = new GameObject(ProbeName);
            probeGo.transform.SetParent(root, false);
            probeGo.transform.position = new Vector3(0, 1.6f, 1.25f);
            var probe = probeGo.AddComponent<ReflectionProbe>();
            probe.mode = ReflectionProbeMode.Realtime;
            probe.refreshMode = ReflectionProbeRefreshMode.ViaScripting;
            probe.timeSlicingMode = ReflectionProbeTimeSlicingMode.NoTimeSlicing;
            probe.size = new Vector3(10, 3.5f, 9);
            probe.resolution = 128;
            if (Application.isPlaying) probeGo.AddComponent<RenderProbeOnce>().probe = probe;

            // Volume: global, one profile
            var volGo = new GameObject(VolumeName);
            volGo.transform.SetParent(root, false);
            var vol = volGo.AddComponent<Volume>();
            vol.isGlobal = true;
            vol.sharedProfile = MakeProfile();

            // Post-processing is off by default on cameras; turn it on for the main camera.
            var cam = Camera.main;
            if (cam != null)
            {
                var data = cam.GetUniversalAdditionalCameraData();
                if (data != null) data.renderPostProcessing = true;
            }
        }

        /// <summary>Warm soft-shadow sun entering from the window wall (left, -x) and travelling toward +x and down.</summary>
        public static Light ConfigureSun(Light l)
        {
            l.type = LightType.Directional;
            l.color = new Color(1f, 0.96f, 0.88f);
            l.intensity = 1.1f;
            l.shadows = LightShadows.Soft;
            l.shadowStrength = 0.75f;
            l.transform.rotation = Quaternion.Euler(48f, 70f, 0f);
            return l;
        }

        /// <summary>Neutral tonemapping, gentle colour grading and light bloom. Nothing from the comfort ban list.</summary>
        public static VolumeProfile MakeProfile()
        {
            var p = ScriptableObject.CreateInstance<VolumeProfile>();
            p.name = "Room look";
            p.Add<Tonemapping>(true).mode.Override(TonemappingMode.Neutral);

            var grade = p.Add<ColorAdjustments>(true);
            grade.postExposure.Override(0.1f);
            grade.contrast.Override(8f);
            grade.saturation.Override(6f);

            var bloom = p.Add<Bloom>(true);
            bloom.threshold.Override(1.0f);
            bloom.intensity.Override(0.2f);
            bloom.scatter.Override(0.6f);
            return p;
        }

        /// <summary>
        /// Puts the texture at Resources/<paramref name="resourcePath"/> on the material (base map) and resets its tint
        /// to white so the picture shows true. Returns false and leaves the material untouched when the file is missing.
        /// </summary>
        public static bool ApplyTexture(Material m, string resourcePath, float tiling = 1f)
        {
            if (m == null) return false;
            var tex = Resources.Load<Texture2D>(resourcePath);
            if (tex == null) return false;
            m.mainTexture = tex;
            m.mainTextureScale = new Vector2(tiling, tiling);
            m.color = Color.white;
            return true;
        }

        static Light FindDirectional(Transform root)
        {
            foreach (var l in Object.FindObjectsByType<Light>(FindObjectsSortMode.None))
                if (l.type == LightType.Directional && !l.transform.IsChildOf(root)) return l;
            return null;
        }
    }

    /// <summary>Renders the reflection probe one frame after the room is built, then removes itself.</summary>
    public class RenderProbeOnce : MonoBehaviour
    {
        public ReflectionProbe probe;
        System.Collections.IEnumerator Start()
        {
            yield return null;
            if (probe != null) probe.RenderProbe();
            Destroy(this);
        }
    }
}
