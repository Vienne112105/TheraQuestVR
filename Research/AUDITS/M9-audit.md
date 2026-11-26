# M9.1 — Manuscript Audit

- **File audited:** `Research/THERAQUEST- MANUSCRIPT.md` (export of 9 October 2026; the human confirmed on 2026-11-16 that it matches the Google Doc / Word master).
- **Date:** 2026-11-16. **Nothing in the manuscript was edited.**
- **Read:** front matter, Chapters 1, 2 and 3 (3.1 to 3.8, 3.10) and the reference list. **Section 3.9 was not audited** (out of scope, DEC-029); two things seen in passing are listed under "Reported only".
- **Line numbers** are lines of the `.md` file. To find a place in the master, search for the quoted words.
- **Checked against:** `genOS-main/brain/00_PROJECT.md`, `30_DECISIONS.md` and the code in `Main/TheraQuestVR` (tracker, server, Unity).

**Problem types:** SYS = does not match the built system · STR = structure, numbering, headings · LANG = language · CITE = citation or reference · FIG = figure or table · DEC = needs your decision first (see the list below).

**Counts:** 138 items (one, C2-15, is a no-action note) — SYS 45, LANG 34, STR 21, CITE 20, FIG 16; an item can have two types. 59 of them wait on one of the 15 decisions below.

---

## Decisions needed from you (answer these before M9.2 starts)

| ID | Question | Why it matters |
|----|----------|----------------|
| D1 | **Tense.** Keep Chapter 3 in proposal style (present and "will"), or change to past tense now that the system is built? | Chapter 3 mixes "employed", "is conducted" and "will participate". One choice is applied everywhere. |
| D2 | **Section 2.3 numbering.** The contents list 2.3.1 TAM, 2.3.2 DeLone and McLean and 2.3.3 Self-Determination Theory, but the body has none of them. Were they removed on purpose? | Decides whether the body is renumbered 2.3.1 to 2.3.4 (and the contents, List of Figures and Chapter 2 introduction are corrected) or the three sections are restored from the master. |
| D3 | **Dates.** The title page says April 2026. Section 3.4.1 says Evaluation in September and Deployment in October to November 2026. The participant evaluation and the hardware run have not happened yet. Keep the plan as written, or change it to what really happened? | Affects 3.4.1, the Gantt figure and 3.3 Deployment. |
| D4 | **Headset wording.** The text says "standalone VR headsets". The system runs on a PC with the headset tethered over Quest Link, with a desktop mode when no headset is connected. May I change the wording to that? | Also, 2.2.5 argues that tethered cabling is a barrier to home use, which now argues against your own setup. It needs a sentence that explains the choice (the PC runs the tracker and database). |
| D5 | **Tracking wording.** The text says "3D posture" tracking "within an HMD-based VR system" using "VR cameras". The system measures 2D joint angles from one external webcam (MediaPipe Pose). May I change the wording to that? | Affects 1.1, 1.5 Limitation 2, 3.6.3, 3.7.1, 3.8.1 and 3.8.3. Section 3.9 (Euclidean error in three dimensions) has the same issue but is out of scope: you decide separately. |
| D6 | **Comparison claim.** The problem statement's aim 5 says the study examines the impact "compared to conventional rehabilitation methods", and Scope 5 says it assesses "adherence improvement". The methodology has no comparison group and no before-and-after adherence measure. Keep, soften or remove? | This is a research claim: I will not change it without your yes. |
| D7 | **Adherence depth.** 3.4.2 and 3.6.3 say adherence is session-level only, with no frequency or long-term analysis. Scope 4 says "session frequency". The built dashboard shows a 14-day calendar, adherence percentage, attention flags and phase readiness. Which one should the manuscript describe? | Affects 1.5, 1.6, 3.4.2, 3.6.3 and 3.8.3. |
| D8 | **Automatic difficulty.** 2.3.4 and the Gamification Module say the system adjusts difficulty by itself. In the built system the therapist moves the patient to the next phase; the system only recommends it. Change the text to that? | Affects 2.3.4 Flow Theory and 3.6.3 Gamification Module. |
| D9 | **New detail.** How much of what was built should be added to Chapter 3: first-person view with the coach window, the therapist desktop app, the built-in clinical protocols, posture and safety-limit checks, tracking-loss safeguards? Options: none, one or two sentences each, or a short paragraph each. | The milestone is "polish existing content", so the default is one or two sentences where the current text is wrong or silent. |
| D10 | **Privacy wording.** 3.10 says "Participant identities are anonymized". The dashboard stores real names with consent, and only the patient code leaves it (DEC-027); backups are encrypted; data stays on the clinic PC (RA 10173). May I rewrite 3.10 to say that? | Ethics text is yours; I will propose exact wording in the change list. |
| D11 | **Login model.** The flowchart and use case show one login that sends the user to a Patient or Therapist path. In the built system the therapist logs in to the desktop app with a password and the patient's game loads the program by patient code. Change the text, and redraw the two figures? | Affects 3.5.1, 3.6.1 and their figures. |
| D12 | **Missing references.** Eleven sources are cited but not in the reference list (see CITE items). For each: will you supply the reference, or should the citation be removed? | I will not invent reference entries. |
| D13 | **Figures.** Which figures should be redrawn to match the built system (candidates: use case, ERD, flowchart, architecture, the six module figures, class diagram, Gantt), and do you want screenshots of the game and the therapist app added? | Scope of M9.4. |
| D14 | **Instruments.** Objective 4 says "SUS or ISO 25010"; the methodology uses SUS only. Chapter 3 also promises "user satisfaction", a "user feedback questionnaire" and an "observation checklist" that are never described as instruments. Remove the mentions, or will you describe the instruments? | Instruments are yours. |
| D15 | **"Movement Classifier".** 3.6.3 says the tracker decides which exercise the patient is doing. The built tracker does not: the exercise comes from the prescription, and the evaluator classifies each repetition as correct or incorrect. Change the text to that? | Keeps 3.6.3 in line with the confusion matrix in 3.9 (correct vs incorrect movement). |

### Answers from the human (2026-11-16)

| ID | Answer |
|----|--------|
| D1 | Present tense for the system and the method; "will" for steps that have not happened yet (participant evaluation). |
| D2 | TAM, DeLone and McLean and Self-Determination Theory were removed on purpose. Renumber the four remaining theories 2.3.1 to 2.3.4 and fix the contents, the List of Figures, the captions and the Chapter 2 introduction. |
| D3 | Update to real dates, but the dates are **not decided yet** (the only decision still open). Until they are: development phases are worded as done (January to November 2026); the evaluation and deployment dates and the title-page date are listed in the change list as "to be supplied by the human". The Gantt figure is redrawn in M9.4 once the dates exist. |
| D4 | Change to tethered Quest Link with desktop fallback everywhere, and add one sentence in 2.2.5 explaining why (the PC runs the tracker and the database). |
| D5 | Change the wording to 2D joint angles from one external webcam (1.1, Limitation 2, 3.6.3, 3.7.1, 3.8.1, 3.8.3). Section 3.9 stays untouched and is only reported. |
| D6 | Soften both: aim 5 and Scope 5 are reworded to what the study can show (how the integrated system supports adherence monitoring). Exact wording goes in the change list for the human's approval before it is applied. |
| D7 | Describe what is built: session completion plus the 14-day calendar, adherence percentage and attention flags the therapist sees. |
| D8 | Therapist-approved progression: the system recommends, the therapist approves. Rewards are XP levels, badges, stars and combo streaks. |
| D9 | One or two sentences per built feature, only where the current text is wrong or silent. |
| D10 | Rewrite 3.10: RA 10173, consent to name storage, code-only exports, encrypted backups, local storage. Exact wording goes in the change list for approval. |
| D11 | Rewrite 3.5.1 and 3.6.1 (therapist password login in the desktop app; the game loads the program by patient code) and redraw the use case diagram and the flowchart in M9.4. |
| D12 | **Remove the citations** that have no reference entry (Laver 2017, De Guzman 2024, Buckingham 2024, Yang 2023, Deterding 2011, Winstein 2014, Ebrahimi 2025, Tu 2026, Zhu 2025, Navea 2025b, Sunido & Soreño 2026), and reword any sentence left without a source so it claims less. Each removal is listed in the change list. "Schmidt & Lee, 2011" is a year mismatch with a listed entry (R6), not a missing reference: it is flagged, not removed. |
| D13 | Redraw in M9.4: the six module figures, the ERD and class diagram, the architecture and the two data flow diagrams, plus the use case diagram and flowchart (D11). **No new screenshots.** The Gantt figure waits on D3. |
| D14 | Remove the mentions: Objective 4 says SUS only; the undescribed "user feedback questionnaire", "observation checklist" and "user satisfaction" wording are removed or folded into SUS. |
| D15 | Change 3.6.3: no exercise-type classifier; the exercise comes from the prescription and each repetition is classified as correct or incorrect. |

---

## Front matter (lines 1 to 183)

| ID | Line | Section | Quoted text | Type | Proposed action |
|----|------|---------|-------------|------|-----------------|
| F1 | 15 | Title page | "April 2026" | STR, DEC D3 | Keep or update the date. |
| F2 | 8 | Title page | "Submitted to the Department of / College of Computing..." | LANG | "Department of" is followed by a college name; confirm the department name. |
| F3 | 27 | Contents | "1.2 Statement of the Problem" | STR | The body has no 1.2 heading (see C1-9). |
| F4 | 61 to 73 | Contents | 2.3.1 TAM … 2.3.7 COM-B | STR, DEC D2 | Body has four theory sections numbered 2.3.2 to 2.3.5. |
| F5 | 55 to 59 | Contents | 2.2.1 to 2.2.4 | STR | 2.2.5 System Feasibility is in the body but not in the contents. |
| F6 | 77 | Contents | "2.4.1 Research Gap and Study Positioning" | STR | No such heading in the body. Remove the entry or restore the heading. |
| F7 | 83 to 91 | Contents | "3.4 … 76", "3.4.1 … 68", "3.4.2 … 105" | STR | Page numbers out of order. Regenerate the contents in the master after the edits. |
| F8 | 95 | Contents | "Entity Relationship DIagram" | LANG | "Diagram". |
| F9 | 119, 135 | Contents | "Research Instruments", "Ethical Consideration" | STR | Body says "Research Instrument" and "Ethical Considerations". Make them the same. |
| F10 | 149 to 153 | List of Figures | Figures 2.3.1 to 2.3.5 | FIG, DEC D2 | Body captions are numbered 2.3.4 to 2.3.7 and there is no Self-Determination Theory figure. |
| F11 | 156 | List of Figures | "Project Timeline of the TheraQuest VR System" | FIG | Body caption says "Project Gantt Timeline of the Development of…". Use one title. |
| F12 | 175 | List of Tables | "Related Literature" | FIG | Body caption says "Related Literatures". Use "Literature". |

## Chapter 1 (lines 185 to 358)

| ID | Line | Section | Quoted text | Type | Proposed action |
|----|------|---------|-------------|------|-----------------|
| C1-1 | 193 | 1.1 | "(Laver et al., 2017)" | CITE, DEC D12 | Not in the reference list. Also check that the source supports "decreasing perceived pain and fatigue". |
| C1-2 | 193 | 1.1 | "has created many new doors" | LANG | "has opened new possibilities". |
| C1-3 | 195 | 1.1 | "3D posture and movement tracking … directly within an HMD-based VR system" | SYS, DEC D5 | 2D joint angles from a single external webcam. |
| C1-4 | 195 | 1.1 | "optical markers that would occlude the patient's view" | LANG | Unclear reasoning; simplify to "no markers or wearable sensors". Also "his/her" → "their". |
| C1-5 | 197 | 1.1 | "these types of game elements" | LANG | Gamification has not been introduced yet in this section; "these" points to nothing. Reword the paragraph opening and fix the stray period before the citation. |
| C1-6 | 199 | 1.1 | "more and more research about VR and rehab, there is a big gap" | LANG | Informal. "Although research on VR rehabilitation is growing, fully integrated systems remain scarce". |
| C1-7 | 201 to 205 | 1.1 | LIKHA Summit 2025; "2026–2028 research roadmap" | CITE | Three paragraphs of institutional claims with no source. Add the CSU sources or mark as institutional documents. |
| C1-8 | 201 to 207, 239, 244 | 1.1, 1.4 | LIKHA and SDG alignment | LANG | The same alignment is stated four times. Shorten the repeats (no content removed without your OK). |
| C1-9 | 209 | 1.2 | "Patient adherence to home-based physical therapy remains…" | STR | Insert the missing heading "1.2 Statement of the Problem" before this paragraph. |
| C1-10 | 211 | 1.2 | "The lack of these enabling technologies" | LANG | "these" has no referent; name the technologies. |
| C1-11 | 213 | 1.2 | "through the design, development, and evaluation of TheraQuest VR, the study aims to:" | LANG | Run-on sentence; split. |
| C1-12 | 219 | 1.2 | "compared to conventional rehabilitation methods" | DEC D6 | Research claim with no comparison in the methodology. |
| C1-13 | 213 to 235 | 1.2, 1.3 | five aims, then four objectives | STR | Two different lists of aims. Say how they relate (problems vs objectives) or align them. Your call on content. |
| C1-14 | 227 to 232 | 1.3 | "aims to: 1. To design and develop" | LANG | Doubled "to". Also remove the "○" marks in the sub-list. |
| C1-15 | 235 | 1.3 | "(e.g., SUS or ISO 25010 usability criteria)" | DEC D14 | Methodology uses SUS only. |
| C1-16 | 242 | 1.4 | "enabling therapists to monitor patients remotely" | SYS | The dashboard is a local desktop app on the clinic PC. Reword to "review recorded sessions without being present during the exercise" (matches 1.6 Remote Monitoring). |
| C1-17 | 265 | 1.5 Scope | "Wellness Monitoring and Analytics" | LANG | The term used everywhere else is "Adherence Monitoring". |
| C1-18 | 265 | 1.5 Scope | "session frequency" | SYS, DEC D7 | Contradicts 3.4.2 ("rather than … frequency analysis"). |
| C1-19 | 267 | 1.5 Scope | "adherence improvement" | DEC D6 | Not measured by any instrument in Chapter 3. |
| C1-20 | 269 | 1.5 Scope | "Evaluation will involve" | LANG, DEC D1 | Tense. |
| C1-21 | 275 | 1.5 Limitations | "standalone VR headsets like the Meta Quest" | SYS, DEC D4 | Tethered PC VR over Quest Link, desktop fallback. |
| C1-22 | 276 | 1.5 Limitations | "depends on consumer-level VR cameras" | SYS, DEC D5 | Depends on a consumer webcam and its placement (side view or front view per exercise). |
| C1-23 | 277 to 281 | 1.5 Limitations | (missing) | SYS, DEC D9 | Real limits not stated: one camera measures movement in one plane only; exercises that cannot be seen by the camera are done untracked; the patient must be cleared for active movement. |
| C1-24 | 283 | 1.5 | empty "###" heading | STR | Remove. |
| C1-25 | 303 | 1.6 | "The … system was developed in this study." | LANG | Sentence fragment: "The … system developed in this study." |
| C1-26 | 324, 333, 348, 351, 354 | 1.6 | "This study, it includes…", "In this study, the setting refers to where…", "it refers to TheraQuest VR is referred to as" | LANG | Five broken definition sentences; rewrite each as "In this study, it refers to…". |
| C1-27 | 285 to 355 | 1.6 | Definition of Terms | SYS, DEC D9 | Terms used by the built system and Chapter 3 but not defined: range of motion, repetition, markerless tracking, session, patient code. Add only if you want them. |

## Chapter 2 (lines 359 to 521)

| ID | Line | Section | Quoted text | Type | Proposed action |
|----|------|---------|-------------|------|-----------------|
| C2-1 | 361 | Intro | "technology acceptance, system effectiveness, motivation, and motor learning" | STR, DEC D2 | Names theories (TAM, DeLone and McLean) that are not in 2.3. |
| C2-2 | 369, 443 | 2.1.1, 2.2.4 | "(De Guzman et al., 2024)" | CITE, DEC D12 | Not in the reference list. |
| C2-3 | 371 | 2.1.1 | "(Buckingham et al., 2024)" | CITE, DEC D12 | Not in the reference list. |
| C2-4 | 375, 415 | 2.1.2, 2.2.1 | "(Yang, 2023)" | CITE, DEC D12 | Not in the reference list. |
| C2-5 | 395 | 2.1.4 | "(Stepanenko & Dubko, 2025\)" | LANG | Missing full stop at the end of the paragraph. |
| C2-6 | 401 | 2.1.5 | "(Maya et al., 2021)" | CITE | The reference entry has no journal and its link is the same as the Consing and Aguila entry. Check the source. |
| C2-7 | 419, 427, 429, 431, 503 | 2.2, 2.3 | empty "###" / "##" headings | STR | Remove (five). |
| C2-8 | 413 | 2.2.1 | "Virtual Reality in Physical Rehabilitation" | STR | Same title as 2.1.2 and largely the same content and sources as 2.1.2. Shorten the overlap or state what 2.2.1 adds. |
| C2-9 | 437 | 2.2.3 | "(Navea et al., 2025; …)" | CITE | Reference list has "2025a"; Table 1 also cites "2025b", which is not in the list. |
| C2-10 | 437 | 2.2.3 | "(Warsinsky et al., 2021; Lee et al., 2025)" | CITE | Lee et al. (2025) is about gamification in clinical reasoning education, and Tung et al. (2024) about orthopedic education; check that they support claims about rehabilitation systems. |
| C2-11 | 439 to 441 | 2.2.4 | "In addition, a local study by…" | LANG | The section opens with "In addition". Also, the title says "Rehabilitation Adherence" but the first study is about professionals' attitudes. |
| C2-12 | 447 to 457 | 2.2.5 | whole section | LANG | Much denser and longer than 2.2.1 to 2.2.4 and written in a different voice. Even out the style; no content change. |
| C2-13 | 453 | 2.2.5 | "(… Sunido & Soreño, 2026)" | CITE, DEC D12 | You cite your own study as a source for a general trend; not in the reference list. Remove the self-citation. |
| C2-14 | 453 | 2.2.5 | "tethered cabling create technical barriers … shift toward standalone HMD units" | SYS, DEC D4 | Argues against the tethered setup the system uses. |
| C2-15 | 457 | 2.2.5 | "cloud-based adherence dashboards" | — | Describes the literature, not TheraQuest. Language edit only (plan rule 4). No action. |
| C2-16 | 461 | 2.3 | "(Deterding et al., 2011)" | CITE, DEC D12 | Not in the reference list. Gamification principles are named here but have no section of their own. |
| C2-17 | 463, 469, 471 | 2.3, 2.3.2 | "(Schmidt & Lee, 2011)", "(Winstein et al., 2014)", "(Winstein, Kay, & Woollacott, 2014)" | CITE, DEC D12 | The list has Schmidt et al. (2018), not 2011. Winstein is not in the list, and the two citations name it differently; check the authors. |
| C2-18 | 465 to 496 | 2.3.2 to 2.3.5 | headings 2.3.2 to 2.3.5; captions "Figure 2.3.4" to "Figure 2.3.7" | STR, FIG, DEC D2 | Headings, captions, contents and List of Figures use three different numberings. |
| C2-19 | 471 | 2.3.2 | "Furthermore, the study draws from Motor Learning Theory" | LANG | "Furthermore" opens what is now the first theory. |
| C2-20 | 485 | 2.3.4 | "Figure 2.3.6 Flow Theory" | FIG | Caption with no image in the `.md` (the file exists in `Figures/figures`). Confirm the master has it. |
| C2-21 | 490 | 2.3.4 | "adaptive difficulty levels" | SYS, DEC D8 | Not automatic in the built system. |
| C2-22 | 497 | 2.3.5 | "(Based on Michie et al, 2011)" | LANG | "et al." needs a full stop. |
| C2-23 | 505 | 2.4 | "## **2\.4 Synthesis…" | STR | 2.4.1 is in the contents only (see F6). |
| C2-24 | 511 to 520 | Table 1 | Ebrahimi et al. (2025); Tu et al. (2026); Zhu et al. (2025); Navea et al. (2025b) | CITE, DEC D12 | In Table 1 but not in the reference list. Lee et al. and Stepanenko and Dubko each appear in two rows. |
| C2-25 | 511 | Table 1 | "Study; Study; Case-control…" | LANG | Six sources share one row with semicolon lists, so it is hard to tell which method belongs to which source. Consider one source per row (bigger change: your call). |

## Chapter 3 (lines 522 to 1316, without 3.9)

| ID | Line | Section | Quoted text | Type | Proposed action |
|----|------|---------|-------------|------|-----------------|
| C3-1 | 526, 532 | Intro, 3.1 | "user satisfaction"; "observation checklists" | DEC D14 | No instrument is described for either. |
| C3-2 | 530 | 3.1 | "This study employed" | LANG, DEC D1 | Only past-tense sentence in the section. |
| C3-3 | 540, 591 | 3.2 | "excluding diagnosis and clinical decision-making" / "support clinical decision-making" | LANG | The two statements contradict each other. Suggest "inform the therapist's decisions" in the second. |
| C3-4 | 542 | 3.2 | "Figure 3.2.1" | FIG | Caption with no image in the `.md` (file exists). Confirm the master has it. |
| C3-5 | 544, 569, 571, 593 | 3.2 | empty "###" headings | STR | Remove (four). |
| C3-6 | 548 | 3.2 item 1 | "by wearing a VR headset" | SYS, DEC D9 | Add the desktop mode in a few words. |
| C3-7 | 550, 567, 581, 604, 616 | 3.2 | "monitoring support ." | LANG | Space before the full stop in five places (probably deleted citation marks). |
| C3-8 | 554 | 3.2 item 2 | "real-time camera input, VR environment controls" | SYS | Camera input is one external webcam; the therapist's parameters come from the prescription saved in the dashboard. |
| C3-9 | 641 | 3.3 | "Iterative Incremental Model" | LANG | Elsewhere "Iterative-Incremental". Use one spelling. |
| C3-10 | 647 | 3.3 | "(GeeksforGeeks, n.d.)" | CITE | The reference entry is the site's home page, not the article. Give the article title and link. |
| C3-11 | 651 | 3.3 | "### The Initial Planning Phase establishes…" | STR | A whole paragraph is formatted as a heading. Make it body text. |
| C3-12 | 651, 683 | 3.3 | "standalone VR HMDs"; "target standalone VR hardware" | SYS, DEC D4 | As C1-21. |
| C3-13 | 663, 679 | 3.3 | "(OpenCV/MediaPipe)" | SYS | MediaPipe Pose for landmarks, OpenCV for camera capture. |
| C3-14 | 671 | 3.3 Testing | "Euclidean distance error and angle error calculations against reference standards" | SYS | The built evaluation tools compute a confusion matrix and angle error. Wording depends on what you decide for 3.9 (reported only). |
| C3-15 | 677 | 3.3 | "Iteration (Iterate) Phase" | LANG | "Iteration Phase". |
| C3-16 | 691 to 713 | 3.4.1 | "from January to November 2026" | SYS, DEC D3 | Timeline vs what happened. |
| C3-17 | 655, 699; 659, 701 | 3.3, 3.4.1 | phase descriptions | LANG | 3.4.1 repeats 3.3 almost word for word for each phase. Shorten 3.4.1 to dates and outputs. |
| C3-18 | 725 | 3.4.2 | "from sensor or camera data … pose estimation and movement recognition" | SYS, DEC D15 | Webcam only; no movement recognition. |
| C3-19 | 731 | 3.4.2 | "rather than long-term behavioral tracking or frequency analysis" | SYS, DEC D7 | As C1-18. |
| C3-20 | 733 | 3.4.2 | "The system shall display progress…" | LANG | The only requirement with no bold key phrase; make the six consistent. |
| C3-21 | 735 to 747 | 3.4.2 | (missing) | SYS, DEC D9 | Built safety behaviour is not a requirement here: stop alert at the safety angle limit, rejecting repetitions done with a compensating posture, pausing when tracking is lost. |
| C3-22 | 751 | 3.5 | "Use Case diagrams, Entity Relationship diagrams (ERD), and System Flowcharts" | STR | Section 3.5 contains the use case, ERD and data flow diagrams; the flowchart is in 3.6.1. |
| C3-23 | 757, 769 | 3.5.1, 3.5.2 | "Figure 3.5.1.1", "Figure 3.5.2.1" | FIG | Captions with no image in the `.md` (files exist). Confirm the master has them. |
| C3-24 | 763 | 3.5.1 | "user authentication" | SYS, DEC D11 | Therapist password login; patient code in the game. |
| C3-25 | 771 to 785 | 3.5.2 | Physical Therapist "area of specialization"; Patient "age, and gender"; Adherence Record entity | SYS, FIG, DEC D13 | The ERD is the design-stage model. The built database also holds protocols with phases, prescriptions, clinical notes (pain, soreness, swelling), repetition records, the patient code and login sessions. I will compare field by field against `server.py` in M9.3 before proposing text or a new figure. |
| C3-26 | 803 | 3.5.3 | "B. LEVEL 1 DFD" | LANG | "B. Level 1 DFD" (matches "A. Level 0 DFD"). |
| C3-27 | 805 | 3.5.3 | one 190-word paragraph | LANG | Split into two or three sentences groups; no content change. |
| C3-28 | 811 to 817 | 3.5.3 | data flow text | SYS, DEC D9 | Gamification is missing from the flow, and the flow does not show the three programs (tracker, game, server). One sentence can fix the text; the figure is D13. |
| C3-29 | 827 | 3.6.1 | "Figure 3.6.1.1" | FIG | Caption with no image in the `.md` (file exists). Title also ends "…of the TheraQuest VR" (add "System"). |
| C3-30 | 825, 829 | 3.6.1 | "The system flowchart illustrates…" twice | LANG | Two paragraphs open the same way and say the same thing; merge. |
| C3-31 | 831 | 3.6.1 | "determines whether the user is a Patient or a Physical Therapist" | SYS, DEC D11 | Two separate programs, not one login. |
| C3-32 | 851, 857, 865 | 3.6.2, 3.6.3 | "four layer", "real time feedback", "session level" | LANG | Hyphenate when used before a noun ("four-layer", "real-time", "session-level"); the manuscript mixes both. |
| C3-33 | 853 to 859 | 3.6.2 | four layers | SYS, DEC D9 | Correct as a logical view. It does not say how the parts run: Python tracker → UDP → Unity game ↔ local REST server with SQLite ↔ therapist desktop app. Add one or two sentences. |
| C3-34 | 873 to 877 | 3.6.3 VR Environment | "hand movements, head orientation, and positional data … forwards these to the motion tracking pipeline"; "raw user movement data sent to the motion tracking module" | SYS, DEC D5 | The headset does not feed motion tracking; the webcam does. The first-person view and coach window are not mentioned (D9). |
| C3-35 | 885 | 3.6.3 Motion Tracking | "built-in VR cameras or external webcams, positional data from VR tracking hardware including controllers" | SYS, DEC D5 | One external webcam. |
| C3-36 | 885 | 3.6.3 Motion Tracking | "OpenCV or MediaPipe" | SYS | As C3-13. |
| C3-37 | 887 | 3.6.3 Motion Tracking | "Frame Preprocessor normalizes and denoises" | SYS | No denoising step in the tracker code. Describe what it does (capture, pose landmarks, visibility checks, angle smoothing) after a closer read in M9.3. |
| C3-38 | 887 | 3.6.3 Motion Tracking | "Movement Classifier compares the detected gesture patterns against known exercise types" | SYS, DEC D15 | No such classifier. |
| C3-39 | 911, 913 | 3.6.3 Feedback | "voice instructions"; "corrective guidance text that is also logged to the performance database" | SYS | I found sound cues and on-screen captions but no spoken voice in the game code, and have not confirmed that feedback text is stored. Verify both in M9.3. |
| C3-40 | 923, 925 | 3.6.3 Gamification | "adjusting the level or complexity of subsequent tasks"; "next-level trigger that advances the exercise difficulty" | SYS, DEC D8 | Therapist-approved phase change. Built rewards are XP levels, badges, stars and combo streaks. |
| C3-41 | 935, 937 | 3.6.3 Adherence | "complete, incomplete, or missed"; "does not analyze long-term behavioral patterns" | SYS, DEC D7 | The built statuses are complete, incomplete, missed, pending and rest day. |
| C3-42 | 867 to 937 | 3.6.3 | six module figures | FIG, DEC D13 | Each figure shows the components the text names (for example the Movement Classifier), so text changes here mean figure changes. |
| C3-43 | 949 | 3.7.1 Hardware | "a VR headset, such as the Meta Quest" | SYS, DEC D4 | Meta Quest over Quest Link; desktop mode without it. |
| C3-44 | 953 | 3.7.1 Hardware | "built-in VR tracking cameras or external webcams" | SYS, DEC D5 | One webcam, 2 to 3 metres away, side or front view by exercise. |
| C3-45 | 955 | 3.7.1 Hardware | "adequate physical space" | SYS | The project sets a figure (at least 2 × 2 m, no window behind the patient). Add it. |
| C3-46 | 959 | 3.7.1 Software | "the Unity engine" | SYS | Unity 6 with the Universal Render Pipeline and OpenXR. |
| C3-47 | 961 | 3.7.1 Software | "OpenCV or MediaPipe, or any similar libraries" | SYS | MediaPipe Pose and OpenCV. Also fix the comma inside the bold text. |
| C3-48 | 963 | 3.7.1 Software | "such as C\# and Python is used" | LANG, SYS | "C# and Python are used". Python also runs the server and the therapist app; the dashboard is HTML, CSS and JavaScript. |
| C3-49 | 965 | 3.7.1 Software | "A database system is required" | SYS | SQLite, stored locally on the clinic PC. Also "by physical therapist" → "by the physical therapist". |
| C3-50 | 971 to 995 | 3.7.2 | "VRSystem class represents the main system controller" | SYS, FIG, DEC D13 | Design-stage class model. The built code has no such single controller. Text and figure are compared with the Unity scripts in M9.3 and M9.4. |
| C3-51 | 997 to 1007 | 3.7.3 | testing types | SYS, DEC D9 | The project has automated tests (tracker, server, evaluation tools, Unity EditMode, run by one script) and a record-and-replay harness for the tracker. One or two sentences if you want them. |
| C3-52 | 1011 | 3.8 | "healthy volunteers for system testing and refinement" | LANG, DEC D1 | Tense across 3.8: "is conducted", "will participate", "are given". |
| C3-53 | 1021 | 3.8.1 | "VR headsets, computer systems, and motion tracking devices" | SYS, DEC D5 | "a webcam" in place of "motion tracking devices". |
| C3-54 | 1029, 1035, 1037 | 3.8.2 | "licensed physical therapists (PT doctors)" | LANG | "PT doctors" is informal and may be inaccurate. Use "licensed physical therapists" throughout. |
| C3-55 | 1045, 1047 | 3.8.3 | "expected and detected joint coordinates" | SYS, DEC D5 | Tied to the Euclidean error in 3.9: reported only until you decide. |
| C3-56 | 1053 | 3.8.3 | "completed, incomplete, or missed" | SYS, DEC D7 | As C3-41. |
| C3-57 | 1055 to 1071 | 3.8.3 | "Evaluation Statements for Physical Therapists" and "Expert Evaluation of System Outputs" | STR | Two instruments answered by the same experts about the same reports. Say how they differ, or merge. Your call. |
| C3-58 | 1073 | 3.8.3 | "Data Gathering Procedures" | STR | It is a sub-heading of Research Instrument but describes the procedure. Suggest its own number (3.8.4) and add it to the contents. |
| C3-59 | 1083 | 3.8.3 | "the user feedback questionnaire" | DEC D14 | Not described anywhere. |
| C3-60 | 1309 | 3.10 | "to protect the rights, safety, and well-being…" | STR | The section starts in the middle of a sentence. The opening words are missing in the export; check the master. |
| C3-61 | 1313 | 3.10 | "Participant identities are anonymized" | SYS, DEC D10 | As D10. |
| C3-62 | 1311, 1315 | 3.10 | (missing) | SYS, DEC D10 | No mention of RA 10173, of consent to the name being stored, or of the physician clearance for active movement that the project requires. |

## References (lines 1317 to 1403)

| ID | Line | Quoted text | Type | Proposed action |
|----|------|-------------|------|-----------------|
| R1 | 1385 to 1403 | Berton … GeeksforGeeks | CITE | The last ten entries were appended after "Warsinsky" and are not in alphabetical order or in the same format (journal names not in italics). Sort and reformat. |
| R2 | 1325, 1387 | Bateni et al. (2024) | CITE | Listed twice. Remove the second. |
| R3 | 1367, 1389 | Pérez-Maletzki et al. (2023); Feng et al. (2019) | CITE | In the list but not cited in Chapters 1 to 3 (3.9 has no citations). Cite or remove. |
| R4 | 1351, 1361, 1363, 1369, 1373, 1381 | "Matsangidou, M., et al."; "Oduoye, M. O., et al."… | CITE | Six entries use "et al." in the reference list. APA lists the authors (up to 20). You supply the names; I will not guess them. |
| R5 | 1361, 1363 | Oduoye; Oudshoorn | CITE | No volume, issue or article number. |
| R6 | 1401 | Schmidt, Lee, Winstein, Wulf, & Zelaznik (2018) | CITE | In-text citations say "Schmidt & Lee, 2011". Make text and list agree. |
| R7 | — | Missing entries | CITE, DEC D12 | Cited but not listed: Laver et al. (2017); De Guzman et al. (2024); Buckingham et al. (2024); Yang (2023); Deterding et al. (2011); Winstein et al. (2014); Sunido & Soreño (2026); Ebrahimi et al. (2025); Tu et al. (2026); Zhu et al. (2025); Navea et al. (2025b). |

## Figures and tables

| ID | Item | Type | Finding |
|----|------|------|---------|
| G1 | Embedded images | FIG | 15 images are embedded. Captions with no image in the `.md`: Figure 2.3.6 Flow Theory, 3.2.1, 3.5.1.1, 3.5.2.1, 3.6.1.1. All five exist as files in `Research/Figures/figures/`, so this is probably an export gap, not a gap in the master. Please confirm. |
| G2 | Figure 2.3.x | FIG, DEC D2 | No Self-Determination Theory figure or section in the body, but it is in the List of Figures. |
| G3 | Tables 1 to 9 | FIG | All nine captions exist and match the List of Tables in number. Punctuation differs ("Table 1\.", "Table 2.", "Table 2**.") and Table 4 says "5 Point" while Table 7 says "5-Point". Tables 2 to 9 are inside 3.9: captions are not edited; the list is. |
| G4 | Design-stage figures | FIG, DEC D13 | Use case, ERD, flowchart, architecture, six module figures and class diagram all show the design as planned. Which ones change depends on D4, D5, D8, D11, D13 and D15. |
| G5 | Figure 3.4.1.1 Gantt | FIG, DEC D3 | Changes only if you change the timeline. |

## Reported only (Section 3.9, not edited)

- Line 1137: the Euclidean distance error is described for a "three-dimensional" space, and 3.8.3 collects "joint coordinates". The built tracker measures 2D joint angles. This touches your analysis method, so it is your decision and outside M9.
- Line 1303: heading "3.9. 4Expert Evaluation of System Outputs" has a misplaced space ("3.9.4 Expert…"). I will not fix it unless you say so, because it is inside 3.9.

## What is already consistent (no action)

- The six module names are used the same way in 3.3, 3.5.3, 3.6.2 and 3.6.3.
- Participant numbers (5 to 10 patients, 5 to 10 healthy volunteers, 3 to 5 therapists) are stated once and not contradicted.
- All 15 embedded images have a caption, and Tables 1 to 9 are numbered in order.
- No results or findings are claimed anywhere in Chapters 1 to 3.

## Baseline for the "do not touch" check

Recorded 2026-11-16 before any edit:

- Section 3.9: `194feb23bdce611f848d547f08d349a4117e40c68e9fc0f57f4de8d18388dc2c`
- Image lines: `d68fc33713e9f40da64055b868b8e39c928b2a8f28982f16b211523b4d8171e3`

Commands (run in `Research/`):

```
sed -n '/^## \*\*3\.9 /,/^## \*\*3\.10 /p' "THERAQUEST- MANUSCRIPT.md" | sha256sum
grep '^\[image' "THERAQUEST- MANUSCRIPT.md" | sha256sum
```
