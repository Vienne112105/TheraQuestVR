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
            // Warm bounce: light that has hit the wood floor and cream ceiling comes back warm, so shadows are
            // warm-dark rather than grey, and the sky-blue only comes from above.
            RenderSettings.ambientSkyColor = new Color(0.62f, 0.68f, 0.74f);
            RenderSettings.ambientEquatorColor = new Color(0.66f, 0.58f, 0.48f);
            RenderSettings.ambientGroundColor = new Color(0.58f, 0.40f, 0.26f);
            RenderSettings.ambientIntensity = 0.85f;

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

        const float SunPitch = 48f, SunYaw = 70f;

        /// <summary>Direction the sun's light travels (used to aim the light shafts).</summary>
        public static Vector3 SunDirection() => Quaternion.Euler(SunPitch, SunYaw, 0f) * Vector3.forward;

        /// <summary>Sets the tiling of every map the room materials use, so they stay in step.</summary>
        public static void SetTiling(Material m, Vector2 scale)
        {
            m.mainTextureScale = scale;
            foreach (var n in new[] { "_BumpMap", "_ParallaxMap" })
                if (m.HasProperty(n) && m.GetTexture(n) != null) m.SetTextureScale(n, scale);
        }

        /// <summary>Warm soft-shadow sun entering from the window wall (left, -x) and travelling toward +x and down.</summary>
        public static Light ConfigureSun(Light l)
        {
            l.type = LightType.Directional;
            l.color = new Color(1f, 0.96f, 0.88f);
            l.intensity = 1.6f;
            l.shadows = LightShadows.Soft;
            l.shadowStrength = 0.95f;   // high-contrast shadows anchor the props to the floor
            l.shadowBias = 0.03f;
            l.shadowNormalBias = 0.3f;
            l.transform.rotation = Quaternion.Euler(SunPitch, SunYaw, 0f);
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
        public static bool ApplyTexture(Material m, string resourcePath, Vector2? tiling = null, float bump = 1f, float parallax = 0.03f)
        {
            if (m == null) return false;
            var tex = Resources.Load<Texture2D>(resourcePath);
            if (tex == null) return false;
            var scale = tiling ?? Vector2.one;
            m.mainTexture = tex;
            m.mainTextureScale = scale;
            m.color = Color.white;

            // Optional relief: <path>_normal (light on bumps) and <path>_height (parallax: surfaces shift with the view)
            var normal = Resources.Load<Texture2D>(resourcePath + "_normal");
            if (normal != null && m.HasProperty("_BumpMap"))
            {
                m.SetTexture("_BumpMap", normal);
                m.SetTextureScale("_BumpMap", scale);
                m.SetFloat("_BumpScale", bump);
                m.EnableKeyword("_NORMALMAP");
            }
            var height = Resources.Load<Texture2D>(resourcePath + "_height");
            if (height != null && m.HasProperty("_ParallaxMap"))
            {
                m.SetTexture("_ParallaxMap", height);
                m.SetTextureScale("_ParallaxMap", scale);
                m.SetFloat("_Parallax", parallax);
                m.EnableKeyword("_PARALLAXMAP");
            }
            return true;
        }

        static Light FindDirectional(Transform root)
        {
            foreach (var l in Object.FindObjectsByType<Light>())
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
