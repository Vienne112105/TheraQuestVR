using System.Reflection;
using NUnit.Framework;
using UnityEngine;

namespace TheraQuest.Tests
{
    /// <summary>
    /// M8.4: the coach window and side-mirror frames, placed exactly as the game places them, stay inside the comfortable
    /// field of view in the headset (<see cref="ViewComfort"/>) and inside the screen on the laptop.
    /// </summary>
    public class CoachFrameComfortTests
    {
        const BindingFlags Any = BindingFlags.Instance | BindingFlags.NonPublic | BindingFlags.Public;
        GameObject host, camGo;
        HUDController hud;
        Camera cam;

        [SetUp]
        public void SetUp()
        {
            host = new GameObject("Comfort test HUD");
            hud = host.AddComponent<HUDController>();
            typeof(HUDController).GetMethod("Awake", Any).Invoke(hud, null);   // builds the panels (not run in EditMode)
            camGo = new GameObject("Comfort test camera");
            cam = camGo.AddComponent<Camera>();
        }

        [TearDown]
        public void TearDown()
        {
            if (HUDController.View != null) Object.DestroyImmediate(HUDController.View.gameObject);
            Object.DestroyImmediate(host);
            Object.DestroyImmediate(camGo);
        }

        Canvas Panel(string field) => (Canvas)typeof(HUDController).GetField(field, Any).GetValue(hud);

        void Layout(bool headset, float questH)
        {
            typeof(HUDController).GetField("questH", Any).SetValue(hud, questH);
            typeof(HUDController).GetMethod("LayoutView", Any).Invoke(hud, new object[] { cam, headset });
        }

        static void Frame(Canvas c, out Vector3 centre, out float yaw, out Vector2 size)
        {
            var t = c.transform;
            centre = t.localPosition;
            yaw = t.localEulerAngles.y;
            size = ((RectTransform)t).sizeDelta * t.localScale.x;
        }

        [Test]
        public void Headset_FramesInsideComfortableView()
        {
            // The coach window shows under the minimised quest card; check a slightly taller card too
            foreach (float questH in new[] { HUDController.QuestMinimisedH, HUDController.QuestMinimisedH + 80f })
            {
                Layout(true, questH);
                foreach (var name in new[] { "coachCanvas", "mirrorCanvas" })
                {
                    Frame(Panel(name), out var centre, out float yaw, out var size);
                    Assert.Greater(size.x, 0.1f, name + " has a real size");
                    var where = "";
                    foreach (var corner in ViewComfort.Corners(centre, yaw, size)) where += ViewComfort.Angles(corner) + " ";
                    Assert.IsTrue(ViewComfort.Comfortable(centre, yaw, size),
                        $"{name} (quest card {questH}): centre {ViewComfort.Angles(centre)}, corners {where}");
                }
            }
        }

        [Test]
        public void Laptop_FramesInsideTheScreen()
        {
            foreach (var aspect in new[] { 16f / 9f, 1920f / 904f, 16f / 10f })
            {
                cam.fieldOfView = 60f;
                cam.aspect = aspect;
                Layout(false, HUDController.QuestMinimisedH);
                foreach (var name in new[] { "coachCanvas", "mirrorCanvas" })
                {
                    Frame(Panel(name), out var centre, out float yaw, out var size);
                    Assert.IsTrue(ViewComfort.InsideView(centre, yaw, size, cam.fieldOfView, cam.aspect), $"{name} at aspect {aspect}");
                }
            }
        }

        [Test]
        public void Limits_RejectAPanelFarToTheSide()
        {
            Assert.IsTrue(ViewComfort.Comfortable(new Vector3(0f, 0f, 1.6f), 0f, new Vector2(0.5f, 0.5f)));
            Assert.IsFalse(ViewComfort.Comfortable(new Vector3(1.6f, 0f, 1f), 0f, new Vector2(0.5f, 0.5f)), "58 degrees to the side");
            Assert.IsFalse(ViewComfort.Comfortable(new Vector3(0f, 0.8f, 1.6f), 0f, new Vector2(0.5f, 0.5f)), "too high");
            Assert.IsFalse(ViewComfort.Comfortable(new Vector3(0f, -1.5f, 1.6f), 0f, new Vector2(0.5f, 0.5f)), "too low");
        }
    }
}
