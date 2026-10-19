"""
Unit tests for TheraQuest VR Clinical Evaluation & Analytics Pipeline (M2.2).
Validates mathematical equations from Section 3.9 of the Research Manuscript.
"""

import math
import os
import unittest
from evaluate_clinical_metrics import (
    calculate_confusion_matrix,
    calculate_euclidean_distance_error,
    calculate_angle_error,
    interpret_weighted_mean,
    calculate_adherence_evaluation,
    interpret_sus_score,
    calculate_sus_score,
    run_synthetic_benchmark,
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

    def test_synthetic_benchmark_suite(self):
        """Ensure the clinical benchmark test vectors pass all Table 2 & 9 criteria."""
        bench = run_synthetic_benchmark()
        self.assertEqual(bench["status"], "PASS")
        self.assertTrue(bench["confusion_matrix"]["benchmarks_met"])
        self.assertTrue(bench["angle_error"]["acceptable"])
        self.assertTrue(bench["euclidean_distance"]["acceptable"])
        self.assertTrue(bench["adherence_pt_evaluation"]["clinical_acceptability"])
        self.assertTrue(bench["system_usability_scale"]["acceptable_usability"])


if __name__ == "__main__":
    unittest.main()
