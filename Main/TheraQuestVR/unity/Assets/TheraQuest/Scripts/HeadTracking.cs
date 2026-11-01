using System.Collections.Generic;
using UnityEngine;
using UnityEngine.XR;

namespace TheraQuest
{
    /// <summary>
    /// Minimal VR camera rig that needs no extra packages.
    /// With a headset on Quest Link, it follows your head. Without one, the camera
    /// stays at seated/standing eye height so the app runs on the laptop screen.
    /// Every patient sees from the same default height, whatever their own (M5.8, DEC-021): the headset's height is
    /// shifted to the posture's default when it is calibrated, which only happens in an instant re-center moment.
    /// Put this on the Main Camera, which should be a child of an empty "Rig" object.
    /// </summary>
    public class HeadTracking : MonoBehaviour
    {
        [Tooltip("The view's default height for the current posture (FirstPersonMath.EyeHeight).")]
        public float desktopEyeHeight = FirstPersonMath.StandingEye;
        /// <summary>Look up / down in desktop mode (set by PlayerMover from the mouse).</summary>
        [HideInInspector] public float desktopPitch;
        public bool HeadsetActive { get; private set; }

        Transform rig;
        static readonly List<XRInputSubsystem> subsystems = new List<XRInputSubsystem>();
        bool originSet, heightSet;
        float trackedY, heightOffset;

        void Awake() { rig = transform.parent; }

        /// <summary>
        /// Puts the view at this height from now on: on the laptop directly, in the headset by offsetting the
        /// patient's real head height as it is right now (so call it when they are in position).
        /// </summary>
        public void SetEyeHeight(float eye)
        {
            desktopEyeHeight = eye;
            heightOffset = FirstPersonMath.HeightOffset(eye, trackedY);
        }
        void OnEnable() { Application.onBeforeRender += Apply; }
        void OnDisable() { Application.onBeforeRender -= Apply; }
        void Update() { Apply(); }

        void Apply()
        {
            var head = InputDevices.GetDeviceAtXRNode(XRNode.CenterEye);
            if (!head.isValid) head = InputDevices.GetDeviceAtXRNode(XRNode.Head);
            HeadsetActive = head.isValid && XRSettings.isDeviceActive;

            if (!HeadsetActive)
            {
                transform.localPosition = new Vector3(0, desktopEyeHeight, 0);
                transform.localRotation = Quaternion.Euler(desktopPitch, 0, 0);
                return;
            }

            if (!originSet)
            {
                SubsystemManager.GetSubsystems(subsystems);
                foreach (var s in subsystems) s.TrySetTrackingOriginMode(TrackingOriginModeFlags.Floor);
                originSet = true;
            }

            if (head.TryGetFeatureValue(CommonUsages.centerEyePosition, out Vector3 pos) ||
                head.TryGetFeatureValue(CommonUsages.devicePosition, out pos))
            {
                trackedY = pos.y;
                if (!heightSet) { heightSet = true; SetEyeHeight(desktopEyeHeight); }
                transform.localPosition = pos + Vector3.up * heightOffset;
            }
            if (head.TryGetFeatureValue(CommonUsages.centerEyeRotation, out Quaternion rot) ||
                head.TryGetFeatureValue(CommonUsages.deviceRotation, out rot))
                transform.localRotation = rot;
        }

        /// <summary>
        /// Turn the rig so the patient faces the exercise area from where they are now.
        /// Lying down, it is their feet that point at it (they look at the ceiling).
        /// </summary>
        public void Recenter(bool lying = false)
        {
            if (rig == null || !HeadsetActive) return;
            float yaw = FirstPersonMath.FlatYaw(transform.localRotation * Vector3.forward, transform.localRotation * Vector3.up, lying);
            rig.rotation = Quaternion.Euler(0, -yaw, 0);
            Vector3 headWorld = transform.position;
            rig.position -= new Vector3(headWorld.x, 0, headWorld.z);
        }
    }
}
