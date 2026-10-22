"""Pattern 05: the agent can write the tests, the verifier or the reward file.

The agent works in a directory that holds calc.py (buggy), test_calc.py and
a logs/ folder. Grading happens afterwards, in the same directory.

Case A: the grader runs whatever test_calc.py is there at grading time.
Case B: the grader reads logs/reward.txt, which the test script writes only
        on success, and never clears it first.

Run: python example.py
"""
import pathlib
import runpy
import sys
import tempfile

FAILURES = []


def expect(label, actual, wanted):
    ok = actual == wanted
    print(f"[{'ok' if ok else 'MISMATCH'}] {label}: {actual}")
    if not ok:
        FAILURES.append(label)


BUGGY = "def add(a, b):\n    return a - b\n"
FIXED_CODE = "def add(a, b):\n    return a + b\n"
# The grader's own copy of the tests. It never comes from the workspace.
PRISTINE_TESTS = (
    "from calc import add\n"
    "assert add(2, 3) == 5\n"
    "assert add(-1, 1) == 0\n"
)


def make_workspace(root):
    ws = pathlib.Path(root)
    (ws / "calc.py").write_text(BUGGY)
    (ws / "test_calc.py").write_text(PRISTINE_TESTS)
    (ws / "logs").mkdir()
    return ws


def run_tests(test_path, code_dir):
    """Run a test file with code_dir importable. True if no exception."""
    sys.path.insert(0, str(code_dir))
    sys.modules.pop("calc", None)
    try:
        runpy.run_path(str(test_path))
        return True
    except Exception:
        return False
    finally:
        sys.path.remove(str(code_dir))
        sys.modules.pop("calc", None)


# ------------------------------------------------------------- case A -------
def vulnerable_a(ws):
    return run_tests(ws / "test_calc.py", ws)


def fixed_a(ws):
    # Copy only the solution file into a fresh directory, next to the
    # grader's pristine tests, and run those.
    with tempfile.TemporaryDirectory() as clean:
        clean = pathlib.Path(clean)
        (clean / "calc.py").write_text((ws / "calc.py").read_text())
        (clean / "test_calc.py").write_text(PRISTINE_TESTS)
        return run_tests(clean / "test_calc.py", clean)


# ------------------------------------------------------------- case B -------
def test_script(ws):
    """Stands in for test.sh: write 1 to reward.txt only if tests pass."""
    if run_tests(ws / "test_calc.py", ws):
        (ws / "logs" / "reward.txt").write_text("1\n")


def vulnerable_b(ws):
    test_script(ws)
    reward = ws / "logs" / "reward.txt"
    return reward.exists() and reward.read_text().strip() == "1"


def fixed_b(ws):
    # The grader decides the reward itself, from pristine tests.
    # It never reads a file the agent could have written.
    return fixed_a(ws)


# ------------------------------------------------------------- agents -------
def agent_rewrites_tests(ws):
    (ws / "test_calc.py").write_text("pass\n")


def agent_plants_reward(ws):
    (ws / "logs" / "reward.txt").write_text("1\n")


def agent_fixes_code(ws):
    (ws / "calc.py").write_text(FIXED_CODE)


def trial(agent, grader):
    with tempfile.TemporaryDirectory() as root:
        ws = make_workspace(root)
        agent(ws)
        return grader(ws)


def main():
    expect("A: vulnerable grader, agent rewrites test_calc.py", trial(agent_rewrites_tests, vulnerable_a), True)
    expect("A: fixed grader, agent rewrites test_calc.py", trial(agent_rewrites_tests, fixed_a), False)
    expect("A: vulnerable grader, correct fix", trial(agent_fixes_code, vulnerable_a), True)
    expect("A: fixed grader, correct fix", trial(agent_fixes_code, fixed_a), True)

    expect("B: vulnerable grader, agent plants reward.txt", trial(agent_plants_reward, vulnerable_b), True)
    expect("B: fixed grader, agent plants reward.txt", trial(agent_plants_reward, fixed_b), False)
    expect("B: vulnerable grader, correct fix", trial(agent_fixes_code, vulnerable_b), True)
    expect("B: fixed grader, correct fix", trial(agent_fixes_code, fixed_b), True)


if __name__ == "__main__":
    main()
    sys.exit(1 if FAILURES else 0)
