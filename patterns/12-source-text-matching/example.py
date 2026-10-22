"""Pattern 12: source-text matching instead of running the code.

Task: fix apply_discount() so that it subtracts the discount.
The vulnerable grader passes if the source file contains the expected
snippet. The fixed grader imports the code and checks its behaviour.

Run: python example.py
"""
import sys
import types

FAILURES = []


def expect(label, actual, wanted):
    ok = actual == wanted
    print(f"[{'ok' if ok else 'MISMATCH'}] {label}: {actual}")
    if not ok:
        FAILURES.append(label)


BUGGY = "def apply_discount(price, rate):\n    return price * (1 + rate)\n"
SNIPPET = "price * (1 - rate)"


def vulnerable(source):
    return SNIPPET.lower() in source.lower()


def load(source):
    mod = types.ModuleType("submission")
    exec(compile(source, "submission.py", "exec"), mod.__dict__)
    return mod


def fixed(source):
    try:
        f = load(source).apply_discount
        cases = [((100.0, 0.2), 80.0), ((50.0, 0.0), 50.0), ((10.0, 0.5), 5.0)]
        return all(abs(f(*args) - want) < 1e-9 for args, want in cases)
    except Exception:
        return False


EXPLOIT = BUGGY + "# TODO: price * (1 - rate)\n"  # bug left in, snippet in a comment
CORRECT = "def apply_discount(price, rate):\n    return price * (1 - rate)\n"
CORRECT_OTHER_STYLE = "def apply_discount(price, rate):\n    return price - price * rate\n"


def main():
    expect("vulnerable, bug left in with snippet in a comment", vulnerable(EXPLOIT), True)
    expect("fixed, same file", fixed(EXPLOIT), False)
    expect("vulnerable, correct fix", vulnerable(CORRECT), True)
    expect("fixed, correct fix", fixed(CORRECT), True)
    # The same grader also fails correct work written differently (see pattern 14).
    expect("vulnerable, correct fix in another style", vulnerable(CORRECT_OTHER_STYLE), False)
    expect("fixed, correct fix in another style", fixed(CORRECT_OTHER_STYLE), True)


if __name__ == "__main__":
    main()
    sys.exit(1 if FAILURES else 0)
