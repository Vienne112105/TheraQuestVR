"""Tests for run_tests.py: output parsing and exit code only (no suite is launched)."""
import os
import sys
import tempfile
import unittest

import run_tests as rt


class UnittestOutputTests(unittest.TestCase):
    def test_ok(self):
        out = "....\n----------------------------------------------------------------------\nRan 66 tests in 4.2s\n\nOK\n"
        self.assertEqual(rt.parse_unittest(out), (66, 0))

    def test_ok_with_skips(self):
        out = "Ran 12 tests in 0.1s\n\nOK (skipped=2)\n"
        self.assertEqual(rt.parse_unittest(out), (12, 0))

    def test_failed(self):
        out = "Ran 10 tests in 1.0s\n\nFAILED (failures=2, errors=1)\n"
        self.assertEqual(rt.parse_unittest(out), (10, 3))

    def test_no_summary(self):
        self.assertEqual(rt.parse_unittest("ImportError: no module"), (0, 0))


class NUnitXmlTests(unittest.TestCase):
    def write(self, text):
        fd, path = tempfile.mkstemp(suffix=".xml")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
        self.addCleanup(os.remove, path)
        return path

    def test_counts(self):
        path = self.write('<?xml version="1.0"?><test-run id="2" total="91" passed="89" failed="2" skipped="0"></test-run>')
        self.assertEqual(rt.parse_nunit(path), (91, 2))

    def test_missing_file(self):
        self.assertIsNone(rt.parse_nunit(os.path.join(tempfile.gettempdir(), "no_such_results.xml")))


class ExitCodeTests(unittest.TestCase):
    def r(self, status):
        return rt.Result("x", status, 1, 0, 0.0, "")

    def test_all_passed_or_skipped(self):
        self.assertEqual(rt.exit_code([self.r(rt.PASSED), self.r(rt.SKIPPED)]), 0)

    def test_any_failed(self):
        self.assertEqual(rt.exit_code([self.r(rt.PASSED), self.r(rt.FAILED)]), 1)


class TrackerPythonTests(unittest.TestCase):
    def test_falls_back_without_venv(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(rt.tracker_python(d), sys.executable)

    def test_uses_venv(self):
        with tempfile.TemporaryDirectory() as d:
            exe = os.path.join(d, ".venv", "Scripts", "python.exe")
            os.makedirs(os.path.dirname(exe))
            open(exe, "w").close()
            self.assertEqual(rt.tracker_python(d), exe)


if __name__ == "__main__":
    unittest.main()
