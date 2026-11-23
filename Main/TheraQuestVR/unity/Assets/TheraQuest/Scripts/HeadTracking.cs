using Unity.XR.CoreUtils;
using UnityEngine;
using UnityEngine.InputSystem.XR;

namespace TheraQuest
{
    /// <summary>
    /// The view, on the laptop or in the headset (M10.1, DEC-030). The camera sits in a standard XR Origin built by
    /// <see cref="XrRig"/>: in the headset a TrackedPoseDriver moves it with the patient's head; on the laptop this
    /// component puts it at the posture's eye height with the mouse pitch.
    /// Every patient sees from the same default height, whatever their own (M5.8, DEC-021): in the headset the
    /// difference is put on the Camera Offset, and it is only recalibrated in an instant re-center moment.
    /// Put this on the Main Camera, which should be a child of an empty "Rig" object.
    /// </summary>
    public class HeadTracking : MonoBehaviour
    {
        [Tooltip("The view's default height for the current posture (FirstPersonMath.EyeHeight).")]
        public float desktopEyeHeight = FirstPersonMath.StandingEye;
        /// <summary>Look up / down in desktop mode (set by PlayerMover from the mouse).</summary>
        [HideInInspector] public float desktopPitch;
        public bool HeadsetActive { get; private set; }

        XROrigin origin;
        Transform offset;
        TrackedPoseDriver driver;
        bool heightSet, qualitySet;
        float trackedY, heightOffset;

        /// <summary>The object that is moved and turned to walk, turn and re-center (the XR Origin).</summary>
        public Transform Rig => EnsureRig() ? origin.transform : transform.parent;

        bool EnsureRig()
        {
            if (origin != null) return true;
            var cam = GetComponent<Camera>();
            var parent = transform.parent;
            if (cam == null || parent == null) return false;
            // Already built: the camera's parent is the Camera Offset under the origin
            origin = parent.GetComponentInParent<XROrigin>();
            if (origin == null) origin = XrRig.Build(parent, cam);
            if (origin == null) return false;
            offset = origin.CameraFloorOffsetObject.transform;
            driver = GetComponent<TrackedPoseDriver>();
            return true;
        }

        void Awake() { EnsureRig(); }

        /// <summary>
        /// Puts the view at this height from now on: on the laptop directly, in the headset by offsetting the
        /// patient's real head height as it is right now (so call it when they are in position).
        /// </summary>
        public void SetEyeHeight(float eye)
        {
            desktopEyeHeight = eye;
            heightOffset = FirstPersonMath.HeightOffset(eye, trackedY);
        }
        // Remove before adding: building the rig in Awake toggles it off and on, which can enable this twice
        void OnEnable() { Application.onBeforeRender -= ApplyPose; Application.onBeforeRender += ApplyPose; }
        void OnDisable() { Application.onBeforeRender -= ApplyPose; }
        void Update() { ApplyPose(); }

        /// <summary>Applies this frame's view (called every frame and before rendering; public for the tests).</summary>
        public void ApplyPose()
        {
            // A destroyed copy left hooked in (Play mode without domain reload) unhooks itself
            if (!this) { Application.onBeforeRender -= ApplyPose; return; }
            EnsureRig();
            bool wasHeadset = HeadsetActive;
            HeadsetActive = XrMode.InHeadset;
            if (HeadsetActive != wasHeadset || !qualitySet) { XrQuality.Apply(GetComponent<Camera>(), HeadsetActive); qualitySet = true; }
            if (driver != null && driver.enabled != HeadsetActive) driver.enabled = HeadsetActive;

            if (!HeadsetActive)
            {
                heightSet = false;   // recalibrate when the headset comes back
                if (offset != null) offset.localPosition = Vector3.zero;
                transform.localPosition = new Vector3(0, desktopEyeHeight, 0);
                transform.localRotation = Quaternion.Euler(desktopPitch, 0, 0);
                return;
            }

            // The pose driver has put the tracked head (floor origin) in the camera's local pose
            trackedY = transform.localPosition.y;
            if (!heightSet)
            {
                // On the first headset frames the camera still holds the laptop pose: calibrate from the headset itself
                var hmd = UnityEngine.XR.InputDevices.GetDeviceAtXRNode(UnityEngine.XR.XRNode.Head);
                // Before tracking starts the headset reports the floor (0): wait for a real head height
                if (!hmd.TryGetFeatureValue(UnityEngine.XR.CommonUsages.isTracked, out bool tracked) || !tracked) return;
                if (!hmd.TryGetFeatureValue(UnityEngine.XR.CommonUsages.centerEyePosition, out Vector3 eyePos) || eyePos.y < 0.1f) return;
                trackedY = eyePos.y;
                heightSet = true;
                SetEyeHeight(desktopEyeHeight);
            }
            // Written every frame: XROrigin resets the offset to 0 whenever the runtime changes the tracking origin
            if (offset != null) offset.localPosition = Vector3.up * heightOffset;
        }

        /// <summary>
        /// Turn the rig so the patient faces the exercise area from where they are now.
        /// Lying down, it is their feet that point at it (they look at the ceiling).
        /// </summary>
        public void Recenter(bool lying = false)
        {
            var rig = Rig;
            if (rig == null || !HeadsetActive) return;
            float yaw = FirstPersonMath.FlatYaw(transform.localRotation * Vector3.forward, transform.localRotation * Vector3.up, lying);
            rig.rotation = Quaternion.Euler(0, -yaw, 0);
            Vector3 headWorld = transform.position;
            rig.position -= new Vector3(headWorld.x, 0, headWorld.z);
            Recentered?.Invoke();
        }

        /// <summary>Raised after an instant re-center in the headset: the panels are put back in front of the patient.</summary>
        public static event System.Action Recentered;
    }
}
