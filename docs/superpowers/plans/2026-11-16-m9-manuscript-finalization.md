# M9 — Manuscript Finalization & Polish

## Context

The capstone manuscript (`Research/THERAQUEST- MANUSCRIPT.md`, about 21,800 words, Chapters 1 to 3 plus references, dated April 2026, last exported 9 October) was written before most of the system was built. The human asked on 2026-11-16 for a new milestone to finalize and polish its **existing** content. No new chapters are written.

Human decisions (2026-11-16):

- Scope: language and flow edit, sync with the built system, figures and screenshots. **Section 3.9 (Data Analysis) numbers and metrics are out of scope.**
- M9 becomes the current milestone. M8 stays `active` in the roadmap with M8.2 and M8.6 still `TBF` and M8.3, M8.4, M8.5, M8.7 `planned`.
- **The master copy is a Google Doc / Word file.** The repo `.md` is a working copy. Every edit must also be delivered as a change list the human can apply to the master by hand.
- Review is **by chapter**: one diff and one change list per chapter.

## What the first read found (seeds for the audit)

- Text that contradicts the built system:
  - "3D posture ... tracking ... directly within an HMD-based VR system" (1.1) and "consumer-level VR cameras" (1.5 Limitation 2): the system uses 2D angles from one external webcam (MediaPipe Pose).
  - "standalone VR headsets" (1.5, 3.3, Deployment phase): the system is tethered PC VR (Quest Link) with a desktop fallback; a standalone APK is out of scope in `00_PROJECT.md`.
  - "built-in VR tracking cameras or external webcams" (3.6.3 Motion Tracking Module, 3.7.1).
  - "OpenCV or MediaPipe, or any similar libraries" and an unnamed "database system" (3.7.1): it is MediaPipe Pose plus OpenCV, and SQLite.
  - Nothing on the first-person view (DEC-021), the therapist desktop app, the patient code and name rule (DEC-027), encrypted backups, or URP (DEC-028).
- Structure problems:
  - The table of contents lists 2.3.1 TAM and 2.3.2 DeLone and McLean, but the body has no such sections; body headings start at 2.3.2 Motor Learning, while the List of Figures numbers the same figures 2.3.1 to 2.3.5 and the figure files are named 2.3.4 to 2.3.7.
  - The heading for 1.2 Statement of the Problem is missing (the text is there).
  - Empty headings (`###` with no text), a paragraph formatted as a heading (3.3 Initial Planning Phase), "3.9. 4Expert", page numbers in the contents that are out of order.
  - 21 figures are listed, 15 images are embedded.
- Language: mixed tense (past "employed", future "will be"), repeated fragments such as "This study, it ...", Objective 4 still says "SUS or ISO 25010".
- Section 3.9 says the system "operates within a three-dimensional" space for Euclidean error. This is in the out-of-scope section, so it is only reported to the human, not edited.

## Rules for all M9 work

1. Research aims, objectives, benchmark targets, participants and instruments are the human's. A change to any of them is proposed in the change list and applied only after a yes.
2. No invented citations, numbers or results. A claim with no source is flagged, not fixed.
3. The 15 base64 image lines at the end of the `.md` (`[imageN]: <data:image...`) and Section 3.9 are never edited. Both are checked by hash before and after each chapter.
4. Chapter 2 literature claims about other systems (for example "cloud-based dashboards") describe the literature, not TheraQuest: language edit only.
5. Edits use the Edit tool on exact text (never a whole-file rewrite, never a shell replace).
6. Truth for the sync: `genOS-main/brain/00_PROJECT.md`, `30_DECISIONS.md`, `brain/systems/*.md` (AvatarCoach, ClinicalBackend, ExerciseEvaluation, Gamification, MotionTracking, SessionOrchestration, TherapistDashboard, VRClinicExperience), then the code (`Main/TheraQuestVR/server/server.py` schema and routes, `tracker/`, Unity scripts under `Assets/TheraQuest`).
7. Patient names never appear in a figure or screenshot (DEC-027): throwaway database, codes only.
8. Check the 5-hour usage limit at the start of each chapter and stop at 80%.

## Step 0 — Record the milestone (first thing after approval)

- Copy this plan to `docs/superpowers/plans/2026-11-16-m9-manuscript-finalization.md`.
- `genOS-main/brain/50_ROADMAP.md`: add Index rows and sections for `M9` (active) and `M9.1` (active), `M9.2`, `M9.3`, `M9.4` (planned), using the roadmap milestone template; add M9 to the suggested sequence. M8 rows unchanged.
- `genOS-main/brain/20_PROGRESS.yaml`: `current_milestone: M9.1`; add an M9 line to `working_on`; keep the two TBF lines and `pending_human_tests` as they are; set `systems_in_scope` to the systems the audit reads.
- `genOS-main/brain/30_DECISIONS.md`: new decision (next free number after DEC-028): the Google Doc / Word file is the manuscript master, the repo `.md` is a working copy, edits are delivered with per-chapter change lists, Section 3.9 is excluded from M9.
- `genOS-main/brain/60_AGENTS.md`: note that no installed agent covers academic editing; `testing-reality-checker` is used in M9.3 to check that claims match the real system. No new agent is installed.
- Create branch `m9-manuscript` from the current branch. Only `Research/`, the plan and the brain files are committed there; the human's uncommitted files (`TheraQuest.unity`, `.gitignore`, `.graphifyignore`, `.mcp.json`, `Assets/Screenshots`) and the uncommitted sign-up form are left alone.

## M9.1 — Audit (read-only on the manuscript)

- Ask the human whether the 9 October `.md` still matches the master. If the master has moved on, the human re-exports before the audit.
- Read the whole manuscript (text lines only) and write `Research/M9-audit.md`: one table per chapter with columns ID, section, quoted text, problem type (system mismatch / structure / language / figure / needs human decision), proposed action.
- Open decisions collected for the human in one list, at least:
  - tense for Chapter 3 (keep proposal future tense, or past tense now that the system is built);
  - the 2.3 numbering (were TAM and DeLone and McLean removed on purpose?);
  - the title-page date and the January to November 2026 timeline;
  - how much new system detail to add (first-person view, desktop therapist app, privacy rule);
  - which figures to redraw, keep or drop.
- **Done when:** the human has read the audit and answered the open decisions.

## M9.2 — Language and flow edit (Chapter 1, then 2, then 3)

- Per chapter: grammar, clarity, consistent terms (1.6 Definition of Terms is the reference), consistent tense as decided, headings and numbering repaired, captions matched to the List of Figures and List of Tables, table of contents entries matched to headings.
- No new claims and no meaning changes. Chapter 3 skips 3.9.
- Deliver per chapter: the edited `.md` section and `Research/M9-changes-chapter-N.md` (section, original text, new text, reason) so the human can apply it to the master.
- **Done when:** the human approves each chapter; one commit per approved chapter.

## M9.3 — Sync with the built system

- Work through the audit's system-mismatch items: 1.1, 1.3, 1.5 scope and limitations, 1.6 terms, 3.2 conceptual framework layers, 3.3 and 3.4 phases, timeline and requirements, 3.5 and 3.6 analysis, architecture and module text, 3.7.1 hardware and software, 3.7.3 testing, 3.10 ethics (RA 10173, code and name, consent, encrypted backup).
- Each change is checked against the brain and the code and appended to the same per-chapter change list with its source (DEC number, system file or code path).
- Items that change a research claim wait for the human's yes.
- **Done when:** every system-mismatch item in the audit is closed or marked "kept by the human"; human approves.

## M9.4 — Figures and screenshots

- For each figure the audit marks as not matching (candidates: use case, ERD, context and data flow diagrams, flowchart, architecture, the six module figures, class diagram, Gantt timeline): build a corrected version from the real system (ERD from the `server.py` schema, class diagram from the Unity scripts, architecture from the systems files) and save it as an image in `Research/Figures/figures/` beside the old one. The human picks keep or replace.
- Screenshots (only where the human wants them): game views from Unity Play mode and the therapist app on a throwaway database, codes only. Game screenshots are taken after the human approves the M8.2 look; if that is still pending they are marked provisional.
- Update captions, the List of Figures and the List of Tables. Because the master is a Google Doc / Word file, new images are delivered as files plus a placement list (figure number, caption, after which paragraph); the base64 lines in the `.md` are not regenerated.
- **Done when:** every figure and table label matches its list entry and the human approves the figure set.

## Completion criteria for M9

- `Research/M9-audit.md` has no open item except those the human chose to leave.
- The human approved Chapters 1, 2 and 3 and the figure set.
- Section 3.9 and the image lines are byte-identical to the start.
- A change list exists for every chapter so the master can be brought in line.

## Verification

- Before the first edit and after each chapter, in `Research/`:
  - hash of the image lines: `grep '^\[image' "THERAQUEST- MANUSCRIPT.md" | sha256sum`
  - hash of Section 3.9: `sed -n '/^## \*\*3\.9 /,/^## \*\*3\.10 /p' "THERAQUEST- MANUSCRIPT.md" | sha256sum`
  - both must be unchanged.
- Label check: every `**Figure x**` and `**Table x**` caption in the body appears once in its list with the same title, and the reverse (grep both and compare).
- Structure check: `grep -n '^#'` shows no empty headings and numbering in order; every contents entry has a heading.
- `git diff --stat` per chapter touches only `Research/` (plus brain files at shutdown).
- Each chapter's change list is spot-checked against `git diff` so nothing was edited without an entry.
- Brain Sanity Gate from `genOS-main/AGENTS.md` at shutdown.

## Sessions

One chapter per session keeps usage under the limit. Recommended: Claude Opus (Thinking: High), new session for M9.1.

```
kickoff execute the approved plan: docs/superpowers/plans/2026-11-16-m9-manuscript-finalization.md (M9.1 only)
```

Still paused and waiting on the human: M8.2 Clinic Room Look and M8.6 Dashboard Visual Refresh checks.
