"""
Unit tests for TheraQuest VR Clinical Evaluation & Analytics Pipeline (M2.2, M4.5).
Validates mathematical equations from Section 3.9 of the Research Manuscript.
"""

import math
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "server"))
import server  # noqa: E402  (records sessions the way Unity uploads them)

from evaluate_clinical_metrics import (
    calculate_confusion_matrix,
    calculate_euclidean_distance_error,
    calculate_angle_error,
    interpret_weighted_mean,
    calculate_adherence_evaluation,
    interpret_sus_score,
    calculate_sus_score,
    run_self_test,
    evaluate_real,
    overall_status,
    format_report_markdown,
    NOT_MEASURED,
    TABLE_2_BENCHMARKS
)

class TestClinicalMetrics(unittest.TestCase):

    def test_confusion_matrix_perfect(self):
        """Test ideal classification scenario (100% precision, recall, accuracy, f1)."""
        cm = calculate_confusion_matrix(tp=50, tn=50, fp=0, fn=0)
        self.assertEqual(cm["accuracy"], 100.0)
        self.assertEqual(cm["precision"], 100.0)
        self.assertEqual(cm["recall"], 100.0)
        self.assertEqual(cm["f1_score"], 100.0)
        self.assertTrue(cm["benchmarks_met"])

    def test_confusion_matrix_sub_benchmark(self):
        """Test classification that falls below Table 2 minimum acceptance criteria."""
        cm = calculate_confusion_matrix(tp=60, tn=10, fp=20, fn=10)
        self.assertEqual(cm["accuracy"], 70.0)  # Below 85%
        self.assertEqual(cm["precision"], 75.0) # Below 80%
        self.assertFalse(cm["benchmarks_met"])
        self.assertFalse(cm["evaluations"]["accuracy"]["passed"])

    def test_angle_error_calculations(self):
        """Assert angle error |Theta_exp - Theta_det| matches Section 3.9.1.3."""
        expected = [90.0, 120.0, 45.0, 85.0]
        detected = [88.0, 123.0, 44.0, 80.0]
        # errors: [2.0, 3.0, 1.0, 5.0] -> mean = 2.75
        res = calculate_angle_error(expected, detected, tolerance_deg=10.0)
        self.assertEqual(res["mean_angle_error_deg"], 2.75)
        self.assertEqual(res["max_angle_error_deg"], 5.0)
        self.assertEqual(res["within_5deg_pct"], 100.0)
        self.assertTrue(res["acceptable"])

    def test_euclidean_distance_3d(self):
        """Assert 3D Euclidean distance formula d = sqrt(dx^2 + dy^2 + dz^2)."""
        p1 = [(0.0, 0.0, 0.0)]
        p2 = [(0.03, 0.04, 0.0)]  # 3-4-5 triangle -> 0.05m = 5cm
        res = calculate_euclidean_distance_error(p1, p2, tolerance_m=0.05)
        self.assertEqual(res["mean_distance_m"], 0.05)
        self.assertEqual(res["mean_distance_cm"], 5.0)
        self.assertEqual(res["tolerance_pass_rate_pct"], 100.0)

    def test_adherence_weighted_mean_and_interpretation(self):
        """Assert Table 4 & Table 5 Likert weighted mean calculation and verbal labels."""
        self.assertEqual(interpret_weighted_mean(4.8), "Very High / Highly Acceptable")
        self.assertEqual(interpret_weighted_mean(3.9), "High / Acceptable")
        self.assertEqual(interpret_weighted_mean(3.0), "Moderate")
        self.assertEqual(interpret_weighted_mean(2.0), "Low")
        self.assertEqual(interpret_weighted_mean(1.2), "Very Low")

    def test_sus_scoring_formula(self):
        """Assert System Usability Scale formula with alternating odd/even scoring."""
        # Perfect SUS score (5 on odd items, 1 on even items):
        # Odd items (1,3,5,7,9): 5 - 1 = 4
        # Even items (2,4,6,8,10): 5 - 1 = 4
        # Total sum = 10 * 4 = 40; Final = 40 * 2.5 = 100
        perfect_response = [[5, 1, 5, 1, 5, 1, 5, 1, 5, 1]]
        sus = calculate_sus_score(perfect_response)
        self.assertEqual(sus["mean_sus_score"], 100.0)
        self.assertEqual(sus["interpretation"], "Excellent")
        self.assertTrue(sus["acceptable_usability"])

        # Worst SUS score (1 on odd, 5 on even):
        # Odd: 1 - 1 = 0; Even: 5 - 5 = 0; Total = 0
        worst_response = [[1, 5, 1, 5, 1, 5, 1, 5, 1, 5]]
        sus_worst = calculate_sus_score(worst_response)
        self.assertEqual(sus_worst["mean_sus_score"], 0.0)
        self.assertEqual(sus_worst["interpretation"], "Awful")
        self.assertFalse(sus_worst["acceptable_usability"])

    def test_self_test_is_labelled_synthetic(self):
        """The self-test computes its status and says it is synthetic example data (DEC-011)."""
        bench = run_self_test()
        self.assertEqual(bench["data_source"]["mode"], "self-test")
        self.assertEqual(bench["status"], overall_status(bench))
        self.assertIn("SYNTHETIC EXAMPLE DATA", format_report_markdown(bench))


class TestRealInputs(unittest.TestCase):
    """Real-data path: rep events recorded through the server, joined to study CSV files."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="tq_eval_")
        self.db = os.path.join(self.tmp, "theraquest.db")
        self._real_db = server.DB_PATH
        server.DB_PATH = self.db
        server.init_db()
        con = server.db()
        self.eid = con.execute("SELECT exercise_id FROM exercise WHERE code='shoulderAbd'").fetchone()[0]
        pid = con.execute("SELECT patient_id FROM patient WHERE code='P-001'").fetchone()[0]

        def rep(attempt, valid, peak):
            return {"exercise_id": self.eid, "attempt": attempt, "set": 1, "peak": peak, "error": abs(90 - peak),
                    "accuracy": 90, "valid": valid}

        # webcam session: the system counted reps 1, 2, 3 and rejected 4, 5
        reps = [rep(1, True, 88), rep(2, True, 92), rep(3, True, 70), rep(4, False, 60), rep(5, False, 89)]
        server.save_session(con, {"patient_id": pid, "session_uuid": "cam-1", "input_source": "webcam",
                                  "started_at": "2026-10-20T09:00:00", "ended_at": "2026-10-20T09:10:00",
                                  "exercises": [], "rep_events": reps})
        # keyboard session: left out by default
        server.save_session(con, {"patient_id": pid, "session_uuid": "kbd-1", "input_source": "keyboard",
                                  "started_at": "2026-10-20T10:00:00", "ended_at": "2026-10-20T10:10:00",
                                  "exercises": [], "rep_events": [rep(1, True, 90)]})
        con.close()

    def tearDown(self):
        server.DB_PATH = self._real_db
        shutil.rmtree(self.tmp, ignore_errors=True)

    def csv(self, name, header, *rows):
        path = os.path.join(self.tmp, name)
        with open(path, "w", encoding="utf-8", newline="") as f:
            for line in (header,) + rows:
                f.write(line + "\r\n")
        return path

    LABELS = "session_uuid,exercise_code,attempt,therapist_label"
    GONIO = "session_uuid,exercise_code,attempt,goniometer_deg"
    SUS = "respondent,q1,q2,q3,q4,q5,q6,q7,q8,q9,q10"

    def test_no_inputs_is_not_measured(self):
        res = evaluate_real(self.db)
        self.assertEqual(res["status"], "NOT MEASURED")
        for key in ("confusion_matrix", "angle_error", "system_usability_scale", "adherence_pt_evaluation"):
            self.assertEqual(res[key]["status"], NOT_MEASURED)
        report = format_report_markdown(res)
        self.assertNotIn("[PASS]", report)
        self.assertNotIn("SYNTHETIC", report)

    def test_empty_template_files_are_not_measured(self):
        tpl = os.path.join(HERE, "templates")
        res = evaluate_real(self.db, os.path.join(tpl, "rep_labels.csv"), os.path.join(tpl, "goniometer.csv"),
                            os.path.join(tpl, "sus.csv"), os.path.join(tpl, "pt_survey.csv"))
        self.assertEqual(res["status"], "NOT MEASURED")

    def test_known_labels_give_known_confusion_matrix(self):
        # therapist: 1 correct + counted (TP), 2 correct + counted (TP), 3 incorrect + counted (FP),
        # 4 incorrect + rejected (TN), 5 correct + rejected (FN); 9 has no rep event; kbd-1 is not webcam
        labels = self.csv("labels.csv", self.LABELS,
                          "cam-1,shoulderAbd,1,correct", "cam-1,shoulderAbd,2,correct", "cam-1,shoulderAbd,3,incorrect",
                          "cam-1,shoulderAbd,4,incorrect", "cam-1,shoulderAbd,5,correct", "cam-1,shoulderAbd,9,correct",
                          "kbd-1,shoulderAbd,1,correct")
        cm = evaluate_real(self.db, rep_labels=labels)["confusion_matrix"]
        self.assertEqual((cm["tp"], cm["tn"], cm["fp"], cm["fn"]), (2, 1, 1, 1))
        self.assertEqual(cm["unmatched_labels"], 2)
        self.assertEqual(cm["accuracy"], 60.0)
        self.assertAlmostEqual(cm["precision"], 66.67)
        self.assertAlmostEqual(cm["recall"], 66.67)

    def test_webcam_filter_can_be_turned_off(self):
        labels = self.csv("labels.csv", self.LABELS, "kbd-1,shoulderAbd,1,correct")
        self.assertEqual(evaluate_real(self.db, rep_labels=labels)["confusion_matrix"]["status"], NOT_MEASURED)
        cm = evaluate_real(self.db, rep_labels=labels, webcam_only=False)["confusion_matrix"]
        self.assertEqual(cm["tp"], 1)

    def test_known_goniometer_gives_known_mae(self):
        gonio = self.csv("gonio.csv", self.GONIO, "cam-1,shoulderAbd,1,90", "cam-1,shoulderAbd,2,90")
        ae = evaluate_real(self.db, goniometer=gonio)["angle_error"]
        self.assertEqual(ae["sample_count"], 2)
        self.assertEqual(ae["mean_angle_error_deg"], 2.0)       # |90-88| and |90-92|

    def test_surveys_and_overall_status(self):
        labels = self.csv("labels.csv", self.LABELS, "cam-1,shoulderAbd,1,correct", "cam-1,shoulderAbd,2,correct",
                          "cam-1,shoulderAbd,4,incorrect")
        gonio = self.csv("gonio.csv", self.GONIO, "cam-1,shoulderAbd,1,90")
        sus = self.csv("sus.csv", self.SUS, "R1,5,1,5,1,5,1,5,1,5,1", "R2,4,2,4,2,4,2,4,2,4,2")
        pt_rows = [f"PT{r},{n},{score}" for n in range(1, 9) for r, score in ((1, 5), (2, 4))]
        pt = self.csv("pt.csv", "respondent,statement,score", *pt_rows)
        res = evaluate_real(self.db, labels, gonio, sus, pt)
        self.assertEqual(res["system_usability_scale"]["mean_sus_score"], 87.5)
        self.assertEqual(res["adherence_pt_evaluation"]["overall_weighted_mean"], 4.5)
        self.assertEqual(res["status"], "PASS")
        self.assertEqual(evaluate_real(self.db, labels, gonio, sus)["status"], "INCOMPLETE")   # no PT survey
        bad_sus = self.csv("bad.csv", self.SUS, "R1,1,5,1,5,1,5,1,5,1,5")
        self.assertEqual(evaluate_real(self.db, labels, gonio, bad_sus, pt)["status"], "FAIL")

    def test_bad_label_value_rejected(self):
        labels = self.csv("labels.csv", self.LABELS, "cam-1,shoulderAbd,1,maybe")
        with self.assertRaises(ValueError):
            evaluate_real(self.db, rep_labels=labels)


if __name__ == "__main__":
    unittest.main()
