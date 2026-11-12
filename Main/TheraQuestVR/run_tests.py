"""Run every TheraQuest test suite and print one summary table.

    python run_tests.py                  all suites (Unity last)
    python run_tests.py --no-unity       skip the Unity EditMode tests
    python run_tests.py --only server,tracker
    python run_tests.py --unity-exe "C:\\path\\to\\Unity.exe"

Exit code 0 when every suite passed or was skipped, 1 when any failed.
Unity is SKIPPED (not failed) when its Editor is not installed or already has the project open.
"""
import argparse
import os
import re
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET
from collections import namedtuple

ROOT = os.path.dirname(os.path.abspath(__file__))
UNITY_PROJECT = os.path.join(ROOT, "unity")

PASSED, FAILED, SKIPPED = "PASSED", "FAILED", "SKIPPED"
Result = namedtuple("Result", "name status tests failures seconds note")

PY_SUITES = ("runner", "server", "tracker", "evaluation")
ALL_SUITES = PY_SUITES + ("unity",)


def parse_unittest(output):
    """(tests run, failures + errors) from unittest's summary; (0, 0) if there is none."""
    ran = re.search(r"^Ran (\d+) tests?", output, re.M)
    if not ran:
        return 0, 0
    bad = sum(int(n) for n in re.findall(r"(?:failures|errors)=(\d+)", output))
    return int(ran.group(1)), bad


def parse_nunit(path):
    """(total, failed) from a Unity NUnit results file, or None if it is missing or unreadable."""
    try:
        run = ET.parse(path).getroot()
        return int(run.get("total", 0)), int(run.get("failed", 0))
    except (OSError, ET.ParseError, ValueError):
        return None


def exit_code(results):
    return 1 if any(r.status == FAILED for r in results) else 0


def tracker_python(tracker_dir):
    """The tracker's own venv (MediaPipe lives there), else this Python."""
    exe = os.path.join(tracker_dir, ".venv", "Scripts", "python.exe")
    return exe if os.path.isfile(exe) else sys.executable


def run_python_suite(name):
    if name == "runner":
        cwd, python, args = ROOT, sys.executable, ["test_run_tests"]
    else:
        cwd = os.path.join(ROOT, name)
        python = tracker_python(cwd) if name == "tracker" else sys.executable
        args = ["discover", "-p", "test_*.py"]
    start = time.time()
    proc = subprocess.run([python, "-m", "unittest", *args], cwd=cwd,
                          capture_output=True, text=True, encoding="utf-8", errors="replace")
    output = proc.stdout + proc.stderr
    tests, bad = parse_unittest(output)
    ok = proc.returncode == 0 and tests > 0
    note = "" if ok else output.strip().splitlines()[-1] if output.strip() else "no output"
    if not ok and tests == 0:
        note = "no tests ran: " + note
    return Result(name, PASSED if ok else FAILED, tests, bad, time.time() - start, note), output


def default_unity_exe():
    try:
        with open(os.path.join(UNITY_PROJECT, "ProjectSettings", "ProjectVersion.txt"), encoding="utf-8") as f:
            version = re.search(r"m_EditorVersion:\s*(\S+)", f.read()).group(1)
    except (OSError, AttributeError):
        return None
    return os.path.join(os.environ.get("ProgramFiles", r"C:\Program Files"),
                        "Unity", "Hub", "Editor", version, "Editor", "Unity.exe")


def editor_has_project_open():
    """The open Editor keeps Temp/UnityLockfile locked; a closed one may leave the file behind unlocked."""
    lock = os.path.join(UNITY_PROJECT, "Temp", "UnityLockfile")
    if not os.path.exists(lock):
        return False
    try:
        with open(lock, "a"):
            return False
    except OSError:
        return True


def run_unity_suite(unity_exe):
    start = time.time()
    if not unity_exe or not os.path.isfile(unity_exe):
        return Result("unity", SKIPPED, 0, 0, 0.0, f"Unity not found at {unity_exe}"), ""
    if editor_has_project_open():
        return Result("unity", SKIPPED, 0, 0, 0.0, "the Unity Editor has the project open; close it to run these"), ""
    tmp = tempfile.mkdtemp(prefix="theraquest_unity_")
    results_xml, log = os.path.join(tmp, "results.xml"), os.path.join(tmp, "unity.log")
    cmd = [unity_exe, "-batchmode", "-nographics", "-projectPath", UNITY_PROJECT,
           "-runTests", "-testPlatform", "EditMode", "-testResults", results_xml, "-logFile", log]
    try:
        proc = subprocess.run(cmd, timeout=1800)
        code = proc.returncode
    except subprocess.TimeoutExpired:
        return Result("unity", FAILED, 0, 0, time.time() - start, f"timed out after 30 min; log: {log}"), ""
    counts = parse_nunit(results_xml)
    if counts is None:
        return Result("unity", FAILED, 0, 0, time.time() - start, f"no results (exit {code}); log: {log}"), ""
    tests, failed = counts
    ok = code == 0 and failed == 0 and tests > 0
    note = "" if ok else f"exit {code}; results: {results_xml}"
    return Result("unity", PASSED if ok else FAILED, tests, failed, time.time() - start, note), ""


def print_table(results):
    print()
    print(f"{'Suite':<12}{'Status':<9}{'Tests':>6}{'Failed':>8}{'Time':>9}  Note")
    print("-" * 70)
    for r in results:
        print(f"{r.name:<12}{r.status:<9}{r.tests:>6}{r.failures:>8}{r.seconds:>8.1f}s  {r.note}")
    print("-" * 70)
    total = sum(r.tests for r in results)
    skipped = [r.name for r in results if r.status == SKIPPED]
    if exit_code(results):
        verdict = "FAILED"
    elif any(r.status == PASSED for r in results):
        verdict = "ALL PASSED"
    else:
        verdict = "NOTHING RAN"
    print(f"{verdict}: {total} tests" + (f"  (SKIPPED: {', '.join(skipped)})" if skipped else ""))


def main(argv=None):
    ap = argparse.ArgumentParser(description="Run all TheraQuest test suites.")
    ap.add_argument("--only", help="comma-separated suites: " + ",".join(ALL_SUITES))
    ap.add_argument("--no-unity", action="store_true", help="skip the Unity EditMode tests")
    ap.add_argument("--unity-exe", help="path to Unity.exe (default: the project's version under Unity Hub)")
    args = ap.parse_args(argv)

    suites = list(ALL_SUITES)
    if args.only:
        suites = [s.strip() for s in args.only.split(",") if s.strip()]
        unknown = [s for s in suites if s not in ALL_SUITES]
        if unknown:
            ap.error("unknown suite(s): " + ", ".join(unknown))

    results = []
    for name in suites:
        if name == "unity":
            if args.no_unity:
                results.append(Result("unity", SKIPPED, 0, 0, 0.0, "--no-unity"))
                continue
            print("Running unity EditMode tests (batch mode, this takes a few minutes)...", flush=True)
            result, output = run_unity_suite(args.unity_exe or default_unity_exe())
        else:
            print(f"Running {name}...", flush=True)
            result, output = run_python_suite(name)
        if result.status == FAILED and output:
            print(output)
        results.append(result)

    print_table(results)
    return exit_code(results)


if __name__ == "__main__":
    sys.exit(main())
