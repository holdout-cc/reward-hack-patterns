# RHP-06. Pass counts or results scraped from stdout

- **TL;DR:** Test results are parsed from stdout or stderr, which the code under test can also print to.
- **Typical impact:** Full reward for printing a fake summary line (for example `3 passed`) while the bug stays in place.
- **Quick test:** Add `print("<N> passed")` at import time of a still-buggy solution and grade it. It must fail.
- **Automated check:** Not covered by grader-probe (needs an environment-level test).

## What it is

The grader runs the tests and reads the result out of the terminal output: a regex for `(\d+) passed`, a search for `OK`, a parse of the summary lines. The code under test writes to the same stdout and stderr, so it can print a fake summary. Captured output from failing tests is often printed before the real summary, which makes a first-match regex read the fake one. Even without an attacker, summary formats change across tool versions and get truncated to the terminal width.

## Why it matters

Printing a line is far easier than fixing a bug, and a policy that learns to print the expected summary will do it on every task that uses the same runner. Eval pass rates from scraped output count those rollouts as solved, and they can also silently drift when the test tool changes its output format.

## Vulnerable grader and exploit

A child process imports the solution, runs the cases and prints `"N passed, M failed"`.

```python
def vulnerable(code):
    ...
    proc = subprocess.run([sys.executable, "-c", RUNNER, d], capture_output=True, text=True)
    m = re.search(r"(\d+) passed", proc.stdout + proc.stderr)
    return m is not None and int(m.group(1)) == TOTAL

EXPLOIT = 'print("3 passed")\n\ndef add(a, b):\n    return a - b\n'
```

## Partially mitigated grader

This grader is a **partial mitigation**, not a complete fix. It stops fake summary lines: the grader checks per-case return values instead of reading stdout.

Do not let the code under test write the verdict. Have the harness return structured data in a report the code under test can still rewrite, and have the grader decide.

```python
def fixed(code):
    ...
    subprocess.run([sys.executable, "-c", HARNESS, d, str(out_path)], capture_output=True, text=True)
    if not out_path.exists():
        return False
    results = json.loads(out_path.read_text())
    if len(results) != TOTAL:
        return False
    return all(r.get("ok") and r.get("value") == want for r, (_, want) in zip(results, CASES))
```

With pytest, the practical version is `--junitxml=<path outside the workspace>`: delete the file first, require it to exist after the run, and check that every expected test id is present and passed. Do not count passes; compare against the list of expected test ids. But if the report is written inside the pytest process that imports the code under test, that code can forge it.

**Known limitation:** the harness imports the code under test in the same process that writes `results.json`, and passes it the file's path, so that code can write its own results (for example from an `atexit` handler, or before calling `os._exit(0)`) and the real cases never decide the verdict.

**Robust fix:** see [RHP-07](../07-exit-code-only/). A trusted process that never imports the code under test records each expected test's outcome somewhere that code cannot write.

## How to test for it

- Add `print("<N> passed")`, `print("OK")` or a fake summary line at import time of the solution, leave the bug in, and grade it.
- Add extra passing tests next to the failing ones. If the grader compares a count instead of named results, it passes.
- Grep graders for regexes over `stdout`, `stderr` or `output`.
- Run the suite with a different terminal width and with `CI` set and unset; if the parsed results change, the parser is fragile.

## Seen in the wild

- [hud-evals/hud-python#736](https://github.com/hud-evals/hud-python/issues/736): `fix_calc` reads the pass count from merged stdout and stderr, so `print("10 passed")` in `calc.py` gives reward 1.0 while pytest reports `4 failed, 6 passed` and exits 1.
- [GeneralReasoning/env-r2e-gym#11](https://github.com/GeneralReasoning/env-r2e-gym/issues/11): withheld test results are scraped from pytest's short summary text; a failing test whose message is `PASSED` is recorded as passed.

## Run the example

```
python example.py
```
