# ExerciseEvaluation

## Purpose
Evaluates real-time patient kinematics against prescribed clinical rehabilitation targets, validating movement form, enforcing safety limits, and driving the repetition counting state machine.

## Status
`stable`

## Responsibilities
- Track repetition progress through a biomechanical state machine: start threshold (>60% of target), peak angle capture, and return threshold (<25%).
- Assess repetition accuracy against target angles and tolerance windows (linear scoring: 85–100% within tolerance, -3% penalty per extra degree).
- Perform compensatory posture checks to invalidate bad-form reps. The checks (metric, limit, message) come with each exercise from the server `LIBRARY` (DEC-012): trunk lean > 12° or > 35°, upper arm > 30° from the trunk, knee flexion > 15°, thigh > 20° from vertical.
- In side view, use the tracker's signed elevation for flexion / extension exercises, so a movement in the wrong direction never scores (M4.6).
- Record every rep attempt (valid or not) as a rep event uploaded with the session, the real input of the evaluation pipeline (M4.5).
- Enforce therapist-defined safety maximum angles, instantly triggering visual/auditory STOP alerts on hyperextension/overreach.
- Manage isometric hold timers and tolerance jitter windows for static endurance exercises.

## Dependencies
- `MotionTracking`: Consumes incoming joint angle streams.
- `ClinicalBackend`: Receives prescribed target angles, tolerance, safety limits, and rep/set configurations.
- Inter-system: Emits events to `Gamification` and `SessionOrchestration`.

## Runtime References
- `Main/TheraQuestVR/unity/Assets/TheraQuest/Scripts/ExerciseEvaluator.cs`: Repetition state machine, accuracy formula, safety boundary checks, and hold timing.
- `Main/TheraQuestVR/unity/Assets/TheraQuest/Scripts/MotionInput.cs`: Posture validation heuristics and keyboard/fake input bridging.
- `Main/TheraQuestVR/unity/Assets/TheraQuest/Scripts/ProgramRules.cs`: Validation and clamping of prescriptions before a session.
- `Main/TheraQuestVR/unity/Assets/TheraQuest/Tests/Editor/ExerciseEvaluatorTests.cs`: EditMode tests for rep counting, scoring, safety, hold, rest and program validation.
- `Main/TheraQuestVR/unity/Assets/TheraQuest/Scripts/DataModels.cs`: Data definitions for exercise prescriptions, performance metrics, and rep events.

## Invariants
- Every exercise passes `ProgramRules` before evaluation: exercises with no positive target are dropped; tolerance ≥ 1°, reps and sets ≥ 1, side normalized to L / R / best side (M4.3).
- An exercise repetition that breaches compensatory posture thresholds is flagged invalid and awarded minimal points (2 pts).
- Exceeding the therapist's safety maximum halts repetition accumulation and logs an unsafe rep event.
- Repetitions cannot count during set-rest periods.
- Only verified tracker readings are evaluated (DEC-022). Without one, counting pauses, the hold timer stops and the rep's peak stays what was measured; a gap over 2 s drops the open rep without counting an attempt. The tracker's estimates are for display and never reach the evaluator.
- An extension exercise scores only when the signed angle shows the limb behind the trunk; with no signed reading it has no reading at all.
- Unity holds no per-exercise rules keyed by code: posture checks, direction and pose come from the program.
- A webcam exercise counts only after the patient's resting angle is known, and scores the movement above it (DEC-026).
- A rep shorter than `ExerciseEvaluator.MinRepSeconds` is noise: no attempt and no feedback.
- Patient Lock (M10.5): while the tracker says another person has taken the patient's place (`patient: different`), and until it says the locked patient is tracked again, nothing is evaluated: the same pause as a tracking loss (`TrackingPaused`, via `PatientGate`). Reps already counted are kept, an open rep is dropped without an attempt, and nothing the other person does is scored.

## Notes
- Posture thresholds were derived from clinical physical therapy literature to avoid hip/spine substitution patterns during isolated limb exercises.

## Future Changes
- Dynamic tolerance tuning based on patient fatigue curves.
- Velocity and jerkiness (smoothness) metrics to assess motor control improvement.
