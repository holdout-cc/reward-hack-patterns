# Changelog

Pattern IDs (`RHP-01` to `RHP-17`) and folder names are stable across versions. New patterns get new IDs; existing IDs are not renumbered or reused.

## 1.1.0 - 2026-10-25

- Each pattern has a stable ID, `RHP-01` to `RHP-17`, matching its existing number. Folder names and links are unchanged.
- Each pattern page starts with an at-a-glance block: a one-sentence summary, the typical impact, the quickest test, and the matching [grader-probe](https://github.com/holdout-cc/grader-probe) check where there is one.
- The index table shows each pattern's ID and the number of public issues its page links. A "Which pattern is this?" list maps symptoms to patterns, and each checklist item starts with the pattern ID.
- Added `CITATION.cff`, a "Citing" section in the README and this changelog; updated the contributing guide.
- `tests/test_docs.py` checks the pattern headers and sections, the index table and checklist, relative links and `CITATION.cff`; CI runs it next to the examples.
- The fixed graders in RHP-06, RHP-07 and RHP-15 are labelled partial mitigations, with the stronger and robust fixes described separately.

## 1.0.0 - 2026-10-22

- First public version, not tagged at the time: 17 patterns, each with a README and a runnable standard-library example, the ship checklist, the example test runner, and CI on Python 3.9 to 3.13.
