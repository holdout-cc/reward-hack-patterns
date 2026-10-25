# Contributing

Thanks for helping. Three kinds of contribution are welcome: new patterns, improvements to existing ones (clearer explanation, better fix, simpler example), and new "Seen in the wild" links.

## Proposing a new pattern

Open an issue first if you're unsure whether it's a separate pattern or a variant of an existing one. A new pattern should describe a way a grader gives credit for work that wasn't done, or fails work that was, that isn't already covered.

A pattern pull request adds a folder `patterns/NN-short-slug/`, where `NN` is the next unused number. The pattern's ID is `RHP-NN`. Once a pattern is published, its ID and folder name do not change and are not reused, so links and citations keep working.

The folder has two files:

- `README.md` with a title `# RHP-NN. Name`, then an at-a-glance list of four items: **TL;DR** (one sentence), **Typical impact** (what a policy can get from it), **Quick test** (the single most effective probe) and **Automated check** (a link to the [grader-probe](https://github.com/holdout-cc/grader-probe/blob/main/docs/checks.md) check that tests it, or "Not covered by grader-probe" with what is needed instead). Then these sections, in this order: **What it is**, **Why it matters**, **Vulnerable grader and exploit**, **Fixed grader** (**Partially mitigated grader** when the example only raises the bar), **How to test for it**, **Seen in the wild**. Keep it short; the existing patterns are the model.
- `example.py`: a self-contained demo that uses only the Python standard library and runs on Python 3.9 or later. It must show three things and exit non-zero if any of them fails:
  1. the vulnerable grader gives credit to the exploit;
  2. the fixed grader rejects it;
  3. the correct answer passes both graders.

Write the toy grader from scratch. Don't copy code from the project where you saw the pattern.

Add a row for the pattern to the table in the top-level `README.md` and a line to the checklist.

## Adding a "Seen in the wild" link

A link should point to a public issue, pull request or write-up that shows a concrete instance of the pattern in a named project, ideally with a reproduction. Describe the instance in one line. If the instance only partly fits the pattern, say so in that line.

Please don't link to private reports, unconfirmed suspicions, or anything that would help someone attack a live system.

## Before you open a pull request

```
python tests/test_examples.py
```

All examples must pass. CI runs the same check on Python 3.9 to 3.13.
