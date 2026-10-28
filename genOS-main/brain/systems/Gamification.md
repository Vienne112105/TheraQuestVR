# Gamification

## Purpose
Maintains patient motivation and adherence through real-time feedback loops, scoring mechanics, achievement badges, streak multipliers, and player level progression.

## Status
`stable` (M5.5 and M5.6 done; human checks passed 2026-10-28)

## Responsibilities
- Calculate real-time repetition points based on accuracy and consecutive combo multipliers: `Points = 10 * accuracy * combo` (range x1.0 to x2.0).
- Award bonus points (+50 XP) upon full session completion.
- Evaluate session performance star ratings (3 stars for ≥90% accuracy, 2 stars for ≥75%, 1 star otherwise, 0 for early termination).
- Track player experience points (XP) and level-ups (Level 2 at 100 XP, +60 XP per subsequent level).
- Play affirmative audio chimes ("Awesome", "Great", "Perfect", "Victory") and trigger celebratory particle/HUD effects.
- Award achievement badges based on performance streaks and milestones.

## Dependencies
- Inter-system: Subscribes to rep and session completion events from `ExerciseEvaluation` and `SessionOrchestration`.

## Runtime References
- `Main/TheraQuestVR/unity/Assets/TheraQuest/Scripts/GamificationManager.cs`: Score calculation, combo counters, XP persistence, and badge unlock logic.
- `Main/TheraQuestVR/unity/Assets/TheraQuest/Scripts/FeedbackManager.cs`: Audio cue management and motivational banner triggers.
- `Main/TheraQuestVR/unity/Assets/TheraQuest/Scripts/MusicPlayer.cs`: Background music: shuffled lo-fi playlist from `Resources/Music`, generated ambient loop as fallback.
- `Main/TheraQuestVR/unity/Assets/TheraQuest/Resources/` (`Audio`, `Music`, `Badges`): M5.6 assets (sources and licences in `Assets/TheraQuest/CREDITS.md`); badge icons via `UIKit.BadgeIcon` / `UIKit.BadgeTag`.
- `Main/TheraQuestVR/unity/Assets/TheraQuest/*.mp3`: Audio asset clips ("Awesome sound", "great sound", "miss sound", "Perfect sound", "victory sound").

## Invariants
- Badges and player XP progression must persist locally between workout sessions.
- Incomplete sessions terminated prematurely award 0 stars.
- Earned and locked badges must look different (earned gold, locked grey), wherever badges are shown.
- Every sound, music track and icon keeps a working fallback when its file is missing (DEC-015), and every third-party asset is credited with a verifiable licence.

## Notes
- Gamification mechanics are balanced to reward accuracy and consistency over rapid movement velocity to prevent patient injury.

## Future Changes
- Daily quest streaks and unlockable clinic cosmetics/environments.
- Therapist-customizable reward profiles.
