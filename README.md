# reward-hack-patterns

A practical catalogue of the ways RL environment graders and eval scorers give credit for work that was not done, or fail work that was.

It is written for people who build RL environments and benchmarks. Each pattern has a short explanation, a minimal vulnerable grader with its exploit, a fixed grader, a way to test for it, and links to real public issues where it was found. Every pattern also has a small, runnable Python example (standard library only) that shows the vulnerable grader accepting the exploit, the fixed grader rejecting it, and a correct answer passing both.

The examples are toys. They are deliberately small so the bug is visible in a few lines. Real instances are usually spread across a config file, a container mount and a scoring script, which is why they survive review.

## Patterns

| # | Pattern | What goes wrong |
|---|---------|-----------------|
| 01 | [Do-nothing passes](patterns/01-do-nothing-passes/) | The initial state already satisfies the verifier, so a no-op scores. |
| 02 | [First-match, last-match and multiple answers](patterns/02-first-vs-last-match/) | Answer extraction reads a draft, or accepts any of several answers. |
| 03 | [Substring and hedge matching](patterns/03-substring-and-hedge-matching/) | `gold in reply` passes lists of candidates, negations and echoes. |
| 04 | [Loose similarity thresholds](patterns/04-loose-similarity-thresholds/) | Fuzzy overlap and low thresholds accept wrong or unrelated answers. |
| 05 | [Agent-writable grader files](patterns/05-agent-writable-grader-files/) | The agent can edit the tests, the verifier, the reward file or the reference input. |
| 06 | [Stdout scraping](patterns/06-stdout-scraping/) | Pass counts are read from output the code under test can print to. |
| 07 | [Exit-code-only checks](patterns/07-exit-code-only/) | `os._exit(0)` before the tests run counts as passing. |
| 08 | [Failure defaults to pass](patterns/08-failure-defaults-to-pass/) | Exceptions, missing data and skips count as passed or are left out. |
| 09 | [Errors dropped from the aggregate](patterns/09-errors-dropped-from-aggregate/) | Agent-caused errors are labelled infrastructure and leave the mean or pass@k. |
| 10 | [LLM-judge parsing](patterns/10-llm-judge-parsing/) | `bool("false")` is `True`, and unparseable verdicts become passes. |
| 11 | [Partial credit adds up](patterns/11-partial-credit-adds-up/) | Format and process items reach the threshold without a correct result. |
| 12 | [Source-text matching](patterns/12-source-text-matching/) | The expected snippet in a comment passes; the code is never run. |
| 13 | [Ignored options](patterns/13-ignored-options/) | Tolerances, schemas and budgets are accepted and then not applied. |
| 14 | [Correct work failed](patterns/14-correct-work-failed/) | Byte-level comparisons and wrong labels reject equivalent correct work. |
| 15 | [Submission disables the checker](patterns/15-submission-disables-checker/) | The output shares a program with the tests, or carries a directive that turns the check off. |
| 16 | [Incomplete evidence](patterns/16-incomplete-evidence/) | The grader sees a summary (action name, final reply, trimmed messages), not what was done. |
| 17 | [Unverified reference answers](patterns/17-unverified-reference-answers/) | The label comes from a model or from agent-writable input and is never checked. |

## Checklist before you ship an environment

1. Run every task's verifier on the untouched initial state. Nothing should pass.
2. If answers are extracted from text, require exactly one answer in a defined slot, and test a reply that lists many.
3. Replace `gold in reply` with normalised equality, and test a hedge list, a negation and a prompt echo.
4. Score a fixed junk answer against every reference under each similarity threshold you ship. The pass rate should be zero.
5. Make sure the agent cannot write any file the grader reads: tests, test scripts, reward files, reference inputs, test-runner config.
6. Grade from a structured report on a channel the code under test cannot write to, not from stdout.
7. Never use the exit code as the only pass signal; require evidence that every expected test ran and passed.
8. Treat exceptions, missing data and skipped required checks as failures, and check what score every failure path writes.
9. Count agent-caused errors as 0; exclude only harness errors, retry them, and withhold the aggregate if any remain.
10. Parse judge verdicts strictly (a JSON boolean or one exact verdict line) and score parse errors as errors, not passes.
11. Compute the best score reachable with each outcome item failed; it must be below the pass threshold.
12. Grade code by running it, never by searching its source text.
13. For every option a scorer accepts, have a test where that option changes the result; reject unknown options.
14. Rewrite each reference solution in an equivalent form (key order, quotes, formatting, algorithm) and check it still passes.
15. Run submission and tests in separate namespaces or processes, and reject checker directives in the submission.
16. Check the content of actions (arguments, items, results), not only their names, and give judges and monitors the full event log.
17. Verify reference answers independently of where they came from, and store them outside the agent's environment.

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
```

The examples need Python 3.9 or later and nothing outside the standard library. CI runs them on Python 3.9 to 3.13.

## About the "Seen in the wild" links

The links point to public issues filed on the named repositories, each with a reproduction. Some may have been fixed or closed since; the issue thread is the place to check current status. The toy examples here are written from scratch and do not reuse code from those repositories.

## Contributing

Issues and pull requests are welcome: new patterns, better fixes, clearer examples, or public instances of a pattern that should be linked. For a new pattern, please include a runnable stdlib-only `example.py` in the same shape as the others, and make sure `python tests/test_examples.py` passes. For a new "Seen in the wild" link, please link a public issue or write-up that shows the instance. See [CONTRIBUTING.md](CONTRIBUTING.md) for the details.

## License

MIT. See [LICENSE](LICENSE).

---

Maintained by Holdout · hello@holdout.cc · https://holdout.cc
