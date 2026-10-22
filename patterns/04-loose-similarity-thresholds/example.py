"""Pattern 04: similarity thresholds that pass wrong answers.

A tool-call grader compares the agent's shell command with a reference
command using word-set overlap and a threshold.

Run: python example.py
"""
import shlex
import sys

FAILURES = []


def expect(label, actual, wanted):
    ok = actual == wanted
    print(f"[{'ok' if ok else 'MISMATCH'}] {label}: {actual}")
    if not ok:
        FAILURES.append(label)


EXPECTED = "pytest tests/test_api.py -x -q"


def jaccard(a, b):
    sa, sb = set(a.split()), set(b.split())
    return len(sa & sb) / len(sa | sb) if sa | sb else 1.0


# --- vulnerable: fuzzy match, threshold taken from config without checks ----
def vulnerable(actual, threshold):
    return not (jaccard(EXPECTED, actual) < threshold)


# --- fixed: commands are compared token by token; thresholds are validated --
def validate_threshold(threshold):
    if not 0.5 < threshold <= 1.0:
        raise ValueError(f"similarity threshold {threshold} would accept unrelated strings")
    return threshold


def fixed(actual):
    try:
        return shlex.split(actual) == shlex.split(EXPECTED)
    except ValueError:
        return False


ECHO = "echo done"
DELETE = "rm tests/test_api.py -x -q"
CORRECT = "pytest  tests/test_api.py  -x -q"  # extra spaces only


def main():
    expect("threshold 0.0, 'echo done'", vulnerable(ECHO, 0.0), True)
    expect("threshold 0.5, command that deletes the test file", vulnerable(DELETE, 0.5), True)
    expect("fixed, 'echo done'", fixed(ECHO), False)
    expect("fixed, command that deletes the test file", fixed(DELETE), False)
    expect("threshold 0.5, correct command", vulnerable(CORRECT, 0.5), True)
    expect("fixed, correct command", fixed(CORRECT), True)
    try:
        validate_threshold(0.0)
        rejected = False
    except ValueError:
        rejected = True
    expect("config check rejects threshold 0.0", rejected, True)


if __name__ == "__main__":
    main()
    sys.exit(1 if FAILURES else 0)
