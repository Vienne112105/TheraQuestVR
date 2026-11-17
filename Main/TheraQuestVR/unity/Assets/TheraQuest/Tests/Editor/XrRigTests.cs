using NUnit.Framework;
using Unity.XR.CoreUtils;
using UnityEngine;
using UnityEngine.InputSystem.XR;

namespace TheraQuest.Tests
{
    /// <summary>M10.1 / DEC-030: the plain Rig → Main Camera becomes a standard XR Origin at runtime.</summary>
    public class XrRigTests
    {
        GameObject rig;
        Camera cam;

        [SetUp]
        public void SetUp()
        {
            rig = new GameObject("Rig");
            cam = new GameObject("Main Camera").AddComponent<Camera>();
            cam.transform.SetParent(rig.transform, false);
            cam.transform.localPosition = new Vector3(0, 1.55f, 0);
        }

        [TearDown]
        public void TearDown() { Object.DestroyImmediate(rig); }

        [Test]
        public void Build_MakesRigCameraOffsetCamera()
        {
            var origin = XrRig.Build(rig.transform, cam);
            Assert.IsNotNull(origin);
            Assert.AreSame(rig, origin.gameObject);
            Assert.AreSame(rig, origin.Origin);
            Assert.AreSame(cam, origin.Camera);
            Assert.AreEqual(XrRig.OffsetName, origin.CameraFloorOffsetObject.name);
            Assert.AreSame(rig.transform, origin.CameraFloorOffsetObject.transform.parent);
            Assert.AreSame(origin.CameraFloorOffsetObject.transform, cam.transform.parent);
            Assert.AreEqual(XROrigin.TrackingOriginMode.Floor, origin.RequestedTrackingOriginMode);
            Assert.AreEqual(1.55f, cam.transform.localPosition.y, 1e-5f, "camera keeps its local pose");
            Assert.IsTrue(rig.activeSelf);
        }

        [Test]
        public void Build_AddsDisabledPoseDriverForTheHeadset()
        {
            XrRig.Build(rig.transform, cam);
            var d = cam.GetComponent<TrackedPoseDriver>();
            Assert.IsNotNull(d);
            Assert.IsFalse(d.enabled, "only HeadTracking turns it on, in the headset");
            Assert.AreEqual(TrackedPoseDriver.TrackingType.RotationAndPosition, d.trackingType);
            StringAssert.Contains("centerEyePosition", d.positionInput.action.bindings[0].path);
            StringAssert.Contains("centerEyeRotation", d.rotationInput.action.bindings[0].path);
        }

        [Test]
        public void Build_TwiceChangesNothing()
        {
            var first = XrRig.Build(rig.transform, cam);
            var second = XrRig.Build(rig.transform, cam);
            Assert.AreSame(first, second);
            Assert.AreEqual(1, rig.GetComponents<XROrigin>().Length);
            Assert.AreEqual(1, rig.transform.childCount, "one Camera Offset only");
            Assert.AreEqual(1, cam.GetComponents<TrackedPoseDriver>().Length);
        }

        [Test]
        public void HeadTracking_RigIsTheOrigin_AndBuildsItOnce()
        {
            var head = cam.gameObject.AddComponent<HeadTracking>();
            Assert.AreSame(rig.transform, head.Rig);
            Assert.AreSame(rig.transform, head.Rig, "second call finds the existing origin");
            Assert.AreEqual(1, rig.transform.childCount);
        }

        [Test]
        public void HeadTracking_OnTheLaptop_KeepsPostureHeightAndPitch()
        {
            var head = cam.gameObject.AddComponent<HeadTracking>();
            head.SetEyeHeight(FirstPersonMath.SeatedEye);
            head.desktopPitch = 20f;
            head.ApplyPose();   // no XR display in EditMode: laptop view
            Assert.IsFalse(head.HeadsetActive);
            Assert.AreEqual(new Vector3(0, FirstPersonMath.SeatedEye, 0), cam.transform.localPosition);
            Assert.AreEqual(20f, cam.transform.localEulerAngles.x, 1e-3f);
            Assert.AreEqual(Vector3.zero, cam.transform.parent.localPosition, "no headset offset on the laptop");
            Assert.IsFalse(cam.GetComponent<TrackedPoseDriver>().enabled);
        }
    }
}
