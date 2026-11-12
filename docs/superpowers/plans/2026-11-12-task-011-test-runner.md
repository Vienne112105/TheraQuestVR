# TASK-011: One script that runs all test suites

Backlog item, not a milestone (no `current_milestone` change). Branch: new `task-011-test-runner` from `main`.

## Goal
`python run_tests.py` (in `Main/TheraQuestVR/`) runs every suite, prints one table (suite, status, tests run, failures, seconds) and exits non-zero if any suite fails.

## Restraint (YAGNI / stdlib)
- Single stdlib-only file, no pytest, no config file, no CI wiring.
- Reuse each suite's existing runner: `python -m unittest` for Python, Unity's own `-runTests` for EditMode.

## Suites
| Suite | Working dir | Command | Python |
|---|---|---|---|
| server | `server/` | `-m unittest discover -p "test_*.py"` | `sys.executable` |
| tracker | `tracker/` | same | `tracker/.venv/Scripts/python.exe` if present (MediaPipe lives there), else `sys.executable` |
| evaluation | `evaluation/` | same | `sys.executable` |
| unity | `unity/` | `Unity.exe -batchmode -nographics -runTests -testPlatform EditMode -projectPath unity -testResults <tmp>.xml` | n/a |

## Unity handling
- Editor path: `C:\Program Files\Unity\Hub\Editor\6000.6.5f1\Editor\Unity.exe`, version read from `ProjectSettings/ProjectVersion.txt`; override with `--unity-exe`.
- Report **SKIPPED** (not failed) when the exe is missing, or when `unity/Temp/UnityLockfile` shows the Editor has the project open (batch mode cannot open it). `--no-unity` skips on purpose. Skipped never hides a failure but is printed loudly.
- Counts parsed from the NUnit XML (`test-run` attributes `total`, `failed`).
- Run it last (slowest).

## Flags
`--only server,tracker` / `--no-unity` / `--unity-exe PATH`. Nothing else.

## Tests (test first)
`test_run_tests.py` beside the script, pure parsers only (no suites launched):
1. parse unittest output "Ran N tests ... OK" and "FAILED (failures=2, errors=1)".
2. parse NUnit XML sample into total/failed.
3. exit code non-zero when any result is FAILED; zero when all PASSED or SKIPPED.
4. tracker python selection falls back to `sys.executable` when no venv.

## Steps
1. Write `test_run_tests.py` (red), then `run_tests.py` (green).
2. Run `python run_tests.py --no-unity`; confirm counts match last known (server 66, authorization 13, backup 11 inside server's discover; tracker 96).
3. With the Editor closed, run the full script; confirm Unity 91.
4. One README line under the tests section (next to line 56).
5. Brain: move TASK-011 to Done in `40_BACKLOG.md`; shutdown summary. Commit on the branch.

## Done when
Full run reports all four suites with the known counts, a failing test makes exit code 1, and Unity-open gives SKIPPED with a reason.

## Risks
Unity batch run can take minutes and fails if the Editor holds the project: handled by the lockfile check. Server tests use throwaway databases (existing `testsupport.py`), so the live database is not touched.
