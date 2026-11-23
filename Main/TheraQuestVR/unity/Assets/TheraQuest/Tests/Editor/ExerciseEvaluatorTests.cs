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
        public void ComingBackDown_AfterTheTarget_IsLowering_WithGoodGuidance()
        {
            var ev = new ExerciseEvaluator(Ex());
            for (float a = 0; a <= 90; a += 5) ev.Update(a, null, Dt);      // up to the target
            ev.Update(70f, null, Dt);                                         // on the way back down, below the band
            Assert.AreEqual(LiveState.Lowering, ev.State);
            var (text, tone) = FeedbackManager.LiveMessage(ev, null);
            Assert.AreEqual(Tone.Good, tone);
            StringAssert.Contains("lower", text);
        }

        [Test]
        public void StillShortOfTheTarget_IsRising()
        {
            var ev = new ExerciseEvaluator(Ex());
            for (float a = 0; a <= 70; a += 5) ev.Update(a, null, Dt);
            Assert.AreEqual(LiveState.Rising, ev.State);
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
            var r = Rep(ev, 90f, upSeconds: 0.4f, downSeconds: 0.4f);
            Assert.IsTrue(r[0].tooFast);
            Assert.IsFalse(r[0].valid);
        }

        [Test]
        public void WebcamBlipIsNotARep()
        {
            // M6.5: up past the start line and back under the end line within a few frames
            var ev = new ExerciseEvaluator(Ex());
            Assert.AreEqual(0, Rep(ev, 90f, upSeconds: 0.15f, downSeconds: 0.15f).Count);
            Assert.AreEqual(0, ev.Attempts);
            Assert.IsFalse(Rep(ev, 90f, upSeconds: 0.6f, downSeconds: 0.6f)[0].tooFast, "an ordinary quick rep is not rushed");
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
        public void TooFastMessageShowsTheDurationWithOneDecimal()
        {
            var ev = new ExerciseEvaluator(ExerciseEvaluatorTests.Ex());
            var r = ExerciseEvaluatorTests.Rep(ev, 90f, upSeconds: 0.4f, downSeconds: 0.4f);
            Assert.IsTrue(r[0].tooFast);
            StringAssert.IsMatch(@"Moved too quickly \(\d\.\ds\)", ev.Describe(r[0]));
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

    /// <summary>Tracking-loss safeguards (DEC-022): only verified readings can count toward a rep.</summary>
    public class TrackingLossTests
    {
        const float Dt = 0.02f;

        static void Run(ExerciseEvaluator ev, float from, float to, float seconds)
        {
            for (float t = 0; t < seconds; t += Dt) ev.Update(Mathf.Lerp(from, to, t / seconds), null, Dt);
            ev.Update(to, null, Dt);
        }

        static void Pause(ExerciseEvaluator ev, float seconds)
        {
            for (float t = 0; t < seconds; t += Dt) ev.TrackingPaused(Dt);
        }

        [Test]
        public void ShortGapKeepsTheRepAndItsMeasuredPeak()
        {
            var ev = new ExerciseEvaluator(ExerciseEvaluatorTests.Ex());
            Run(ev, 0f, 90f, 1f);
            Pause(ev, 0.5f);
            Run(ev, 90f, 0f, 1f);
            Assert.AreEqual(1, ev.Attempts);
            Assert.AreEqual(1, ev.ValidReps);
            Assert.AreEqual(90f, ev.RepEvents[0].peak, 0.5f);
        }

        [Test]
        public void GapNeverCountsARepOrRaisesThePeak()
        {
            var ev = new ExerciseEvaluator(ExerciseEvaluatorTests.Ex());
            Run(ev, 0f, 60f, 1f);
            Pause(ev, 1f);
            Assert.AreEqual(0, ev.Attempts);
            Run(ev, 60f, 0f, 1f);
            Assert.AreEqual(1, ev.Attempts);
            Assert.AreEqual(0, ev.ValidReps, "only reached 60 where it could be seen");
            Assert.AreEqual(60f, ev.RepEvents[0].peak, 0.5f);
        }

        [Test]
        public void LongGapDropsTheRepWithoutCountingAnAttempt()
        {
            var ev = new ExerciseEvaluator(ExerciseEvaluatorTests.Ex());
            Run(ev, 0f, 90f, 1f);
            Pause(ev, 2.5f);
            Run(ev, 90f, 0f, 1f);    // the angle was never "lowered" in a rep that is still open
            Assert.AreEqual(0, ev.ValidReps);
            Assert.LessOrEqual(ev.Attempts, 1);
            Assert.AreEqual(0, ev.RepEvents.FindAll(e => e.valid).Count);
        }

        [Test]
        public void LongGapAtTheBottomStartsCleanly()
        {
            var ev = new ExerciseEvaluator(ExerciseEvaluatorTests.Ex());
            Run(ev, 0f, 90f, 1f);
            Pause(ev, 2.5f);
            ev.Update(0f, null, Dt);
            Assert.AreEqual(0, ev.Attempts, "the dropped rep is not scored");
            Run(ev, 0f, 90f, 1f);
            Run(ev, 90f, 0f, 1f);
            Assert.AreEqual(1, ev.ValidReps);
        }

        [Test]
        public void StateIsNeverLeftOnTargetDuringAGap()
        {
            var ev = new ExerciseEvaluator(ExerciseEvaluatorTests.Ex());
            Run(ev, 0f, 90f, 1f);
            Assert.AreNotEqual(LiveState.Idle, ev.State);
            ev.TrackingPaused(Dt);
            Assert.AreEqual(LiveState.Idle, ev.State);
        }

        [Test]
        public void HoldTimerStopsDuringAGap()
        {
            var ev = new ExerciseEvaluator(ExerciseEvaluatorTests.Ex(hold: 2f));
            Run(ev, 0f, 90f, 1f);
            float held = ev.HoldTime;
            Pause(ev, 1f);
            Assert.AreEqual(held, ev.HoldTime, 0.001f);
        }

        [Test]
        public void GapTimeStillCountsTowardTheRepsDuration()
        {
            var ev = new ExerciseEvaluator(ExerciseEvaluatorTests.Ex());
            Run(ev, 0f, 90f, 0.2f);
            Pause(ev, 1f);
            Run(ev, 90f, 0f, 0.2f);
            Assert.IsFalse(ev.RepEvents[0].too_fast);
        }

        [Test]
        public void EstimateIsKeptApartFromTheMeasuredAngle()
        {
            var ex = new ExerciseDef { side = "R", measure = "elbowFlex" };
            var p = JsonUtility.FromJson<MotionPacket>("{\"visible\":true,\"trackingState\":\"degraded\",\"R\":{\"elbowFlex\":-1},\"estR\":{\"elbowFlex\":80}}");
            Assert.AreEqual("degraded", p.trackingState);
            Assert.AreEqual(-1f, MotionInput.MeasuredAngle(ex, p.For("R")), "no reading to score");
            Assert.AreEqual(80f, MotionInput.EstimatedAngle(ex, p), "for display");
        }

        [Test]
        public void NoEstimateMeansNoDisplayAngle()
        {
            var ex = new ExerciseDef { side = "L", measure = "elbowFlex" };
            var p = JsonUtility.FromJson<MotionPacket>("{\"visible\":false}");
            Assert.AreEqual(-1f, MotionInput.EstimatedAngle(ex, p));
            Assert.AreEqual(-1f, MotionInput.EstimatedAngle(ex, null));
        }
    }

    /// <summary>M5.8: default height, the first-person limbs, the view's aim and the tutorial.</summary>
    public class FirstPersonTests
    {
        static FirstPersonMath.Chain Main(string pose, float angle, int side = 1) => FirstPersonMath.Limbs(pose, side, angle)[0];

        [Test]
        public void EveryHeightEndsAtTheSameDefaultEye()
        {
            foreach (float tracked in new[] { 1.40f, 1.60f, 1.95f })
                Assert.AreEqual(FirstPersonMath.StandingEye, tracked + FirstPersonMath.HeightOffset(FirstPersonMath.StandingEye, tracked), 0.0001f);
            Assert.Greater(FirstPersonMath.EyeHeight("standing"), FirstPersonMath.EyeHeight("seated"));
            Assert.Greater(FirstPersonMath.EyeHeight("seated"), FirstPersonMath.EyeHeight("lying"));
            Assert.AreEqual(0f, FirstPersonMath.ViewLift("standing"));
            Assert.Greater(FirstPersonMath.ViewLift("lying"), 0f, "lying down the view sees the limbs from above");
        }

        [Test]
        public void DefaultBodyFitsTheRoom()
        {
            // Standing, the foot is at the floor; seated, the foot is on the floor with the thigh level
            var standing = Main("hipExt", 0f);
            Assert.AreEqual(0f, FirstPersonMath.StandingEye + standing.end.y, 0.05f);
            var seated = Main("kneeExt", 0f);
            Assert.AreEqual(0f, FirstPersonMath.SeatedEye + seated.end.y, 0.05f);
            Assert.AreEqual(seated.root.y, seated.mid.y, 0.001f);
        }

        [Test]
        public void ArmReachesTheTargetAngleOnTheOperatedSide()
        {
            var right = Main("shoulderAbd", 90f);
            Assert.AreEqual(right.root.y, right.end.y, 0.001f, "level at 90 degrees");
            Assert.Greater(right.end.x, right.root.x);
            Assert.Less(Main("shoulderAbd", 90f, -1).end.x, Main("shoulderAbd", 90f, -1).root.x);
            var up = Main("shoulderFlex", 90f);
            Assert.Greater(up.end.z, 0.4f, "straight ahead at 90 degrees");
        }

        [Test]
        public void SquatKeepsTheFeetDownAndUsesBothLegs()
        {
            var limbs = FirstPersonMath.Limbs("miniSquat", 1, 40f);
            Assert.AreEqual(2, limbs.Length);
            Assert.AreEqual(Main("miniSquat", 0f).end.y, limbs[0].end.y, 0.001f);
            Assert.Less(limbs[0].root.y, Main("miniSquat", 0f).root.y, "hips drop");
        }

        [Test]
        public void OnlyLimbsThatEndBehindGetTheMirror()
        {
            foreach (var pose in new[] { "shoulderExt", "hipExt", "hamstringCurl" })
            {
                Assert.IsTrue(FirstPersonMath.BehindBody(pose), pose);
                Assert.Less(Main(pose, 45f).end.z, Main(pose, 45f).root.z + 0.001f, pose);
            }
            foreach (var pose in new[] { "shoulderAbd", "shoulderFlex", "elbowFlex", "march", "kneeExt", "slr", "supineFlex" })
                Assert.IsFalse(FirstPersonMath.BehindBody(pose), pose);
        }

        [Test]
        public void LyingFrameSendsTheFeetForwardAndSideLyingKeepsTheMovingSideUp()
        {
            var feet = FirstPersonMath.BodyFrame("lying", 1) * Vector3.down;
            Assert.AreEqual(1f, feet.z, 0.001f);
            Assert.AreEqual(1f, (FirstPersonMath.BodyFrame("lying", 1) * Vector3.forward).y, 0.001f, "toes up");
            foreach (int s in new[] { 1, -1 })
            {
                var frame = FirstPersonMath.BodyFrame("sidelying", s);
                Assert.AreEqual(1f, (frame * new Vector3(s, 0f, 0f)).y, 0.001f, "moving side on top");
                Assert.AreEqual(1f, (frame * Vector3.down).z, 0.001f, "feet ahead");
            }
            Assert.AreEqual(Quaternion.identity, FirstPersonMath.BodyFrame("standing", 1));
        }

        [Test]
        public void BodyDirectionComesFromTheHeadTopWhenLying()
        {
            Assert.AreEqual(90f, FirstPersonMath.FlatYaw(Vector3.right, Vector3.up, false), 0.01f);
            // Face to the ceiling, top of the head toward -X: the feet point toward +X
            Assert.AreEqual(90f, FirstPersonMath.FlatYaw(Vector3.up, Vector3.left, true), 0.01f);
            // Standing but looking straight down: the top of the head still gives the direction
            Assert.AreEqual(0f, FirstPersonMath.FlatYaw(Vector3.down, Vector3.forward, false), 0.01f);
        }

        [Test]
        public void AimLooksTowardTheMovementAndStaysInLimits()
        {
            FirstPersonMath.Aim(new Vector3(0.3f, -0.9f, 0.1f), new Vector3(0.7f, -0.2f, 0f), out float yaw, out float pitch);
            Assert.Greater(yaw, 30f, "toward the right arm");
            Assert.Greater(pitch, 0f, "looks down");
            FirstPersonMath.Aim(Vector3.up, Vector3.up, out _, out pitch);
            Assert.AreEqual(-60f, pitch, 0.01f);
            FirstPersonMath.Aim(Vector3.down, Vector3.down, out _, out pitch);
            Assert.AreEqual(75f, pitch, 0.01f);
        }

        [Test]
        public void TutorialWalksThroughAndCanBeSkipped()
        {
            var t = new Tutorial();
            Assert.IsFalse(t.Active);
            t.Begin();
            for (int i = 0; i < Tutorial.Steps.Length; i++)
            {
                Assert.IsTrue(t.Active);
                Assert.AreEqual(Tutorial.Steps[i], t.Text);
                t.Next();
            }
            Assert.IsFalse(t.Active);
            t.Begin();
            t.Skip();
            Assert.IsFalse(t.Active);
        }
    }

    /// <summary>M5.5: summary and Progress page shaping, and the gamification rules behind them.</summary>
    public class ProgressViewsTests
    {
        [Test]
        public void XpSpanWithinOneLevel()
        {
            var x = ProgressViews.Xp(20, 70);           // level 1 needs 100 XP
            Assert.AreEqual(1, x.fromLevel);
            Assert.AreEqual(1, x.toLevel);
            Assert.AreEqual(0.2f, x.fromFrac, 0.001f);
            Assert.AreEqual(0.7f, x.toFrac, 0.001f);
            Assert.IsFalse(x.LevelUp);
        }

        [Test]
        public void XpSpanAcrossALevelUp()
        {
            var x = ProgressViews.Xp(90, 130);          // level 2 starts at 100 and needs 160 more
            Assert.IsTrue(x.LevelUp);
            Assert.AreEqual(2, x.toLevel);
            Assert.AreEqual(30f / 160f, x.toFrac, 0.001f);
        }

        [Test]
        public void BadgeCodesBecomeNamesOnce()
        {
            CollectionAssert.AreEqual(new[] { "Combo 10", "mystery" }, ProgressViews.BadgeNames(new[] { "combo10", "mystery", "combo10" }));
        }

        [Test]
        public void GalleryMarksEarnedBadgesFromServerOrGame()
        {
            var fromGame = ProgressViews.Gallery(null, new[] { "first" });
            Assert.AreEqual(GamificationManager.BadgeNames.Count, fromGame.Count);
            Assert.IsTrue(fromGame.Find(b => b.code == "first").earned);
            Assert.IsFalse(fromGame.Find(b => b.code == "lv5").earned);
            var server = new ProgressInfo { badges = new[] { new BadgeInfo { code = "first", name = "First steps", earned = false } } };
            Assert.IsTrue(ProgressViews.Gallery(server, new[] { "first" })[0].earned);   // earned since the last download
        }

        [Test]
        public void ProgressPageListsBadgesSessionsAndOfflineNote()
        {
            var p = new ProgramResponse
            {
                patient = new PatientInfo { code = "P-001", xp = 150, streak = 2, badges = new[] { "first" } },
                progress = new ProgressInfo
                {
                    totalSessions = 3, completeSessions = 2,
                    recent = new[] { new RecentSession { started_at = "2026-10-20T09:00:00", status = "complete", stars = 3, valid = 16, points = 140 } },
                },
            };
            // Tab 1: profile
            string profile = ProgressViews.ProgressPage(p, true, ProgressViews.ProgressTab.Profile);
            StringAssert.Contains("Level 2", profile);
            StringAssert.Contains("2</b> day streak", profile);
            StringAssert.Contains("2</b> of 3 sessions", profile);
            StringAssert.Contains("1</b> of 7 badges", profile);
            StringAssert.DoesNotContain("Offline", profile);
            StringAssert.DoesNotContain("2026-10-20", profile);
            StringAssert.Contains("Offline", ProgressViews.ProgressPage(p, false, ProgressViews.ProgressTab.Profile));
            // Tab 2: recent sessions
            StringAssert.Contains("2026-10-20", ProgressViews.ProgressPage(p, true, ProgressViews.ProgressTab.Sessions));
            // Tab 3: badges are cards drawn by the menu; the text is the count above them, and each card says how to earn it
            string badges = ProgressViews.ProgressPage(p, true, ProgressViews.ProgressTab.Badges);
            StringAssert.Contains(ProgressViews.Headline("1") + " of 7 badges earned", badges);   // the count is the headline (M8.5)
            StringAssert.StartsWith(ProgressViews.Headline("Level 2"), profile);
            StringAssert.DoesNotContain("2026-10-20", badges);
            foreach (var code in GamificationManager.BadgeNames.Keys) Assert.IsNotEmpty(ProgressViews.BadgeHint(code), code);
            Assert.AreEqual("", ProgressViews.BadgeHint("mystery"));
            p.progress.recent = new RecentSession[0];
            StringAssert.Contains("No sessions yet", ProgressViews.ProgressPage(p, true, ProgressViews.ProgressTab.Sessions));
        }

        [Test]
        public void NewBadgesLineShowsIconsAndNamesOnce()
        {
            CollectionAssert.AreEqual(new[] { "combo10", "mystery" }, ProgressViews.BadgeCodes(new[] { "combo10", "", "mystery", "combo10" }));
            string line = ProgressViews.NewBadgesLine(new[] { "combo10" }, 2);
            StringAssert.StartsWith("New badges: ", line);
            StringAssert.Contains("<sprite name=\"combo10\"", line);
            StringAssert.Contains("Combo 10", line);
            StringAssert.Contains("★", ProgressViews.NewBadgesLine(new[] { "mystery" }, 1));   // no icon: a star
        }

        [Test]
        public void GamificationScoringComboAndBadges()
        {
            var g = new GamificationManager(new[] { "fullrom" });
            var unlocked = new List<string>();
            g.BadgeUnlocked += unlocked.Add;
            var good = new RepResult { valid = true, accuracy = 100, error = 0f };
            Assert.AreEqual(10, g.ScoreRep(good));                  // combo 1: x1.0
            Assert.AreEqual(11, g.ScoreRep(good));                  // combo 2: x1.1
            Assert.AreEqual(2, g.ScoreRep(new RepResult { valid = false }));
            Assert.AreEqual(0, g.Combo);
            for (int i = 0; i < 5; i++) g.ScoreRep(good);
            CollectionAssert.Contains(unlocked, "perfect");
            CollectionAssert.DoesNotContain(unlocked, "fullrom");   // already owned
            g.AddCompletionBonus();
            Assert.AreEqual(3, GamificationManager.Stars(92f, true));
            Assert.AreEqual(0, GamificationManager.Stars(92f, false));
        }
    }

    /// <summary>Game fonts and outline colours (UIKit).</summary>
    public class UIKitStyleTests
    {
        [Test]
        public void TextMeshProFontsCoverTheSymbolsTheGameUses()
        {
            Assert.IsNotNull(TMPro.TMP_Settings.defaultFontAsset, "TextMesh Pro essentials are missing");
            var body = UIKit.TmpFontFor(30, FontStyle.Normal);
            StringAssert.StartsWith("Nunito-SemiBold", body.name);
            StringAssert.StartsWith("LuckiestGuy-Regular", UIKit.TmpFontFor(72, FontStyle.Bold).name);
            // Glyphs the game fonts lack come from the DejaVu fallback
            foreach (char c in "★✓▶◀●☺↑↓‹›·°…×±")
                Assert.IsTrue(body.HasCharacter(c, true, true), $"no glyph for {c} (U+{(int)c:X4})");
        }

        [Test]
        public void EveryBadgeHasAnIcon()
        {
            Assert.IsNotNull(UIKit.BadgeSprites, "Resources/Badges/BadgeSprites is missing");
            foreach (var code in GamificationManager.BadgeNames.Keys)
            {
                Assert.IsNotNull(UIKit.BadgeIcon(code), code);
                Assert.GreaterOrEqual(UIKit.BadgeSprites.GetSpriteIndexFromName(code), 0, code);
            }
            Assert.IsNull(UIKit.BadgeIcon("mystery"));
            StringAssert.Contains("★", UIKit.BadgeTag("mystery", true));
        }

        [Test]
        public void FontsLoadAndAreChosenBySizeAndWeight()
        {
            Assert.AreEqual("LuckiestGuy-Regular", UIKit.FontFor(72, FontStyle.Bold).name);
            Assert.AreEqual("LuckiestGuy-Regular", UIKit.FontFor(UIKit.DisplaySize, FontStyle.Normal).name);
            Assert.AreEqual("Nunito-ExtraBold", UIKit.FontFor(30, FontStyle.Bold).name);
            Assert.AreEqual("Nunito-SemiBold", UIKit.FontFor(30, FontStyle.Normal).name);
        }

        [Test]
        public void PanelColoursComeFromTheFiveColourPalette()
        {
            string[] palette = { "1D3557", "277DA1", "F3722C", "43AA8B", "F8F9FA" };
            foreach (var c in new[] { UIKit.Ink, UIKit.Teal, UIKit.Blue, UIKit.Orange, UIKit.Yellow, UIKit.Green, UIKit.Pink, UIKit.Purple, UIKit.White })
                CollectionAssert.Contains(palette, ColorUtility.ToHtmlStringRGB(c));
            Assert.IsTrue(UIKit.IsDark(UIKit.Ink));          // navy text gets a light outline
            Assert.IsFalse(UIKit.IsDark(UIKit.Orange));
            Assert.IsFalse(UIKit.IsDark(UIKit.White));
        }

        [Test]
        public void OutlineIsALighterShadeOfTheTextColour()
        {
            var light = UIKit.Lighter(UIKit.Orange);
            Assert.Greater(light.r + light.g + light.b, UIKit.Orange.r + UIKit.Orange.g + UIKit.Orange.b);
            Assert.AreEqual(UIKit.Orange.a, light.a);
            Assert.AreEqual(Color.white, UIKit.Lighter(Color.black, 1f));
            Assert.AreEqual(UIKit.Orange, UIKit.Lighter(UIKit.Orange, 0f));
        }
    }

    /// <summary>Sounds and music (M5.6).</summary>
    public class AudioTests
    {
        [Test]
        public void ShuffleKeepsEveryTrackAndAvoidsRepeatingTheLastOne()
        {
            var rng = new System.Random(1);
            for (int n = 0; n < 50; n++)
            {
                var list = new List<string> { "a", "b", "c", "d" };
                MusicPlayer.Shuffle(list, "a", rng);
                Assert.AreNotEqual("a", list[0]);
                CollectionAssert.AreEquivalent(new[] { "a", "b", "c", "d" }, list);
            }
        }

        [Test]
        public void EveryCoachHasAnUprightHumanoidAvatarSoTheIdlesPlay()
        {
            foreach (var name in new[] { "Free Woman Tall", "Free Man Tall" })
            {
                var avatar = Resources.Load<Avatar>("CoachAvatars/" + name);
                Assert.IsNotNull(avatar, name + ": run TheraQuest > Build Coach T-Pose Avatars");
                Assert.IsTrue(avatar.isValid && avatar.isHuman, name);
            }
            Assert.IsNotNull(Resources.Load<AnimationClip>(HumanoidCoach.DefaultTalk));
        }

        [Test]
        public void RoomDecorationAndChairModelsAreInResources()
        {
            foreach (var m in new[] { "Room/Furniture/chairCushion", "Room/Furniture/pottedPlant", "Room/Furniture/lampSquareCeiling",
                                      "Room/Gym/treadmill", "Room/Gym/exercise_ball", "Room/Gym/dumbbell_rack",
                                      "Room/Gym/rowing_machine", "Room/Furniture/loungeSofa" })
                Assert.IsNotNull(Resources.Load<GameObject>(m), m);
        }

        [Test]
        public void LofiTracksAndHoldSoundAreInResources()
        {
            Assert.AreEqual(9, Resources.LoadAll<AudioClip>(MusicPlayer.PlaylistFolder).Length);
            Assert.IsNotNull(Resources.Load<AudioClip>("Audio/HoldComplete"));
            Assert.IsNotNull(Resources.Load<AnimationClip>(HumanoidCoach.DefaultIdle));
        }

        [Test]
        public void ReverbAddsATailAndStaysInRange()
        {
            var dry = AudioClip.Create("dry", 4410, 1, 44100, false);
            var d = new float[4410];
            for (int i = 0; i < d.Length; i++) d[i] = Mathf.Sin(i * 0.1f) * 0.5f;
            dry.SetData(d, 0);
            var wet = FeedbackManager.Reverb(dry, 0.6f);
            Assert.AreEqual(4410 + 61740, wet.samples);
            var w = new float[wet.samples];
            wet.GetData(w, 0);
            float tail = 0f, peak = 0f;
            for (int i = 0; i < w.Length; i++) { peak = Mathf.Max(peak, Mathf.Abs(w[i])); if (i > 8000) tail = Mathf.Max(tail, Mathf.Abs(w[i])); }
            Assert.Greater(tail, 0.001f);   // something rings on after the dry sound
            Assert.LessOrEqual(peak, 0.9001f);
        }
    }

    /// <summary>M6.3: the camera setup check before each exercise.</summary>
    public class CameraSetupTests
    {
        const string Good = "\"valid\":true,\"framedL\":{\"shoulderElev\":true,\"hipElev\":true,\"kneeFlex\":true}," +
                            "\"framedR\":{\"shoulderElev\":true,\"hipElev\":true,\"kneeFlex\":false},";

        static MotionPacket Packet(string setup, bool visible = true, string state = "tracking") =>
            JsonUtility.FromJson<MotionPacket>($"{{\"visible\":{(visible ? "true" : "false")},\"trackingState\":\"{state}\"," +
                                               $"\"setup\":{{{setup}}}}}");

        static ExerciseDef Ex(string measure = "shoulderElev", string view = "side", string side = "", string posture = "standing") =>
            new ExerciseDef { measure = measure, view = view, side = side, posture = posture };

        static SetupIssue Issue(ExerciseDef ex, MotionPacket p, bool receiving = true) => CameraSetup.Check(ex, p, receiving).issue;

        [Test]
        public void AllGoodWhenFramedAtTheRightDistanceAndView()
        {
            var p = Packet(Good + "\"view\":\"side\",\"size\":0.3,\"light\":0.95");
            Assert.AreEqual(SetupIssue.None, Issue(Ex(), p));
        }

        [Test]
        public void NoTrackerAndNobodyInViewComeFirst()
        {
            Assert.AreEqual(SetupIssue.NoTracker, Issue(Ex(), null, false));
            Assert.AreEqual(SetupIssue.NotInView, Issue(Ex(), Packet(Good + "\"view\":\"side\",\"size\":0.3,\"light\":0.9", state: "lost")));
            Assert.AreEqual(SetupIssue.NotInView, Issue(Ex(), JsonUtility.FromJson<MotionPacket>("{\"visible\":true}")), "older tracker, no setup");
        }

        [Test]
        public void TheExercisesOwnLimbMustBeInFrame()
        {
            var p = Packet(Good + "\"view\":\"side\",\"size\":0.3,\"light\":0.9");
            Assert.AreEqual(SetupIssue.OutOfFrame, Issue(Ex("kneeFlex", side: "R"), p), "right ankle out of frame");
            Assert.AreEqual(SetupIssue.None, Issue(Ex("kneeFlex", side: "L"), p));
            Assert.AreEqual(SetupIssue.None, Issue(Ex("kneeFlex"), p), "either side will do");
            StringAssert.Contains("leg", CameraSetup.Check(Ex("kneeFlex", side: "R"), p, true).message);
        }

        [Test]
        public void DistanceIsCheckedOnlyWhenUpright()
        {
            var close = Packet(Good + "\"view\":\"side\",\"size\":0.5,\"light\":0.9");
            Assert.AreEqual(SetupIssue.TooClose, Issue(Ex(), close));
            Assert.AreEqual(SetupIssue.None, Issue(Ex(posture: "lying"), close));
            Assert.AreEqual(SetupIssue.TooFar, Issue(Ex(), Packet(Good + "\"view\":\"side\",\"size\":0.08,\"light\":0.9")));
        }

        [Test]
        public void ViewMustMatchTheExercise()
        {
            var front = Packet(Good + "\"view\":\"front\",\"size\":0.3,\"light\":0.9");
            Assert.AreEqual(SetupIssue.WrongView, Issue(Ex(view: "side"), front));
            Assert.AreEqual(SetupIssue.None, Issue(Ex(view: "front"), front));
            Assert.AreEqual(SetupIssue.WrongView, Issue(Ex(view: "front"), Packet(Good + "\"view\":\"\",\"size\":0.3,\"light\":0.9")));
        }

        [Test]
        public void PoorLightIsReportedLast()
        {
            Assert.AreEqual(SetupIssue.PoorLight, Issue(Ex(), Packet(Good + "\"view\":\"side\",\"size\":0.3,\"light\":0.4")));
        }

        [Test]
        public void PersonLostFollowsTheTrackingState()
        {
            Assert.IsTrue(JsonUtility.FromJson<MotionPacket>("{\"visible\":true,\"trackingState\":\"lost\"}").PersonLost);
            Assert.IsTrue(JsonUtility.FromJson<MotionPacket>("{\"visible\":false}").PersonLost);
            Assert.IsFalse(JsonUtility.FromJson<MotionPacket>("{\"visible\":true,\"trackingState\":\"degraded\"}").PersonLost);
        }
    }

    /// <summary>Side-on, only the limb doing the exercise is measured, through left/right swaps (M6.5).</summary>
    public class MovingLimbTests
    {
        static MotionPacket Packet(float left, float right) =>
            new MotionPacket { visible = true, L = new AngleSet { kneeFlex = left }, R = new AngleSet { kneeFlex = right } };

        [Test]
        public void TheMovingLegIsMeasuredWhateverItIsLabelled()
        {
            var curl = new ExerciseDef { pose = "hamstringCurl", measure = "kneeFlex", view = "side", targetAngle = 90f };
            Assert.AreEqual("R", MotionInput.MovingSide(curl, Packet(8f, 70f)));
            Assert.AreEqual("L", MotionInput.MovingSide(curl, Packet(72f, 6f)), "labels swapped: still the curling leg");
            Assert.AreEqual("R", MotionInput.MovingSide(curl, Packet(-1f, 40f)), "one leg hidden");
            Assert.IsNull(MotionInput.MovingSide(curl, Packet(-1f, -1f)));
            var squat = new ExerciseDef { pose = "miniSquat", measure = "kneeFlex", view = "side", targetAngle = 30f };
            Assert.IsNull(MotionInput.MovingSide(squat, Packet(8f, 30f)), "both legs move: the tracker's side");
        }

        [Test]
        public void ADropoutHoldsTheAngleButARealLoweringPassesThrough()
        {
            var f = new DropoutFilter();
            const float dt = 1f / 30f;
            Assert.AreEqual(70f, f.Apply(70f, dt));
            Assert.AreEqual(70f, f.Apply(20f, dt), "50 degrees in one frame: a dropout");
            Assert.AreEqual(68f, f.Apply(68f, dt), "back on the leg");
            for (int i = 0; i < 12; i++) f.Apply(10f, dt);
            Assert.AreEqual(10f, f.Apply(10f, dt), "a drop lasting longer than the hold is real");
            Assert.AreEqual(5f, f.Apply(5f, dt));
            f.Reset();
            for (float a = 90f; a > 0f; a -= 6f) Assert.AreEqual(a, f.Apply(a, dt), "lowering at 180 degrees a second");
        }
    }

    /// <summary>Standing position measured before hip abduction (M6.5).</summary>
    public class RestBaselineTests
    {
        static float Feed(RestBaseline b, float angle, float seconds, float dt = 1f / 30f)
        {
            float last = 0f;
            for (float t = 0f; t < seconds; t += dt) last = b.Adjust(angle, dt);
            return last;
        }

        [Test]
        public void StandingStillSetsTheRestingAngle()
        {
            var b = new RestBaseline();
            Assert.AreEqual(0f, Feed(b, 9f, 0.5f), "nothing counts until the standing position is known");
            Assert.IsFalse(b.Ready);
            Feed(b, 9f, 0.7f);
            Assert.IsTrue(b.Ready);
            Assert.AreEqual(9f, b.Value, 0.01f);
            Assert.AreEqual(25f, b.Adjust(34f, 1f / 30f), 0.01f, "the lift is measured from the standing position");
            Assert.AreEqual(0f, b.Adjust(5f, 1f / 30f), "never below the standing position");
        }

        [Test]
        public void MovingOrRaisedLegIsNotTakenAsStanding()
        {
            var b = new RestBaseline();
            for (int i = 0; i < 90; i++) b.Adjust(i % 2 == 0 ? 3f : 12f, 1f / 30f);   // wobbling
            Assert.IsFalse(b.Ready);
            Feed(b, 40f, 2f);                                                          // leg held out
            Assert.IsFalse(b.Ready);
        }

        [Test]
        public void ARepDoesNotMoveTheRestingAngleButStandingStillAgainRefreshesIt()
        {
            var b = new RestBaseline();
            Feed(b, 8f, 1.2f);
            Feed(b, 35f, 1.5f);                      // holding the leg out is not standing
            Assert.AreEqual(8f, b.Value, 0.01f);
            Feed(b, 11f, 1.2f);                      // back near the standing position, still
            Assert.AreEqual(11f, b.Value, 0.01f);
            Assert.IsTrue(RestBaseline.Uses(new ExerciseDef { pose = "hipAbd" }));
            Assert.IsTrue(RestBaseline.Uses(new ExerciseDef { pose = "hamstringCurl" }), "every exercise (M6.5)");
        }

        [Test]
        public void RestingLimitStaysUnderTheStartLine()
        {
            Assert.AreEqual(25f, RestBaseline.RestLimit(new ExerciseDef { targetAngle = 90f }));
            Assert.AreEqual(15f, RestBaseline.RestLimit(new ExerciseDef { targetAngle = 25f }), 0.01f);
            Assert.AreEqual(10f, RestBaseline.RestLimit(new ExerciseDef { targetAngle = 10f }));
            var b = new RestBaseline();
            b.Reset(new ExerciseDef { targetAngle = 25f });
            Feed(b, 18f, 2f);                        // above 60% of the target: already moving, not resting
            Assert.IsFalse(b.Ready);
            Feed(b, 6f, 1.2f);
            Assert.IsTrue(b.Ready);
            Assert.AreEqual(6f, b.Value, 0.01f);
        }
    }

    /// <summary>Ankle exercises and the out-of-plane live limb (M6.4).</summary>
    public class AnkleAndTiltTests
    {
        static FirstPersonMath.Chain Main(string pose, float angle, int side = 1) => FirstPersonMath.Limbs(pose, side, angle)[0];

        /// <summary>Angle between the shin (ankle to knee) and the foot (ankle to toes), degrees.</summary>
        static float FootAngle(FirstPersonMath.Chain c) => Vector3.Angle(c.mid - c.end, c.tip - c.end);

        [Test]
        public void AnkleFieldsAndLimbDirectionsParse()
        {
            var p = JsonUtility.FromJson<MotionPacket>(
                "{\"visible\":true,\"ankleDF\":12.5,\"L\":{\"anklePF\":30}," +
                "\"setup\":{\"valid\":true,\"framedL\":{\"ankleDF\":true,\"anklePF\":true}}," +
                "\"dirL\":{\"arm\":[0.0,-1.0,0.0],\"leg\":[0.1,-0.99,0.0]}}");
            Assert.AreEqual(12.5f, p.Get("ankleDF"), 0.001f);
            Assert.AreEqual(30f, p.L.Get("anklePF"), 0.001f);
            Assert.IsTrue(p.setup.framedL.Get("anklePF"));
            Assert.IsFalse(p.setup.framedR.Get("ankleDF"));
            Assert.IsTrue(p.dirL.TryGet(false, out var arm));
            Assert.AreEqual(-1f, arm.y, 0.001f);
            Assert.IsTrue(p.dirL.TryGet(true, out _));
            Assert.IsFalse(p.dirR != null && p.dirR.TryGet(false, out _), "no direction sent for the right side");
            Assert.AreEqual("foot", CameraSetup.LimbWord("anklePF"));
            Assert.AreEqual("leg", CameraSetup.LimbWord("kneeFlex"));
        }

        [Test]
        public void FootTurnsByTheAnkleAngle()
        {
            Assert.AreEqual(90f, FootAngle(Main("heelRaise", 0f)), 0.5f);
            Assert.AreEqual(120f, FootAngle(Main("heelRaise", 30f)), 0.5f, "toes point down");
            Assert.Less(Main("heelRaise", 30f).tip.y, Main("heelRaise", 0f).tip.y);
            Assert.AreEqual(2, FirstPersonMath.Limbs("heelRaise", 1, 30f).Length, "both heels");
            Assert.AreEqual(120f, FootAngle(Main("seatedHeelRaise", 30f)), 0.5f);
            Assert.AreEqual(75f, FootAngle(Main("anklePump", 15f)), 0.5f, "toes come up");
            Assert.AreEqual(Main("anklePump", 0f).end, Main("anklePump", 15f).end, "the leg holds still");
        }

        [Test]
        public void AnklePosesHaveAPostureWordAndFootView()
        {
            Assert.AreEqual("lying", FirstPersonMath.PostureOf(new ExerciseDef { pose = "anklePump" }));
            Assert.AreEqual("seated", FirstPersonMath.PostureOf(new ExerciseDef { pose = "seatedHeelRaise" }));
            Assert.AreEqual("standing", FirstPersonMath.PostureOf(new ExerciseDef { pose = "heelRaise" }));
            Assert.AreEqual("Toes up", FirstPersonMath.Word("anklePump"));
            Assert.AreEqual("Heels up", FirstPersonMath.Word("heelRaise"));
            foreach (var pose in new[] { "anklePump", "heelRaise", "seatedHeelRaise" })
            {
                Assert.IsTrue(FirstPersonMath.AnklePose(pose), pose);
                Assert.IsFalse(FirstPersonMath.BehindBody(pose), pose);
                Assert.AreEqual(Vector3.zero, FirstPersonMath.PlaneNormal(pose, 1), "the foot never leans");
            }
            Assert.IsFalse(FirstPersonMath.AnklePose("kneeExt"));
        }

        static Vector3 Dir(float outDeg, float x = 1f) =>
            new Vector3(x * Mathf.Sin(outDeg * Mathf.Deg2Rad), -Mathf.Cos(outDeg * Mathf.Deg2Rad), 0f);

        [Test]
        public void LeanOutOfThePlaneHasADeadZoneAndACap()
        {
            Assert.AreEqual(10f, FirstPersonMath.OutOfPlane("shoulderFlex", 1, Dir(30f)), 0.1f, "30 out, minus the arm's dead zone");
            Assert.AreEqual(0f, FirstPersonMath.OutOfPlane("shoulderFlex", 1, Dir(18f)), 0.001f, "a hanging arm sits outside the hip");
            Assert.AreEqual(-10f, FirstPersonMath.OutOfPlane("shoulderFlex", 1, Dir(30f, -1f)), 0.1f, "across the body");
            Assert.AreEqual(10f, FirstPersonMath.OutOfPlane("shoulderFlex", -1, Dir(30f, -1f)), 0.1f, "left arm: out is -x");
            Assert.AreEqual(18f, FirstPersonMath.OutOfPlane("slr", 1, Dir(30f)), 0.1f, "legs have a smaller dead zone");
            Assert.AreEqual(FirstPersonMath.MaxTilt, FirstPersonMath.OutOfPlane("shoulderFlex", 1, Vector3.right), 0.001f);
            Assert.AreEqual(10f, FirstPersonMath.OutOfPlane("shoulderAbd", 1, new Vector3(0f, -0.866f, 0.5f)), 0.1f, "frontal: forward");
            Assert.AreEqual(0f, FirstPersonMath.OutOfPlane("elbowFlex", 1, Vector3.right), "the elbow never leans");
        }

        [Test]
        public void TiltKeepsTheLimbsShapeAndInPlaneAngle()
        {
            var c = Main("shoulderFlex", 90f);
            var t = FirstPersonMath.Tilt(c, "shoulderFlex", 1, 30f);
            Assert.AreEqual(c.root, t.root);
            Assert.AreEqual((c.end - c.root).magnitude, (t.end - t.root).magnitude, 0.001f);
            Assert.AreEqual(30f, Mathf.Asin((t.mid - t.root).normalized.x) * Mathf.Rad2Deg, 0.1f, "leans out to the right");
            var flat = Vector3.ProjectOnPlane(t.mid - t.root, Vector3.right);
            Assert.AreEqual(90f, Vector3.Angle(flat, Vector3.down), 0.1f, "the webcam's angle is kept in the plane");
            var none = FirstPersonMath.Tilt(c, "elbowFlex", 1, 30f);
            Assert.AreEqual(c.end, none.end);
        }

        [Test]
        public void TiltComesFromTheMeasuredSidesDirection()
        {
            var p = JsonUtility.FromJson<MotionPacket>("{\"visible\":true,\"dirR\":{\"arm\":[0.5,-0.866,0.0]}}");
            var flex = new ExerciseDef { pose = "shoulderFlex", side = "R" };
            Assert.AreEqual(10f, MotionInput.TiltFrom(flex, p, "R"), 0.1f);
            Assert.IsTrue(float.IsNaN(MotionInput.TiltFrom(flex, p, "L")), "nothing sent for that side");
            Assert.AreEqual(0f, MotionInput.TiltFrom(new ExerciseDef { pose = "elbowFlex" }, p, "R"));
        }
    }
}
