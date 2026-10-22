# 03. Substring, containment and hedge matching

## What it is

The grader checks that the expected answer appears somewhere in the reply (`gold in reply`) instead of checking that the reply is the answer. A reply that lists several candidates ("Lisbon, Madrid, Paris, Rome"), negates the answer ("it is not Lisbon") or simply repeats a word from the prompt will pass. The same bug appears in log parsers that look for a status keyword anywhere in a line, and in document checks that search the whole text for a value that should sit in a specific field.

## Why it matters

Hedging is easy to learn and costs nothing, so an RL policy will find it quickly once it pays. Eval scores then measure whether the gold string was mentioned, not whether the model knew the answer, and the gap grows with longer, chattier replies.

## Vulnerable grader and exploit

```python
GOLD = "Lisbon"

def vulnerable_answer(reply):
    return GOLD.lower() in reply.lower()

HEDGE = "Lisbon, Madrid, Paris, Rome, Berlin"    # passes
NEGATED = "It is not Lisbon, it is Porto."        # passes
```

A status parser with the same flaw:

```python
def vulnerable_status(line):
    if "PASSED" in line:
        return "PASSED"
    if "FAILED" in line:
        return "FAILED"

vulnerable_status("FAILED tests/test_geo.py::test_distance - PASSED")   # "PASSED"
```

The agent controls the failure message, so it can make a failing test print `PASSED`.

## Fixed grader

Normalise, then compare for equality. Parse structured lines by position.

```python
def normalise(text):
    text = text.strip().lower()
    text = re.sub(r"^(the answer is|answer:)\s*", "", text)
    return text.strip(string.punctuation + " ")

def fixed_answer(reply):
    return normalise(reply) == normalise(GOLD)

def fixed_status(line):
    first = line.split(maxsplit=1)[0] if line.strip() else ""
    return first if first in {"PASSED", "FAILED", "ERROR", "SKIPPED"} else "UNKNOWN"
```

If free-form answers are expected, extract a single answer first (see [02](../02-first-vs-last-match/)) and compare that.

## How to test for it

- Submit the list of all answer options, and a sentence that negates the gold answer. Both must fail.
- Submit a reply that only repeats words from the prompt. If the gold answer is in the prompt, a containment check passes it.
- Grep graders for ` in reply`, ` in output`, `.find(`, `contains`. Each one needs a reason.
- For log or report parsers, put the success keyword inside a failure message and check the result.

## Seen in the wild

- [PrimeIntellect-ai/verifiers#2948](https://github.com/PrimeIntellect-ai/verifiers/issues/2948): the `deepwiki` and `scratchpad` examples grade with a substring check; a list of eight languages, or "It is Rust, not Python", scores 1.0, and echoing the prompt's word scores 1.0 on 20 of 20 tasks.
- [GeneralReasoning/env-r2e-gym#11](https://github.com/GeneralReasoning/env-r2e-gym/issues/11): `parse_log` looks for `PASSED` before `FAILED` anywhere in a pytest summary line, so a failing test whose message is `PASSED` is scored as passed.
- [UiPath/coder_eval#234](https://github.com/UiPath/coder_eval/issues/234): in the court-form task, required values are matched as substrings of the whole PDF text rather than in named form fields, so a plain PDF with the values printed on it passes those checks.

## Run the example

```
python example.py
```
