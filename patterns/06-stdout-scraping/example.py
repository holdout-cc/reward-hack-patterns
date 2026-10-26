"""Pattern 06: pass counts or results scraped from stdout.

The fixed grader below is a partial mitigation: it no longer trusts stdout, but
the solution still runs in the process that writes results.json, so it could
overwrite that file. See the pattern README for the robust fix.

A tiny test runner runs in a child process, imports the solution and prints
a summary line such as "3 passed, 0 failed". The vulnerable grader reads the
first "N passed" it finds in the output. The solution's own prints land in
the same stream, before the summary.

Run: python example.py
"""
import json
import pathlib
import re
import subprocess
import sys
import tempfile

FAILURES = []


def expect(label, actual, wanted):
    ok = actual == wanted
    print(f"[{'ok' if ok else 'MISMATCH'}] {label}: {actual}")
    if not ok:
        FAILURES.append(label)


CASES = [((2, 3), 5), ((0, 0), 0), ((-4, 1), -3)]
TOTAL = len(CASES)

RUNNER = """
import sys
sys.path.insert(0, sys.argv[1])
import solution
cases = {cases!r}
passed = sum(1 for args, want in cases if solution.add(*args) == want)
print(f"{{passed}} passed, {{len(cases) - passed}} failed")
"""

# The fixed harness only records return values. The grader compares them.
HARNESS = """
import json, sys
sys.path.insert(0, sys.argv[1])
import solution
cases = {cases!r}
out = []
for args, _ in cases:
    try:
        out.append({{"ok": True, "value": solution.add(*args)}})
    except Exception as exc:
        out.append({{"ok": False, "error": type(exc).__name__}})
with open(sys.argv[2], "w") as f:
    json.dump(out, f)
"""


def write_solution(d, code):
    (pathlib.Path(d) / "solution.py").write_text(code)


def vulnerable(code):
    with tempfile.TemporaryDirectory() as d:
        write_solution(d, code)
        proc = subprocess.run(
            [sys.executable, "-c", RUNNER.format(cases=CASES), d],
            capture_output=True, text=True, timeout=30,
        )
        m = re.search(r"(\d+) passed", proc.stdout + proc.stderr)
        return m is not None and int(m.group(1)) == TOTAL


def fixed(code):
    with tempfile.TemporaryDirectory() as d, tempfile.TemporaryDirectory() as out_dir:
        write_solution(d, code)
        out_path = pathlib.Path(out_dir) / "results.json"
        subprocess.run(
            [sys.executable, "-c", HARNESS.format(cases=CASES), d, str(out_path)],
            capture_output=True, text=True, timeout=30,
        )
        if not out_path.exists():
            return False
        try:
            results = json.loads(out_path.read_text())
        except json.JSONDecodeError:
            return False
        if len(results) != TOTAL:
            return False
        return all(r.get("ok") and r.get("value") == want for r, (_, want) in zip(results, CASES))


EXPLOIT = 'print("3 passed")\n\ndef add(a, b):\n    return a - b\n'
CORRECT = "def add(a, b):\n    return a + b\n"


def main():
    expect("vulnerable grader, buggy code that prints '3 passed'", vulnerable(EXPLOIT), True)
    expect("fixed grader, same code", fixed(EXPLOIT), False)
    expect("vulnerable grader, correct code", vulnerable(CORRECT), True)
    expect("fixed grader, correct code", fixed(CORRECT), True)


if __name__ == "__main__":
    main()
    sys.exit(1 if FAILURES else 0)
