"""Pattern 09: errors and infrastructure failures dropped from the mean or pass@k.

An eval runs two tasks. The agent solves task 1. On task 2 it either gives a
wrong answer, or returns a malformed tool call that makes the harness raise.
The vulnerable aggregator treats every exception as an infrastructure error
and leaves it out of the mean.

Run: python example.py
"""
import json
import sys

FAILURES = []


def expect(label, actual, wanted):
    ok = actual == wanted
    print(f"[{'ok' if ok else 'MISMATCH'}] {label}: {actual}")
    if not ok:
        FAILURES.append(label)


class InfraError(Exception):
    """Raised only by the harness itself: sandbox died, provider 5xx, etc."""


GOLD = {"t1": 42, "t2": 7}


def score(task_id, raw_reply):
    reply = json.loads(raw_reply)  # raises on malformed agent output
    return 1.0 if reply.get("answer") == GOLD[task_id] else 0.0


# --- vulnerable: any exception becomes "error" and leaves the denominator ---
def vulnerable_trial(task_id, raw_reply):
    try:
        return {"status": "scored", "reward": score(task_id, raw_reply)}
    except Exception:
        return {"status": "error", "reward": None}


def vulnerable_mean(trials):
    scored = [t["reward"] for t in trials if t["status"] == "scored"]
    return sum(scored) / len(scored)


def vulnerable_pass_at_k(attempts):
    # attempts: list of trial dicts for one task; errors are ignored
    usable = [a for a in attempts if a["status"] == "scored"]
    return any(a["reward"] == 1.0 for a in usable) if usable else None  # None = "excluded"


# --- fixed: only harness-raised InfraError is excluded, and it is reported --
def fixed_trial(task_id, raw_reply, infra_failure=False):
    if infra_failure:
        return {"status": "infra_error", "reward": None}
    try:
        return {"status": "scored", "reward": score(task_id, raw_reply)}
    except InfraError:
        return {"status": "infra_error", "reward": None}
    except Exception:
        # The agent produced output we could not use: that is a failed task.
        return {"status": "scored", "reward": 0.0}


def fixed_mean(trials):
    infra = sum(t["status"] == "infra_error" for t in trials)
    if infra:
        # Do not publish a mean over a smaller set; retry or mark incomplete.
        return {"mean": None, "complete": False, "infra_errors": infra}
    return {"mean": sum(t["reward"] for t in trials) / len(trials), "complete": True, "infra_errors": 0}


GOOD_T1 = '{"answer": 42}'
WRONG_T2 = '{"answer": 3}'
BROKEN_T2 = '{"answer": 3'  # truncated JSON
GOOD_T2 = '{"answer": 7}'


def main():
    honest = [vulnerable_trial("t1", GOOD_T1), vulnerable_trial("t2", WRONG_T2)]
    broken = [vulnerable_trial("t1", GOOD_T1), vulnerable_trial("t2", BROKEN_T2)]
    expect("vulnerable mean, honest wrong answer on t2", vulnerable_mean(honest), 0.5)
    expect("vulnerable mean, malformed output on t2", vulnerable_mean(broken), 1.0)

    f_broken = [fixed_trial("t1", GOOD_T1), fixed_trial("t2", BROKEN_T2)]
    expect("fixed mean, malformed output on t2", fixed_mean(f_broken)["mean"], 0.5)

    expect("vulnerable pass@2 on t2, all attempts malformed", vulnerable_pass_at_k([vulnerable_trial("t2", BROKEN_T2)] * 2), None)
    f_attempts = [fixed_trial("t2", BROKEN_T2)] * 2
    expect("fixed pass@2 on t2, all attempts malformed", any(a["reward"] == 1.0 for a in f_attempts), False)

    solved = [fixed_trial("t1", GOOD_T1), fixed_trial("t2", GOOD_T2)]
    expect("vulnerable mean, both solved", vulnerable_mean([vulnerable_trial("t1", GOOD_T1), vulnerable_trial("t2", GOOD_T2)]), 1.0)
    expect("fixed mean, both solved", fixed_mean(solved)["mean"], 1.0)

    outage = [fixed_trial("t1", GOOD_T1), fixed_trial("t2", "", infra_failure=True)]
    expect("fixed mean with a real outage is withheld, not inflated", fixed_mean(outage)["complete"], False)


if __name__ == "__main__":
    main()
    sys.exit(1 if FAILURES else 0)
