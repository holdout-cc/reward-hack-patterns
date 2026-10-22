"""Pattern 11: format-only or partial-credit rewards that add up past the pass threshold.

A weighted rubric: format, tool use and explanation length are cheap; only
the last item checks the answer. Pass threshold 0.6.

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


GOLD = 128
THRESHOLD = 0.6


def has_format(t):
    return re.search(r"^Final answer: -?\d+$", t["reply"], re.M) is not None


def used_tool(t):
    return "calculator" in t["tools_called"]


def explained(t):
    return len(t["reply"].split()) >= 15


def correct(t):
    m = re.search(r"^Final answer: (-?\d+)$", t["reply"], re.M)
    return m is not None and int(m.group(1)) == GOLD


RUBRIC = [(has_format, 0.2), (used_tool, 0.2), (explained, 0.2), (correct, 0.4)]


def weighted(t):
    return sum(w for check, w in RUBRIC if check(t))


# --- vulnerable: pass if the weighted sum reaches the threshold -------------
def vulnerable(t):
    return weighted(t) >= THRESHOLD


# --- fixed: correctness is a gate; the other items only shape the score -----
def fixed(t):
    return correct(t) and weighted(t) >= THRESHOLD


def max_score_without(check_name):
    """Lint: the best score reachable while a given item is failed."""
    return sum(w for check, w in RUBRIC if check.__name__ != check_name)


WRONG_BUT_TIDY = {
    "tools_called": ["calculator"],
    "reply": "I multiplied the two numbers with the calculator, checked the units twice "
    "and rounded to the nearest whole number.\nFinal answer: 112",
}
CORRECT = {
    "tools_called": ["calculator"],
    "reply": "I multiplied 16 by 8 with the calculator, checked that the units are "
    "boxes, and no rounding was needed.\nFinal answer: 128",
}


def main():
    expect("vulnerable, wrong answer with format/tool/explanation", vulnerable(WRONG_BUT_TIDY), True)
    expect("fixed, same reply", fixed(WRONG_BUT_TIDY), False)
    expect("vulnerable, correct reply", vulnerable(CORRECT), True)
    expect("fixed, correct reply", fixed(CORRECT), True)
    expect("lint: best score with 'correct' failed reaches the threshold",
           round(max_score_without("correct"), 6) >= THRESHOLD, True)


if __name__ == "__main__":
    main()
    sys.exit(1 if FAILURES else 0)
