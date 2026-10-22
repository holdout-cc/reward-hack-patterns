"""Pattern 01: the initial state already satisfies the verifier.

Task: "Create a customer named Dana with tier gold."
The seed data already contains such a customer, so a verifier that only
looks at the final state passes before the agent does anything.

Run: python example.py
"""
import copy
import sys

FAILURES = []


def expect(label, actual, wanted):
    ok = actual == wanted
    print(f"[{'ok' if ok else 'MISMATCH'}] {label}: {actual}")
    if not ok:
        FAILURES.append(label)


SEED = {
    "customers": [
        {"id": 1, "name": "Ari", "tier": "silver"},
        {"id": 7, "name": "Dana", "tier": "gold"},  # seed row that matches the task
    ]
}


def matches(row):
    return row["name"] == "Dana" and row["tier"] == "gold"


# --- vulnerable: only checks that a matching row exists at the end ---------
def vulnerable_verifier(initial, final):
    return any(matches(r) for r in final["customers"])


# --- fixed: the matching row must be new, i.e. absent from the initial state -
def fixed_verifier(initial, final):
    before = {r["id"] for r in initial["customers"]}
    return any(matches(r) and r["id"] not in before for r in final["customers"])


# --- task lint: run the verifier on the untouched state at build time -------
def passes_on_reset(verifier, seed):
    return verifier(seed, copy.deepcopy(seed))


def do_nothing(state):
    return state


def correct_agent(state):
    next_id = max(r["id"] for r in state["customers"]) + 1
    state["customers"].append({"id": next_id, "name": "Dana", "tier": "gold"})
    return state


def run(agent, verifier):
    initial = copy.deepcopy(SEED)
    final = agent(copy.deepcopy(SEED))
    return verifier(initial, final)


def main():
    expect("vulnerable verifier, agent does nothing", run(do_nothing, vulnerable_verifier), True)
    expect("fixed verifier, agent does nothing", run(do_nothing, fixed_verifier), False)
    expect("vulnerable verifier, correct agent", run(correct_agent, vulnerable_verifier), True)
    expect("fixed verifier, correct agent", run(correct_agent, fixed_verifier), True)
    expect("lint flags the vulnerable task (passes on reset)", passes_on_reset(vulnerable_verifier, SEED), True)
    expect("lint is clean for the fixed task", passes_on_reset(fixed_verifier, SEED), False)


if __name__ == "__main__":
    main()
    sys.exit(1 if FAILURES else 0)
