namespace TheraQuest
{
    public enum SetupIssue { None, NoTracker, NotInView, OutOfFrame, TooClose, TooFar, WrongView, PoorLight }

    /// <summary>
    /// Camera setup check before each exercise (M6.3): is the camera placed so this exercise can be measured?
    /// Uses the tracker's setup checks (packet "setup"); the exercise says what it needs (its angle, view and
    /// posture). Guidance only: the patient can start anyway, and scoring never reads it.
    /// </summary>
    public static class CameraSetup
    {
        public const float TooCloseSize = 0.42f;   // torso over this share of the image height: closer than ~2 m
        public const float TooFarSize = 0.12f;     // under this: further than ~6 m
        public const float MinLight = 0.6f;

        /// <summary>The first problem found, in the order the patient should fix them, and its message.</summary>
        public static (SetupIssue issue, string message) Check(ExerciseDef ex, MotionPacket p, bool receiving)
        {
            if (!receiving || p == null) return (SetupIssue.NoTracker, "The camera isn't running. Ask for help");
            if (p.PersonLost || p.setup == null || !p.setup.valid) return (SetupIssue.NotInView, "Step into the camera's view");
            var s = p.setup;
            string measure = ex != null && !string.IsNullOrEmpty(ex.measure) ? ex.measure : "shoulderElev";
            string side = ex != null ? ex.side : "";
            bool framed = side == "L" ? s.framedL.Get(measure)
                        : side == "R" ? s.framedR.Get(measure)
                        : s.framedL.Get(measure) || s.framedR.Get(measure);
            if (!framed) return (SetupIssue.OutOfFrame, $"Step back so your whole {LimbWord(measure)} is in view");
            string posture = ex != null ? ex.posture : "";
            bool upright = posture != "lying" && posture != "sidelying";   // lying: the torso runs across the image
            if (upright && s.size > TooCloseSize) return (SetupIssue.TooClose, "Step back a little from the camera");
            if (upright && s.size >= 0f && s.size < TooFarSize) return (SetupIssue.TooFar, "Come a little closer to the camera");
            string want = ex != null && ex.view == "front" ? "front" : "side";
            if (s.view != want) return (SetupIssue.WrongView, want == "side" ? "Turn side-on to the camera" : "Face the camera");
            if (s.light < MinLight) return (SetupIssue.PoorLight, "Turn on more light");
            return (SetupIssue.None, "Camera is set up");
        }

        public static string LimbWord(string measure) =>
            measure == "hipElev" || measure == "kneeFlex" || measure == "kneeExt" ? "leg" : "arm";
    }
}
