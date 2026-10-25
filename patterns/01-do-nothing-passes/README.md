# RHP-01. Do-nothing passes: the initial state already satisfies the verifier

## What it is

The verifier checks the final state for some condition, and that condition is already true when the episode starts. Typical causes: seed data that already contains the row a "create" task asks for, a fixture file that already has the expected content, or a state check that only looks at the end and never compares it with the start. An agent that does nothing, or calls "submit" straight away, gets full reward.

## Why it matters

In RL, a no-op is the cheapest policy there is, so any task where it scores 1.0 teaches the policy that doing nothing is fine. In evals, these tasks raise every model's score by the same amount and make the benchmark look easier and less discriminative than it is.

## Vulnerable grader and exploit

Task: "Create a customer named Dana with tier gold." The seed already has one.

```python
SEED = {"customers": [{"id": 1, "name": "Ari", "tier": "silver"},
                      {"id": 7, "name": "Dana", "tier": "gold"}]}

def vulnerable_verifier(initial, final):
    return any(matches(r) for r in final["customers"])

# exploit: return the state unchanged
```

## Fixed grader

Require a change relative to the initial state, and lint every task by running its verifier on the untouched state.

```python
def fixed_verifier(initial, final):
    before = {r["id"] for r in initial["customers"]}
    return any(matches(r) and r["id"] not in before for r in final["customers"])

def passes_on_reset(verifier, seed):
    return verifier(seed, copy.deepcopy(seed))   # must be False for every task
```

## How to test for it

- For every task, run the verifier on the freshly reset environment with no agent actions. Any pass is a bug in the task or the verifier. Make this a CI check over the whole dataset, not a one-off.
- Also try the "submit immediately" and "empty answer" agents.
- For write tasks, check that the verifier reads the initial state at all. If it only takes the final state as input, it cannot tell new work from seed data.

## Seen in the wild

- [openenv/OpenEnv#1475](https://github.com/openenv/OpenEnv/issues/1475): in `agent_world_model_env`, 1,681 of 10,000 code verifiers return `complete` on the untouched seeded database, because the seed already holds the row the task asks the agent to create.
- [Handshake-AI-Research/ATLAS-Finance#12](https://github.com/Handshake-AI-Research/ATLAS-Finance/issues/12): on three tasks a blank workbook fails every section gate, every critical criterion is then skipped, and the trial counts as a pass for pass@k (see also [RHP-08](../08-failure-defaults-to-pass/)).

## Run the example

```
python example.py
```
