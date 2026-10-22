# 04. Similarity thresholds that pass wrong answers

## What it is

The grader scores the answer by fuzzy similarity to a reference (word-set Jaccard, edit distance, token overlap, a relative-difference formula) and passes it above a threshold. Overlap is not correctness: a command that deletes a file can share most of its words with the command that runs it, and a threshold of 0 or close to it accepts anything. The threshold often lives in a config file, where nobody checks what it does.

## Why it matters

A policy will find the cheapest string that clears the bar, which is often a fixed reply that works on every step. In evals, loose similarity turns near misses and unrelated answers into passes, and the error depends on answer length, so it is uneven across tasks.

## Vulnerable grader and exploit

```python
EXPECTED = "pytest tests/test_api.py -x -q"

def jaccard(a, b):
    sa, sb = set(a.split()), set(b.split())
    return len(sa & sb) / len(sa | sb)

def vulnerable(actual, threshold):
    return not (jaccard(EXPECTED, actual) < threshold)

vulnerable("echo done", 0.0)                    # True: nothing is below 0.0
vulnerable("rm tests/test_api.py -x -q", 0.5)  # True: overlap is 0.6
```

## Fixed grader

Use exact comparison after normalisation for anything with exact semantics (commands, code, ids, numbers). Keep fuzzy matching for free text, and validate its threshold.

```python
def fixed(actual):
    try:
        return shlex.split(actual) == shlex.split(EXPECTED)
    except ValueError:
        return False

def validate_threshold(threshold):
    if not 0.5 < threshold <= 1.0:
        raise ValueError(f"similarity threshold {threshold} would accept unrelated strings")
```

The right floor depends on the metric; the point is to reject values that make the check meaningless, and to measure what passes.

## How to test for it

- Score a fixed junk answer ("echo done", "N/A", the empty string) against every reference in the dataset. Report the pass rate. It should be zero.
- Score a corrupted reference (first word kept, rest replaced) and a one-token edit that changes meaning. Those should fail.
- Plot score distributions for correct and incorrect answers on a labelled sample and pick the threshold from that, not by feel.
- Check every config that sets a threshold, not just the default.

## Seen in the wild

- [NVIDIA-NeMo/Gym#4900](https://github.com/NVIDIA-NeMo/Gym/issues/4900): two shipped configs set `word_count_similarity_threshold: 0.0`, so the check can never fail for multi-word arguments; `execute_bash(command="echo done")` passed all 346 sampled SWE rows that have a multi-word string argument.
- [braintrustdata/autoevals#251](https://github.com/braintrustdata/autoevals/issues/251): `NumericDiff` scores nearby positive numbers at about `1 - relative_error / 2`, so a wrong year scores 0.9998 and clears a 0.99 bar (see also [13](../13-ignored-options/)).

## Run the example

```
python example.py
```
