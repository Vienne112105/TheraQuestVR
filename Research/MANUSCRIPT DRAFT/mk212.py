import json
E = []


def R(match, old, new, src):
    E.append({"op": "replace", "match": match, "old": old, "new": new, "source": src})


W = "M9.3 headset connection: cable or Air Link (human choice 2026-11-26; Air Link not yet tested, HW.2)"
R("Hardware Dependency:", "connected to it by Quest Link,", "connected to it by Quest Link, either by cable or wirelessly through Air Link,", W)
R("(e.g., a VR headset connected to the computer by Quest Link", "connected to the computer by Quest Link,", "connected to the computer by cable or wirelessly through Air Link,", W)
R("the VR headset connected to it by Quest Link", "connected to it by Quest Link,", "connected to it by cable or wirelessly through Air Link,", W)
R("The system requires a VR headset", "connected to the computer by Quest Link,", "connected to the computer by Quest Link, either by cable or wirelessly through Air Link,", W)
R("An adequate physical space is required", "Because the headset hides the room and is connected to the computer by a cable, the cable is kept clear of the patient", "Because the headset hides the room, any connecting cable is kept clear of the patient", W)

P = "M9.3 M10.5 Patient Lock (built 2026-11-26, tracker/patient_lock.py; human: add it now, before the two-person check)"
R("Patient Safety:", "or when the headset is taken off.", "or when the headset is taken off. The system also treats the first person it detects as the patient and pauses the session if another person takes the patient's place, until the patient is tracked again; a person who only stands nearby, such as the supervisor, does not pause it.", P)
R("The Motion Tracking Module is responsible for capturing", "five-stage pipeline", "six-stage pipeline", P)
R("The Frame Preprocessor resizes", "body parts within each frame. The Landmark Smoother", "body parts within each frame. The Patient Lock treats the first body detected in the session as the patient and passes on only that body, so that another person is never measured; if another person takes the patient's place, the session pauses until the patient is tracked again. The Landmark Smoother", P)

json.dump(E, open("M9-edits-draft-2.12.json", "w"), indent=1, ensure_ascii=False)

