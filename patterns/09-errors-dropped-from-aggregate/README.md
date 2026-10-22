# 09. Errors and infrastructure failures dropped from the mean or pass@k

## What it is

The aggregate score leaves out trials marked as errors, on the reasoning that infrastructure failures should not count against the model. The trouble is in how a trial gets that label. If any exception, missing report or crash is classed as "infrastructure", then failures the agent caused (malformed tool-call JSON, an empty reply, code that kills the test runner before it writes its report) leave the denominator instead of scoring 0. A failed task becomes "no data", and the mean goes up.

## Why it matters

Per-trial rewards are often unaffected, so training may not see it directly, but any metric used for model selection, checkpoint ranking or a leaderboard rewards breaking the harness on tasks the model would fail. It also hides real flakiness: a run with many dropped trials reports the same kind of number as a clean one.

## Vulnerable grader and exploit

```python
def vulnerable_trial(task_id, raw_reply):
    try:
        return {"status": "scored", "reward": score(task_id, raw_reply)}
    except Exception:
        return {"status": "error", "reward": None}

def vulnerable_mean(trials):
    scored = [t["reward"] for t in trials if t["status"] == "scored"]
    return sum(scored) / len(scored)

# task 1 solved, task 2 answered wrongly          -> mean 0.5
# task 1 solved, task 2 returns '{"answer": 3'     -> mean 1.0
```

## Fixed grader

Only errors raised by the harness itself, before or outside the agent's control, are excluded. Anything caused by the agent's output scores 0. Excluded trials are retried, and if any remain, the aggregate is withheld or flagged rather than computed over fewer tasks.

```python
class InfraError(Exception):
    """Raised only by the harness itself: sandbox died, provider 5xx, etc."""

def fixed_trial(task_id, raw_reply, infra_failure=False):
    if infra_failure:
        return {"status": "infra_error", "reward": None}
    try:
        return {"status": "scored", "reward": score(task_id, raw_reply)}
    except InfraError:
        return {"status": "infra_error", "reward": None}
    except Exception:
        return {"status": "scored", "reward": 0.0}

def fixed_mean(trials):
    infra = sum(t["status"] == "infra_error" for t in trials)
    if infra:
        return {"mean": None, "complete": False, "infra_errors": infra}
    return {"mean": sum(t["reward"] for t in trials) / len(trials), "complete": True, "infra_errors": 0}
```

For pass@k, an attempt that errors because of the agent is a failed attempt, not a missing one.

## How to test for it

- Run a small eval where the agent solves half the tasks and, on the other half, returns truncated JSON, an empty reply, or code that crashes the test runner at import. The score must be the same as when it answers those tasks wrongly.
- List every code path that sets a trial to "error" or "excluded". For each, ask whether the agent's output can reach it.
- Report the number of excluded trials next to every aggregate, and fail the run when it is above zero after retries.

## Seen in the wild

- [hud-evals/hud-python#737](https://github.com/hud-evals/hud-python/issues/737): a missing JUnit report marks the grade `isError` and `Job.reward` leaves error runs out of the mean; two lines in the agent's package make pytest exit before writing the report, so a failed task is dropped instead of counting as 0.
- [sierra-research/tau2-bench#672](https://github.com/sierra-research/tau2-bench/issues/672): malformed tool-call JSON and empty replies from the agent model end up as `infrastructure_error` after retries, and the 2.0 score drops them from the denominator, so a failed task can score the same as a solved one.

## Run the example

```
python example.py
```
