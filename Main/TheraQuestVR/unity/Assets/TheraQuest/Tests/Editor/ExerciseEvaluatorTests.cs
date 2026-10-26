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
        public void TooFastMessageShowsTheDurationWithOneDecimal()
        {
            var ev = new ExerciseEvaluator(ExerciseEvaluatorTests.Ex());
            var r = ExerciseEvaluatorTests.Rep(ev, 90f, upSeconds: 0.25f, downSeconds: 0.25f);
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

    /// <summary>Auto-focus framing math (ViewFocus.Frame).</summary>
    public class ViewFocusTests
    {
        static readonly Vector3 Cam = new Vector3(0f, 1.55f, 0f);

        static ViewFocus.RigPose Frame(Bounds b, float headroom = 0f) =>
            ViewFocus.Frame(Cam, 1.55f, b, headroom, 60f, 16f / 9f, 1.3f, 1.3f, 4.5f);

        [Test]
        public void StandingCoachIsFramedHeadToFootStraightAhead()
        {
            var b = new Bounds(new Vector3(0f, 0.9f, 3.5f), new Vector3(0.6f, 1.8f, 0.4f));
            var p = Frame(b, 0.35f);
            Assert.AreEqual(0f, p.yaw, 0.01f);
            Assert.AreEqual(0f, p.rigPosition.x, 0.001f);
            Assert.AreEqual(0f, p.rigPosition.y, 0.001f);                     // stays on the floor
            Assert.AreEqual(3.5f - p.distance, p.rigPosition.z, 0.001f);      // moved along the line to the coach
            float halfV = Mathf.Atan((b.extents.y + 0.175f) / p.distance) * Mathf.Rad2Deg;
            Assert.Less(halfV, 30f, "coach height fits inside the 60° view");
        }

        [Test]
        public void ExerciseOnTheTableLooksDownMoreThanStanding()
        {
            var standing = Frame(new Bounds(new Vector3(0f, 0.9f, 3.5f), new Vector3(0.6f, 1.8f, 0.4f)), 0.35f);
            var lying = Frame(new Bounds(new Vector3(0f, 0.55f, 3.5f), new Vector3(0.8f, 0.7f, 2.0f)));
            Assert.Greater(lying.pitch, standing.pitch);
            Assert.Greater(lying.pitch, 0f);
        }

        [Test]
        public void SmallMotionsGetCloserButNeverInsideTheMinimum()
        {
            var small = Frame(new Bounds(new Vector3(0f, 1.2f, 3.5f), new Vector3(0.2f, 0.2f, 0.2f)));
            var big = Frame(new Bounds(new Vector3(0f, 0.9f, 3.5f), new Vector3(0.6f, 1.8f, 0.4f)), 0.35f);
            Assert.AreEqual(1.3f, small.distance, 0.001f);
            Assert.Greater(big.distance, small.distance);
        }

        [Test]
        public void TurnsToACoachOffToTheSide()
        {
            var p = Frame(new Bounds(new Vector3(3f, 0.9f, 0f), new Vector3(0.6f, 1.8f, 0.4f)), 0.35f);
            Assert.AreEqual(90f, p.yaw, 0.01f);
            Assert.AreEqual(3f - p.distance, p.rigPosition.x, 0.001f);
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
            StringAssert.Contains("1</b> of 7 badges earned", badges);
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
        public void EveryCoachModelIsAHumanoidSoTheIdleClipPlays()
        {
            var guids = UnityEditor.AssetDatabase.FindAssets("t:Model", new[] { "Assets/TheraQuest/Coaches" });
            Assert.IsNotEmpty(guids);
            foreach (var guid in guids)
            {
                string path = UnityEditor.AssetDatabase.GUIDToAssetPath(guid);
                Avatar avatar = null;
                foreach (var a in UnityEditor.AssetDatabase.LoadAllAssetsAtPath(path)) if (a is Avatar av) avatar = av;
                Assert.IsNotNull(avatar, path);
                Assert.IsTrue(avatar.isValid && avatar.isHuman, path + " is not a valid Humanoid (see CoachModelImporter)");
            }
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
}
