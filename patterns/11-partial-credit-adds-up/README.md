# 11. Format-only or partial-credit rewards that add up past the pass threshold

## What it is

The reward is a weighted sum of rubric items, and the cheap items (output format, calling some tool, writing enough words, producing a file) are worth enough together to reach the pass threshold, or to get within one easy item of it, without the item that checks the actual result. A response that is tidy and wrong passes, and a response that is right but misses a style item can fail.

## Why it matters

A policy optimises the sum, so it will collect the cheap items first and may never need the expensive one. In evals, "pass" stops meaning "did the task", and the score mostly measures compliance with the format.

## Vulnerable grader and exploit

```python
RUBRIC = [(has_format, 0.2), (used_tool, 0.2), (explained, 0.2), (correct, 0.4)]
THRESHOLD = 0.6

def vulnerable(t):
    return weighted(t) >= THRESHOLD

WRONG_BUT_TIDY = {"tools_called": ["calculator"],
                  "reply": "I multiplied the two numbers with the calculator, checked the units twice "
                           "and rounded to the nearest whole number.\nFinal answer: 112"}   # 0.6, passes
```

## Fixed grader

Make the outcome check a gate. Partial credit can shape the score above or below it, but cannot replace it.

```python
def fixed(t):
    return correct(t) and weighted(t) >= THRESHOLD
```

Lint the rubric: for each item that measures the outcome, compute the best score reachable with that item failed, and require it to be below the threshold.

```python
def max_score_without(check_name):
    return sum(w for check, w in RUBRIC if check.__name__ != check_name)

assert max_score_without("correct") < THRESHOLD   # fails for the vulnerable rubric
```

## How to test for it

- For every rubric, compute the maximum score achievable with each outcome item failed. If it reaches the threshold, the rubric is broken.
- Write a response that satisfies every format and process item and gets the answer wrong. Grade it.
- Look at transcript or process rules (for example "made a bash call", "wrote a file") and check whether any honest attempt gets them for free. Those weights are a constant offset, not a signal.

## Seen in the wild

- [Toloka/tolokaforge#1933](https://github.com/Toloka/tolokaforge/issues/1933): transcript rules worth 0.35 of the score are met by any agent that calls `bash` and `write_file` and uses a few expected words, so the unfixed file already scores 0.783 against a 0.8 threshold, and adding the expected snippet in a comment tips it to 1.0 (see [12](../12-source-text-matching/)).

## Run the example

```
python example.py
```
