using Unity.XR.CoreUtils;
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.InputSystem.XR;

namespace TheraQuest
{
    /// <summary>
    /// Turns the scene's plain camera rig into a standard XR Origin at runtime (M10.1, DEC-030), so the scene file
    /// needs no change:  Rig (XROrigin, floor tracking) → Camera Offset → Main Camera (TrackedPoseDriver).
    /// The pose driver starts disabled: <see cref="HeadTracking"/> turns it on only while the headset is in use,
    /// so the laptop view keeps its own camera position. Safe to call more than once.
    /// </summary>
    public static class XrRig
    {
        public const string OffsetName = "Camera Offset";

        public static XROrigin Build(Transform rig, Camera cam)
        {
            if (rig == null || cam == null) return null;
            var origin = rig.GetComponent<XROrigin>();
            if (origin != null) return origin;

            var offset = new GameObject(OffsetName).transform;
            offset.SetParent(rig, false);
            cam.transform.SetParent(offset, false);   // keeps the camera's local pose

            var driver = cam.GetComponent<TrackedPoseDriver>();
            if (driver == null) driver = cam.gameObject.AddComponent<TrackedPoseDriver>();
            driver.trackingType = TrackedPoseDriver.TrackingType.RotationAndPosition;
            driver.updateType = TrackedPoseDriver.UpdateType.UpdateAndBeforeRender;
            driver.positionInput = new InputActionProperty(new InputAction("Head Position", InputActionType.Value, "<XRHMD>/centerEyePosition", expectedControlType: "Vector3"));
            driver.rotationInput = new InputActionProperty(new InputAction("Head Rotation", InputActionType.Value, "<XRHMD>/centerEyeRotation", expectedControlType: "Quaternion"));
            driver.trackingStateInput = new InputActionProperty(new InputAction("Head Tracking State", InputActionType.Value, "<XRHMD>/trackingState", expectedControlType: "Integer"));
            driver.enabled = false;

            // Configure while inactive so XROrigin.Awake sees its fields set
            bool wasActive = rig.gameObject.activeSelf;
            rig.gameObject.SetActive(false);
            origin = rig.gameObject.AddComponent<XROrigin>();
            origin.Origin = rig.gameObject;
            origin.CameraFloorOffsetObject = offset.gameObject;
            origin.Camera = cam;
            origin.RequestedTrackingOriginMode = XROrigin.TrackingOriginMode.Floor;
            rig.gameObject.SetActive(wasActive);
            return origin;
        }
    }
}
