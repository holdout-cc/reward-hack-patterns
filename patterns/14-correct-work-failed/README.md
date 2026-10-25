# RHP-14. Correct work wrongly failed

## What it is

The grader rejects correct work because it compares the wrong representation. Typical forms: the final state is checked by hashing its serialised text, so key order, whitespace, list order or `10` versus `10.0` all fail; code is checked for one spelling of the fix, so a different quote style or argument order fails; a reference label is wrong, so the right answer is marked incorrect; or a parse error on a penalty criterion applies the penalty. This is the false-negative side of the catalogue: no exploit, just lost credit.

## Why it matters

In RL, false negatives push the policy toward the grader's quirks (one quote style, one key order) and away from correct work done differently, and they add noise that slows learning. In evals, they cap the achievable score and penalise models for formatting choices that have nothing to do with the task.

## Vulnerable grader and the work it fails

```python
EXPECTED_HASH = hashlib.sha256(json.dumps(EXPECTED_STATE).encode()).hexdigest()

def vulnerable_state(final_text):
    return hashlib.sha256(final_text.encode()).hexdigest() == EXPECTED_HASH

# same state, different key order, spacing, list order and 10 vs 10.0: fails
EQUIVALENT_STATE = '{"quota": 10, "roles": ["viewer", "editor"],\n "user": "kim"}'

def vulnerable_code(source):
    return "replace(',', '')" in source and "except (ValueError, TypeError)" in source

# correct code with double quotes and the other exception order: fails
```

## Fixed grader

Compare meaning, not bytes. Parse, canonicalise the parts that do not matter (key order, set-like lists, numeric type), and compare. For code, run it.

```python
def canonical(obj):
    if isinstance(obj, dict):
        return {k: canonical(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return sorted((canonical(v) for v in obj), key=repr)   # roles are a set
    if isinstance(obj, (int, float)) and not isinstance(obj, bool):
        return round(float(obj), 9)
    return obj

def fixed_state(final_text):
    try:
        return canonical(json.loads(final_text)) == canonical(EXPECTED_STATE)
    except json.JSONDecodeError:
        return False
```

Decide per field what is significant. If list order matters for a field, do not sort it.

## How to test for it

- Take each task's reference solution and rewrite it in a different but equivalent form: reorder keys, reformat, swap quote styles, rename local variables, use a different algorithm. Every variant must pass.
- Run the reference solution through the grader. It sounds obvious, but a reference that fails is a common finding.
- Look at tasks where strong models fail with outputs that look right, and read the grader's comparison.
- Spot-check reference labels independently (see [RHP-17](../17-unverified-reference-answers/)).

## Seen in the wild

- [Toloka/tolokaforge#1933](https://github.com/Toloka/tolokaforge/issues/1933): the correct one-character fix scores 0.783 and fails, and in the second example a correct fix written with double quotes and `except (TypeError, ValueError)` scores 0.5125 and fails, because the grader matches exact source text.
- [PrimeIntellect-ai/verifiers#2947](https://github.com/PrimeIntellect-ai/verifiers/issues/2947): the proposer's unverified answer is the solvers' ground truth, so with solver training on, solvers who answer a mislabelled problem correctly get 0.
- [Handshake-AI-Research/gandalf-the-grader#47](https://github.com/Handshake-AI-Research/gandalf-the-grader/issues/47): a quoted `"false"` on a negative-weight criterion is read as true, so the penalty is applied to work the judge said did not trigger it.

## Run the example

```
python example.py
```
