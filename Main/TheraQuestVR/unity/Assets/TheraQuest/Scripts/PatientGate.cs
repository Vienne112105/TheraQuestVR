namespace TheraQuest
{
    /// <summary>
    /// Patient Lock (M10.5): the exercise must be done by the patient, not by another person. The tracker locks onto
    /// the first body it sees and says "different" when another body has taken the patient's place (a person who is
    /// only in view never does). From that packet until the locked patient is tracked again the exercise is paused:
    /// nothing is scored and reps already counted are kept. A pause is also counted, for the therapist's dashboard.
    /// The pause is latched: it ends when the tracker says "ok" (the patient is tracked again) or "locking" (the
    /// tracker was told to lock onto a new patient), not when the other person merely leaves view.
    /// </summary>
    public sealed class PatientGate
    {
        public bool Paused { get; private set; }
        public int Pauses { get; private set; }
        public float PausedSeconds { get; private set; }

        public void Reset()
        {
            Paused = false;
            Pauses = 0;
            PausedSeconds = 0f;
        }

        /// <param name="webcam">the session is driven by the webcam tracker (keyboard and simulated input have no patient to lock)</param>
        /// <param name="receiving">tracker packets are arriving; a silent tracker lifts the pause (it restarts without a lock)</param>
        public void Tick(MotionPacket latest, bool webcam, bool receiving, float dt)
        {
            string state = latest != null ? latest.patient : null;
            if (!webcam || !receiving || state == "ok" || state == "locking")
                Paused = false;
            else if (state == "different" && !Paused)
            {
                Paused = true;
                Pauses++;
            }
            if (Paused) PausedSeconds += dt;
        }
    }
}
