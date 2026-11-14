# M8 — Visual & UX Polish (plan, 2026-11-14)

Status: **approved by the human on 2026-11-14** ("Approve M8"). M8 and its children are in
`genOS-main/brain/50_ROADMAP.md` (the authority for criteria and status); M8 and M8.1 are `active` and
`20_PROGRESS.yaml → current_milestone` is `M8.1`. DEC-028 is recorded.

**Objective:** Make the game look and feel finished, and make the therapist app clearer to read at a glance, before
the study and the hardware run (HW). The game moves to the Universal Render Pipeline (URP), which `00_PROJECT.md`
already names. The room, feedback, hologram and menus get a visual pass. The dashboard gets a visual refresh and
shows data the server already sends.

**Human choices at kickoff (2026-11-14):**
- Renderer: switch to URP first, then polish.
- Game scope: room look, feedback motion, hologram and coach window, menus and summary.
- Dashboard: visual refresh plus the hidden data (14-day adherence calendar, phase history, per-exercise stats).
- Assets: Claude picks candidates (CC0 or licensed) or generates them; the human chooses from previews. Every chosen
  asset is credited in `Assets/TheraQuest/CREDITS.md` with its licence, and has a fallback when missing (DEC-015).

**Governing agent rules (persona gate):**
- `unity-shader-graph-artist`: in URP, never use Built-in shaders (use URP Lit/Unlit or custom URP HLSL with
  `TEXTURE2D`/`CBUFFER_START` macros); prefer alpha clip to alpha blend where quality allows; check every new
  shader in the Frame Debugger and profiler against a budget; document every exposed parameter.
- `level-designer`: use lighting, colour and geometry to guide attention (the exercise spot and coach window are the
  "critical path"); record each layout or lighting change with before and after screenshots.
- `xr-interface-architect`: comfort first. UI stays in the comfortable field of view, nothing moves the headset view,
  and no full-view flashes. Every effect has a non-motion fallback.
- `unity-architect` / `ponytail`: reuse the one place that already owns each concern (`UIKit` for colours, fonts and
  panels; `ClinicRoom` for the room; `FirstPersonGuide` for limbs). No new packages besides URP (already installed),
  no dark mode, no new game screens, and no therapist detail added to patient screens (keep them short).

**Comfort rules for every child (VR):** no motion blur, vignette, chromatic aberration, film grain, depth of field
or camera shake. UI transitions are 0.25 s or shorter and only fade or scale the panel, never the view. Effects stay
small and near the limb or panel they belong to. Red stays for safety only (DEC-016).

**Test suites (all must stay green):** `python run_tests.py` in `Main/TheraQuestVR` (runner, server, tracker,
evaluation and Unity EditMode). Baseline 2026-11-12: 308 passed. The Unity suite is skipped while the Editor has the
project open, so run it from the Editor's Test Runner or with the Editor closed.

**Track order:** the game track (M8.1 → M8.2 → M8.4, then M8.3 → M8.5) and the dashboard track (M8.6 → M8.7) share no
files, so they can run in parallel sessions. Within a track, run children one at a time: M8.3 and M8.5 both edit
`UIKit.cs`, and M8.6 and M8.7 both edit `dashboard.html`.

---

## M8.1 — URP Migration

**Objective:** Render the game with URP and look at least as good as now, with nothing pink and no frame-rate loss.

Write the failing EditMode tests first:
1. `GraphicsSettings.defaultRenderPipeline` and every quality level use the project's URP asset.
2. Every material under `Assets/TheraQuest` (including `Resources/Room`, coach and Little Guys materials) uses a URP
   or TextMeshPro shader, never `Standard`, `Legacy Shaders/*` or a Built-in custom shader.
3. Materials made at runtime (`ClinicRoom.Mat`, the coach material, the hologram) use a URP shader. Find these
   through one helper, so the test can call it.
4. The Hologram shader compiles under URP (`Shader.Find` is not null and `isSupported`).

Then:
- Create `Assets/TheraQuest/Settings/URP` with one pipeline asset and one Forward renderer (MSAA 4x, HDR on, soft
  shadows, SSAO off until M8.2). Assign it in Graphics and in every Quality level.
- Convert the imported model materials with the Render Pipeline Converter (Built-in to URP).
- Port `Resources/Shaders/Hologram.shader` to URP HLSL (same look; the visual rework is M8.4).
- `HumanoidCoach` stops swapping the Little Guys material for `Standard`. The pack's own URP material is used, which
  closes the known issue in `20_PROGRESS.yaml`.
- Room primitives use URP Lit. The coach window and side-mirror render textures keep 4x anti-aliasing.
- Run XR Plug-in Management with OpenXR under URP once (`TheraQuest → Set Up OpenXR`). Note it for HW.2, because no
  headset is available here.
- Record DEC-028 (switch to URP). Remove the URP known issue from `20_PROGRESS.yaml`.

**Completion criteria:** the tests above pass; the full suite is green; Play mode shows the menu, get-ready, an exercise
(each of the four postures), the summary and the Progress page with no pink or missing materials, compared with
before screenshots; average frame time on this PC is not worse than the Built-in baseline measured at the start.

## M8.2 — Clinic Room Look

**Objective:** A calm, bright clinic whose lighting draws the eye to the exercise spot and coach window.

- Before screenshots from three fixed viewpoints (patient eye standing, seated, lying), kept for comparison.
- Lighting: one soft directional "sun" through the windows with soft shadows; warm lamp points kept; gradient or
  skybox ambient; one reflection probe rendered once after `ClinicRoom` builds the room (the room is built at runtime,
  so nothing is baked).
- Materials: floor, walls and ceiling with textures (2 to 3 candidate sets each, CC0 or generated, chosen by the
  human), keeping the current colours as the fallback.
- One URP Volume: neutral tonemapping, gentle colour grading, light bloom, SSAO. Nothing from the banned list above.
- The exercise spot marker and yoga mat read clearly against the new floor.
- Performance budget: frame time on this PC within 10% of the M8.1 result. Check in the profiler.

**Completion criteria:** before and after screenshots from the three viewpoints are approved by the human; frame-time
budget met; the full suite is green; the room still builds with every texture missing (fallback colours).

## M8.3 — Feedback Motion

**Objective:** Make every important moment feel responsive without hurting comfort.

- One small `UIKit` helper to fade or scale a panel in or out (0.15 to 0.25 s, unscaled time). Used by menus, HUD
  cards, pop-ups, the summary and the Progress page.
- Small effects (CC0 or generated sprites, chosen by the human): a burst at the live limb on a good rep, a ring that
  fills during a hold and pops on hold complete, a level-up and badge reveal effect on the summary. Combo streaks get a
  subtle pulse on the HUD.
- A posture fault or STOP gets no celebration. It keeps its red, instant, non-animated warning.
- Each effect falls back to the current static look when its asset is missing.

Tests first (EditMode): transition durations stay within 0.25 s and end in the final state when skipped; a STOP or
unsafe rep never triggers a reward effect; effects are created only for counted events.

**Completion criteria:** tests pass; the full suite is green; Play-mode recording or screenshots of each moment checked
by the human.

## M8.4 — Hologram & Coach Window

**Objective:** The target limb, live limb and coach window are the clearest things in view.

- Rework the URP hologram: fresnel rim, soft inner fill, alpha clip where possible, one colour for the target and one
  for the live limb from the palette, and a gentle glow when the live limb is inside tolerance (no flicker).
- Coach window: framed panel in `UIKit` style with a soft backdrop behind the coach, and restyled arrows and word guides
  (larger, outlined, same palette). The side-mirror panel gets the same frame.
- Check at the default heights for all four postures, including lying and side-lying (the hardest to read).
- Document every exposed shader parameter. Check the shader in the Frame Debugger.

Tests first (EditMode): the in-tolerance state switches the material property only when the evaluator says the angle
is within tolerance; the window and mirror frames stay inside the comfortable field-of-view limits in
`VRClinicExperience`.

**Completion criteria:** tests pass; the full suite is green; human approves before and after screenshots per posture.

## M8.5 — Menus & Summary Polish

**Objective:** Consistent, tidy menus that stay short.

- Spacing and type-size scale in `UIKit` (a few named sizes and gaps), used by the main menu, Settings, Progress page
  tabs and the summary.
- One card and one button style with clear hover, focus and pressed states for mouse, keyboard and controller.
- Summary and Progress page: clearer hierarchy (one headline number, then details) without adding content.
- Re-check the HUD and menu distances and scale against the invariants (1.35 m menus, 1.45 m HUD).

Tests first (EditMode): every button has distinct normal, highlighted, pressed and selected colours; menu pages fit their
panel at the smallest text preset.

**Completion criteria:** tests pass; the full suite is green; human Play-mode check of every menu page and the summary.

---

## M8.6 — Dashboard Visual Refresh

**Objective:** The therapist sees what matters for a patient at a glance.

- Type and spacing scale in the `:root` tokens; one consistent button, card and table style.
- Patient chart header: code, name, protocol and phase, adherence rate, last session and attention flags in one row.
- Caseload table: clearer flag chips, row hover and focus, sticky header.
- Chart.js styling from tokens (`cssVar()`), consistent axes, tooltips and empty states.
- Keep every M5.1 rule: keyboard use, dialogs, status not by colour alone, fits 980 × 640, no external fonts or
  unpinned CDN URLs, `esc()` on every API value.
- Before and after screenshots of the login, caseload, chart (three sub-tabs) and main dialogs, on a throwaway
  database with test data (never the live database).

**Completion criteria:** server tests pass; browser check at 980 × 640 and full size with no horizontal scroll and no
console errors; the therapist exe is rebuilt; human walkthrough in the desktop app.

## M8.7 — Dashboard Hidden Data

**Objective:** Show the data the server already sends but the page hides.

- 14-day adherence calendar (Complete / Incomplete / Missed, with text or icon and not colour alone) on the Activity tab.
- Phase history timeline (phase, start date, who approved).
- Per-exercise stats table (sessions, average accuracy, best, unsafe reps), counted sessions only (M7.1).
- Empty, loading and error states for each.

Tests first (`server/test_backend.py`): add tests only if the payload needs a change. Confirm the existing dashboard
endpoint already returns all three, and that the per-exercise stats use counted sources only.

**Completion criteria:** server tests pass; browser check on the throwaway database with a patient who has no sessions,
one with missed days, and one with a phase change; the exe is rebuilt; human walkthrough in the desktop app.

---

**Systems:** VRClinicExperience, AvatarCoach, Gamification, TherapistDashboard.
**Dependencies:** M5, M7. M8 does not need hardware. HW.2 should later confirm URP in the headset.
**Done when:** all seven children are done (human checks passed).
