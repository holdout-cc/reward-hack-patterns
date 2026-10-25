# RHP-17. Reference answers that nobody verified

- **TL;DR:** The reference answer comes from a model or from input the agent can change, and nobody checks it.
- **Typical impact:** In self-play, false or ambiguous labels can earn the maximum proposer reward while solvers who answer correctly get 0; eval error concentrates on the hardest labels.
- **Quick test:** Check a sample of labels with a method that does not depend on where they came from.
- **Automated check:** Not covered by grader-probe (needs an environment-level test).

## What it is

The "ground truth" the grader compares against is not established independently. It comes from a model (a self-play proposer, a synthetic data generator), or it is recomputed at grading time from inputs the agent could change. The grader then checks agreement with a label that may be wrong, ambiguous or controlled by the party being graded. In self-play, a proposer paid for problems that split the solvers can earn full reward with a false or ambiguous label, because wrong labels split solvers just as well as hard problems do.

## Why it matters

Wrong labels are trained in: the solvers who get the right answer are pushed away from it, and the proposer is paid for producing confusion. Eval scores computed against unverified labels have an unknown error, and it is not random: it is concentrated on the problems where labels are hardest to get right.

## Vulnerable grader and exploit

```python
def learnability(label, solver_answers):
    p = sum(a == label for a in solver_answers) / len(solver_answers)
    return 4 * p * (1 - p)

def vulnerable(problem, label, solver_answers):
    return learnability(label, solver_answers)

vulnerable("7 + 8", 16, [15, 15, 16, 16])   # 1.0 for a false label
```

## Fixed grader

Confirm the label independently before it counts: run a reference solution, check it with an exact method, or require agreement from a strong reference solver. Labels that fail are rejected, and so are the solver rollouts graded against them.

```python
def fixed(problem, label, solver_answers):
    try:
        truth = evaluate(problem)               # independent check
    except (ValueError, SyntaxError, ZeroDivisionError):
        return 0.0
    if truth != label:
        return 0.0
    return learnability(label, solver_answers)
```

For static datasets, the same idea: store reference answers that were checked, keep them outside the agent's environment, and do not recompute them from task inputs at grading time.

## How to test for it

- Sample tasks and check their labels with a method that does not depend on the label's source.
- In self-play, measure the proposer reward on deliberately false and deliberately ambiguous problems. It should be zero.
- Check where the expected answer comes from at grading time. If it is computed from a file, ask who can write that file.
- Look for tasks where the solvers that disagree with the label agree with each other. That is a sign the label is wrong.

## Seen in the wild

- [PrimeIntellect-ai/verifiers#2947](https://github.com/PrimeIntellect-ai/verifiers/issues/2947): `proposer_solver` uses the proposer's answer as the solvers' ground truth after checking only that it is an integer, so false or ambiguous problems earn maximum learnability.
- [UiPath/coder_eval#233](https://github.com/UiPath/coder_eval/issues/233): the expected mass is not stored but recomputed at grading time from an input file the agent can overwrite (see [RHP-05](../05-agent-writable-grader-files/)).

## Run the example

```
python example.py
```
