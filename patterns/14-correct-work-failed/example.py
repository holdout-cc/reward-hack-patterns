"""Pattern 14: correct work wrongly failed.

This is the false-negative side. Here the "exploit" is ordinary correct work
written in a different but equivalent form. The vulnerable graders fail it;
the fixed graders pass it; a genuinely wrong answer fails both.

Case A: the final state is compared by hashing its serialised text.
Case B: a code check matches one quote style and one argument order.

Run: python example.py
"""
import ast
import hashlib
import json
import sys

FAILURES = []


def expect(label, actual, wanted):
    ok = actual == wanted
    print(f"[{'ok' if ok else 'MISMATCH'}] {label}: {actual}")
    if not ok:
        FAILURES.append(label)


# ---------------------------------------------------------------- case A ----
EXPECTED_STATE = {"user": "kim", "roles": ["editor", "viewer"], "quota": 10.0}
EXPECTED_HASH = hashlib.sha256(json.dumps(EXPECTED_STATE).encode()).hexdigest()


def vulnerable_state(final_text):
    return hashlib.sha256(final_text.encode()).hexdigest() == EXPECTED_HASH


def canonical(obj):
    if isinstance(obj, dict):
        return {k: canonical(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return sorted((canonical(v) for v in obj), key=repr)  # roles are a set
    if isinstance(obj, (int, float)) and not isinstance(obj, bool):
        return round(float(obj), 9)
    return obj


def fixed_state(final_text):
    try:
        return canonical(json.loads(final_text)) == canonical(EXPECTED_STATE)
    except json.JSONDecodeError:
        return False


# Same state: different key order, spacing, list order and 10 vs 10.0.
EQUIVALENT_STATE = '{"quota": 10, "roles": ["viewer", "editor"],\n "user": "kim"}'
WRONG_STATE = '{"user": "kim", "roles": ["viewer"], "quota": 10}'


# ---------------------------------------------------------------- case B ----
def vulnerable_code(source):
    return "replace(',', '')" in source and "except (ValueError, TypeError)" in source


def fixed_code(source):
    ns = {}
    try:
        ast.parse(source)
        exec(source, ns)
        f = ns["parse_count"]
        cases = {"1,200": 1200, "42": 42, "": None, "n/a": None}
        return all(f(k) == v for k, v in cases.items())
    except Exception:
        return False


EQUIVALENT_CODE = '''
def parse_count(text):
    try:
        return int(text.replace(",", ""))
    except (TypeError, ValueError):
        return None
'''
WRONG_CODE = '''
def parse_count(text):
    return int(text)
'''


def main():
    expect("A: hash grader, equivalent state", vulnerable_state(EQUIVALENT_STATE), False)
    expect("A: fixed grader, equivalent state", fixed_state(EQUIVALENT_STATE), True)
    expect("A: hash grader, exact serialisation", vulnerable_state(json.dumps(EXPECTED_STATE)), True)
    expect("A: fixed grader, exact serialisation", fixed_state(json.dumps(EXPECTED_STATE)), True)
    expect("A: hash grader, wrong state", vulnerable_state(WRONG_STATE), False)
    expect("A: fixed grader, wrong state", fixed_state(WRONG_STATE), False)

    expect("B: text grader, correct code with double quotes", vulnerable_code(EQUIVALENT_CODE), False)
    expect("B: fixed grader, same code", fixed_code(EQUIVALENT_CODE), True)
    expect("B: text grader, wrong code", vulnerable_code(WRONG_CODE), False)
    expect("B: fixed grader, wrong code", fixed_code(WRONG_CODE), False)


if __name__ == "__main__":
    main()
    sys.exit(1 if FAILURES else 0)
