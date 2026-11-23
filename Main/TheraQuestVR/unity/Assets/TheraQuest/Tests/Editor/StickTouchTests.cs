using NUnit.Framework;
using UnityEngine;

namespace TheraQuest.Tests
{
    /// <summary>A faulty thumbstick that reads far past the dead zone must not walk the patient when no thumb is on it.</summary>
    public class StickTouchTests
    {
        [Test]
        public void UntouchedStick_IsIgnored_EvenFarPastTheDeadZone()
        {
            Assert.AreEqual(Vector2.zero, InputHelper.StickValue(new Vector2(0.87f, 0.02f), true, false));
        }

        [Test]
        public void TouchedStick_UsesTheDeadZone()
        {
            Assert.Greater(InputHelper.StickValue(new Vector2(0.87f, 0f), true, true).x, 0.5f);
            Assert.AreEqual(Vector2.zero, InputHelper.StickValue(new Vector2(0.2f, 0f), true, true));
        }

        [Test]
        public void HeadsetWalkHint_PointsToTheKeyboard()
        {
            StringAssert.Contains("W A S D", ControlHints.Controller.Walk, "walking is keyboard only, also in the headset");
        }

        [Test]
        public void StickWithoutTouchSensor_KeepsTheDeadZoneOnly()
        {
            Assert.Greater(InputHelper.StickValue(new Vector2(0.87f, 0f), false, false).x, 0.5f);
        }
    }
}
