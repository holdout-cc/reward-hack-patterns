# RHP-12. Source-text matching instead of running the code

- **TL;DR:** Code is graded by searching its source for an expected snippet instead of running it.
- **Typical impact:** The bug can stay in place with the snippet pasted in a comment, and correct fixes written another way fail.
- **Quick test:** Leave the bug in, add the expected snippet in a comment, and grade it. It must fail.
- **Automated check:** Partly: when the grader only searches for the expected answer text, grader-probe's [`candidate_list`](https://github.com/holdout-cc/grader-probe/blob/main/docs/checks.md#candidate_list), [`rejects_gold`](https://github.com/holdout-cc/grader-probe/blob/main/docs/checks.md#rejects_gold) and [`long_padding`](https://github.com/holdout-cc/grader-probe/blob/main/docs/checks.md#long_padding) probes contain that text and can flag it; a snippet hidden in a code comment is not built in, so add it as your own [`custom_no_credit`](https://github.com/holdout-cc/grader-probe/blob/main/docs/checks.md#custom_no_credit) response.

## What it is

A coding task is graded by checking whether the source file contains an expected snippet (`"price * (1 - rate)" in source`) rather than by running the code. Comments, string literals and dead code all count, so the bug can stay in place with the snippet pasted in a comment. The same check fails correct fixes written any other way (see [RHP-14](../14-correct-work-failed/)).

## Why it matters

The cheapest policy is to copy the grader's string into the file, which teaches nothing about fixing code and is easy to find once the snippet appears in a task file, an error message or a similar task. Eval scores measure whether the model guessed the exact spelling, and they both overcount (snippet in a comment) and undercount (equivalent fix in another style).

## Vulnerable grader and exploit

```python
BUGGY = "def apply_discount(price, rate):\n    return price * (1 + rate)\n"
SNIPPET = "price * (1 - rate)"

def vulnerable(source):
    return SNIPPET.lower() in source.lower()

EXPLOIT = BUGGY + "# TODO: price * (1 - rate)\n"     # bug left in, passes
```

## Fixed grader

Run the code and check behaviour.

```python
def fixed(source):
    try:
        f = load(source).apply_discount
        cases = [((100.0, 0.2), 80.0), ((50.0, 0.0), 50.0), ((10.0, 0.5), 5.0)]
        return all(abs(f(*args) - want) < 1e-9 for args, want in cases)
    except Exception:
        return False
```

Keep the behaviour tests hidden from the agent and run them in a clean copy (see [RHP-05](../05-agent-writable-grader-files/)). If a structural check is truly needed (for example "must not call `eval`"), parse the code with `ast` so comments and strings do not count, and do not let it decide pass/fail on its own.

## How to test for it

- Leave the bug in, add the expected snippet in a comment or a string, and grade it. It must fail.
- Write a correct fix in a different style (other quotes, operand order, a helper function). It must pass.
- Grep task configs for `contains`, `regex` or `in source` checks on code files.

## Seen in the wild

- [Toloka/tolokaforge#1933](https://github.com/Toloka/tolokaforge/issues/1933): the bundled coding examples pass if the source contains `amount * (1 + tax_rate)`; the unfixed file with that text in a comment scores 1.0, and the code is never run.

## Run the example

```
python example.py
```
