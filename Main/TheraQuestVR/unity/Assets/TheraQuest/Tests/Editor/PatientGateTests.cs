using NUnit.Framework;
using UnityEngine;

namespace TheraQuest.Tests
{
    /// <summary>Patient Lock (M10.5): the exercise pauses while another person has the patient's place, reps are kept, and
    /// it resumes only when the locked patient is tracked again.</summary>
    public class PatientGateTests
    {
        const float Dt = 0.02f;

        static MotionPacket Packet(string patient, string tracking = "tracking") =>
            JsonUtility.FromJson<MotionPacket>($"{{\"visible\":true,\"trackingState\":\"{tracking}\",\"patient\":\"{patient}\",\"bodies\":2}}");

        /// <summary>One frame the way SessionManager runs it: the gate decides whether the evaluator is updated or paused.</summary>
        static void Frame(PatientGate gate, ExerciseEvaluator ev, MotionPacket packet, float angle, bool webcam = true, bool receiving = true)
        {
            gate.Tick(packet, webcam, receiving, Dt);
            if (gate.Paused) ev.TrackingPaused(Dt);
            else ev.Update(angle, null, Dt);
        }

        static void Rep(PatientGate gate, ExerciseEvaluator ev, MotionPacket packet, float peak = 90f)
        {
            for (float t = 0; t < 1f; t += Dt) Frame(gate, ev, packet, peak * t);
            for (float t = 0; t <= 1f; t += Dt) Frame(gate, ev, packet, peak * (1f - t));
            Frame(gate, ev, packet, 0f);
        }

        [Test]
        public void ThePacketCarriesTheStatusAndAnOlderTrackerLeavesItEmpty()
        {
            Assert.IsTrue(Packet("different").DifferentPerson);
            Assert.IsFalse(Packet("ok").DifferentPerson);
            Assert.AreEqual(2, Packet("ok").bodies);
            var old = JsonUtility.FromJson<MotionPacket>("{\"visible\":true,\"trackingState\":\"tracking\"}");
            Assert.IsFalse(old.DifferentPerson);
            var gate = new PatientGate();
            gate.Tick(old, true, true, Dt);
            Assert.IsFalse(gate.Paused);
        }

        [Test]
        public void AnotherPersonPausesAndOnlyThePatientReturningResumes()
        {
            var gate = new PatientGate();
            gate.Tick(Packet("ok"), true, true, Dt);
            Assert.IsFalse(gate.Paused);
            gate.Tick(Packet("different", "lost"), true, true, Dt);
            Assert.IsTrue(gate.Paused);
            gate.Tick(Packet("away", "lost"), true, true, Dt);   // the other person left view, the patient is not back
            Assert.IsTrue(gate.Paused, "still paused until the locked patient is tracked again");
            gate.Tick(Packet("ok", "reacquiring"), true, true, Dt);
            Assert.IsFalse(gate.Paused);
        }

        [Test]
        public void AwayAloneIsNotThisPause()
        {
            var gate = new PatientGate();
            gate.Tick(Packet("away", "lost"), true, true, Dt);   // the patient stepped out of view: the tracking-loss pause handles it
            Assert.IsFalse(gate.Paused);
            Assert.AreEqual(0, gate.Pauses);
        }

        [Test]
        public void ARepAlreadyCountedIsKeptAndTheOtherPersonCountsNothing()
        {
            var gate = new PatientGate();
            var ev = new ExerciseEvaluator(ExerciseEvaluatorTests.Ex());
            Rep(gate, ev, Packet("ok"));
            Assert.AreEqual(1, ev.ValidReps);
            Rep(gate, ev, Packet("different", "lost"), 90f);      // the other person does two full reps in front of the camera
            Rep(gate, ev, Packet("different", "lost"), 90f);
            Assert.AreEqual(1, ev.ValidReps, "the reps of another person never count");
            Assert.AreEqual(1, ev.Attempts);
            Rep(gate, ev, Packet("ok"));
            Assert.AreEqual(2, ev.ValidReps, "the patient carries on from the reps already counted");
        }

        [Test]
        public void AnotherPersonMidRepDropsThatRepWithoutScoringIt()
        {
            var gate = new PatientGate();
            var ev = new ExerciseEvaluator(ExerciseEvaluatorTests.Ex());
            for (float t = 0; t < 1f; t += Dt) Frame(gate, ev, Packet("ok"), 90f * t);
            for (float t = 0; t < 3f; t += Dt) Frame(gate, ev, Packet("different", "lost"), 90f);
            Assert.AreEqual(0, ev.Attempts);
            Assert.AreEqual(0, ev.ValidReps);
            Assert.AreEqual(LiveState.Idle, ev.State);
        }

        [Test]
        public void PausesAndPausedSecondsAreCountedForTheDashboard()
        {
            var gate = new PatientGate();
            var ev = new ExerciseEvaluator(ExerciseEvaluatorTests.Ex());
            for (int i = 0; i < 50; i++) Frame(gate, ev, Packet("different", "lost"), 0f);   // 1 s
            for (int i = 0; i < 5; i++) Frame(gate, ev, Packet("ok"), 0f);
            for (int i = 0; i < 100; i++) Frame(gate, ev, Packet("different", "lost"), 0f);  // 2 s, a second pause
            Assert.AreEqual(2, gate.Pauses);
            Assert.AreEqual(3f, gate.PausedSeconds, 0.05f);
            gate.Reset();
            Assert.AreEqual(0, gate.Pauses);
            Assert.AreEqual(0f, gate.PausedSeconds);
            Assert.IsFalse(gate.Paused);
        }

        [Test]
        public void OnlyTheWebcamHasAPatientToLock()
        {
            var gate = new PatientGate();
            gate.Tick(Packet("different"), false, true, Dt);      // keyboard or simulated input
            Assert.IsFalse(gate.Paused);
            gate.Tick(Packet("different"), true, true, Dt);
            Assert.IsTrue(gate.Paused);
            gate.Tick(Packet("different"), true, false, Dt);      // the tracker went silent: it restarts without a lock
            Assert.IsFalse(gate.Paused);
        }

        [Test]
        public void ANewPatientLockEndsThePause()
        {
            var gate = new PatientGate();
            gate.Tick(Packet("different"), true, true, Dt);
            gate.Tick(Packet("locking"), true, true, Dt);         // R pressed in the tracker window
            Assert.IsFalse(gate.Paused);
        }

        [Test]
        public void TheUploadCarriesThePauseCountForTheDashboard()
        {
            var up = new SessionUpload { other_person_pauses = 2, other_person_seconds = 45 };
            var json = JsonUtility.ToJson(up);
            StringAssert.Contains("\"other_person_pauses\":2", json);
            StringAssert.Contains("\"other_person_seconds\":45", json);
        }
    }
}
