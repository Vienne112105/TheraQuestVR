import json
E = []


def R(match, old, new, src):
    E.append({"op": "replace", "match": match, "old": old, "new": new, "source": src})


R("Scope of Clinical Application:",
  "Patient participants are outpatient or subacute orthopedic patients in the active-recovery stage who have been cleared by a physician for active, low-to-moderate-load exercise. Patients who are limited to passive movement or who may not bear weight are not included.",
  "Patient participants are orthopedic post-operative patients whose recovery precautions are set by their physician or physical therapist.",
  "M9.3 Ch1 PT consult 2026-11-26 patient stage (human yes)")
E.append({"op": "insert_after", "match": "Scope of Clinical Application:",
          "text": "**Exercise Coverage:** The prototype covers the shoulder, elbow, hip, knee and ankle. Wrist exercises are not yet included and are identified as future work. The system is designed for stationary exercises and is not intended for gait or other movements that involve travelling.",
          "source": "M9.3 Ch1 PT consult: wrist and gait limitation (human yes)"})
R("A total of 5 to 10 physical therapy patients",
  "5 to 10 physical therapy patients in the active-recovery stage, cleared by a physician for active exercise, will participate",
  "5 to 10 orthopedic post-operative patients, whose recovery precautions are set by their physician or physical therapist, will participate",
  "M9.3 Ch3 PT consult patient stage (human yes)")
R("The Adherence Record entity tracks whether",
  "fully completed or left incomplete.",
  "fully completed, partially completed, or missed.",
  "M9.3 PT consult adherence word: partial (human yes)")
R("The Completion Checker verifies whether",
  "complete, incomplete, or missed", "complete, partial, or missed",
  "M9.3 PT consult adherence word: partial (human yes)")
R("This instrument focuses on determining whether",
  "completed, incomplete, or missed", "completed, partial, or missed",
  "M9.3 PT consult adherence word: partial (human yes)")
json.dump(E, open("M9-edits-draft-2.8.json", "w"), indent=1, ensure_ascii=False)
print(len(E))
