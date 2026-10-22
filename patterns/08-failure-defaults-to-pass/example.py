"""Pattern 08: exceptions, missing data and crashes that default to pass.

Case A: a form-filling task. The grader extracts checkbox values from the
        submitted document and skips a check when nothing was extracted.
        The task is all-or-nothing: "pass if no check failed".
Case B: a check wrapped in try/except that returns True on any error.
Case C: a lower-is-better metric where the failure path writes 0.0.

Run: python example.py
"""
import math
import sys

FAILURES = []


def expect(label, actual, wanted):
    ok = actual == wanted
    print(f"[{'ok' if ok else 'MISMATCH'}] {label}: {actual}")
    if not ok:
        FAILURES.append(label)


# ---------------------------------------------------------------- case A ----
REQUIRED = {"is_resident": True, "has_prior_claim": False}


def extract_checkboxes(doc):
    return dict(doc.get("fields", {}))  # {} for a document without form fields


def vulnerable_form(doc):
    boxes = extract_checkboxes(doc)
    results = []
    for name, want in REQUIRED.items():
        if not boxes:
            results.append("skipped")  # "nothing to check"
            continue
        results.append("passed" if boxes.get(name) == want else "failed")
    return "failed" not in results


def fixed_form(doc):
    boxes = extract_checkboxes(doc)
    # Every required check must positively pass. Missing means failed.
    return all(name in boxes and boxes[name] == want for name, want in REQUIRED.items())


PLAIN_TEXT_DOC = {"text": "Name: Jo Bloggs  Claim: 400"}  # no form fields at all
CORRECT_DOC = {"text": "...", "fields": {"is_resident": True, "has_prior_claim": False}}


# ---------------------------------------------------------------- case B ----
def parse_amount(text):
    return float(text.replace("$", ""))


def vulnerable_amount(answer):
    try:
        return math.isclose(parse_amount(answer), 400.0)
    except Exception:
        return True  # "don't penalise the agent for our parser"


def fixed_amount(answer):
    try:
        return math.isclose(parse_amount(answer), 400.0)
    except Exception:
        return False


# ---------------------------------------------------------------- case C ----
# Reward is perplexity, lower is better. Real runs score around 360-430.
def vulnerable_perplexity(run):
    if run.get("crashed") or not run.get("selection"):
        return 0.0  # "failure" -- but 0.0 is the best possible value here
    return run["perplexity"]


def fixed_perplexity(run):
    if run.get("crashed") or not run.get("selection"):
        return math.inf  # worst possible value, and callers also get invalid=True
    return run["perplexity"]


def best(scores):
    return min(scores, key=scores.get)


def main():
    expect("A: vulnerable, document with no form fields", vulnerable_form(PLAIN_TEXT_DOC), True)
    expect("A: fixed, document with no form fields", fixed_form(PLAIN_TEXT_DOC), False)
    expect("A: vulnerable, correctly filled form", vulnerable_form(CORRECT_DOC), True)
    expect("A: fixed, correctly filled form", fixed_form(CORRECT_DOC), True)

    expect("B: vulnerable, answer the parser chokes on", vulnerable_amount("four hundred"), True)
    expect("B: fixed, same answer", fixed_amount("four hundred"), False)
    expect("B: vulnerable, correct answer", vulnerable_amount("$400"), True)
    expect("B: fixed, correct answer", fixed_amount("$400"), True)

    runs = {"empty submission": {"selection": []}, "real run": {"selection": [1, 2], "perplexity": 367.3}}
    expect("C: vulnerable, best run on leaderboard", best({k: vulnerable_perplexity(v) for k, v in runs.items()}), "empty submission")
    expect("C: fixed, best run on leaderboard", best({k: fixed_perplexity(v) for k, v in runs.items()}), "real run")


if __name__ == "__main__":
    main()
    sys.exit(1 if FAILURES else 0)
