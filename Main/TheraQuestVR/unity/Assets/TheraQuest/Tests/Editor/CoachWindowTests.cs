using NUnit.Framework;
using UnityEngine;

namespace TheraQuest.Tests
{
    /// <summary>M8.2: the coach window's word label stays clear of the arrow and the coach, and inside the picture.</summary>
    public class CoachWindowTests
    {
        static readonly Vector2 Chip = new Vector2(250f / 592f, 52f / 592f);   // as built in HUDController

        static Rect ChipRect(Vector2 centre) => new Rect(centre.x - Chip.x / 2f, centre.y - Chip.y / 2f, Chip.x, Chip.y);

        // An arrow curving up the right of the body, like shoulder abduction
        static Vector2[] RightArc()
        {
            var p = new Vector2[12];
            for (int i = 0; i < p.Length; i++)
            {
                float t = i / (p.Length - 1f);
                p[i] = new Vector2(0.55f + 0.3f * Mathf.Sin(t * 1.5f), 0.35f + 0.35f * t);
            }
            return p;
        }

        [Test]
        public void Chip_StaysInsidePicture()
        {
            var c = HUDController.PlaceWordChip(Chip, new Vector2(0.7f, 0.5f), RightArc(), new Rect(0.25f, 0.05f, 0.25f, 0.9f));
            var r = ChipRect(c);
            Assert.GreaterOrEqual(r.xMin, 0f); Assert.LessOrEqual(r.xMax, 1f);
            Assert.GreaterOrEqual(r.yMin, 0f); Assert.LessOrEqual(r.yMax, 1f);
        }

        [Test]
        public void Chip_DoesNotCoverTheArrowOrTheBody()
        {
            var path = RightArc();
            var body = new Rect(0.25f, 0.05f, 0.25f, 0.9f);
            var r = ChipRect(HUDController.PlaceWordChip(Chip, new Vector2(0.7f, 0.5f), path, body));
            foreach (var p in path) Assert.IsFalse(r.Contains(p), "chip covers the arrow at " + p);
            Assert.IsFalse(r.Overlaps(body), "chip overlaps the coach's body");
        }

        [Test]
        public void Chip_WorksWithoutAPath()
        {
            var c = HUDController.PlaceWordChip(Chip, new Vector2(0.5f, 0.5f), null, new Rect(0.3f, 0.1f, 0.4f, 0.8f));
            Assert.That(c.x, Is.InRange(0f, 1f)); Assert.That(c.y, Is.InRange(0f, 1f));
        }

        [Test]
        public void Chip_IsDeterministic()
        {
            var a = HUDController.PlaceWordChip(Chip, new Vector2(0.7f, 0.5f), RightArc(), new Rect(0.25f, 0.05f, 0.25f, 0.9f));
            var b = HUDController.PlaceWordChip(Chip, new Vector2(0.7f, 0.5f), RightArc(), new Rect(0.25f, 0.05f, 0.25f, 0.9f));
            Assert.AreEqual(a, b);
        }
    }
}
