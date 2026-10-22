"""Pattern 03: substring, containment and hedge matching.

Case A: a short-answer task graded with `gold in reply`.
Case B: a test-status parser that looks for "PASSED" anywhere in a line.

Run: python example.py
"""
import re
import string
import sys

FAILURES = []


def expect(label, actual, wanted):
    ok = actual == wanted
    print(f"[{'ok' if ok else 'MISMATCH'}] {label}: {actual}")
    if not ok:
        FAILURES.append(label)


# ---------------------------------------------------------------- case A ----
GOLD = "Lisbon"


def vulnerable_answer(reply):
    return GOLD.lower() in reply.lower()


def normalise(text):
    text = text.strip().lower()
    text = re.sub(r"^(the answer is|answer:)\s*", "", text)
    return text.strip(string.punctuation + " ")


def fixed_answer(reply):
    return normalise(reply) == normalise(GOLD)


HEDGE = "Lisbon, Madrid, Paris, Rome, Berlin"
NEGATED = "It is not Lisbon, it is Porto."
CORRECT_A = "The answer is Lisbon."

# ---------------------------------------------------------------- case B ----
# A pytest-style summary line for a failing test whose message is "PASSED".
FAILED_LINE = "FAILED tests/test_geo.py::test_distance - PASSED"
PASSED_LINE = "PASSED tests/test_geo.py::test_distance"


def vulnerable_status(line):
    if "PASSED" in line:
        return "PASSED"
    if "FAILED" in line:
        return "FAILED"
    return "UNKNOWN"


def fixed_status(line):
    # The status is the first token; anything after it is test id or message.
    first = line.split(maxsplit=1)[0] if line.strip() else ""
    return first if first in {"PASSED", "FAILED", "ERROR", "SKIPPED"} else "UNKNOWN"


def main():
    expect("A: substring grader, hedge list", vulnerable_answer(HEDGE), True)
    expect("A: substring grader, negated answer", vulnerable_answer(NEGATED), True)
    expect("A: fixed grader, hedge list", fixed_answer(HEDGE), False)
    expect("A: fixed grader, negated answer", fixed_answer(NEGATED), False)
    expect("A: substring grader, correct", vulnerable_answer(CORRECT_A), True)
    expect("A: fixed grader, correct", fixed_answer(CORRECT_A), True)

    expect("B: substring parser, failing test with message 'PASSED'", vulnerable_status(FAILED_LINE), "PASSED")
    expect("B: fixed parser, same line", fixed_status(FAILED_LINE), "FAILED")
    expect("B: substring parser, real pass", vulnerable_status(PASSED_LINE), "PASSED")
    expect("B: fixed parser, real pass", fixed_status(PASSED_LINE), "PASSED")


if __name__ == "__main__":
    main()
    sys.exit(1 if FAILURES else 0)
