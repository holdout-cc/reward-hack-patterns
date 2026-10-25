# RHP-10. LLM-judge output parsing that defaults to the positive label

- **TL;DR:** The judge's verdict is parsed loosely, so `"false"`, other wording or an empty reply becomes a pass.
- **Typical impact:** Unmet criteria scored as met, with no error reported, and rewards that can shift when the judge model or prompt changes.
- **Quick test:** Feed the verdict parser `{"met": "false"}`, an empty string and a negative verdict that avoids your keyword. None may pass.
- **Automated check:** Not covered by grader-probe (the bug is in the verdict parser; test it directly with fixed judge outputs).

## What it is

A model-graded check asks the judge for a verdict and then parses the reply loosely. Two common forms: the judge returns JSON and the grader calls `bool()` on the value, so the string `"false"` (or `"no"`, or `"0"`) is truthy and becomes a pass; or the judge returns text and the grader passes unless it finds a specific negative keyword, so any other wording, a refusal or an empty reply is a pass. Either way, the parser's failure mode is the positive label.

## Why it matters

How often a judge quotes its booleans or skips the expected keyword depends on the judge model and the prompt, and it can change when either changes, so rewards drift without anyone touching the grader. When the graded output is in the judge's prompt, the agent may also be able to steer the judge's formatting. In evals, a parse failure that becomes a pass inflates scores in a way that never shows up as an error.

## Vulnerable grader and exploit

```python
def vulnerable_json(judge_output):
    return bool(json.loads(judge_output)["met"])

vulnerable_json('{"met": "false"}')        # True

def vulnerable_text(judge_output):
    return "FAIL" not in judge_output.upper()

vulnerable_text("The response is incorrect: the total is wrong.")   # True
vulnerable_text("")                                                  # True
```

## Fixed grader

Accept only the exact format you asked for. Anything else is a parse error, which scores 0 and is logged, so you can see how often it happens.

```python
def fixed_json(judge_output):
    try:
        met = json.loads(judge_output)["met"]
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        raise JudgeParseError(f"unreadable verdict: {judge_output!r}") from exc
    if isinstance(met, bool):
        return met
    raise JudgeParseError(f"'met' must be a JSON boolean, got {met!r}")

def fixed_text(judge_output):
    lines = [ln.strip() for ln in judge_output.strip().splitlines() if ln.strip()]
    m = re.fullmatch(r"VERDICT:\s*(PASS|FAIL)", lines[-1]) if lines else None
    if m is None:
        raise JudgeParseError(f"no verdict line in {judge_output!r}")
    return m.group(1) == "PASS"
```

If you would rather map `"true"`/`"false"` strings explicitly, do that with a fixed table and still reject everything else. Structured outputs or a tool-call schema with a boolean field also help, but keep the strict parse.

Note that failing closed can turn into the opposite bug when a criterion has negative weight: a parse error on a penalty criterion should not apply the penalty either. Record it as an error and handle it separately.

## How to test for it

- Feed the parser `{"met": "false"}`, `{"met": "no"}`, `{"met": 0}`, `{"met": null}`, `{}`, an empty string, a refusal, and a verdict in a code fence. Only the exact positive form should pass.
- Feed the text parser a negative verdict that avoids your keyword ("incorrect", "does not meet", "no").
- Log the raw judge output and the parsed value side by side for a sample of real runs and look for disagreements.

## Seen in the wild

- [Handshake-AI-Research/gandalf-the-grader#47](https://github.com/Handshake-AI-Research/gandalf-the-grader/issues/47): `Verdict.from_raw` normalises `met` with Python truthiness, so a judge verdict of `"met": "false"` or `"no"` is stored as met, and an empty workspace with all-false quoted verdicts scores 1.0.

## Run the example

```
python example.py
```
