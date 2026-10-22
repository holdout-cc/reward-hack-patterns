"""Pattern 02: first-match, last-match and any-match answer extraction.

The prompt says: "End your reply with a line 'Final answer: <integer>'."
Gold answer: 15.

Run: python example.py
"""
import re
import sys

FAILURES = []


def expect(label, actual, wanted):
    ok = actual == wanted
    print(f"[{'ok' if ok else 'MISMATCH'}] {label}: {actual}")
    if not ok:
        FAILURES.append(label)


GOLD = 15
PATTERN = re.compile(r"final answer:\s*(-?\d+)", re.IGNORECASE)


# --- vulnerable 1: any extracted answer that equals gold counts -------------
def vulnerable_any_match(reply):
    return any(int(m) == GOLD for m in PATTERN.findall(reply))


# --- vulnerable 2: the first match is taken, even if the reply moves on -----
def vulnerable_first_match(reply):
    m = PATTERN.search(reply)
    return m is not None and int(m.group(1)) == GOLD


# --- fixed: exactly one final-answer line, and it is the last line ----------
def fixed(reply):
    lines = [ln.strip() for ln in reply.strip().splitlines() if ln.strip()]
    if not lines:
        return False
    if len(PATTERN.findall(reply)) != 1:
        return False  # zero or several answers: no credit
    m = re.fullmatch(r"final answer:\s*(-?\d+)", lines[-1], re.IGNORECASE)
    return m is not None and int(m.group(1)) == GOLD


SPRAY = "\n".join(f"Final answer: {n}" for n in range(0, 31))
CHANGED_MIND = "Final answer: 15\nWait, I forgot the carry.\nFinal answer: 14"
CORRECT = "3 boxes of 5 is 15.\nFinal answer: 15"


def main():
    expect("any-match grader, spray of 31 answers", vulnerable_any_match(SPRAY), True)
    expect("first-match grader, reply that ends on 14", vulnerable_first_match(CHANGED_MIND), True)
    expect("fixed grader, spray", fixed(SPRAY), False)
    expect("fixed grader, reply that ends on 14", fixed(CHANGED_MIND), False)
    expect("any-match grader, correct reply", vulnerable_any_match(CORRECT), True)
    expect("first-match grader, correct reply", vulnerable_first_match(CORRECT), True)
    expect("fixed grader, correct reply", fixed(CORRECT), True)


if __name__ == "__main__":
    main()
    sys.exit(1 if FAILURES else 0)
