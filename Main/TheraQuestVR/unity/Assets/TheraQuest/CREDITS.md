# Third-party assets

Every asset that is not made in this project is listed here with its source and licence (M5.6 rule).
The licence text sits next to the files. Everything listed under M5.6 was downloaded on 2026-10-26 and chosen by
the human from previews (fonts, music, hold sound, badge-chime reverb, badge icons).

## Fonts (`Resources/Fonts`)

| File | Font | Source | Licence |
|------|------|--------|---------|
| `LuckiestGuy-Regular.ttf` | Luckiest Guy, by Astigmatic | Google Fonts (fonts.google.com/specimen/Luckiest+Guy) | Apache License 2.0 (`LuckiestGuy-LICENSE.txt`) |
| `Nunito-SemiBold.ttf`, `Nunito-ExtraBold.ttf` | Nunito, by The Nunito Project Authors | Google Fonts (fonts.google.com/specimen/Nunito) | SIL Open Font License 1.1 (`Nunito-OFL.txt`) |
| `DejaVuSans-Bold.ttf` | DejaVu Sans Bold 2.37, by the DejaVu fonts team (based on Bitstream Vera) | github.com/dejavu-fonts/dejavu-fonts/releases/tag/version_2_37 (`dejavu-fonts-ttf-2.37.zip`) | Bitstream Vera Fonts licence + Arev Fonts licence, DejaVu changes public domain (`DejaVu-LICENSE.txt`) |

Used by `UIKit`: Luckiest Guy for text 44 px and larger (headings, numbers, rewards), Nunito for the rest.
DejaVu Sans Bold only supplies symbols the other two fonts lack (★ ✓ ▶ ◀ ● ☺ ↑ ↓), as a TextMeshPro fallback.

TextMeshPro's own essentials (`Assets/TextMesh Pro`, including Liberation Sans under the SIL OFL 1.1,
`TextMesh Pro/Fonts/LiberationSans - OFL.txt`) come from Unity's `com.unity.ugui` package (Unity Companion License).

## Music (`Resources/Music`)

Background music, played as a shuffled playlist by `MusicPlayer` (the generated ambient loop is the fallback).

| File | Track | Author | Source | Licence |
|------|-------|--------|--------|---------|
| `omfgdude - Lofi Hip Hop Loop.ogg` | Lofi Hip Hop Loop | omfgdude (OMF-Games) | opengameart.org/content/lofi-hip-hop-loop | CC0 1.0 (`omfgdude-LICENSE.txt`) |
| `omfgdude - Lofi Again.ogg` | Lofi Again | omfgdude | opengameart.org/content/lofi-again | CC0 1.0 (`omfgdude-LICENSE.txt`) |
| `omfgdude - Chill Lofi Inspired.mp3` | Chill lofi inspired | omfgdude | opengameart.org/content/chill-lofi-inspired | CC0 1.0 (`omfgdude-LICENSE.txt`) |
| `Holizna - City In The Rearview.ogg`, `Holizna - Families.ogg`, `Holizna - Opinions.ogg`, `Holizna - Old Age.ogg`, `Holizna - Dream Pop.ogg`, `Holizna - Autumn.ogg` | six tracks from the Chill Beats collection | Holizna | opengameart.org/content/chill-beats-collection (`chill_beats.zip`) | CC0 1.0 (`Holizna-LICENSE.txt`) |

## Sound effects

| File | Used for | Source | Licence |
|------|----------|--------|---------|
| `Resources/Audio/HoldComplete.ogg` | hold complete | `confirmation_002.ogg` from Kenney "Interface Sounds" 1.0, kenney.nl/assets/interface-sounds | CC0 1.0 (`Resources/Audio/Kenney-InterfaceSounds-License.txt`) |

Menu click, STOP warning, level up and badge unlocked stay generated in code (`FeedbackManager`, human choice);
the badge chime has a generated reverb tail.

The rep sounds in `Assets/TheraQuest` (`miss sound.mp3`, `great sound.mp3`, `Awesome sound.mp3`, `Perfect sound.mp3`,
`victory sound.mp3`) were in the project before M5.6; their source and licence are not recorded yet (see below).

## Badge icons (`Resources/Badges`)

`BadgeSheet.png` holds one 128 px white icon per badge (tinted gold when earned, grey when locked);
`BadgeSprites.asset` maps the same cells for icons inside TextMeshPro text.

| Badge | Icon | Source | Licence |
|-------|------|--------|---------|
| First steps (`first`) | `flag_triangle.png` | Kenney "Board Game Icons" 1.1, kenney.nl/assets/board-game-icons | CC0 1.0 (`Kenney-BoardGameIcons-License.txt`) |
| Perfect form (`perfect`) | `award.png` | Kenney "Board Game Icons" 1.1 | CC0 1.0 |
| Combo 10 (`combo10`) | `exploding.png` | Kenney "Board Game Icons" 1.1 | CC0 1.0 |
| Bullseye (`fullrom`) | `target.png` (White/2x) | Kenney "Game Icons", kenney.nl/assets/game-icons | CC0 1.0 (`Kenney-GameIcons-License.txt`) |
| On a roll (`streak3`) | `fire.png` | Kenney "Board Game Icons" 1.1 | CC0 1.0 |
| Consistent (`adh80`) | `checkmark.png` (White/2x) | Kenney "Game Icons" | CC0 1.0 |
| Level 5 (`lv5`) | `crown_a.png` | Kenney "Board Game Icons" 1.1 | CC0 1.0 |

The icons were trimmed, scaled to fit a 128 px cell and recoloured white so the game can tint them.

## Logo icon (`Resources/Icons`)

| File | Used for | Source | Licence |
|------|----------|--------|---------|
| `Headset.png` | VR headset logo beside the game name on the main menu | the `vr-cardboard` glyph (U+F729) of Font Awesome Free 6.7.2 `fa-solid-900.ttf` by Fonticons, Inc., github.com/FortAwesome/Font-Awesome (6.x branch, `webfonts/`), rendered to a 256 px white PNG the game tints | SIL Open Font License 1.1, which Font Awesome applies to its font files (`FontAwesome-LICENSE.txt`; the same icon as SVG is CC BY 4.0). Downloaded 2026-10-26 |

## Coach models (`Assets/LuceedStudio`)

| Files | Source | Licence |
|-------|--------|---------|
| `Free Woman Tall.prefab`, `Free Man Tall.prefab` (and the rest of the pack, kept as imported) | "Little Guys - Free Sample" by Luceed Studio, Unity Asset Store, imported by the human through Package Manager > My Assets on 2026-10-27 | Standard Unity Asset Store EULA (no licence file in the pack) |

The coach since 2026-10-27 (human request). The pack's own URP material is used as imported (M8.1, DEC-028).

| Files | Source | Licence |
|-------|--------|---------|
| `Resources/CoachTextures/coach_woman.png`, `coach_man.png` | Repaint of the pack's `T_FreeWoman.png` and `T_FreeMan.png` (white top and teal shorts or trousers; the face, eyes and hair are exactly the pack's, because they share picture cells with the clothes), made with a script on 2026-11-14 (M8.2, human choice "C"; first version wrongly closed both coaches' eyes, fixed the same day). A derivative of the Little Guys textures, loaded by `CoachReskin` onto a copy of the material; a missing file keeps the pack's original look. | Same as the pack (Asset Store EULA) |
`Resources/CoachAvatars/Free Woman Tall.asset` and `Free Man Tall.asset` are Humanoid avatars made in this project
from the pack's models straightened to a T-pose (`TheraQuest > Build Coach T-Pose Avatars`), so the idle clips play upright.

## Room decorations and exercise props (`Resources/Room`)

Chosen by the human from previews on 2026-10-27; built into the room by `ClinicRoom` and `PropBuilder` at runtime.

| Files | Source | Licence |
|-------|--------|---------|
| `Gym/`: `treadmill`, `rowing_machine`, `wall_mirror`, `exercise_ball`, `medicine_ball`, `yoga_mat_rolled`, `foam_roller`, `dumbbell_rack`, `weight_tree`, `weight_plate_stack`, `dumbbell`, `gym_towel_bench`, `resistance_band`, `water_bottle` (FBX) | "Low Poly Gym Pack" v1.0 by reodesuxz, reodesuxz.itch.io/low-poly-gym-pack (free download, `LowPolyGymPack_v1.0.zip`, downloaded by the human 2026-10-27) | Pack licence (`Gym/LowPolyGymPack-LICENSE.txt`): free for personal and commercial projects, no attribution required; the files must not be resold or redistributed as standalone assets, so keep this repository private or strip them before sharing it |
| `Furniture/`: `chairCushion` (the seated-exercise chair), `loungeSofa`, `pottedPlant`, `plantSmall2`, `lampRoundFloor`, `lampSquareCeiling`, `bookcaseOpen`, `books`, `sideTable`, `coatRackStanding`, `trashcan`, `radio` (FBX) | Kenney "Furniture Kit" 2.0, kenney.nl/assets/furniture-kit (`kenney_furniture-kit.zip`, downloaded 2026-10-27) | CC0 1.0 (`Furniture/Kenney-FurnitureKit-License.txt`) |

## Coach animation (`Resources/CoachAnimations`)

| File | Source | Licence |
|------|--------|---------|
| `Idle_Loop.anim` | the `Idle_Loop` clip of Quaternius' "Universal Animation Library" (Standard), opengameart.org/content/universal-animation-library (`universal_animation_librarystandard.zip`, Unity FBX), also at quaternius.com/packs/universalanimationlibrary.html | CC0 1.0 (`Idle_Loop-LICENSE.txt`) |
| `Idle_Talking_Loop.anim` | the `Idle_Talking_Loop` clip of the same library and download (re-downloaded 2026-10-27); the coach gestures with it while it speaks | CC0 1.0 (`Idle_Loop-LICENSE.txt`) |

Imported as a Humanoid clip (loop on, root baked in place) and saved on its own; the rest of the library is not in the project.

## Not yet recorded

Assets that were in the project before M5.6 and whose source the human still has to confirm:
the five rep sounds above. (The older coach models in `Coaches/FBX-Female` and `Coaches/FBX-male` were removed on
2026-10-27; the coaches are the Little Guys.)
