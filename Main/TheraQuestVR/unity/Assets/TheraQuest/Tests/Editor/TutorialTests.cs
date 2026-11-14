using NUnit.Framework;

namespace TheraQuest.Tests
{
    /// <summary>The tutorial before the first exercise: every step moves on by itself after 3.5 s, and Start still moves on sooner.</summary>
    public class TutorialTests
    {
        [Test]
        public void StepDuration_IsThreePointFiveSeconds() => Assert.AreEqual(3.5f, Tutorial.StepSeconds);

        [Test]
        public void Step_AdvancesOnlyAfterItsTimeIsUp()
        {
            var t = new Tutorial(); t.Begin();
            Assert.IsFalse(t.Tick(1.0f));
            Assert.IsFalse(t.Tick(2.0f));      // 3.0 s so far
            Assert.IsTrue(t.Tick(0.6f));       // 3.6 s: time is up
        }

        [Test]
        public void Next_RestartsTheClockForTheNextStep()
        {
            var t = new Tutorial(); t.Begin();
            Assert.IsTrue(t.Tick(4f));
            t.Next();
            Assert.AreEqual(1, t.Step);
            Assert.AreEqual(Tutorial.StepSeconds, t.SecondsLeft, 0.001f);
            Assert.IsFalse(t.Tick(3.4f));
        }

        [Test]
        public void StartPress_CanMoveOnBeforeTheTimer()
        {
            var t = new Tutorial(); t.Begin();
            t.Tick(0.5f);
            t.Next();                           // what the Start button does
            Assert.AreEqual(1, t.Step);
        }

        [Test]
        public void PausedTime_DoesNotCount()
        {
            var t = new Tutorial(); t.Begin();
            for (int i = 0; i < 1000; i++) Assert.IsFalse(t.Tick(0f));
            Assert.AreEqual(0, t.Step);
        }

        [Test]
        public void WalksThroughEveryStepAutomatically_ThenEnds()
        {
            var t = new Tutorial(); t.Begin();
            int steps = 0;
            while (t.Active && steps < 20)
            {
                if (t.Tick(Tutorial.StepSeconds + 0.01f)) t.Next();
                steps++;
            }
            Assert.IsFalse(t.Active);
            Assert.AreEqual(Tutorial.Steps.Length, steps);
        }

        [Test]
        public void Skip_EndsTheTutorial()
        {
            var t = new Tutorial(); t.Begin();
            t.Skip();
            Assert.IsFalse(t.Active);
            Assert.IsFalse(t.Tick(10f));
        }
    }
}
