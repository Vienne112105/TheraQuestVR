using System.Collections.Generic;
using NUnit.Framework;
using UnityEngine;

namespace TheraQuest.Tests
{
    /// <summary>Rep counting, scoring and safety rules of the Exercise Evaluation Module (README section 8).</summary>
    public class ExerciseEvaluatorTests
    {
        const float Dt = 0.02f;

        internal static ExerciseDef Ex(float target = 90, float tol = 10, int reps = 3, int sets = 1, float safetyMax = 0,
                              float hold = 0, float rest = 0) =>
            new ExerciseDef { id = 1, code = "shoulderAbd", name = "Test", targetAngle = target, tolerance = tol,
                              reps = reps, sets = sets, safetyMax = safetyMax, holdSeconds = hold, restSeconds = rest };

        /// <summary>Raise from 0 to peak, optionally stay there, then lower to 0, at a steady pace.</summary>
        internal static List<RepResult> Rep(ExerciseEvaluator ev, float peak, float upSeconds = 1f, float holdSeconds = 0f,
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

    /// <summary>Per-rep log (M4.5) and exercise rules sent by the server (M4.6, DEC-012).</summary>
    public class RepLogAndRulesTests
    {
        // ---------------------------------------------------------- per-rep log (M4.5)
        [Test]
        public void RepEventsRecordEveryAttemptWithItsSet()
        {
            var ev = new ExerciseEvaluator(ExerciseEvaluatorTests.Ex(reps: 2, sets: 2));
            ExerciseEvaluatorTests.Rep(ev, 90f);
            ExerciseEvaluatorTests.Rep(ev, 70f);                       // short: an attempt, not a rep
            ExerciseEvaluatorTests.Rep(ev, 90f);                       // completes set 1
            ExerciseEvaluatorTests.Rep(ev, 90f, fault: "Keep your trunk upright");
            var log = ev.RepEvents;
            Assert.AreEqual(4, log.Count);
            CollectionAssert.AreEqual(new[] { 1, 2, 3, 4 }, log.ConvertAll(e => e.attempt));
            CollectionAssert.AreEqual(new[] { 1, 1, 1, 2 }, log.ConvertAll(e => e.set));
            CollectionAssert.AreEqual(new[] { true, false, true, false }, log.ConvertAll(e => e.valid));
            Assert.AreEqual("Keep your trunk upright", log[3].fault);
            Assert.AreEqual(1, log[0].exercise_id);
            Assert.AreEqual(90f, log[0].peak, 0.5f);
            Assert.Less(log[0].t, log[2].t);
        }

        // ---------------------------------------------------------- exercise rules from the server (M4.6)
        static ExerciseDef Rule(string measure = "shoulderElev", string view = "side", string direction = "",
                                string pose = "shoulderFlex", params PostureCheck[] checks) =>
            new ExerciseDef { id = 7, code = "anyNewCode", measure = measure, view = view, direction = direction,
                              pose = pose, posture = "standing", targetAngle = 90, tolerance = 10, reps = 1, sets = 1,
                              checks = checks };

        static PostureCheck Check(string metric, float max, string message) =>
            new PostureCheck { metric = metric, max = max, message = message };

        [Test]
        public void PostureChecksComeFromTheExercise()
        {
            var ex = Rule(checks: Check("trunkLean", 12, "Keep your trunk upright"));
            var p = new MotionPacket { trunkLean = 20 };
            Assert.AreEqual("Keep your trunk upright", MotionInput.PostureFault(ex, p, p));
            p.trunkLean = 5;
            Assert.IsNull(MotionInput.PostureFault(ex, p, p));
            p.trunkLean = -1;                                   // not visible: never a fault
            Assert.IsNull(MotionInput.PostureFault(ex, p, p));
            Assert.IsNull(MotionInput.PostureFault(Rule(), new MotionPacket { trunkLean = 40 }, new MotionPacket()));
            Assert.AreEqual("Keep your trunk upright", MotionInput.FaultText(ex));
        }

        [Test]
        public void SideAngleChecksUseTheMeasuredSide()
        {
            var ex = Rule(checks: Check("kneeFlex", 15, "Keep your knee straight"));
            var p = new MotionPacket { kneeFlex = 0 };
            p.R.kneeFlex = 30;
            Assert.IsNull(MotionInput.PostureFault(ex, p, p));
            Assert.AreEqual("Keep your knee straight", MotionInput.PostureFault(ex, p, p.R));
        }

        [Test]
        public void ExtensionScoresOnlyMovementBehindTheTrunk()
        {
            var ex = Rule(direction: "ext", pose: "shoulderExt");
            var s = new AngleSet { shoulderElev = 40, shoulderElevSigned = 40 };     // arm forward
            Assert.AreEqual(0f, MotionInput.MeasuredAngle(ex, s));
            s.shoulderElevSigned = -40;                                               // arm back
            Assert.AreEqual(40f, MotionInput.MeasuredAngle(ex, s));
            s.shoulderElevSigned = AngleSet.SignedInvalid;                            // direction unknown
            Assert.AreEqual(-1f, MotionInput.MeasuredAngle(ex, s));
        }

        [Test]
        public void FlexionIgnoresMovementBehindTheTrunk()
        {
            var ex = Rule(measure: "hipElev", direction: "flex", pose: "march");
            var s = new AngleSet { hipElev = 30, hipElevSigned = -30 };
            Assert.AreEqual(0f, MotionInput.MeasuredAngle(ex, s));
            s.hipElevSigned = 30;
            Assert.AreEqual(30f, MotionInput.MeasuredAngle(ex, s));
            s.hipElevSigned = AngleSet.SignedInvalid;                                 // older tracker: unsigned
            Assert.AreEqual(30f, MotionInput.MeasuredAngle(ex, s));
            Assert.AreEqual(30f, MotionInput.MeasuredAngle(Rule(measure: "hipElev", view: "front", direction: "flex"), s));
        }

        [Test]
        public void ServerJsonFillsRulesAndSignedAngles()
        {
            var ex = JsonUtility.FromJson<ExerciseDef>(
                "{\"id\":3,\"code\":\"x\",\"measure\":\"shoulderElev\",\"view\":\"side\",\"pose\":\"shoulderExt\"," +
                "\"posture\":\"standing\",\"direction\":\"ext\",\"checks\":[{\"metric\":\"trunkLean\",\"max\":12,\"message\":\"m\"}]}");
            Assert.AreEqual("shoulderExt", ex.pose);
            Assert.AreEqual(1, ex.checks.Length);
            Assert.AreEqual(12f, ex.checks[0].max);
            var p = JsonUtility.FromJson<MotionPacket>("{\"shoulderElev\":30,\"shoulderElevSigned\":-30,\"R\":{\"hipElevSigned\":12.5}}");
            Assert.AreEqual(-30f, p.shoulderElevSigned);
            Assert.AreEqual(AngleSet.SignedInvalid, p.hipElevSigned);
            Assert.AreEqual(12.5f, p.R.hipElevSigned);
        }

        [Test]
        public void NewExerciseWithAnExistingPoseNeedsNoClientCode()
        {
            // An exercise code Unity has never seen, defined only by its server LIBRARY entry
            var ex = Rule(measure: "shoulderElev", view: "front", direction: "abd", pose: "shoulderAbd",
                          checks: Check("trunkLean", 12, "Keep your trunk upright"));
            ex.code = "brandNewRaise";
            Assert.AreEqual("shoulderAbd", FigureVisualizer.PoseOf(ex));
            var s = new MotionPacket { shoulderElev = 90, trunkLean = 3 };
            Assert.AreEqual(90f, MotionInput.MeasuredAngle(ex, s));
            Assert.IsNull(MotionInput.PostureFault(ex, s, s));
            var ev = new ExerciseEvaluator(ex);
            Assert.IsTrue(ExerciseEvaluatorTests.Rep(ev, 90f)[0].valid);
            Assert.IsTrue(ev.Done);
        }

        [Test]
        public void MissingPoseFallsBackToTheMeasuredAngle()
        {
            Assert.AreEqual("hipAbd", FigureVisualizer.PoseOf(new ExerciseDef { measure = "hipElev", view = "front" }));
            Assert.AreEqual("slr", FigureVisualizer.PoseOf(new ExerciseDef { measure = "hipElev", view = "side" }));
            Assert.AreEqual("shoulderFlex", FigureVisualizer.PoseOf(new ExerciseDef { measure = "shoulderElev", view = "side" }));
        }
    }

    /// <summary>M5.4 session flow: countdown, restart and control hints.</summary>
    public class SessionFlowTests
    {
        [Test]
        public void CountdownShowsThreeTwoOneGoThenFinishes()
        {
            var c = new Countdown(3, 0.6f);
            Assert.IsFalse(c.Active);
            c.Begin();
            var shown = new List<int>();
            for (int i = 0; i < 400 && !c.Finished; i++)
                if (c.Tick(0.02f)) shown.Add(c.Number);
            CollectionAssert.AreEqual(new[] { 3, 2, 1, 0 }, shown);
            Assert.IsTrue(c.Finished);
            Assert.IsFalse(c.Active);
        }

        [Test]
        public void CountdownFreezesWhilePaused()
        {
            var c = new Countdown();
            c.Begin();
            c.Tick(0.02f);
            for (int i = 0; i < 1000; i++) c.Tick(0f);   // Time.deltaTime is 0 while paused
            Assert.AreEqual(3, c.Number);
            Assert.IsTrue(c.Active);
            c.Cancel();
            Assert.IsFalse(c.Active);
            Assert.IsFalse(c.Finished);
        }

        [Test]
        public void RestartStartsSetsAgainButKeepsEveryAttempt()
        {
            var ev = new ExerciseEvaluator(ExerciseEvaluatorTests.Ex(reps: 2, sets: 2, safetyMax: 100));
            ExerciseEvaluatorTests.Rep(ev, 90f);
            ExerciseEvaluatorTests.Rep(ev, 110f);   // unsafe, not counted
            Assert.AreEqual(1, ev.ValidReps);
            ev.RestartSets();
            Assert.AreEqual(0, ev.ValidReps);
            Assert.AreEqual(1, ev.SetNumber);
            Assert.AreEqual(1, ev.Restarts);
            Assert.AreEqual(2, ev.Attempts);
            Assert.AreEqual(1, ev.UnsafeReps);
            Assert.AreEqual(2, ev.RepEvents.Count);
            ExerciseEvaluatorTests.Rep(ev, 90f);
            Assert.AreEqual(1, ev.ValidReps);
            Assert.AreEqual(3, ev.RepEvents[2].attempt);   // attempt numbers keep going, so rep log rows stay unique
            var result = ev.ToResult();
            Assert.AreEqual(1, result.valid_reps);
            Assert.AreEqual(3, result.attempts);
        }

        [Test]
        public void ControlHintsMatchTheDevice()
        {
            Assert.AreEqual("Space", ControlHints.For(false).Start);
            Assert.AreEqual("A", ControlHints.For(true).Start);
            Assert.AreEqual("B", ControlHints.For(true).Back);
            StringAssert.Contains("Esc", ControlHints.Keyboard.MenuFooter);
            StringAssert.DoesNotContain("Esc", ControlHints.Controller.MenuFooter);
        }
    }
}
