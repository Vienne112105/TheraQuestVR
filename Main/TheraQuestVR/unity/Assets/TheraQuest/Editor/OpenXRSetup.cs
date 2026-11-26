using UnityEditor;
using UnityEditor.XR.Management;
using UnityEditor.XR.Management.Metadata;
using UnityEngine;
using UnityEngine.XR.Management;
using UnityEngine.XR.OpenXR;
using UnityEngine.XR.OpenXR.Features.Interactions;

namespace TheraQuest.EditorTools
{
    /// <summary>
    /// Menu: TheraQuest → Set Up OpenXR (M4.3, DEC-002).
    /// Turns on the OpenXR loader for Windows (Standalone) with "Initialize XR on Startup" and the
    /// Quest controller profiles (Touch, Touch Plus, Touch Pro), so Quest Link works in Play mode and in a built player.
    /// Without a headset, OpenXR fails to start and the app stays in desktop mode.
    /// Also runs from the command line: -executeMethod TheraQuest.EditorTools.OpenXRSetup.RunBatch
    /// </summary>
    public static class OpenXRSetup
    {
        const string Folder = "Assets/XR";
        const BuildTargetGroup Group = BuildTargetGroup.Standalone;

        [MenuItem("TheraQuest/Set Up OpenXR")]
        public static void Run()
        {
            Debug.Log(Configure() ? "[TheraQuest] OpenXR is set up for Windows." : "[TheraQuest] OpenXR setup failed; see the errors above.");
        }

        public static void RunBatch()
        {
            bool ok = Configure();
            EditorApplication.Exit(ok ? 0 : 1);
        }

        static bool Configure()
        {
            if (!AssetDatabase.IsValidFolder(Folder)) AssetDatabase.CreateFolder("Assets", "XR");

            if (!EditorBuildSettings.TryGetConfigObject(XRGeneralSettings.settingsKey, out XRGeneralSettingsPerBuildTarget perTarget) || perTarget == null)
            {
                perTarget = ScriptableObject.CreateInstance<XRGeneralSettingsPerBuildTarget>();
                AssetDatabase.CreateAsset(perTarget, Folder + "/XRGeneralSettingsPerBuildTarget.asset");
                EditorBuildSettings.AddConfigObject(XRGeneralSettings.settingsKey, perTarget, true);
            }

            if (!perTarget.HasSettingsForBuildTarget(Group)) perTarget.CreateDefaultSettingsForBuildTarget(Group);
            var general = perTarget.SettingsForBuildTarget(Group);
            if (!perTarget.HasManagerSettingsForBuildTarget(Group)) perTarget.CreateDefaultManagerSettingsForBuildTarget(Group);
            general.InitManagerOnStart = true;

            var manager = general.Manager;
            if (manager == null)
            {
                Debug.LogError("[TheraQuest] No XR manager settings for Standalone.");
                return false;
            }
            if (!XRPackageMetadataStore.IsLoaderAssigned(typeof(OpenXRLoader).FullName, Group) &&
                !XRPackageMetadataStore.AssignLoader(manager, typeof(OpenXRLoader).FullName, Group))
            {
                Debug.LogError("[TheraQuest] Could not assign the OpenXR loader.");
                return false;
            }

            UnityEditor.XR.OpenXR.Features.FeatureHelpers.RefreshFeatures(Group);
            var openxr = OpenXRSettings.GetSettingsForBuildTargetGroup(Group);
            // Quest 2 (Touch), Quest 3 and 3S (Touch Plus) and Quest Pro (Touch Pro) controllers (M10.1)
            if (!Enable<OculusTouchControllerProfile>(openxr) | !Enable<MetaQuestTouchPlusControllerProfile>(openxr) |
                !Enable<MetaQuestTouchProControllerProfile>(openxr))
                return false;

            EditorUtility.SetDirty(general);
            EditorUtility.SetDirty(manager);
            EditorUtility.SetDirty(openxr);
            EditorUtility.SetDirty(perTarget);
            AssetDatabase.SaveAssets();
            return true;
        }

        static bool Enable<T>(OpenXRSettings openxr) where T : UnityEngine.XR.OpenXR.Features.OpenXRFeature
        {
            var f = openxr != null ? openxr.GetFeature<T>() : null;
            if (f == null) { Debug.LogError("[TheraQuest] " + typeof(T).Name + " not found in OpenXR settings."); return false; }
            f.enabled = true;
            return true;
        }
    }
}
