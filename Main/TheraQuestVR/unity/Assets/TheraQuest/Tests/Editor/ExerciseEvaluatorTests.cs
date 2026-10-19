using System.Collections.Generic;
using NUnit.Framework;

namespace TheraQuest.Tests
{
    /// <summary>Rep counting, scoring and safety rules of the Exercise Evaluation Module (README section 8).</summary>
    public class ExerciseEvaluatorTests
    {
        const float Dt = 0.02f;

        static ExerciseDef Ex(float target = 90, float tol = 10, int reps = 3, int sets = 1, float safetyMax = 0,
                              float hold = 0, float rest = 0) =>
            new ExerciseDef { id = 1, code = "shoulderAbd", name = "Test", targetAngle = target, tolerance = tol,
                              reps = reps, sets = sets, safetyMax = safetyMax, holdSeconds = hold, restSeconds = rest };

        /// <summary>Raise from 0 to peak, optionally stay there, then lower to 0, at a steady pace.</summary>
        static List<RepResult> Rep(ExerciseEvaluator ev, float peak, float upSeconds = 1f, float holdSeconds = 0f,
                                   float downSeconds = 1f, string fault = null)
        {
            var results = new List<RepResult>();
            ev.RepCompleted += results.Add;
            for (float t = 0; t < upSeconds; t += Dt) ev.Update(peak * t / upSeconds, fault, Dt);
            for (float t = 0; t < holdSeconds; t += Dt) ev.Update(peak, fault, Dt);
            for (float t = 0; t <= downSeconds; t += Dt) ev.Update(peak * (1f - t / downSeconds), fault, Dt);
            ev.Update(0f, fault, Dt);
            ev.RepCompleted -= results.Add;
            return results;
        }

        [Test]
        public void RepOnTargetIsValidAndAccurate()
        {
            var ev = new ExerciseEvaluator(Ex());
            var r = Rep(ev, 90f);
            Assert.AreEqual(1, r.Count);
            Assert.IsTrue(r[0].valid);
            Assert.AreEqual(100, r[0].accuracy);
            Assert.AreEqual(1, ev.ValidReps);
            Assert.AreEqual(1, ev.Attempts);
        }

        [Test]
        public void RepShortOfToleranceIsNotCounted()
        {
            var ev = new ExerciseEvaluator(Ex());
            var r = Rep(ev, 75f);   // 15° short, tolerance 10° -> 85 - 5*3 = 70%
            Assert.IsFalse(r[0].valid);
            Assert.AreEqual(70, r[0].accuracy);
            Assert.AreEqual(0, ev.ValidReps);
            Assert.AreEqual(1, ev.Attempts);
        }

        [Test]
        public void PastSafetyMaxIsUnsafeAndNotCounted()
        {
            var ev = new ExerciseEvaluator(Ex(safetyMax: 100));
            var r = Rep(ev, 110f);
            Assert.IsTrue(r[0].pastSafetyMax);
            Assert.IsFalse(r[0].valid);
            Assert.AreEqual(1, ev.UnsafeReps);
        }

        [Test]
        public void PostureFaultInvalidatesRep()
        {
            var ev = new ExerciseEvaluator(Ex());
            var r = Rep(ev, 90f, fault: "Trunk lean");
            Assert.IsFalse(r[0].valid);
            Assert.AreEqual("Trunk lean", r[0].fault);
        }

        [Test]
        public void HoldMustLastLongEnough()
        {
            var ev = new ExerciseEvaluator(Ex(hold: 1f));
            Assert.IsFalse(Rep(ev, 90f, holdSeconds: 0.3f)[0].valid);
            Assert.IsTrue(Rep(ev, 90f, holdSeconds: 1.3f)[0].valid);
        }

        [Test]
        public void TooFastRepIsNotCounted()
        {
            var ev = new ExerciseEvaluator(Ex());
            var r = Rep(ev, 90f, upSeconds: 0.2f, downSeconds: 0.2f);
            Assert.IsTrue(r[0].tooFast);
            Assert.IsFalse(r[0].valid);
        }

        [Test]
        public void RestBetweenSetsIgnoresReps()
        {
            var ev = new ExerciseEvaluator(Ex(reps: 1, sets: 2, rest: 5f));
            Assert.IsTrue(Rep(ev, 90f)[0].valid);
            Assert.IsTrue(ev.Resting);
            Assert.AreEqual(0, Rep(ev, 90f).Count, "a rep during the rest countdown must not count");
            Assert.AreEqual(1, ev.ValidReps);
        }

        [Test]
        public void DoneAfterAllSets()
        {
            var ev = new ExerciseEvaluator(Ex(reps: 2, sets: 1));
            Rep(ev, 90f);
            Assert.IsFalse(ev.Done);
            Rep(ev, 90f);
            Assert.IsTrue(ev.Done);
            var result = ev.ToResult();
            Assert.AreEqual(2, result.target_reps);
            Assert.AreEqual(2, result.valid_reps);
        }

        [Test]
        public void ZeroToleranceNeverGivesNaNAccuracy()
        {
            var ev = new ExerciseEvaluator(Ex(tol: 0f));
            var r = Rep(ev, 90f);
            Assert.That(r[0].accuracy, Is.InRange(0, 100));
        }
    }

    public class ProgramRulesTests
    {
        [Test]
        public void DropsExercisesWithoutTarget()
        {
            var p = new ProgramResponse
            {
                exercises = new[]
                {
                    new ExerciseDef { name = "ok", targetAngle = 90, tolerance = 10, reps = 8, sets = 1 },
                    new ExerciseDef { name = "bad", targetAngle = 0, tolerance = 10, reps = 8, sets = 1 },
                }
            };
            ProgramRules.Clean(p);
            Assert.AreEqual(1, p.exercises.Length);
            Assert.AreEqual("ok", p.exercises[0].name);
            Assert.IsNotNull(p.phase);
            Assert.IsNotNull(p.patient);
        }

        [Test]
        public void ClampsNumbersAndSide()
        {
            var e = new ExerciseDef { targetAngle = 90, tolerance = 0, reps = 0, sets = -1, holdSeconds = -2, side = " l " };
            ProgramRules.Normalize(e);
            Assert.AreEqual(1f, e.tolerance);
            Assert.AreEqual(1, e.reps);
            Assert.AreEqual(1, e.sets);
            Assert.AreEqual(0f, e.holdSeconds);
            Assert.AreEqual("L", e.side);
            e.side = "x";
            ProgramRules.Normalize(e);
            Assert.AreEqual("", e.side);
        }
    }

    public class UploadQueueRulesTests
    {
        [TestCase(400, true)]
        [TestCase(403, true)]
        [TestCase(409, true)]
        [TestCase(401, false)]   // unknown patient code: fixable on the therapist page, keep it queued
        [TestCase(500, false)]
        [TestCase(0, false)]     // no reply: server down
        public void PermanentRefusals(long status, bool permanent)
        {
            Assert.AreEqual(permanent, ApiClient.IsPermanentRefusal(status));
        }

        [Test]
        public void PatientCodesAreNormalized()
        {
            Assert.AreEqual("P-002", ClientConfig.NormalizeCode("  p-002 "));
            Assert.AreEqual("", ClientConfig.NormalizeCode(null));
        }
    }
}
