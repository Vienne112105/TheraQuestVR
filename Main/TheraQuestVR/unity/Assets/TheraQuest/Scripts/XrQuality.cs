using UnityEngine;
using UnityEngine.Rendering.Universal;
using UnityEngine.XR;

namespace TheraQuest
{
    /// <summary>
    /// A lighter look in the headset (M10.1). Seen on a Quest 2 over Link with an RTX 3050 laptop GPU: the full
    /// laptop look (SSAO, 3648 x 1872 eye buffers) missed frames, and the headset filled them in by guessing,
    /// which made object edges wobble. In the headset the camera uses the second URP renderer (the same, without
    /// SSAO) and slightly smaller eye buffers; on the laptop nothing changes. Runtime settings only: no asset is edited.
    /// </summary>
    public static class XrQuality
    {
        /// <summary>Index of TheraQuest_Renderer_Headset in the URP asset's renderer list (0 is the laptop renderer).</summary>
        public const int HeadsetRenderer = 1;
        /// <summary>Eye buffer size in the headset, relative to what Link asks for (Quest 2: 3648 x 1872 for both eyes).</summary>
        public const float HeadsetResolutionScale = 0.8f;

        /// <summary>Puts the camera on the headset or laptop look. Call when the headset starts or stops being used.</summary>
        public static void Apply(Camera cam, bool headset)
        {
            if (cam != null)
            {
                var data = cam.GetUniversalAdditionalCameraData();
                if (data != null) data.SetRenderer(headset ? HeadsetRenderer : -1);   // -1 = the asset's default
            }
            if (headset) XRSettings.eyeTextureResolutionScale = HeadsetResolutionScale;
        }
    }
}
