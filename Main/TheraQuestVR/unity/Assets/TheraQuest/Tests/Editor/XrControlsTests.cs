using System.IO;
using System.Linq;
using System.Text.RegularExpressions;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.XR.Interaction.Toolkit.Inputs.Readers;

namespace TheraQuest.Tests
{
    /// <summary>M10.2 / DEC-030: the controllers are read through one input actions file, and menus take controller rays.</summary>
    public class XrControlsTests
    {
        static string Paths(string action) =>
            string.Join(" ", XrControls.Asset.FindAction(action, true).bindings.Select(b => b.path));

        [Test]
        public void ButtonMapping_IsKept()
        {
            Assert.IsNotNull(XrControls.Asset, "Resources/" + XrControls.AssetResource + " is missing");
            Assert.AreEqual("<XRController>{RightHand}/{PrimaryButton}", Paths("Controllers/Select"), "A selects");
            Assert.AreEqual("<XRController>{RightHand}/{TriggerButton}", Paths("Controllers/RightTrigger"), "right trigger selects or clicks");
            StringAssert.Contains("{RightHand}/{SecondaryButton}", Paths("Controllers/Back"), "B goes back");
            StringAssert.Contains("{LeftHand}/{MenuButton}", Paths("Controllers/Back"), "left Menu goes back");
            Assert.AreEqual("<XRController>{LeftHand}/{SecondaryButton}", Paths("Controllers/Recenter"), "Y re-centers");
            Assert.AreEqual("<XRController>{LeftHand}/{Primary2DAxisClick}", Paths("Controllers/QuestToggle"), "left stick click shows the quest");
            Assert.AreEqual("<XRController>{LeftHand}/{Primary2DAxisTouch}", Paths("Controllers/LeftStickTouch"), "a stick needs a thumb on it");
            Assert.AreEqual("<XRController>{RightHand}/{Primary2DAxisTouch}", Paths("Controllers/RightStickTouch"));
            Assert.AreEqual("<XRHMD>/userPresence", Paths("Headset/Worn"));
        }

        [Test]
        public void NoController_ReadsAsNothingPressed_AndTheHeadsetCountsAsWorn()
        {
            // No XR devices in the Editor test run
            Assert.IsFalse(XrControls.SelectDown || XrControls.BackDown || XrControls.RecenterDown || XrControls.RightTriggerDown);
            Assert.AreEqual(Vector2.zero, XrControls.LeftStick);
            Assert.AreEqual(Vector2.zero, XrControls.RightStick);
            Assert.IsTrue(XrControls.HeadsetWorn, "no presence sensor counts as worn");
            Assert.IsFalse(XrControls.TryGetTrackedEyePosition(out _));
        }

        /// <summary>Only XrControls reads the XR devices, through input actions: no script asks UnityEngine.XR.InputDevices.</summary>
        [Test]
        public void NoScript_ReadsXRDevicesDirectly()
        {
            var bad = Directory.GetFiles("Assets/TheraQuest/Scripts", "*.cs", SearchOption.AllDirectories)
                .Where(p => Regex.IsMatch(File.ReadAllText(p), @"InputDevices\s*\.\s*GetDevice|XRNode\s*\.|CommonUsages\s*\.|TryGetFeatureValue"))
                .ToList();
            Assert.IsEmpty(bad, "Read controllers through XrControls: " + string.Join(", ", bad));
        }

        [Test]
        public void ControllerRays_BuildTwoUiOnlyRays_OnTheTriggers_Once()
        {
            var offset = new GameObject("Camera Offset");
            var host = new GameObject("Rig");
            try
            {
                var rays = host.AddComponent<ControllerRays>();
                rays.Build(offset.transform);
                rays.Build(offset.transform);
                Assert.AreEqual(2, offset.transform.childCount, "built once");
                foreach (var (ray, trigger) in new[] { (rays.Left, "LeftTrigger"), (rays.Right, "RightTrigger") })
                {
                    Assert.AreEqual(offset.transform, ray.transform.parent);
                    Assert.AreEqual(0, ray.raycastMask.value, "UI only");
                    Assert.IsTrue(ray.enableUIInteraction);
                    Assert.AreEqual(XRInputButtonReader.InputSourceMode.InputActionReference, ray.uiPressInput.inputSourceMode, "a reference: hiding the ray must not turn the shared action off");
                    Assert.AreEqual(trigger, ray.uiPressInput.inputActionReferencePerformed.action.name, "the trigger clicks");
                    Assert.IsNull(ray.GetComponentInChildren<Collider>(), "the handle has no collider");
                    Assert.IsFalse(ray.gameObject.activeSelf, "hidden until a menu opens in the headset");
                }
            }
            finally
            {
                Object.DestroyImmediate(host);
                Object.DestroyImmediate(offset);
            }
        }
    }
}
