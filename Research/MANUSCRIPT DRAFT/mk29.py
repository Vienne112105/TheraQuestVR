import json
E = [
 {"op": "replace", "match": "The Completion Checker verifies whether",
  "old": "monitoring dashboard.",
  "new": "monitoring dashboard. For each day, adherence is classified as complete when the patient finishes all the exercises assigned for that day, partial when only some of the assigned exercises are finished, and missed when none are finished. Each day follows the local time of the computer on which the system runs and lasts 24 hours, from 12:00 midnight (00:00) to 11:59 p.m. (23:59), after which the count starts again for the next day.",
  "source": "M9.3 adherence definition from the PT answer 6, day reset wording (human yes 2026-11-26, third sentence excluded)"},
 {"op": "replace", "match": "This instrument focuses on determining whether",
  "old": "completed, partial, or missed.",
  "new": "completed, partial, or missed, as defined in Section 3.6.3.",
  "source": "M9.3 cross-reference to the adherence definition"},
]
json.dump(E, open("M9-edits-draft-2.9.json", "w"), indent=1, ensure_ascii=False)
