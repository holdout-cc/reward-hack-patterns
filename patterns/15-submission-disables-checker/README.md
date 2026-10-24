# 15. The submission switches the checker off from inside

## What it is

The thing being graded can change how the grader behaves, because the two share a program or because the checker obeys directives in its input. Examples: a harness that pastes the completion and the tests into one source string, so a completion ending in a decorator wraps the test function, or a completion can redefine `assert` helpers and builtins; a type checker or linter run on the output as is, so a leading `# type: ignore`, `# noqa` or a config comment turns it off. The check runs and reports success, but it checked nothing.

## Why it matters

The trick is a fixed string that works on every task using the same harness, so once found it transfers widely. Eval scores are inflated by the share of tasks where the string applies, with no task-specific work at all.

## Vulnerable grader and exploit

One program for completion and tests:

```python
def vulnerable_exec(completion):
    program = PROMPT + completion + "\n" + TEST + "\ncheck(square)\n"
    try:
        exec(program, {})
        return True
    except BaseException:
        return False

# the trailing decorator applies to the test's own `def check`
DECORATOR_EXPLOIT = "    return 0\n@(lambda f: (lambda *a, **k: None))\n"
```

A checker that obeys a directive:

```python
def vulnerable_lint(source):
    return toy_checker(source) == []      # toy_checker returns [] if line 1 is "# checker: off"

EVAL_EXPLOIT = "# checker: off\ndef total(expr):\n    return eval(expr)\n"
```

## Fixed grader

Keep the submission and the checker apart. Parse the submission on its own, allow only the node types you expect, run it in its own namespace, and run the tests in a fresh namespace that receives only the function object. Strip or reject directives that configure the checker.

Separate namespaces alone are a **partial mitigation**, not a complete fix. **Known limitation:** the tests compare values with `==`, and `==` trusts the submission's own equality method, so a returned object can decide for itself that it equals the expected value. **Robust fix:** also check that the returned value has the expected type (for example `type(result) is type(expected)`), or compare on a plain, normalised representation, before trusting equality. The fixed grader below does the type check: return values that are not exactly `int` fail before the test's `==` runs.

```python
def fixed_exec(completion):
    try:
        tree = ast.parse(PROMPT + completion)        # a dangling decorator is a SyntaxError
    except SyntaxError:
        return False
    if not all(isinstance(n, (ast.FunctionDef, ast.Import, ast.ImportFrom)) for n in tree.body):
        return False
    solution_ns, test_ns = {}, {}
    exec(compile(tree, "solution", "exec"), solution_ns)
    exec(TEST, test_ns)
    test_ns["check"](typed(solution_ns["square"]))  # typed(): see below
    return True                                     # (wrapped in try/except in the example)

def typed(candidate):                               # check the type before the test's ==
    def call(*args):
        result = candidate(*args)
        if type(result) is not int:
            raise TypeError(type(result).__name__)
        return result
    return call

def fixed_lint(source):
    if DIRECTIVE in source or not source.strip():
        return False
    return toy_checker(source) == []
```

The solution still runs in the grader's process; for untrusted code, run it in a separate, sandboxed process as well. For real type checkers, also turn off inline suppression in the checker's own config where it supports that, and treat empty extracted code as a failure.

## How to test for it

- Append a decorator line, a redefinition of the test's helper names, or `import builtins; builtins.AssertionError = ...` to a wrong completion. All must fail.
- Prefix a wrong submission with each suppression directive the checker supports. It must fail.
- Submit an empty string and a refusal in prose. Both must fail.
- Check whether the harness builds one source string out of submission and tests. If it does, assume the submission can reach the tests.

## Seen in the wild

- [openai/human-eval#71](https://github.com/openai/human-eval/issues/71): the harness joins prompt, completion and test into one program; a fixed two-line completion ending in a decorator replaces `check()` with a no-op and passes 100 of 164 tasks.
- [langchain-ai/openevals#290](https://github.com/langchain-ai/openevals/issues/290): the pyright and mypy evaluators check the output as is, so a leading `# type: ignore` makes code with type errors pass both, and makes syntax errors and plain prose pass pyright.

## Run the example

```
python example.py
```
