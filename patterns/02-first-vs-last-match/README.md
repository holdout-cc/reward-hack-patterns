# 02. First-match, last-match and multiple answers

## What it is

The grader pulls the answer out of free text with a regex, and the rule for which match counts is wrong. If it takes the first match, a reply that states a draft answer and then changes its mind is graded on the draft. If it accepts any match, a reply can list many candidates and one of them will be right. The same mistake shows up outside answer extraction: any grader that searches a stream for the first "N passed" or "score: X" will pick up text the agent wrote before the real line.

## Why it matters

A policy trained against an any-match grader learns to spray candidates, and one trained against a first-match grader learns to lead with a guess. In evals, both give credit for answers the model did not commit to, and they also fail models whose final answer is right but who wrote a different number earlier.

## Vulnerable grader and exploit

The prompt asks for a final line `Final answer: <integer>`. Gold is 15.

```python
PATTERN = re.compile(r"final answer:\s*(-?\d+)", re.IGNORECASE)

def vulnerable_any_match(reply):
    return any(int(m) == GOLD for m in PATTERN.findall(reply))

def vulnerable_first_match(reply):
    m = PATTERN.search(reply)
    return m is not None and int(m.group(1)) == GOLD

SPRAY = "\n".join(f"Final answer: {n}" for n in range(0, 31))           # any-match passes
CHANGED_MIND = "Final answer: 15\nWait, I forgot the carry.\nFinal answer: 14"  # first-match passes
```

## Fixed grader

Define one answer slot, require exactly one answer, and read it from that slot.

```python
def fixed(reply):
    lines = [ln.strip() for ln in reply.strip().splitlines() if ln.strip()]
    if not lines or len(PATTERN.findall(reply)) != 1:
        return False                      # zero or several answers: no credit
    m = re.fullmatch(r"final answer:\s*(-?\d+)", lines[-1], re.IGNORECASE)
    return m is not None and int(m.group(1)) == GOLD
```

Taking the last match instead of the first is better than nothing, but still lets a reply hedge across several answer lines. Rejecting multiple answers is the safer rule. If you use a structured output format (JSON, a tool call), the extraction problem goes away.

## How to test for it

- Feed the grader a reply that lists every plausible answer. It must fail.
- Feed it a reply that states the right answer first and a wrong one last, and the reverse. Decide which you want and check both.
- Look for `re.search`, `findall` + `any`, and `in` on the reply. Each one needs a stated rule for multiple matches.
- When the text being searched includes output the agent controls (logs, stdout, files), check that agent-written text cannot appear before the line you mean to read.

## Seen in the wild

- [hud-evals/hud-python#736](https://github.com/hud-evals/hud-python/issues/736): the `fix_calc` reward takes the first `(\d+) passed` match in merged stdout and stderr, so `print("10 passed")` in the code under test is read before pytest's real summary line.

## Run the example

```
python example.py
```
