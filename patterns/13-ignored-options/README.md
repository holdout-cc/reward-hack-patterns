# 13. Checks that ignore their own options

## What it is

A scorer or verifier accepts an option that should make it stricter (a tolerance, a schema, a step budget, a required field list) and then does not use it. Often the option is swallowed by `**kwargs`, or passed to a script that is trusted to honour it, or documented but never implemented. The caller believes the check is tight; it runs with its loose default, or with no constraint at all. No error is raised, so the mismatch survives code review and tests that only check the happy path.

## Why it matters

The author picked a tolerance or schema because looser outputs are wrong for the task, so every output between the documented bar and the real one is a wrong answer that gets credit, in training and in reported scores. Because nothing fails loudly, the gap is usually found only by someone reading the scorer's code.

## Vulnerable grader and exploit

```python
def vulnerable_numeric(output, expected, **options):
    # Documented: score = max(0, 1 - |output - expected| / max_diff)
    if output == expected:
        return 1.0
    return 1 - abs(output - expected) / (abs(output) + abs(expected))

vulnerable_numeric(2025, 2024, max_diff=0)   # 0.99975: a wrong year clears a 0.99 bar

def vulnerable_json(text, schema):
    try:
        json.loads(text)                     # schema never used
        return True
    except json.JSONDecodeError:
        return False
```

## Fixed grader

Implement the option, and make unknown options an error.

```python
def fixed_numeric(output, expected, *, max_diff):   # no **kwargs
    if max_diff == 0:
        return 1.0 if output == expected else 0.0
    return max(0.0, 1 - abs(output - expected) / max_diff)

def fixed_json(text, schema):
    try:
        obj = json.loads(text)
    except json.JSONDecodeError:
        return False
    if not isinstance(obj, dict) or set(obj) != set(schema):
        return False
    return all(isinstance(obj[k], t) and not isinstance(obj[k], bool) for k, t in schema.items())
```

When a constraint is enforced by agent-supplied code (a training script told `--max_steps 100`), the verifier must check the result independently: read the step count from the artefact, check the exit status, and reject output that could not have come from a compliant run.

## How to test for it

- For every option a scorer documents, write one test where the option changes the result. If no such test can be written, the option does nothing.
- Pass a misspelt option. It should raise.
- Grep scorers for `**kwargs` in signatures and check each key is read.
- For budgets and limits that the verifier delegates, try exceeding them and see whether the score changes.

## Seen in the wild

- [braintrustdata/autoevals#251](https://github.com/braintrustdata/autoevals/issues/251): `NumericDiff` is documented with `max_diff` and `relative` options, but the Python and JS implementations never read them; with `max_diff=0.01`, a wrong year still scores 0.9998.
- [scaleapi/rsi-benchmark#103](https://github.com/scaleapi/rsi-benchmark/issues/103): the verifier passes `--max_steps 100` to the solver's training script but never checks that 100 steps were trained or that the script exited 0; it scores any `checkpoint-100` directory it finds.

## Run the example

```
python example.py
```
