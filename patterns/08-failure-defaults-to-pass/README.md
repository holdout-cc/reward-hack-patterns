# RHP-08. Exceptions, missing data and crashes that default to pass or "skipped"

## What it is

When a check cannot run, the grader treats it as passed, or marks it skipped and leaves it out. Common forms: `except Exception: return True`; `pytest.skip()` when the data to check is missing; `dict.get(field, "")` so a missing field counts as "correctly empty"; skipped criteria dropped before the pass rule is applied; and a failure path that writes a default score which happens to be the best score (0.0 on a lower-is-better metric). The agent's job is then to make the check unable to run.

## Why it matters

Breaking the grader's input is usually easier than producing the right output, so a policy that finds this path will keep using it. In evals, these tasks reward outputs that are not even in the right shape, and the pass rate looks fine because nothing is reported as failed.

## Vulnerable grader and exploit

An all-or-nothing form task: pass if no check failed.

```python
def vulnerable_form(doc):
    boxes = extract_checkboxes(doc)          # {} for a document without form fields
    results = []
    for name, want in REQUIRED.items():
        if not boxes:
            results.append("skipped")
            continue
        results.append("passed" if boxes.get(name) == want else "failed")
    return "failed" not in results

PLAIN_TEXT_DOC = {"text": "Name: Jo Bloggs  Claim: 400"}   # passes
```

Two more in the example: a parser wrapped in `except Exception: return True`, and a perplexity reward whose failure path returns `0.0`, which ranks an empty submission above every real run.

## Fixed grader

A required check passes only on positive evidence. Missing data, skips and exceptions are failures, recorded with a reason.

```python
def fixed_form(doc):
    boxes = extract_checkboxes(doc)
    return all(name in boxes and boxes[name] == want for name, want in REQUIRED.items())

def fixed_perplexity(run):
    if run.get("crashed") or not run.get("selection"):
        return math.inf          # worst value, plus an explicit invalid flag for consumers
    return run["perplexity"]
```

If a task is pass/fail, write the rule as "every required check passed", not "no check failed". The two differ exactly when checks are skipped.

## How to test for it

- Submit an empty file, a file of the wrong type, and a file with the right text but none of the expected structure. All must fail.
- Make the grader's parser throw (wrong encoding, malformed JSON, a string where a number is expected). The task must fail.
- For each pytest-based verifier, count skipped tests on a bad submission. Any skip of a required check is a bug.
- For metrics where lower is better, check what score every failure path writes, and what a consumer that only reads the number will do with it.

## Seen in the wild

- [UiPath/coder_eval#234](https://github.com/UiPath/coder_eval/issues/234): when checkbox extraction returns `{}`, all 12 checkbox tests call `pytest.skip()`, and missing fields read as `""`, so a text-only PDF with no form fields scores 1.0.
- [Handshake-AI-Research/ATLAS-Finance#12](https://github.com/Handshake-AI-Research/ATLAS-Finance/issues/12): `judge_pass` drops `skipped` criteria before checking the critical ones, and a failed section gate skips its whole section, so not attempting a gated section scores better on pass@k than attempting it and missing one item.
- [scaleapi/rsi-benchmark#102](https://github.com/scaleapi/rsi-benchmark/issues/102): in the data-curation sample every failure path writes reward `0.0` on a lower-is-better perplexity metric, so an empty or invalid submission outranks every real run, including the reference.
- [scaleapi/agentenv-framework#305](https://github.com/scaleapi/agentenv-framework/issues/305): in reward mode a non-zero exit from `test.sh` is described as "already recorded as score 0", but nothing sets it to 0; whatever is in the reward file is used.

## Run the example

```
python example.py
```
