"""Pattern 10: LLM-judge output parsing that defaults to the positive label.

Case A: the judge returns JSON and the grader uses Python truthiness, so the
        string "false" counts as met.
Case B: the judge returns free text and the grader passes unless it finds
        the word "FAIL", so any other wording (or an empty reply) passes.

The judge outputs below are fixed strings; no model is called.

Run: python example.py
"""
import json
import re
import sys

FAILURES = []


def expect(label, actual, wanted):
    ok = actual == wanted
    print(f"[{'ok' if ok else 'MISMATCH'}] {label}: {actual}")
    if not ok:
        FAILURES.append(label)


class JudgeParseError(Exception):
    pass


# ---------------------------------------------------------------- case A ----
def vulnerable_json(judge_output):
    return bool(json.loads(judge_output)["met"])


def fixed_json(judge_output):
    try:
        met = json.loads(judge_output)["met"]
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        raise JudgeParseError(f"unreadable verdict: {judge_output!r}") from exc
    if isinstance(met, bool):
        return met
    raise JudgeParseError(f"'met' must be a JSON boolean, got {met!r}")


# ---------------------------------------------------------------- case B ----
def vulnerable_text(judge_output):
    return "FAIL" not in judge_output.upper()


def fixed_text(judge_output):
    lines = [ln.strip() for ln in judge_output.strip().splitlines() if ln.strip()]
    m = re.fullmatch(r"VERDICT:\s*(PASS|FAIL)", lines[-1]) if lines else None
    if m is None:
        raise JudgeParseError(f"no verdict line in {judge_output!r}")
    return m.group(1) == "PASS"


def grade(parser, judge_output):
    """What the reward pipeline sees. Parse errors score 0 and are logged."""
    try:
        return parser(judge_output)
    except JudgeParseError as exc:
        print(f"      (parse error, scored 0: {exc})")
        return False


def main():
    expect('A: vulnerable, judge wrote {"met": "false"}', grade(vulnerable_json, '{"met": "false"}'), True)
    expect('A: fixed, judge wrote {"met": "false"}', grade(fixed_json, '{"met": "false"}'), False)
    expect('A: vulnerable, {"met": false}', grade(vulnerable_json, '{"met": false}'), False)
    expect('A: fixed, {"met": false}', grade(fixed_json, '{"met": false}'), False)
    expect('A: vulnerable, {"met": true}', grade(vulnerable_json, '{"met": true}'), True)
    expect('A: fixed, {"met": true}', grade(fixed_json, '{"met": true}'), True)

    negative = "The response is incorrect: the total is wrong."
    expect("B: vulnerable, negative verdict without the word FAIL", grade(vulnerable_text, negative), True)
    expect("B: fixed, same verdict", grade(fixed_text, negative), False)
    expect("B: vulnerable, empty judge reply", grade(vulnerable_text, ""), True)
    expect("B: fixed, empty judge reply", grade(fixed_text, ""), False)
    positive = "The total matches the invoice.\nVERDICT: PASS"
    expect("B: vulnerable, correct work", grade(vulnerable_text, positive), True)
    expect("B: fixed, correct work", grade(fixed_text, positive), True)


if __name__ == "__main__":
    main()
    sys.exit(1 if FAILURES else 0)
