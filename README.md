# reward-hack-patterns

A practical catalogue of the ways RL environment graders and eval scorers give credit for work that was not done, or fail work that was.

It is written for people who build RL environments and benchmarks. Each pattern has a short explanation, a minimal vulnerable grader with its exploit, a fixed grader (labelled a partial mitigation where it only raises the bar, with the robust fix described), a way to test for it, and links to real public issues where it was found. Every pattern also has a small, runnable Python example (standard library only) that shows the vulnerable grader accepting the exploit, the fixed grader rejecting it, and a correct answer passing both.

The examples are toys. They are deliberately small so the bug is visible in a few lines. Real instances are usually spread across a config file, a container mount and a scoring script, which is why they survive review.

## Patterns

| ID | Pattern | What goes wrong | Seen in the wild |
|----|---------|-----------------|:----------------:|
| RHP-01 | [Do-nothing passes](patterns/01-do-nothing-passes/) | The initial state already satisfies the verifier, so a no-op scores. | 2 |
| RHP-02 | [First-match, last-match and multiple answers](patterns/02-first-vs-last-match/) | Answer extraction reads a draft, or accepts any of several answers. | 1 |
| RHP-03 | [Substring and hedge matching](patterns/03-substring-and-hedge-matching/) | `gold in reply` passes lists of candidates, negations and echoes. | 3 |
| RHP-04 | [Loose similarity thresholds](patterns/04-loose-similarity-thresholds/) | Fuzzy overlap and low thresholds accept wrong or unrelated answers. | 2 |
| RHP-05 | [Agent-writable grader files](patterns/05-agent-writable-grader-files/) | The agent can edit the tests, the verifier, the reward file or the reference input. | 5 |
| RHP-06 | [Stdout scraping](patterns/06-stdout-scraping/) | Pass counts are read from output the code under test can print to. | 2 |
| RHP-07 | [Exit-code-only checks](patterns/07-exit-code-only/) | `os._exit(0)` before the tests run counts as passing. | 3 |
| RHP-08 | [Failure defaults to pass](patterns/08-failure-defaults-to-pass/) | Exceptions, missing data and skips count as passed or are left out. | 4 |
| RHP-09 | [Errors dropped from the aggregate](patterns/09-errors-dropped-from-aggregate/) | Agent-caused errors are labelled infrastructure and leave the mean or pass@k. | 2 |
| RHP-10 | [LLM-judge parsing](patterns/10-llm-judge-parsing/) | `bool("false")` is `True`, and unparseable verdicts become passes. | 1 |
| RHP-11 | [Partial credit adds up](patterns/11-partial-credit-adds-up/) | Format and process items reach the threshold without a correct result. | 1 |
| RHP-12 | [Source-text matching](patterns/12-source-text-matching/) | The expected snippet in a comment passes; the code is never run. | 1 |
| RHP-13 | [Ignored options](patterns/13-ignored-options/) | Tolerances, schemas and budgets are accepted and then not applied. | 2 |
| RHP-14 | [Correct work failed](patterns/14-correct-work-failed/) | Byte-level comparisons and wrong labels reject equivalent correct work. | 3 |
| RHP-15 | [Submission disables the checker](patterns/15-submission-disables-checker/) | The output shares a program with the tests, or carries a directive that turns the check off. | 2 |
| RHP-16 | [Incomplete evidence](patterns/16-incomplete-evidence/) | The grader sees a summary (action name, final reply, trimmed messages), not what was done. | 3 |
| RHP-17 | [Unverified reference answers](patterns/17-unverified-reference-answers/) | The label comes from a model or from agent-writable input and is never checked. | 2 |

"Seen in the wild" is the number of public issues linked from the pattern's page. One issue can show more than one pattern, so the column adds up to more than the number of distinct issues.

## Which pattern is this?

Start from what you observed:

- A no-op or an immediate submit scores above 0: RHP-01.
- A reply that lists several answers, or changes its mind, gets credit: RHP-02. A negation or the prompt repeated back also passes: RHP-03.
- One fixed junk reply passes many different tasks: RHP-04.
- Scores go up after the agent touches tests, test config or a reward file: RHP-05.
- The tests fail but the task passes. The code printed a summary line: RHP-06. The process exited early: RHP-07. The checks were skipped or raised: RHP-08.
- The mean or pass@k rises when more trials error: RHP-09.
- The judge said no and the criterion still counts as met: RHP-10. A judge or monitor misses something that is in the full event log: RHP-16.
- A wrong answer passes on format alone: RHP-11, or despite a tolerance or schema that should reject it: RHP-13.
- The bug is still in the code and the expected fix is in a comment: RHP-12. A fixed decorator or directive added to any submission passes: RHP-15.
- Correct work fails, or strong models fail with output that looks right: RHP-14. Solvers that disagree with the label agree with each other: RHP-17.

## Checklist before you ship an environment

1. RHP-01: Run every task's verifier on the untouched initial state. Nothing should pass.
2. RHP-02: If answers are extracted from text, require exactly one answer in a defined slot, and test a reply that lists many.
3. RHP-03: Replace `gold in reply` with normalised equality, and test a hedge list, a negation and a prompt echo.
4. RHP-04: Score a fixed junk answer against every reference under each similarity threshold you ship. The pass rate should be zero.
5. RHP-05: Make sure the agent cannot write any file the grader reads: tests, test scripts, reward files, reference inputs, test-runner config.
6. RHP-06: Grade from a structured report on a channel the code under test cannot write to, not from stdout.
7. RHP-07: Never use the exit code as the only pass signal; require evidence that every expected test ran and passed.
8. RHP-08: Treat exceptions, missing data and skipped required checks as failures, and check what score every failure path writes.
9. RHP-09: Count agent-caused errors as 0; exclude only harness errors, retry them, and withhold the aggregate if any remain.
10. RHP-10: Parse judge verdicts strictly (a JSON boolean or one exact verdict line) and score parse errors as errors, not passes.
11. RHP-11: Compute the best score reachable with each outcome item failed; it must be below the pass threshold.
12. RHP-12: Grade code by running it, never by searching its source text.
13. RHP-13: For every option a scorer accepts, have a test where that option changes the result; reject unknown options.
14. RHP-14: Rewrite each reference solution in an equivalent form (key order, quotes, formatting, algorithm) and check it still passes.
15. RHP-15: Run submission and tests in separate namespaces or processes, and reject checker directives in the submission.
16. RHP-16: Check the content of actions (arguments, items, results), not only their names, and give judges and monitors the full event log.
17. RHP-17: Verify reference answers independently of where they came from, and store them outside the agent's environment.

## Running the examples

Each example is self-contained:

```
python patterns/07-exit-code-only/example.py
```

Run them all:

```
python -m pytest tests/
# or, without pytest:
python tests/test_examples.py
python tests/test_docs.py
```

`tests/test_docs.py` checks the pattern pages (ID, at-a-glance block, sections), the index table and checklist, relative links, and `CITATION.cff`.

The examples need Python 3.9 or later and nothing outside the standard library. CI runs them on Python 3.9 to 3.13.

## About the "Seen in the wild" links

The links point to public issues filed on the named repositories, each with a reproduction. Some may have been fixed or closed since; the issue thread is the place to check current status. The toy examples here are written from scratch and do not reuse code from those repositories.

## Citing

Every pattern has a stable ID, `RHP-01` to `RHP-17`. An ID always refers to the same pattern, and pattern folders are not renamed, so links keep working. New patterns get new IDs.

To refer to one pattern, give its ID and name and link its folder:

> RHP-03, Substring and hedge matching, in Holdout's reward-hack-patterns: https://github.com/holdout-cc/reward-hack-patterns/tree/main/patterns/03-substring-and-hedge-matching

To cite the catalogue as a whole, use [CITATION.cff](CITATION.cff) (GitHub shows it as "Cite this repository"), and give the version from [CHANGELOG.md](CHANGELOG.md) if the exact wording matters.

## Contributing

Issues and pull requests are welcome: new patterns, better fixes, clearer examples, or public instances of a pattern that should be linked. For a new pattern, please include a runnable stdlib-only `example.py` in the same shape as the others, and make sure `python tests/test_examples.py` passes. For a new "Seen in the wild" link, please link a public issue or write-up that shows the instance. See [CONTRIBUTING.md](CONTRIBUTING.md) for the details.

## License

MIT. See [LICENSE](LICENSE).

---

Maintained by Holdout · hello@holdout.cc · https://holdout.cc
