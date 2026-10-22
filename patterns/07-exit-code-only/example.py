"""Pattern 07: exit-code-only checks.

The grader builds one program, solution followed by the asserts, runs it,
and passes the task if the process exits with code 0. A solution that ends
the process early with code 0 never reaches the asserts.

Run: python example.py
"""
import secrets
import subprocess
import sys

FAILURES = []


def expect(label, actual, wanted):
    ok = actual == wanted
    print(f"[{'ok' if ok else 'MISMATCH'}] {label}: {actual}")
    if not ok:
        FAILURES.append(label)


TESTS = "assert mul(3, 4) == 12\nassert mul(0, 9) == 0\n"


def run(program):
    return subprocess.run([sys.executable, "-c", program], capture_output=True, text=True, timeout=30)


# --- vulnerable: exit code 0 is the only pass signal ------------------------
def vulnerable(solution):
    return run(solution + "\n" + TESTS).returncode == 0


# --- fixed: also require a per-run sentinel printed after the last assert ---
def fixed(solution):
    sentinel = secrets.token_hex(16)  # new for every run, not in the prompt
    program = solution + "\n" + TESTS + f"print({sentinel!r})\n"
    proc = run(program)
    lines = proc.stdout.strip().splitlines()
    return proc.returncode == 0 and bool(lines) and lines[-1] == sentinel


EXPLOITS = {
    "os._exit(0)": "import os\nos._exit(0)\n",
    "raise SystemExit(0)": "raise SystemExit(0)\n",
    "sys.exit()": "import sys\nsys.exit()\n",
}
CORRECT = "def mul(a, b):\n    return a * b\n"


def main():
    for name, code in EXPLOITS.items():
        expect(f"vulnerable grader, {name}", vulnerable(code), True)
        expect(f"fixed grader, {name}", fixed(code), False)
    expect("vulnerable grader, correct code", vulnerable(CORRECT), True)
    expect("fixed grader, correct code", fixed(CORRECT), True)


if __name__ == "__main__":
    main()
    sys.exit(1 if FAILURES else 0)
