# 07. Exit-code-only checks

## What it is

The grader runs the tests (or a program that is the solution followed by the asserts) and passes the task if the process exits with code 0. Nothing confirms that the tests ran. A solution that ends the process early with code 0 (`os._exit(0)`, `raise SystemExit(0)`, `sys.exit()`, a signal handler, an `atexit` hook) never reaches a single assert. Test runners also exit 0 when every test is skipped or when no tests were collected under some settings.

## Why it matters

One line placed before the tests passes every task that shares the harness, and if solutions are carried into later steps, it passes those too. Eval scores built on exit codes count those runs as solved and cannot tell them apart from correct code.

## Vulnerable grader and exploit

```python
TESTS = "assert mul(3, 4) == 12\nassert mul(0, 9) == 0\n"

def vulnerable(solution):
    return run(solution + "\n" + TESTS).returncode == 0

EXPLOIT = "import os\nos._exit(0)\n"     # also: raise SystemExit(0), sys.exit()
```

## Fixed grader

Require positive evidence that the tests ran to the end, in addition to the exit code.

```python
def fixed(solution):
    sentinel = secrets.token_hex(16)          # new for every run, not in the prompt
    program = solution + "\n" + TESTS + f"print({sentinel!r})\n"
    proc = run(program)
    lines = proc.stdout.strip().splitlines()
    return proc.returncode == 0 and bool(lines) and lines[-1] == sentinel
```

The sentinel is a minimum. Stronger: run the solution inside a harness that catches `BaseException` (which includes `SystemExit`), and report results from a separate process or through a file the solution cannot reach. With pytest, read a JUnit XML report and require every expected test id to be present and passed (see [06](../06-stdout-scraping/)); treat skipped or missing tests as failures.

## How to test for it

- Prepend `import os; os._exit(0)` to a wrong solution. Repeat with `raise SystemExit(0)` and `sys.exit()`. All must fail.
- Make every test skip (for example by making the fixture or data the tests depend on look empty). The task must fail.
- Delete all tests or make collection find none. The task must fail.
- Grep graders for `returncode == 0` and `exit_code == 0` used as the only pass condition.

## Seen in the wild

- [NVIDIA-NeMo/Gym#4901](https://github.com/NVIDIA-NeMo/Gym/issues/4901): the scicode server sets `passed = proc.returncode == 0`; `raise SystemExit(0)` in the generated code passed all 13 scored sub-steps on the example problems.
- [UiPath/coder_eval#234](https://github.com/UiPath/coder_eval/issues/234): `test.sh` writes reward 1 whenever pytest exits 0, and pytest exits 0 when the 12 checkbox tests all skip, so a text-only PDF scores 1.0.
- [hud-evals/hud-python#736](https://github.com/hud-evals/hud-python/issues/736): the report notes that `import os; os._exit(0)` at the top of `calc.py` makes pytest exit 0 without running any tests, so switching that grader to an exit-code check would not fix it.

## Run the example

```
python example.py
```
