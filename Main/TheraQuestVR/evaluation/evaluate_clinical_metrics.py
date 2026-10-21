"""
TheraQuest VR - Clinical Evaluation & Analytics Pipeline (M2, made data-honest in M4.5 / DEC-011)
Authoritative implementation of Section 3.9 (Data Analysis) from the Research Manuscript.

Real metrics come only from real data: the rep_event log Unity uploads (webcam sessions by default) joined
to CSV files from the study (templates in evaluation/templates/). Anything without input is "not measured",
and the overall status is never PASS on missing data. --self-test runs the formulas on synthetic example
vectors and labels the output SYNTHETIC EXAMPLE DATA.

Run:   python evaluate_clinical_metrics.py --rep-labels labels.csv --goniometer gonio.csv --sus sus.csv --pt-survey pt.csv
       python evaluate_clinical_metrics.py --self-test

Computes:
  1. Section 3.9.1 Motion Tracking Accuracy:
     - Confusion Matrix: TP, TN, FP, FN -> Accuracy, Precision, Recall, F1-Score
       Benchmark thresholds (Table 2): Acc >= 85%, Prec >= 80%, Rec >= 80%, F1 >= 80%
     - Euclidean Distance Error: 3D coordinates d = sqrt((x2-x1)^2 + (y2-y1)^2 + (z2-z1)^2)
       Benchmark threshold (Table 3): within PT spatial tolerance
     - Angle Error: |Theta_expected - Theta_detected|
       Benchmark threshold: 5.0 to 10.0 degrees
  2. Section 3.9.2 Adherence Monitoring System Evaluation:
     - Weighted Mean X_bar = sum(f*x)/N, Percentage, Percentage Agreement
     - 5-point Likert Scale & Verbal Interpretation (Tables 4 & 5)
     - 8 Physical Therapist Evaluation Statements (Table 6)
  3. Section 3.9.3 System Usability Scale (SUS):
     - Standard 10 items (Table 8)
     - Odd items: Score = Response - 1; Even items: Score = 5 - Response
     - Final Score = sum(Adjusted Scores) * 2.5
     - Verbal interpretation (Table 9): Excellent (>=80.3), Good (68-80.2), Average (68), Poor (51-67.9), Awful (<51)
"""

import argparse
import csv
import json
import math
import os
import sqlite3
import sys
from typing import Dict, List, Tuple, Any, Optional


# =====================================================================
# 3.9.1 MOTION TRACKING ACCURACY
# =====================================================================

TABLE_2_BENCHMARKS = {
    "min_accuracy": 85.0,
    "min_precision": 80.0,
    "min_recall": 80.0,
    "min_f1_score": 80.0,
}

def calculate_confusion_matrix(tp: int, tn: int, fp: int, fn: int) -> Dict[str, Any]:
    """
    Computes classification metrics from a 2x2 confusion matrix (Section 3.9.1.1).
    TP: True Positives (correct movement correctly identified)
    TN: True Negatives (incorrect/unsafe movement correctly rejected)
    FP: False Positives (incorrect/unsafe movement incorrectly approved)
    FN: False Negatives (correct movement incorrectly rejected)
    """
    total = tp + tn + fp + fn
    if total == 0:
        return {
            "tp": 0, "tn": 0, "fp": 0, "fn": 0, "total": 0,
            "accuracy": 0.0, "precision": 0.0, "recall": 0.0, "f1_score": 0.0,
            "benchmarks_met": False,
            "evaluations": {}
        }

    accuracy = ((tp + tn) / total) * 100.0
    precision = (tp / (tp + fp) * 100.0) if (tp + fp) > 0 else 0.0
    recall = (tp / (tp + fn) * 100.0) if (tp + fn) > 0 else 0.0
    
    if (precision + recall) > 0:
        f1_score = 2.0 * (precision * recall) / (precision + recall)
    else:
        f1_score = 0.0

    evals = {
        "accuracy": {
            "value": round(accuracy, 2),
            "threshold": TABLE_2_BENCHMARKS["min_accuracy"],
            "passed": accuracy >= TABLE_2_BENCHMARKS["min_accuracy"],
            "interpretation": "Acceptable overall classification performance" if accuracy >= 85.0 else "Sub-benchmark performance"
        },
        "precision": {
            "value": round(precision, 2),
            "threshold": TABLE_2_BENCHMARKS["min_precision"],
            "passed": precision >= TABLE_2_BENCHMARKS["min_precision"],
            "interpretation": "Acceptable correctness of positive detections" if precision >= 80.0 else "High false positive rate"
        },
        "recall": {
            "value": round(recall, 2),
            "threshold": TABLE_2_BENCHMARKS["min_recall"],
            "passed": recall >= TABLE_2_BENCHMARKS["min_recall"],
            "interpretation": "Acceptable ability to detect required movements" if recall >= 80.0 else "High false negative rejection"
        },
        "f1_score": {
            "value": round(f1_score, 2),
            "threshold": TABLE_2_BENCHMARKS["min_f1_score"],
            "passed": f1_score >= TABLE_2_BENCHMARKS["min_f1_score"],
            "interpretation": "Acceptable balance between precision and recall" if f1_score >= 80.0 else "Imbalanced classification"
        }
    }

    all_passed = all(item["passed"] for item in evals.values())

    return {
        "tp": tp, "tn": tn, "fp": fp, "fn": fn, "total": total,
        "accuracy": round(accuracy, 2),
        "precision": round(precision, 2),
        "recall": round(recall, 2),
        "f1_score": round(f1_score, 2),
        "benchmarks_met": all_passed,
        "evaluations": evals
    }


def calculate_euclidean_distance_error(
    expected_points: List[Tuple[float, float, float]],
    detected_points: List[Tuple[float, float, float]],
    tolerance_m: float = 0.05
) -> Dict[str, Any]:
    """
    Computes 3D Euclidean distance errors between expected reference joints and detected landmarks (Section 3.9.1.2).
    Formula: d = sqrt((x2 - x1)^2 + (y2 - y1)^2 + (z2 - z1)^2)
    """
    if len(expected_points) != len(detected_points) or len(expected_points) == 0:
        return {"error": "Point lists must be non-empty and of equal length"}

    errors = []
    within_tolerance_count = 0

    for (x1, y1, z1), (x2, y2, z2) in zip(expected_points, detected_points):
        d = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2 + (z2 - z1) ** 2)
        errors.append(d)
        if d <= tolerance_m:
            within_tolerance_count += 1

    n = len(errors)
    mean_error = sum(errors) / n
    max_error = max(errors)
    min_error = min(errors)
    rms_error = math.sqrt(sum(e ** 2 for e in errors) / n)
    tolerance_pass_rate = (within_tolerance_count / n) * 100.0

    return {
        "sample_count": n,
        "mean_distance_m": round(mean_error, 4),
        "mean_distance_cm": round(mean_error * 100.0, 2),
        "rms_distance_cm": round(rms_error * 100.0, 2),
        "max_distance_cm": round(max_error * 100.0, 2),
        "min_distance_cm": round(min_error * 100.0, 2),
        "tolerance_threshold_m": tolerance_m,
        "tolerance_pass_rate_pct": round(tolerance_pass_rate, 2),
        "acceptable": tolerance_pass_rate >= 85.0
    }


def calculate_angle_error(
    expected_angles: List[float],
    detected_angles: List[float],
    tolerance_deg: float = 10.0
) -> Dict[str, Any]:
    """
    Computes absolute angle errors |Theta_expected - Theta_detected| (Section 3.9.1.3).
    Evaluates against clinical allowable tolerance (5.0 to 10.0 degrees).
    """
    if len(expected_angles) != len(detected_angles) or len(expected_angles) == 0:
        return {"error": "Angle lists must be non-empty and of equal length"}

    errors = [abs(exp - det) for exp, det in zip(expected_angles, detected_angles)]
    n = len(errors)

    within_5deg = sum(1 for e in errors if e <= 5.0)
    within_10deg = sum(1 for e in errors if e <= 10.0)
    within_custom = sum(1 for e in errors if e <= tolerance_deg)

    mean_err = sum(errors) / n
    max_err = max(errors)
    min_err = min(errors)
    rms_err = math.sqrt(sum(e ** 2 for e in errors) / n)

    return {
        "sample_count": n,
        "mean_angle_error_deg": round(mean_err, 2),
        "rms_angle_error_deg": round(rms_err, 2),
        "max_angle_error_deg": round(max_err, 2),
        "min_angle_error_deg": round(min_err, 2),
        "within_5deg_pct": round((within_5deg / n) * 100.0, 2),
        "within_10deg_pct": round((within_10deg / n) * 100.0, 2),
        "within_tolerance_pct": round((within_custom / n) * 100.0, 2),
        "tolerance_threshold_deg": tolerance_deg,
        "acceptable": mean_err <= tolerance_deg and (within_10deg / n) >= 0.85
    }


# =====================================================================
# 3.9.2 ADHERENCE MONITORING EVALUATION
# =====================================================================

TABLE_5_INTERPRETATION = [
    (4.21, 5.00, "Very High / Highly Acceptable"),
    (3.41, 4.20, "High / Acceptable"),
    (2.61, 3.40, "Moderate"),
    (1.81, 2.60, "Low"),
    (1.00, 1.80, "Very Low"),
]

PT_EVALUATION_STATEMENTS = [
    "The system accurately records the completion status of prescribed rehabilitation sessions.",
    "The adherence reports generated by the system are clear, understandable, and easy to interpret.",
    "The system provides relevant information needed to monitor patient adherence to prescribed rehabilitation activities.",
    "The adherence monitoring component is functional and reliable in tracking session-level compliance.",
    "The generated adherence reports are useful in supporting the assessment of patient rehabilitation progress.",
    "The information provided by the system is relevant to the clinical monitoring needs of physical therapists.",
    "The system-generated adherence outputs can assist physical therapists in making informed decisions regarding patient rehabilitation management.",
    "Overall, the adherence monitoring component of the TheraQuest VR system is acceptable for rehabilitation monitoring purposes."
]

def interpret_weighted_mean(mean_val: float) -> str:
    """Interprets weighted mean according to Table 5 in Section 3.9.2."""
    for low, high, interp in TABLE_5_INTERPRETATION:
        if low - 0.005 <= mean_val <= high + 0.005:
            return interp
    return "Out of Range"

def calculate_adherence_evaluation(responses_per_statement: List[List[int]]) -> Dict[str, Any]:
    """
    Computes Weighted Mean, percentage distribution, and verbal interpretation for 
    the 8 Physical Therapist Evaluation Statements (Section 3.9.2, Table 6).
    responses_per_statement: List of 8 items, each containing Likert values (1 to 5) from evaluators.
    """
    statement_results = []
    grand_sum = 0.0
    total_evaluators_count = 0

    for idx, statement in enumerate(PT_EVALUATION_STATEMENTS):
        resp = responses_per_statement[idx] if idx < len(responses_per_statement) else []
        n = len(resp)
        if n == 0:
            statement_results.append({
                "statement_no": idx + 1,
                "statement": statement,
                "n": 0,
                "weighted_mean": 0.0,
                "interpretation": "No data",
                "frequency": {str(k): 0 for k in range(1, 6)},
                "percentage": {str(k): 0.0 for k in range(1, 6)}
            })
            continue

        freq = {k: resp.count(k) for k in range(1, 6)}
        fx_sum = sum(k * count for k, count in freq.items())
        weighted_mean = fx_sum / n
        grand_sum += weighted_mean
        total_evaluators_count += 1

        statement_results.append({
            "statement_no": idx + 1,
            "statement": statement,
            "n": n,
            "weighted_mean": round(weighted_mean, 2),
            "interpretation": interpret_weighted_mean(weighted_mean),
            "frequency": {str(k): freq[k] for k in range(1, 6)},
            "percentage": {str(k): round((freq[k] / n) * 100.0, 2) for k in range(1, 6)}
        })

    overall_mean = (grand_sum / total_evaluators_count) if total_evaluators_count > 0 else 0.0

    return {
        "statement_evaluations": statement_results,
        "overall_weighted_mean": round(overall_mean, 2),
        "overall_interpretation": interpret_weighted_mean(overall_mean),
        "clinical_acceptability": overall_mean >= 3.41
    }


# =====================================================================
# 3.9.3 SYSTEM USABILITY SCALE (SUS)
# =====================================================================

SUS_ITEMS = [
    "I think that I would like to use this system frequently.",
    "I found the system unnecessarily complex.",
    "I thought the system was easy to use.",
    "I think that I would need the support of a technical person to be able to use this system.",
    "I found the various functions in this system were well integrated.",
    "I thought there was too much inconsistency in this system.",
    "I would imagine that most people would learn to use this system very quickly.",
    "I found the system very cumbersome to use.",
    "I felt very confident using the system.",
    "I needed to learn a lot of things before I could get going with this system."
]

def interpret_sus_score(score: float) -> str:
    """Interprets SUS score according to Table 9 in Section 3.9.3."""
    if score >= 80.3:
        return "Excellent"
    elif score >= 68.0:
        return "Good" if score > 68.0 else "Average"
    elif score >= 51.0:
        return "Poor"
    else:
        return "Awful"

def calculate_sus_score(evaluator_responses: List[List[int]]) -> Dict[str, Any]:
    """
    Computes standard SUS scores across evaluators (Section 3.9.3).
    Formula:
      Odd items (1, 3, 5, 7, 9): Score = Response - 1
      Even items (2, 4, 6, 8, 10): Score = 5 - Response
      Participant SUS = sum(Adjusted Scores) * 2.5
    """
    individual_scores = []

    for resp in evaluator_responses:
        if len(resp) != 10:
            continue
        adjusted_scores = []
        for i, val in enumerate(resp):
            val = max(1, min(5, int(val)))
            if (i + 1) % 2 == 1:
                # Odd item: 1, 3, 5, 7, 9
                adjusted_scores.append(val - 1)
            else:
                # Even item: 2, 4, 6, 8, 10
                adjusted_scores.append(5 - val)
        participant_sus = sum(adjusted_scores) * 2.5
        individual_scores.append(round(participant_sus, 2))

    if not individual_scores:
        return {
            "evaluator_count": 0,
            "mean_sus_score": 0.0,
            "interpretation": "No data",
            "individual_scores": []
        }

    mean_sus = sum(individual_scores) / len(individual_scores)
    return {
        "evaluator_count": len(individual_scores),
        "mean_sus_score": round(mean_sus, 2),
        "min_sus_score": min(individual_scores),
        "max_sus_score": max(individual_scores),
        "interpretation": interpret_sus_score(mean_sus),
        "acceptable_usability": mean_sus >= 68.0,
        "individual_scores": individual_scores
    }


# =====================================================================
# REAL INPUTS (DEC-011): database rep events + CSV files from the study
# =====================================================================

NOT_MEASURED = "not measured"
SYNTHETIC_BANNER = "SYNTHETIC EXAMPLE DATA - formula self-test only, NOT study results"

# The four benchmarks from the manuscript's success criteria. Euclidean distance needs 3D reference
# positions, which a single 2D webcam study does not collect, so it never decides the overall status.
CORE_SECTIONS = ("confusion_matrix", "angle_error", "system_usability_scale", "adherence_pt_evaluation")


def default_db_path() -> str:
    """Same location as server.py (DEC-010): THERAQUEST_DB, else %LOCALAPPDATA%/TheraQuest/theraquest.db."""
    if os.environ.get("THERAQUEST_DB"):
        return os.environ["THERAQUEST_DB"]
    base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    return os.path.join(base, "TheraQuest", "theraquest.db")


def not_measured(reason: str) -> Dict[str, Any]:
    return {"status": NOT_MEASURED, "reason": reason}


def is_measured(section: Optional[Dict[str, Any]]) -> bool:
    return bool(section) and section.get("status") != NOT_MEASURED and "error" not in section


def _read_csv(path: str, required: List[str]) -> List[Dict[str, str]]:
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fields = [c.strip() for c in (reader.fieldnames or [])]
        missing = [c for c in required if c not in fields]
        if missing:
            raise ValueError(f"{path}: missing column(s) {', '.join(missing)}")
        rows = []
        for raw in reader:
            row = {(k or "").strip(): (v or "").strip() for k, v in raw.items()}
            if any(row.values()):
                rows.append(row)
        return rows


def _rep_key(session_uuid: str, exercise_code: str, attempt: Any) -> Tuple[str, str, int]:
    return (session_uuid.strip(), exercise_code.strip(), int(attempt))


LABEL_CORRECT = {"correct", "1", "yes", "y", "true", "valid"}
LABEL_INCORRECT = {"incorrect", "0", "no", "n", "false", "invalid"}


def load_rep_labels(path: str) -> Dict[Tuple[str, str, int], bool]:
    """Therapist rep labels: session_uuid, exercise_code, attempt, therapist_label (correct / incorrect)."""
    labels = {}
    for i, row in enumerate(_read_csv(path, ["session_uuid", "exercise_code", "attempt", "therapist_label"]), start=2):
        value = row["therapist_label"].lower()
        if value not in LABEL_CORRECT | LABEL_INCORRECT:
            raise ValueError(f"{path} line {i}: therapist_label must be 'correct' or 'incorrect'")
        labels[_rep_key(row["session_uuid"], row["exercise_code"], row["attempt"])] = value in LABEL_CORRECT
    return labels


def load_goniometer(path: str) -> Dict[Tuple[str, str, int], float]:
    """Goniometer readings of the rep's peak: session_uuid, exercise_code, attempt, goniometer_deg."""
    return {_rep_key(r["session_uuid"], r["exercise_code"], r["attempt"]): float(r["goniometer_deg"])
            for r in _read_csv(path, ["session_uuid", "exercise_code", "attempt", "goniometer_deg"])}


def load_sus(path: str) -> List[List[int]]:
    """SUS answers: respondent, q1 ... q10 (1-5 each)."""
    items = [f"q{i}" for i in range(1, 11)]
    out = []
    for i, row in enumerate(_read_csv(path, ["respondent"] + items), start=2):
        answers = [int(row[q]) for q in items]
        if not all(1 <= a <= 5 for a in answers):
            raise ValueError(f"{path} line {i}: SUS answers must be 1-5")
        out.append(answers)
    return out


def load_pt_survey(path: str) -> List[List[int]]:
    """Therapist evaluation (Table 6): respondent, statement (1-8), score (1-5). Returns ratings per statement."""
    per_statement: List[List[int]] = [[] for _ in PT_EVALUATION_STATEMENTS]
    for i, row in enumerate(_read_csv(path, ["respondent", "statement", "score"]), start=2):
        n, score = int(row["statement"]), int(row["score"])
        if not 1 <= n <= len(PT_EVALUATION_STATEMENTS) or not 1 <= score <= 5:
            raise ValueError(f"{path} line {i}: statement must be 1-{len(PT_EVALUATION_STATEMENTS)} and score 1-5")
        per_statement[n - 1].append(score)
    return per_statement


def load_rep_events(db_path: str, webcam_only: bool = True) -> Tuple[Dict[Tuple[str, str, int], Dict[str, Any]], Dict[str, Any]]:
    """Per-rep log recorded by Unity (rep_event table). Keyed by session_uuid + exercise code + attempt."""
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    try:
        tables = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if "rep_event" not in tables:
            return {}, {"rep_events": 0, "excluded_non_webcam": 0, "note": "database has no rep_event table (older server)"}
        rows = con.execute("""
            SELECT s.session_uuid, s.input_source, e.code AS exercise_code, v.attempt, v.valid, v.peak_angle
            FROM rep_event v
            JOIN session s ON s.session_id = v.session_id
            JOIN exercise e ON e.exercise_id = v.exercise_id
            WHERE s.session_uuid IS NOT NULL
        """).fetchall()
        sessions = con.execute("SELECT input_source, COUNT(*) FROM session GROUP BY input_source").fetchall()
        adherence = con.execute("SELECT status, COUNT(*) FROM adherence_record GROUP BY status").fetchall()
    finally:
        con.close()
    events, excluded = {}, 0
    for r in rows:
        if webcam_only and r["input_source"] != "webcam":
            excluded += 1
            continue
        events[_rep_key(r["session_uuid"], r["exercise_code"], r["attempt"])] = dict(r)
    summary = {
        "rep_events": len(events),
        "excluded_non_webcam": excluded,
        "sessions_by_input_source": {(k or "unknown"): n for k, n in sessions},
        "adherence_records_by_status": {k: n for k, n in adherence},
    }
    return events, summary


def confusion_from_labels(labels: Dict[Tuple[str, str, int], bool],
                          events: Dict[Tuple[str, str, int], Dict[str, Any]]) -> Dict[str, Any]:
    """
    Positive class = a correctly performed rep (therapist label). The system "says positive" when it counted the rep.
    TP: correct and counted   TN: incorrect and rejected   FP: incorrect but counted   FN: correct but rejected
    """
    tp = tn = fp = fn = 0
    unmatched = 0
    for key, correct in labels.items():
        ev = events.get(key)
        if ev is None:
            unmatched += 1
            continue
        counted = bool(ev["valid"])
        if correct and counted:
            tp += 1
        elif correct:
            fn += 1
        elif counted:
            fp += 1
        else:
            tn += 1
    if tp + tn + fp + fn == 0:
        return not_measured(f"no therapist labels matched a recorded rep ({unmatched} unmatched)")
    cm = calculate_confusion_matrix(tp=tp, tn=tn, fp=fp, fn=fn)
    cm["unmatched_labels"] = unmatched
    return cm


def angle_error_from_goniometer(readings: Dict[Tuple[str, str, int], float],
                                events: Dict[Tuple[str, str, int], Dict[str, Any]]) -> Dict[str, Any]:
    """Goniometer (expected) vs the tracker's peak angle for the same rep (detected)."""
    pairs = [(deg, events[key]["peak_angle"]) for key, deg in readings.items() if key in events]
    unmatched = len(readings) - len(pairs)
    if not pairs:
        return not_measured(f"no goniometer readings matched a recorded rep ({unmatched} unmatched)")
    ae = calculate_angle_error([p[0] for p in pairs], [p[1] for p in pairs], tolerance_deg=10.0)
    ae["unmatched_readings"] = unmatched
    return ae


def evaluate_real(db_path: Optional[str] = None, rep_labels: Optional[str] = None, goniometer: Optional[str] = None,
                  sus: Optional[str] = None, pt_survey: Optional[str] = None, webcam_only: bool = True) -> Dict[str, Any]:
    """Section 3.9 metrics from real study data only. Anything without input is reported as not measured."""
    db_path = db_path or default_db_path()
    source = {"mode": "real", "database": db_path, "webcam_only": webcam_only,
              "rep_labels": rep_labels, "goniometer": goniometer, "sus": sus, "pt_survey": pt_survey}

    events, db_summary = {}, {"note": "database not found"}
    if os.path.exists(db_path):
        events, db_summary = load_rep_events(db_path, webcam_only)

    def from_reps(path, loader, compute, what):
        if not path:
            return not_measured(f"no {what} file given")
        if not events:
            return not_measured("no recorded rep events" + (" from webcam sessions" if webcam_only else ""))
        return compute(loader(path), events)

    results = {
        "data_source": source,
        "database_summary": db_summary,
        "confusion_matrix": from_reps(rep_labels, load_rep_labels, confusion_from_labels, "therapist rep label"),
        "angle_error": from_reps(goniometer, load_goniometer, angle_error_from_goniometer, "goniometer"),
        "euclidean_distance": not_measured("needs 3D reference joint positions, which this single-webcam study does not collect"),
        "adherence_pt_evaluation": not_measured("no PT survey file given"),
        "system_usability_scale": not_measured("no SUS file given"),
    }
    if pt_survey:
        ratings = load_pt_survey(pt_survey)
        results["adherence_pt_evaluation"] = (calculate_adherence_evaluation(ratings) if any(ratings)
                                              else not_measured("PT survey file has no answers"))
    if sus:
        answers = load_sus(sus)
        results["system_usability_scale"] = calculate_sus_score(answers) if answers else not_measured("SUS file has no answers")
    results["status"] = overall_status(results)
    return results


def section_passed(name: str, section: Dict[str, Any]) -> bool:
    if name == "confusion_matrix":
        return bool(section.get("benchmarks_met"))
    if name == "angle_error":
        return bool(section.get("acceptable"))
    if name == "system_usability_scale":
        return section.get("mean_sus_score", 0) > 68.0          # PROJECT success criterion: mean SUS > 68
    if name == "adherence_pt_evaluation":
        return bool(section.get("clinical_acceptability"))
    return False


def overall_status(results: Dict[str, Any]) -> str:
    """
    PASS only when all four benchmarks were measured and met. Never PASS on missing data:
    NOT MEASURED = nothing measured; INCOMPLETE = nothing failed but something is missing; FAIL = a benchmark failed.
    """
    measured = {n: results.get(n) for n in CORE_SECTIONS if is_measured(results.get(n))}
    if not measured:
        return "NOT MEASURED"
    if not all(section_passed(n, s) for n, s in measured.items()):
        return "FAIL"
    return "PASS" if len(measured) == len(CORE_SECTIONS) else "INCOMPLETE"


# =====================================================================
# FORMULA SELF-TEST (synthetic vectors; never study results)
# =====================================================================

def run_self_test() -> Dict[str, Any]:
    """
    Runs every Section 3.9 formula on fixed, made-up example vectors so the math can be checked.
    The output is labelled SYNTHETIC EXAMPLE DATA and must not be reported as results (DEC-011).
    """
    # 100 example reps: 86 TP, 10 TN, 2 FP, 2 FN
    cm = calculate_confusion_matrix(tp=86, tn=10, fp=2, fn=2)

    ref_angles = [60, 60, 62, 90, 90, 88, 120, 120, 118, 130, 130, 127, 45, 45, 47, 85, 85, 82, 30, 30, 32, 70, 70, 68, 90, 90, 92, 25, 25, 24]
    det_angles = [58.8, 61.2, 60.5, 89.1, 91.4, 86.9, 118.5, 121.0, 117.2, 128.4, 131.2, 125.8, 44.1, 46.2, 45.9, 83.8, 86.1, 81.2, 29.3, 31.0, 30.8, 68.7, 71.3, 67.5, 88.9, 91.5, 90.8, 24.2, 25.8, 23.5]
    ae = calculate_angle_error(ref_angles, det_angles, tolerance_deg=10.0)

    ref_pts = [(0.25, 1.45, 0.10), (0.35, 1.30, 0.12), (0.45, 1.10, 0.15), (-0.25, 1.45, 0.10), (-0.35, 1.30, 0.12)] * 3
    det_pts = [(0.26, 1.44, 0.11), (0.36, 1.31, 0.11), (0.44, 1.09, 0.14), (-0.24, 1.46, 0.11), (-0.36, 1.29, 0.13)] * 3
    ee = calculate_euclidean_distance_error(ref_pts, det_pts, tolerance_m=0.05)

    pt_ratings = [
        [5, 5, 4, 5, 4], [4, 5, 5, 4, 5], [5, 4, 5, 5, 4], [4, 4, 5, 5, 5],
        [5, 5, 4, 4, 5], [4, 5, 5, 4, 4], [5, 4, 4, 5, 5], [5, 5, 5, 4, 5],
    ]
    adh_eval = calculate_adherence_evaluation(pt_ratings)

    sus_responses = [
        [5, 1, 5, 1, 5, 2, 5, 1, 5, 2], [4, 2, 4, 2, 5, 1, 4, 1, 4, 1],
        [5, 1, 5, 2, 4, 2, 5, 1, 5, 2], [4, 2, 5, 1, 4, 1, 5, 2, 4, 1],
        [5, 1, 4, 1, 5, 1, 4, 2, 5, 1], [5, 2, 5, 2, 5, 2, 5, 1, 5, 2],
        [4, 1, 4, 1, 4, 1, 4, 1, 4, 2], [5, 1, 5, 1, 5, 1, 5, 1, 5, 1],
    ]
    sus_eval = calculate_sus_score(sus_responses)

    results = {
        "data_source": {"mode": "self-test", "banner": SYNTHETIC_BANNER},
        "confusion_matrix": cm,
        "angle_error": ae,
        "euclidean_distance": ee,
        "adherence_pt_evaluation": adh_eval,
        "system_usability_scale": sus_eval,
    }
    results["status"] = overall_status(results)
    return results


# =====================================================================
# REPORT
# =====================================================================

def _flag(ok: bool, yes: str = "[PASS]", no: str = "[FAIL]") -> str:
    return yes if ok else no


def format_report_markdown(results: Dict[str, Any]) -> str:
    """Formats evaluation results as Markdown. Every report starts with its data source (DEC-011)."""
    src = results.get("data_source", {})
    synthetic = src.get("mode") == "self-test"
    lines = []
    lines.append("# TheraQuest VR — Clinical Evaluation Report")
    lines.append("*Metrics follow Research Manuscript Section 3.9 (Data Analysis).*\n")
    if synthetic:
        lines.append(f"> **{SYNTHETIC_BANNER}.** These numbers come from fixed example vectors in "
                     "`evaluate_clinical_metrics.py` and only check that the formulas work.\n")
    lines.append("## Data source")
    if synthetic:
        lines.append("- Mode: **self-test** (synthetic example vectors)")
    else:
        lines.append("- Mode: **real study data**")
        lines.append(f"- Database: `{src.get('database')}`" + (" (webcam sessions only)" if src.get("webcam_only") else " (all input sources)"))
        for key, label in (("rep_labels", "Therapist rep labels"), ("goniometer", "Goniometer readings"),
                           ("sus", "SUS answers"), ("pt_survey", "PT survey")):
            lines.append(f"- {label}: " + (f"`{src[key]}`" if src.get(key) else "*none*"))
        db = results.get("database_summary", {})
        if db:
            lines.append(f"- Rep events used: {db.get('rep_events', 0)}; excluded (not webcam): {db.get('excluded_non_webcam', 0)}"
                         + (f"; {db['note']}" if db.get("note") else ""))
    lines.append(f"\n**Overall status: {results.get('status')}**"
                 + (" (computed from the synthetic vectors)" if synthetic else "") + "\n")

    def missing(title, section):
        lines.append(title)
        lines.append(f"- **Not measured:** {section.get('reason', 'no input')}\n")

    cm = results.get("confusion_matrix", {})
    title = "## 1. Motion Tracking Classification Performance (Section 3.9.1.1)"
    if not is_measured(cm):
        missing(title, cm)
    else:
        lines.append(title)
        lines.append("| Metric | Target Benchmark | Measured Value | Compliance | Interpretation |")
        lines.append("| :--- | :---: | :---: | :---: | :--- |")
        for key in ["accuracy", "precision", "recall", "f1_score"]:
            e = cm.get("evaluations", {}).get(key, {})
            lines.append(f"| **{key.capitalize().replace('_', ' ')}** | >= {e.get('threshold')}% | **{e.get('value')}%** | "
                         f"{_flag(e.get('passed', False))} | {e.get('interpretation', '')} |")
        lines.append(f"\n*Confusion matrix: TP = {cm.get('tp')}, TN = {cm.get('tn')}, FP = {cm.get('fp')}, FN = {cm.get('fn')} "
                     f"(Total = {cm.get('total')})"
                     + (f"; unmatched labels = {cm['unmatched_labels']}" if "unmatched_labels" in cm else "") + "*\n")

    ae = results.get("angle_error", {})
    title = "## 2. Goniometer vs. Tracker Angle Error (Section 3.9.1.3)"
    if not is_measured(ae):
        missing(title, ae)
    else:
        lines.append(title)
        lines.append(f"- **Mean Angle Error (MAE):** {ae.get('mean_angle_error_deg')}° over {ae.get('sample_count')} reps "
                     f"(clinical threshold: <= {ae.get('tolerance_threshold_deg')}°)")
        lines.append(f"- **Root Mean Square Error (RMSE):** {ae.get('rms_angle_error_deg')}°")
        lines.append(f"- **Samples within 5°:** {ae.get('within_5deg_pct')}%; **within 10°:** {ae.get('within_10deg_pct')}%")
        lines.append(f"- **Clinical acceptance:** {_flag(ae.get('acceptable', False), '[ACCEPTABLE]', '[NEEDS CALIBRATION]')}\n")

    ee = results.get("euclidean_distance", {})
    title = "## 3. 3D Spatial Euclidean Distance Error (Section 3.9.1.2)"
    if not is_measured(ee):
        missing(title, ee)
    else:
        lines.append(title)
        lines.append(f"- **Mean Distance Error:** {ee.get('mean_distance_cm')} cm; **RMS:** {ee.get('rms_distance_cm')} cm; "
                     f"**Max:** {ee.get('max_distance_cm')} cm")
        lines.append(f"- **Within 5 cm:** {ee.get('tolerance_pass_rate_pct')}% "
                     f"{_flag(ee.get('acceptable', False), '[ACCEPTABLE]', '[EXCESSIVE DEVIATION]')}\n")

    adh = results.get("adherence_pt_evaluation", {})
    title = "## 4. Adherence Monitoring System Evaluation (Section 3.9.2)"
    if not is_measured(adh):
        missing(title, adh)
    else:
        lines.append(title)
        lines.append(f"- **Overall Weighted Mean:** **{adh.get('overall_weighted_mean')} / 5.00** — "
                     f"{adh.get('overall_interpretation')} (Table 5: Acceptable >= 3.41)")
        lines.append(f"- **Clinical Acceptability:** {_flag(adh.get('clinical_acceptability', False), '[ACCEPTABLE]', '[REVISE]')}\n")
        lines.append("| No. | Statement | n | Weighted Mean | Verbal Interpretation |")
        lines.append("| :---: | :--- | :---: | :---: | :--- |")
        for s in adh.get("statement_evaluations", []):
            lines.append(f"| {s.get('statement_no')} | {s.get('statement')} | {s.get('n')} | **{s.get('weighted_mean')}** | {s.get('interpretation')} |")
        lines.append("")

    sus = results.get("system_usability_scale", {})
    title = "## 5. System Usability Scale (SUS) (Section 3.9.3)"
    if not is_measured(sus):
        missing(title, sus)
    else:
        lines.append(title)
        lines.append(f"- **Average SUS Score:** **{sus.get('mean_sus_score')} / 100** from {sus.get('evaluator_count')} respondents "
                     f"— {sus.get('interpretation')} (Table 9)")
        lines.append(f"- **Usability benchmark (mean > 68):** {_flag(section_passed('system_usability_scale', sus))}\n")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="TheraQuest VR - Section 3.9 evaluation. Real metrics come only from the database's rep events "
                    "and the study CSV files (templates in evaluation/templates/); anything missing is 'not measured'.")
    parser.add_argument("--self-test", action="store_true",
                        help="check the formulas on synthetic example vectors (labelled SYNTHETIC; never study results)")
    parser.add_argument("--db", default=None, help="theraquest.db to read rep events from (default: the server's database)")
    parser.add_argument("--rep-labels", default=None, help="CSV: session_uuid,exercise_code,attempt,therapist_label")
    parser.add_argument("--goniometer", default=None, help="CSV: session_uuid,exercise_code,attempt,goniometer_deg")
    parser.add_argument("--sus", default=None, help="CSV: respondent,q1..q10")
    parser.add_argument("--pt-survey", default=None, help="CSV: respondent,statement,score")
    parser.add_argument("--include-non-webcam", action="store_true",
                        help="also use keyboard / simulated sessions (default: webcam sessions only)")
    parser.add_argument("--export-json", default=None, help="save the results to a JSON file")
    parser.add_argument("--export-md", default=None, help="save the report to a Markdown file")
    args = parser.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")   # Windows consoles without UTF-8

    if args.self_test:
        results = run_self_test()
    else:
        try:
            results = evaluate_real(args.db, args.rep_labels, args.goniometer, args.sus, args.pt_survey,
                                    webcam_only=not args.include_non_webcam)
        except (OSError, ValueError, KeyError) as e:
            sys.exit(f"Input error: {e}")

    report = format_report_markdown(results)
    print(report)

    if args.export_json:
        with open(args.export_json, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
        print(f"\nExported JSON report to {args.export_json}")
    if args.export_md:
        with open(args.export_md, "w", encoding="utf-8") as f:
            f.write(report + "\n")
        print(f"Exported Markdown report to {args.export_md}")


if __name__ == "__main__":
    main()
