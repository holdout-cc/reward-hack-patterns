"""Pattern 13: checks that ignore their own options.

Case A: a numeric scorer documented to take max_diff, which it accepts via
        **kwargs and never reads.
Case B: a JSON output check that takes a schema and only checks that the
        output parses.

Run: python example.py
"""
import json
import sys

FAILURES = []


def expect(label, actual, wanted):
    ok = actual == wanted
    print(f"[{'ok' if ok else 'MISMATCH'}] {label}: {actual}")
    if not ok:
        FAILURES.append(label)


PASS_AT = 0.99

# ---------------------------------------------------------------- case A ----
def vulnerable_numeric(output, expected, **options):
    # Documented: score = max(0, 1 - |output - expected| / max_diff)
    # Actual: options are swallowed and a relative formula is used instead.
    if output == expected:
        return 1.0
    return 1 - abs(output - expected) / (abs(output) + abs(expected))


def fixed_numeric(output, expected, *, max_diff):
    # No **kwargs: a misspelt or unsupported option raises TypeError.
    if max_diff == 0:
        return 1.0 if output == expected else 0.0
    return max(0.0, 1 - abs(output - expected) / max_diff)


# ---------------------------------------------------------------- case B ----
SCHEMA = {"invoice_id": str, "total": float}


def vulnerable_json(text, schema):
    try:
        json.loads(text)
        return True
    except json.JSONDecodeError:
        return False


def fixed_json(text, schema):
    try:
        obj = json.loads(text)
    except json.JSONDecodeError:
        return False
    if not isinstance(obj, dict) or set(obj) != set(schema):
        return False
    return all(isinstance(obj[k], t) and not isinstance(obj[k], bool) for k, t in schema.items())


def main():
    # The task asks for a year; 2025 is wrong, the answer is 2024.
    s = vulnerable_numeric(2025, 2024, max_diff=0)
    expect("A: vulnerable, wrong year with max_diff=0 passes the 0.99 bar", s >= PASS_AT, True)
    expect("A: fixed, wrong year with max_diff=0", fixed_numeric(2025, 2024, max_diff=0) >= PASS_AT, False)
    expect("A: vulnerable, correct year", vulnerable_numeric(2024, 2024, max_diff=0) >= PASS_AT, True)
    expect("A: fixed, correct year", fixed_numeric(2024, 2024, max_diff=0) >= PASS_AT, True)
    try:
        fixed_numeric(2025, 2024, max_dif=0)  # typo
        raised = False
    except TypeError:
        raised = True
    expect("A: fixed scorer rejects an unknown option", raised, True)

    wrong = '["not", "an", "invoice"]'
    right = '{"invoice_id": "INV-9", "total": 41.5}'
    expect("B: vulnerable, JSON that ignores the schema", vulnerable_json(wrong, SCHEMA), True)
    expect("B: fixed, same output", fixed_json(wrong, SCHEMA), False)
    expect("B: vulnerable, valid invoice", vulnerable_json(right, SCHEMA), True)
    expect("B: fixed, valid invoice", fixed_json(right, SCHEMA), True)


if __name__ == "__main__":
    main()
    sys.exit(1 if FAILURES else 0)
