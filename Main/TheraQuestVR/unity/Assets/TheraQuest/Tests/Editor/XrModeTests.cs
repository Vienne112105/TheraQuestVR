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
        public void DisplayStopsWhileHeadsetOff_StaysOff()
        {
            var m = new XrModeLogic();
            m.Step(true, true, 0f);
            m.Step(true, false, 1f);
            m.Step(true, false, 2f);
            Assert.AreEqual(C.None, m.Step(false, false, 3f), "still paused, not a fallback");
            Assert.AreEqual(XrState.HeadsetOff, m.State);
        }

        /// <summary>Seen on a Quest 2 over Link: "not worn" is reported, then the display stops the next frame.</summary>
        [Test]
        public void DisplayStopsRightAfterNotWorn_IsHeadsetOff_NotLinkLost()
        {
            var m = new XrModeLogic();
            m.Step(true, true, 0f);
            Assert.AreEqual(C.None, m.Step(true, false, 47.30f));
            Assert.AreEqual(C.HeadsetRemoved, m.Step(false, false, 47.31f));
            Assert.AreEqual(XrState.HeadsetOff, m.State);
            Assert.IsTrue(XrModeLogic.PausesSession(C.HeadsetRemoved, true, false));
        }

        [Test]
        public void PuttingItBackOn_AfterTheDisplayStopped_FiresBack()
        {
            var m = new XrModeLogic();
            m.Step(true, true, 0f);
            m.Step(true, false, 1f);
            m.Step(false, false, 1.1f);
            m.Step(false, false, 20f);
            Assert.AreEqual(C.None, m.Step(true, true, 21f));
            Assert.AreEqual(C.HeadsetBack, m.Step(true, true, 21.6f));
            Assert.AreEqual(XrState.Headset, m.State);
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

        /// <summary>Seen on a Quest 2: unplugging Link made OpenXR quit the game. XrMode refuses, so the session carries on.</summary>
        [Test]
        public void LosingTheRuntime_DoesNotQuitTheGame()
        {
            var flags = System.Reflection.BindingFlags.Static | System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Public;
            typeof(XrMode).GetMethod("ResetForPlay", flags).Invoke(null, null);
            var shouldQuit = typeof(UnityEngine.XR.OpenXR.OpenXRRuntime).GetMethod("ShouldQuit", flags);
            Assert.IsNotNull(shouldQuit, "OpenXR package changed: check how it quits on runtime loss");
            Assert.IsFalse((bool)shouldQuit.Invoke(null, null));
        }

        /// <summary>Seen on a Quest 2: the left stick drifted and walked the patient on the summary.</summary>
        [Test]
        public void StickDrift_IsIgnored_AndAFullPushStillCounts()
        {
            Assert.AreEqual(UnityEngine.Vector2.zero, InputHelper.DeadZone(new UnityEngine.Vector2(0.2f, 0.15f)), "drift (0.25) is ignored");
            var full = InputHelper.DeadZone(new UnityEngine.Vector2(0f, 1f));
            Assert.AreEqual(1f, full.y, 1e-5f, "full push is full speed");
            var half = InputHelper.DeadZone(new UnityEngine.Vector2(0.65f, 0f));
            Assert.AreEqual(0.5f, half.x, 1e-5f, "starts gently from the edge of the dead zone");
            Assert.Greater(InputHelper.DeadZone(new UnityEngine.Vector2(0.31f, 0f)).x, 0f);
        }

        /// <summary>Seen on a Quest 2 with an RTX 3050 laptop: the full look missed frames and edges wobbled. The headset uses a lighter renderer.</summary>
        [Test]
        public void HeadsetRenderer_IsTheLaptopOne_WithoutSSAO()
        {
            var urp = UnityEditor.AssetDatabase.LoadAssetAtPath<UnityEngine.Rendering.Universal.UniversalRenderPipelineAsset>("Assets/TheraQuest/Settings/URP/TheraQuest_URP.asset");
            var list = new UnityEditor.SerializedObject(urp).FindProperty("m_RendererDataList");
            Assert.Greater(list.arraySize, XrQuality.HeadsetRenderer);
            var laptop = (UnityEngine.Rendering.Universal.ScriptableRendererData)list.GetArrayElementAtIndex(0).objectReferenceValue;
            var headset = (UnityEngine.Rendering.Universal.ScriptableRendererData)list.GetArrayElementAtIndex(XrQuality.HeadsetRenderer).objectReferenceValue;
            Assert.AreEqual("TheraQuest_Renderer_Headset", headset.name);
            Assert.IsTrue(laptop.rendererFeatures.Exists(f => f.name == "SSAO" && f.isActive), "the laptop keeps SSAO");
            Assert.IsFalse(headset.rendererFeatures.Exists(f => f.name == "SSAO" && f.isActive), "no SSAO in the headset");
            Assert.That(XrQuality.HeadsetResolutionScale, Is.InRange(0.7f, 1f));
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
