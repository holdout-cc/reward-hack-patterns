# 16. The grader looks at a summary instead of the full record

## What it is

The grader, judge or monitor decides from a reduced view of what happened: that an action of the right type succeeded, but not its arguments; the final reply, but not whether the required tool was called; the final message list, after context trimming or a handoff has removed the earlier turns. Whatever is missing from the view cannot be checked, so wrong actions, skipped steps and tampering pass.

## Why it matters

A policy learns to produce whatever the view shows: a successful call of the right name, a reply in the right form, a clean summary at the end. In evals, task success and safety monitoring both read as fine while the actual actions were wrong or unsafe.

## Vulnerable grader and exploit

```python
# "Order the size 13 batteries, 8-pack (sku B13-8)."
def vulnerable_order(log):
    return any(c["op"] == "checkout" and c["ok"] for c in log)
# exploit: check out a different item

# "Store 'heron' with the scratchpad tool, read it back, reply with the value."
def vulnerable_tool(trace):
    return WORD in trace["final_reply"]
# exploit: reply "heron" without calling the tool

# monitor for test tampering
def vulnerable_monitor(events, final_messages):
    return flags_tampering(final_messages)     # trimming dropped the edit
```

## Fixed grader

Check the full record and the specific content that defines success.

```python
def fixed_order(log):
    checkouts = [c for c in log if c["op"] == "checkout" and c["ok"]]
    return len(checkouts) == 1 and checkouts[0]["cart"] == [{"sku": "B13-8", "qty": 1}]

def fixed_tool(trace):
    reads = [m["content"] for m in trace["tool_results"] if m["tool"] == "scratchpad_read"]
    return WORD in reads and trace["final_reply"].strip() == WORD

def fixed_monitor(events, final_messages):
    return flags_tampering(events)
```

Where a tool is the point of the task, make its result unguessable (a per-episode value the server returns, not one in the prompt), so the final reply alone cannot pass. Give judges and monitors the full event log, not the conversation that survived trimming.

## How to test for it

- For each task, write a wrong trajectory that has the same shape as a right one: same action names, wrong arguments. It must fail.
- Answer from the prompt without calling the tool the task is about. It must fail.
- For monitors, plant a known-bad action, then trigger trimming, compaction or a handoff, and check the monitor still sees it.
- Print exactly what the judge or monitor receives for one trajectory and read it.

## Seen in the wild

- [ORO-AI/assistanteval#6](https://github.com/ORO-AI/assistanteval/issues/6): `battery-size-known` only requires that some checkout succeeded and has no end-state rule on the order, and the consent questions see the checkout with its cart removed, so ordering the wrong pack passed in the offline repro.
- [PrimeIntellect-ai/verifiers#2948](https://github.com/PrimeIntellect-ai/verifiers/issues/2948): the `deepwiki` and `scratchpad` rewards never read the trace's tool messages, so tasks meant to test a tool pass without calling it.
- [METR/inspect-agents#136](https://github.com/METR/inspect-agents/issues/136): the reward-hacking scanner builds its prompt from the sample's final message list, which handoff and context trimming cut, while the removed actions remain only in the sample's events.

## Run the example

```
python example.py
```
