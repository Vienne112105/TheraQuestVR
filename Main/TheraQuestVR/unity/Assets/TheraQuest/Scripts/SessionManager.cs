using System;
using System.Collections;
using System.Collections.Generic;
using System.Text;
using UnityEngine;

namespace TheraQuest
{
    /// <summary>
    /// Runs the game and a rehabilitation session from start to finish (the System Flowchart, Section 3.6.1):
    ///   load program -> main menu -> exercise 1..n (evaluate, feedback, score) -> session summary
    ///   -> upload to server (Adherence Monitoring) -> main menu again.
    /// Esc / B pauses (the exercise freezes). The patient can walk around the clinic (PlayerMover);
    /// starting the quest brings them back to the exercise spot.
    /// Pain, soreness and swelling are recorded by the therapist on the dashboard, not asked here.
    /// If the patient's protocol phase is not for VR (immobilization or passive motion), no session starts.
    /// The menu, music, subtitles, clinic room and walking are added at runtime when the scene
    /// doesn't have them yet, so older scenes work without running Create Scene again.
    /// </summary>
    public class SessionManager : MonoBehaviour
    {
        [Header("References (filled in by TheraQuest > Create Scene)")]
        public ApiClient api;
        public MotionInput motion;
        public MotionReceiver receiver;
        public FeedbackManager feedback;
        public HUDController hud;
        public FigureVisualizer figure;
        public HumanoidCoach coach;     // rigged coach; optional, shows the primitive figure itself when it has no character
        public HeadTracking head;
        [Header("Added at runtime when empty")]
        public MenuController menu;
        public PlayerMover mover;

        enum Phase { Loading, Ready, Running, Uploading, Summary }
        Phase phase = Phase.Loading;

        ProgramResponse program;
        bool online, canStart;
        readonly List<ExerciseEvaluator> evaluators = new List<ExerciseEvaluator>();
        int index;
        GamificationManager game;
        DateTime startedAt;
        string sessionUuid, sessionSource;
        float repMessageTimer;
        bool awaitingReady;          // patient is getting into the start position for the next exercise
        float autoReadyTimer;        // simulated mode continues on its own
        LiveState lastState;
        readonly Countdown countdown = new Countdown();   // 3-2-1 before each exercise (M5.4)
        float celebrateTimer;        // "exercise complete" moment before the next exercise (M5.4)
        const float CelebrateSeconds = 3.5f;
        static ControlHints Keys => ControlHints.Current;

        ExerciseDef Current => program != null && program.exercises.Length > 0 ? program.exercises[Mathf.Clamp(index, 0, program.exercises.Length - 1)] : null;
        ExerciseEvaluator CurrentEval => phase == Phase.Running && index < evaluators.Count ? evaluators[index] : null;
        bool Simulated => motion.source == InputSource.Simulated;

        void Awake()
        {
            SmoothEdges(Camera.main);
            if (menu == null) menu = GetComponent<MenuController>();
            if (menu == null) menu = gameObject.AddComponent<MenuController>();
            menu.session = this;
            if (FindAnyObjectByType<MusicPlayer>() == null) gameObject.AddComponent<MusicPlayer>();
            if (FindAnyObjectByType<Subtitles>() == null) gameObject.AddComponent<Subtitles>();
            if (FindAnyObjectByType<ClinicRoom>() == null) gameObject.AddComponent<ClinicRoom>();
            if (mover == null && head != null && head.transform.parent != null)
            {
                var rig = head.transform.parent.gameObject;
                mover = rig.GetComponent<PlayerMover>();
                if (mover == null) mover = rig.AddComponent<PlayerMover>();
                mover.head = head;
            }
        }

        void OnDestroy() { Time.timeScale = 1f; AudioListener.pause = false; }

        /// <summary>
        /// Anti-aliasing for smooth edges instead of jagged pixels: MSAA where the pipeline allows it, plus
        /// SMAA (high) on a URP camera. Set through reflection, so the scripts also compile without URP.
        /// </summary>
        static void SmoothEdges(Camera cam)
        {
            if (cam == null) return;
            cam.allowMSAA = true;
            var type = Type.GetType("UnityEngine.Rendering.Universal.UniversalAdditionalCameraData, Unity.RenderPipelines.Universal.Runtime");
            if (type == null) return;
            var data = cam.GetComponent(type);
            if (data == null) data = cam.gameObject.AddComponent(type);
            void Set(string property, string value)
            {
                var prop = type.GetProperty(property);
                if (prop != null && prop.PropertyType.IsEnum) prop.SetValue(data, Enum.Parse(prop.PropertyType, value));
            }
            Set("antialiasing", "SubpixelMorphologicalAntiAliasing");
            Set("antialiasingQuality", "High");
        }

        IEnumerator Start()
        {
            hud.SetFeedback("Loading your program…", Tone.Neutral);
            yield return LoadProgram();
        }

        IEnumerator LoadProgram()
        {
            phase = Phase.Loading;
            yield return api.LoadProgram((p, ok) => { program = p; online = ok; });
            if (program.phase == null) program.phase = new PhaseInfo();
            if (program.exercises == null) program.exercises = new ExerciseDef[0];
            index = 0;
            evaluators.Clear();
            game = null;
            hud.SetPatient(program.patient, program.program, online, program.phase);
            hud.SetQuest(program.exercises, null, 0, false);
            canStart = program.phase.vrAllowed && program.exercises.Length > 0;
            ShowReadyBanner();
            phase = Phase.Ready;
            menu.Open(MenuController.Page.Main);
        }

        void ShowReadyBanner()
        {
            if (program.exercises.Length == 0 && !online && api.LastProblem != null)
                hud.SetFeedback(api.LastProblem, Tone.Warn);
            else if (!program.phase.vrAllowed)
                hud.SetFeedback("Right now you exercise with your therapist.\n<size=34>No VR session today</size>", Tone.Warn);
            else if (program.exercises.Length == 0)
                hud.SetFeedback("No exercises prescribed yet. Ask your therapist.", Tone.Warn);
            else
                hud.SetFeedback($"Stand on the teal spot and press Start!\n<size=34>{Keys.Start} to start · {Keys.Back} for the menu</size>", Tone.Neutral);
        }

        // ---------------------------------------------------------------- menu actions
        public bool CanStart => canStart && phase == Phase.Ready;

        public string MenuSubtitle
        {
            get
            {
                if (program == null) return "";
                string plan = !string.IsNullOrEmpty(program.phase.name) ? $"{program.phase.protocol} · {program.phase.name}" : program.program.name;
                GamificationManager.Level(program.patient.xp, out int lv, out _, out _);
                return $"{program.patient.code} · {plan} · level {lv}";
            }
        }

        public string MenuInfo
        {
            get
            {
                if (program == null) return "Loading…";
                var sb = new StringBuilder();
                if (program.exercises.Length == 0 && !online && api.LastProblem != null)
                    sb.Append($"<color={UIKit.HexWarn}>{api.LastProblem}</color>");
                else if (!program.phase.vrAllowed) sb.Append($"<color={UIKit.HexWarn}>Right now you exercise with your therapist, not in VR.</color>");
                else if (program.exercises.Length == 0) sb.Append($"<color={UIKit.HexWarn}>No exercises yet. Ask your therapist.</color>");
                else
                {
                    float seconds = 0f;
                    foreach (var e in program.exercises)
                        seconds += 25f + e.TotalReps * (4f + e.holdSeconds) + Mathf.Max(0, e.sets - 1) * e.restSeconds;
                    sb.Append($"Today: <b>{program.exercises.Length} exercises</b> · about {Mathf.Max(1, Mathf.RoundToInt(seconds / 60f))} minutes");
                    if (GameSettings.ShowDetails && !string.IsNullOrEmpty(program.phase.romGoal)) sb.Append($"\n<color={UIKit.HexMuted}>Goal: {program.phase.romGoal}</color>");
                }
                if (!online && program.exercises.Length > 0)
                    sb.Append($"\n<color={UIKit.HexWarn}>Offline: your results are saved and sent to your therapist later.</color>");
                int queued = api.QueuedCount;
                if (queued > 0)
                    sb.Append($"\n<color={UIKit.HexMuted}>{queued} saved session{(queued == 1 ? " is" : "s are")} waiting to be sent to your therapist.</color>");
                return sb.ToString();
            }
        }

        public string PauseSubtitle => Current != null ? $"{Current.name} · set {CurrentEval?.SetNumber ?? 1} of {Mathf.Max(1, Current.sets)}" : "";

        /// <summary>Pause menu: start the current exercise again from set 1 (not during the "complete" moment).</summary>
        public bool CanRestartExercise => phase == Phase.Running && celebrateTimer <= 0f && CurrentEval != null;

        public void RestartExercise()
        {
            if (!CanRestartExercise) return;
            Resume();
            CurrentEval.RestartSets();
            hud.SetQuest(program.exercises, evaluators, index, true);
            PrepareExercise(restarted: true);
        }

        public void StartQuest()
        {
            if (!CanStart) return;
            menu.Close();
            ReturnToStation();
            BeginSession();
        }

        public void FreeRoam()
        {
            menu.Close();
            var k = Keys;
            hud.SetFeedback($"Explore the clinic! Then press Start on the teal spot\n<size=32>Walk {k.Walk} · Turn {k.Turn} · Menu {k.Back}</size>", Tone.Neutral);
            Subtitles.Say($"Explore the clinic. Walk with {k.Walk}. Come back to the teal spot and press {k.Start} when you're ready.", 5f);
        }

        void Pause()
        {
            Time.timeScale = 0f;
            AudioListener.pause = true;
            menu.Open(MenuController.Page.Pause);
        }

        public void Resume()
        {
            Time.timeScale = 1f;
            AudioListener.pause = false;
            menu.Close();
        }

        public void EndSessionEarly()
        {
            Resume();
            if (phase == Phase.Running) FinishSession(endedEarly: true);
        }

        public void ReturnToStation()
        {
            if (mover != null) mover.ReturnToStation();
            else if (head != null) head.Recenter();
        }

        /// <summary>Therapist page: point this computer at another patient and load their program.</summary>
        public void SwitchPatient(string code)
        {
            if (phase != Phase.Ready && phase != Phase.Loading) return;
            api.SetPatientCode(code);
            menu.Close();
            hud.SetFeedback("Loading your program…", Tone.Neutral);
            StartCoroutine(LoadProgram());
        }

        public string ActivePatientCode => api.Code;
        public bool SessionRunning => phase == Phase.Running;

        /// <summary>Closing the app mid-session: keep what was done so far (queued, sent at the next start).</summary>
        void OnApplicationQuit()
        {
            if (phase != Phase.Running || game == null) return;
            api.QueueOffline(BuildUpload(endedEarly: true, completed: false, out _, out _, out _, out _, out _));
        }

        public void Quit()
        {
#if UNITY_EDITOR
            UnityEditor.EditorApplication.isPlaying = false;
#else
            Application.Quit();
#endif
        }

        // ---------------------------------------------------------------- frame loop
        void Update()
        {
            InputHelper.Tick();
            float dt = Time.deltaTime;   // 0 while paused, which freezes the exercise
            // No walking during an exercise: stick drift or a bumped stick would move the patient (M4.3)
            if (mover != null) mover.locked = menu.IsOpen || phase == Phase.Running;

            var ex = Current;
            motion.Sample(ex, dt);
            UpdateSourceText();

            if (menu.IsOpen) menu.HandleInput();
            else
            {
                // The input source is changed only on the therapist page, never mid-session (M4.3)
                if (InputHelper.RecenterPressed) ReturnToStation();
                switch (phase)
                {
                    case Phase.Ready:
                        if (InputHelper.StartPressed && canStart) StartQuest();
                        else if (InputHelper.BackPressed) menu.Open(MenuController.Page.Main);
                        break;
                    case Phase.Running:
                        if (InputHelper.BackPressed) Pause();
                        else RunExercise(ex, dt);
                        break;
                    case Phase.Summary:
                        if (InputHelper.StartPressed || InputHelper.BackPressed) { hud.HideSummary(); StartCoroutine(LoadProgram()); }
                        break;
                }
            }

            var cur = CurrentEval;
            Tone figTone = cur == null ? Tone.Neutral :
                cur.State == LiveState.OnTarget || cur.State == LiveState.Holding ? Tone.Good :
                cur.State == LiveState.TooFar || cur.State == LiveState.Fault || cur.State == LiveState.Unsafe ? Tone.Bad : Tone.Neutral;
            if (coach != null)
            {
                bool exercising = phase == Phase.Running && !awaitingReady && celebrateTimer <= 0f;
                coach.isSessionActive = exercising;
                coach.ghostVisible = exercising;   // no ghost on the menu, summary or between exercises
                coach.Show(ex, motion.Angle, figTone);
            }
            else figure.Show(ex, motion.Angle, figTone);
            hud.SetExercise(ex, cur, motion.Angle, game != null ? game.Points : 0, game != null ? game.Multiplier : 1f);
        }

        void RunExercise(ExerciseDef ex, float dt)
        {
            if (celebrateTimer > 0f)
            {
                // "Exercise complete" moment, then the next exercise's get-ready card (frozen while paused)
                if ((celebrateTimer -= dt) <= 0f)
                {
                    index++;
                    hud.SetQuest(program.exercises, evaluators, index, true);
                    PrepareExercise();
                }
                return;
            }
            if (awaitingReady)
            {
                if (countdown.Active || countdown.Finished)
                {
                    if (countdown.Tick(dt))
                    {
                        if (countdown.Number > 0) { feedback.PlayClick(); hud.Pop(countdown.Number.ToString(), true); }
                        else if (!countdown.Finished) hud.Pop("GO!", true);
                    }
                    if (countdown.Finished)
                    {
                        countdown.Cancel();
                        awaitingReady = false;
                        ShowRepMessage(ex.cue, Tone.Neutral, 2f);
                        Subtitles.Say(ex.cue, 3f, "Coach");
                    }
                    else hud.SetFeedback(countdown.Number > 0 ? $"Starting in… {countdown.Number}" : "Starting in… Go!", Tone.Neutral);
                    return;
                }
                if (InputHelper.StartPressed || (Simulated && (autoReadyTimer -= dt) <= 0f))
                {
                    countdown.Begin();
                    Subtitles.Say("3, 2, 1, go!", 3f, "Countdown beeps");
                }
                else hud.SetFeedback($"Exercise {index + 1} of {evaluators.Count}: <b>{ex.name}</b>\nGet ready: {ex.position}\n" +
                                     $"<size=34>Camera {ex.CameraText} · press {Keys.Start} when ready</size>", Tone.Neutral);
                return;
            }
            var ev = CurrentEval;
            if (motion.HasReading || ev.Resting) ev.Update(motion.Angle, motion.Fault, dt);
            if (ev.State == LiveState.Unsafe)
            {
                if (lastState != LiveState.Unsafe)
                {
                    feedback.PlayWarning();
                    Subtitles.Say($"STOP. You went past the safe limit of {ex.safetyMax:0}°. Lower slowly.", 3f, "Warning tone");
                }
                repMessageTimer = 0f;   // the STOP warning always shows right away
            }
            else if (ev.State == LiveState.Resting && lastState != LiveState.Resting)
                Subtitles.Say($"Set {ev.SetNumber - 1} of {ev.Sets} done. Rest for {ex.restSeconds:0} seconds.", 3f, "Coach");
            lastState = ev.State;
            if (repMessageTimer > 0f) repMessageTimer -= dt;
            else if (!motion.HasReading && !ev.Resting)
                hud.SetFeedback($"Step into view so your {ex.joint.ToLower()} is visible", Tone.Warn);
            else
            {
                var (msg, tone) = FeedbackManager.LiveMessage(ev, motion.Fault);
                hud.SetFeedback(msg, tone);
            }
        }

        void UpdateSourceText()
        {
            string status;
            if (motion.source == InputSource.Webcam && receiver.Problem != null)
                status = $"<color={UIKit.HexBad}>●</color> {receiver.Problem}";
            else if (GameSettings.ShowDetails)
            {
                if (motion.source == InputSource.Webcam)
                    status = receiver.IsReceiving
                        ? $"<color={UIKit.HexGood}>● Tracker</color> {receiver.PacketsPerSecond:0} fps · side {motion.MeasuredSide}"
                        : $"<color={UIKit.HexBad}>● No tracker data</color>: run tracker.py";
                else status = $"Input: {motion.SourceLabel}";
                status += head != null && head.HeadsetActive ? " · headset on" : " · desktop view";
            }
            else if (motion.source == InputSource.Webcam)
                status = receiver.IsReceiving ? $"<color={UIKit.HexGood}>●</color> Camera is watching. You're good to go!"
                                              : $"<color={UIKit.HexBad}>●</color> Camera can't see you yet. Ask for help.";
            else if (motion.source == InputSource.Keyboard)
                status = $"<color={UIKit.HexWarn}>●</color> Practice: move with {Keys.Angle}";
            else
                status = $"<color={UIKit.HexPurple}>●</color> Demo: the game plays by itself";
            hud.SetSource(status);
        }

        // ------------------------------------------------------------- session flow
        void BeginSession()
        {
            evaluators.Clear();
            foreach (var e in program.exercises)
            {
                var ev = new ExerciseEvaluator(e);
                ev.RepCompleted += OnRep;
                ev.HoldCompleted += OnHoldDone;
                evaluators.Add(ev);
            }
            index = 0;
            celebrateTimer = 0f;
            countdown.Cancel();
            game = new GamificationManager(program.patient.badges);
            game.BadgeUnlocked += code =>
            {
                feedback.PlayBadge();
                ShowRepMessage("Badge unlocked: " + GamificationManager.BadgeNames[code], Tone.Good, 2f);
                Subtitles.Say("Badge unlocked: " + GamificationManager.BadgeNames[code], 2.5f, "Badge chime");
            };
            startedAt = DateTime.Now;
            sessionUuid = Guid.NewGuid().ToString();
            sessionSource = motion.SourceLabel;   // locked for the whole session
            phase = Phase.Running;
            hud.SetQuest(program.exercises, evaluators, index, true);
            PrepareExercise();
        }

        void PrepareExercise(bool restarted = false)
        {
            awaitingReady = true;
            autoReadyTimer = 2.5f;
            repMessageTimer = 0f;
            lastState = LiveState.Idle;
            countdown.Cancel();
            var ex = Current;
            string intro = restarted ? $"Starting {ex.name} again from set 1. Your earlier tries are still saved for your therapist."
                                     : $"{(index > 0 ? "Next: " : "")}{ex.name}.";
            Subtitles.Say($"{intro} {ex.position}. Put the camera {ex.CameraText}, then press {Keys.Start}.", 5f, "Coach");
        }

        /// <summary>The short "exercise complete" moment between exercises (M5.4).</summary>
        void CelebrateExercise(ExerciseEvaluator done)
        {
            celebrateTimer = CelebrateSeconds;
            feedback.PlayHoldComplete();
            hud.Pop("★ EXERCISE COMPLETE ★", true);
            var next = program.exercises[index + 1];
            string acc = GameSettings.ShowDetails && done.Accuracies.Count > 0 ? $" · {Average(done.Accuracies):0}% accuracy" : "";
            hud.SetFeedback($"{done.Exercise.name} complete!\n<size=34>{done.ValidReps} good reps{acc} · Up next: {next.name}</size>", Tone.Good);
            Subtitles.Say($"{done.Exercise.name} complete! Up next: {next.name}.", 3f, "Chime");
        }

        static float Average(List<int> xs)
        {
            float sum = 0f;
            foreach (var x in xs) sum += x;
            return xs.Count > 0 ? sum / xs.Count : 0f;
        }

        void OnRep(RepResult r)
        {
            var ev = CurrentEval;
            int pts = game.ScoreRep(r);
            feedback.PlayRep(r);
            string extra = r.valid && game.Combo > 1 ? $"  ×{game.Multiplier:0.0}" : "";
            hud.Pop($"+{pts}{extra}", r.valid);
            string line;
            switch (FeedbackManager.Grade(r))
            {
                case FeedbackManager.RepGrade.Perfect: line = "Perfect!" + Pct(r); ShowRepMessage(line, Tone.Good, 1.2f); break;
                case FeedbackManager.RepGrade.Awesome: line = "Awesome!" + Pct(r); ShowRepMessage(line, Tone.Good, 1.2f); break;
                case FeedbackManager.RepGrade.Great: line = "Great job!" + Pct(r); ShowRepMessage(line, Tone.Good, 1.2f); break;
                default:
                    line = "Oops! " + (GameSettings.ShowDetails ? ev.Describe(r) : ev.Friendly(r));
                    ShowRepMessage(line, Tone.Bad, 1.8f);
                    break;
            }
            Subtitles.Say(line, r.valid ? 1.6f : 2.6f, FeedbackManager.RepSoundName(r));

            if (ev.Done)
            {
                if (index < evaluators.Count - 1) CelebrateExercise(ev);
                else FinishSession(endedEarly: false);
            }
            hud.SetQuest(program.exercises, evaluators, index, phase == Phase.Running);
        }

        void OnHoldDone(float holdTime)
        {
            feedback.PlayHoldComplete();
            hud.Pop("★ HOLD COMPLETE! ★", true);
            Subtitles.Say("Hold complete! Return to start position.", 2f, "Chime");
        }

        static string Pct(RepResult r) => GameSettings.ShowDetails ? $" {r.accuracy}%" : "";

        void ShowRepMessage(string text, Tone tone, float seconds)
        {
            hud.SetFeedback(text, tone);
            repMessageTimer = seconds;
        }

        /// <summary>Scores the session and uploads it.</summary>
        SessionUpload BuildUpload(bool endedEarly, bool completed, out float avgAcc, out float avgErr,
                                  out int valid, out int attempts, out int unsafeReps)
        {
            var upload = new SessionUpload
            {
                patient_id = program.patient.id,
                patient_code = api.Code,
                session_uuid = sessionUuid,
                started_at = startedAt.ToString("yyyy-MM-ddTHH:mm:ss", System.Globalization.CultureInfo.InvariantCulture),
                ended_at = DateTime.Now.ToString("yyyy-MM-ddTHH:mm:ss", System.Globalization.CultureInfo.InvariantCulture),
                ended_early = endedEarly,
                input_source = sessionSource,
                points = game.Points,
                badges_earned = new List<string>(game.EarnedThisSession)
            };
            float accSum = 0; int accN = 0; float errSum = 0;
            valid = 0; attempts = 0; unsafeReps = 0;
            foreach (var e in evaluators)
            {
                upload.exercises.Add(e.ToResult());
                upload.rep_events.AddRange(e.RepEvents);
                foreach (var a in e.Accuracies) { accSum += a; accN++; }
                foreach (var x in e.Errors) errSum += x;
                valid += e.ValidReps; attempts += e.Attempts; unsafeReps += e.UnsafeReps;
            }
            avgAcc = accN > 0 ? accSum / accN : 0f;
            avgErr = accN > 0 ? errSum / accN : 0f;
            upload.stars = GamificationManager.Stars(avgAcc, completed);
            return upload;
        }

        void FinishSession(bool endedEarly)
        {
            phase = Phase.Uploading;
            bool allDone = true;
            foreach (var e in evaluators) allDone &= e.Done;
            bool completed = !endedEarly && allDone;
            if (completed) game.AddCompletionBonus();

            var upload = BuildUpload(endedEarly, completed, out float avgAcc, out float avgErr,
                                     out int valid, out int attempts, out int unsafeReps);

            hud.SetFeedback("Saving session…", Tone.Neutral);
            StartCoroutine(api.UploadSession(upload, resp =>
            {
                var sb = new StringBuilder();
                sb.AppendLine($"<color={UIKit.HexGood}>✓</color>  <b>{valid}</b> good reps");
                sb.AppendLine($"<color={UIKit.HexGold}>★</color>  <b>{game.Points}</b> points" + (completed ? $"  (+{GamificationManager.CompletionBonus} bonus!)" : ""));
                if (GameSettings.ShowDetails)
                    sb.AppendLine($"<color={UIKit.HexMuted}>{valid}/{attempts} valid · accuracy {avgAcc:0}% · mean error {avgErr:0.0}°</color>");
                if (unsafeReps > 0) sb.AppendLine($"<color={UIKit.HexBad}>!</color>  {unsafeReps} reps went too far. Remember the STOP line.");
                sb.AppendLine();
                if (resp != null)
                {
                    bool levelUp = false;
                    foreach (var n in resp.notes) { sb.AppendLine($"<color={UIKit.HexPurple}>♦</color>  {n}"); levelUp |= n.StartsWith("Level up"); }
                    if (levelUp) { feedback.PlayLevelUp(); Subtitles.Say("Level up!", 2.5f, "Level-up jingle"); }
                    program.patient = resp.patient;
                    hud.SetPatient(resp.patient, program.program, true, program.phase);
                    sb.AppendLine("\nSaved! Your therapist can see how you did.");
                }
                else
                {
                    foreach (var b in game.EarnedThisSession) sb.AppendLine($"<color={UIKit.HexPurple}>♦</color>  Badge: " + GamificationManager.BadgeNames[b]);
                    sb.AppendLine("\nSaved on this computer. It will be sent to your therapist later.");
                }
                sb.AppendLine("Tell your therapist how you feel after today's session.");
                sb.AppendLine($"\n<color={UIKit.HexMuted}>Press {Keys.Start} to continue</color>");
                if (completed)
                {
                    feedback.PlayVictory();
                    Subtitles.Say("Quest cleared! Great work today.", 3f, "Victory fanfare");
                }
                else Subtitles.Say("Session ended. Your progress is saved.", 3f);
                hud.ShowSummary(completed ? "Quest cleared!" : "Good effort!", upload.stars, sb.ToString());
                hud.SetFeedback(completed ? "Great work today" : "Session ended early", Tone.Neutral);
                phase = Phase.Summary;
            }));
        }
    }
}
