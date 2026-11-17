using System.IO;
using System.Text.RegularExpressions;
using NUnit.Framework;
using C = TheraQuest.XrModeLogic.Change;

namespace TheraQuest.Tests
{
    /// <summary>M10.1 / DEC-030: one answer to "is the headset in use?" and the Link lifecycle.</summary>
    public class XrModeTests
    {
        [Test]
        public void NoDisplay_StaysDesktop()
        {
            var m = new XrModeLogic();
            Assert.AreEqual(C.None, m.Step(false, false, 0f));
            Assert.AreEqual(XrState.Desktop, m.State);
        }

        [Test]
        public void DisplayRunning_GoesToHeadset()
        {
            var m = new XrModeLogic();
            Assert.AreEqual(C.HeadsetConnected, m.Step(true, true, 0f));
            Assert.AreEqual(XrState.Headset, m.State);
        }

        [Test]
        public void TakingHeadsetOff_FiresRemovedAfterDebounce()
        {
            var m = new XrModeLogic();
            m.Step(true, true, 0f);
            Assert.AreEqual(C.None, m.Step(true, false, 1f));
            Assert.AreEqual(C.None, m.Step(true, false, 1.3f));
            Assert.AreEqual(C.HeadsetRemoved, m.Step(true, false, 1.6f));
            Assert.AreEqual(XrState.HeadsetOff, m.State);
            Assert.AreEqual(C.None, m.Step(true, false, 3f), "fires once");
        }

        [Test]
        public void PresenceFlicker_DoesNothing()
        {
            var m = new XrModeLogic();
            m.Step(true, true, 0f);
            m.Step(true, false, 1f);
            Assert.AreEqual(C.None, m.Step(true, true, 1.2f));
            Assert.AreEqual(C.None, m.Step(true, false, 1.4f));
            Assert.AreEqual(C.None, m.Step(true, true, 1.6f));
            Assert.AreEqual(XrState.Headset, m.State);
        }

        [Test]
        public void PuttingHeadsetBack_FiresBack()
        {
            var m = new XrModeLogic();
            m.Step(true, true, 0f);
            m.Step(true, false, 1f);
            m.Step(true, false, 2f);
            m.Step(true, true, 3f);
            Assert.AreEqual(C.HeadsetBack, m.Step(true, true, 3.6f));
            Assert.AreEqual(XrState.Headset, m.State);
        }

        [Test]
        public void LinkLostMidSession_FallsBackToDesktop()
        {
            var m = new XrModeLogic();
            m.Step(true, true, 0f);
            Assert.AreEqual(C.FellBackToDesktop, m.Step(false, false, 5f));
            Assert.AreEqual(XrState.LinkLost, m.State);
            Assert.AreEqual(C.None, m.Step(false, false, 6f));
        }

        [Test]
        public void LinkLostWhileHeadsetOff_AlsoFallsBack()
        {
            var m = new XrModeLogic();
            m.Step(true, true, 0f);
            m.Step(true, false, 1f);
            m.Step(true, false, 2f);
            Assert.AreEqual(C.FellBackToDesktop, m.Step(false, false, 3f));
        }

        [Test]
        public void LinkBack_ReturnsToHeadset()
        {
            var m = new XrModeLogic();
            m.Step(true, true, 0f);
            m.Step(false, false, 1f);
            Assert.AreEqual(C.HeadsetConnected, m.Step(true, true, 2f));
            Assert.AreEqual(XrState.Headset, m.State);
        }

        [Test]
        public void HeadsetRemoved_PausesOnlyARunningExercise()
        {
            Assert.IsTrue(XrModeLogic.PausesSession(C.HeadsetRemoved, true, false));
            Assert.IsFalse(XrModeLogic.PausesSession(C.HeadsetRemoved, false, false), "not in the clinic or summary");
            Assert.IsFalse(XrModeLogic.PausesSession(C.HeadsetRemoved, true, true), "menu already open");
            Assert.IsFalse(XrModeLogic.PausesSession(C.FellBackToDesktop, true, false), "Link lost carries on");
            Assert.IsFalse(XrModeLogic.PausesSession(C.HeadsetBack, true, false), "putting it back on does not resume by itself");
        }

        /// <summary>Only XrMode may ask the XR runtime whether a headset is active.</summary>
        [Test]
        public void NoScript_ReadsXRSettingsIsDeviceActive()
        {
            var bad = new System.Collections.Generic.List<string>();
            foreach (var path in Directory.GetFiles("Assets/TheraQuest/Scripts", "*.cs", SearchOption.AllDirectories))
                if (Regex.IsMatch(File.ReadAllText(path), @"XRSettings\s*\.\s*isDeviceActive")) bad.Add(path);
            Assert.IsEmpty(bad, "Use XrMode.InHeadset instead: " + string.Join(", ", bad));
        }
    }
}
