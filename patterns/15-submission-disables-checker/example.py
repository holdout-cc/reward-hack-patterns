"""Pattern 15: the submission switches the checker off from inside.

Case A: the grader pastes the completion and the test code into one program.
        A completion that ends in a decorator wraps the test's own check()
        function and replaces it with a no-op.
Case B: a static checker honours a directive comment that disables it, and
        the grader passes whatever the checker passes.

Separate namespaces are a partial mitigation for case A, not a complete fix.
Known limitation: the test compares values with ==, which trusts the
submission's own equality method.

Stronger (covers equality spoofing): the fixed grader also checks that each
returned value has the expected type before the test's == runs. An exact-type
check also rejects value-correct answers of another type (e.g. 9.0 for 9);
normalise the representation where that matters.

Robust fix (not done here; too heavy for a stdlib example): run the
submission in a separate sandboxed process and compare plain serialized
values, which carry no methods of their own.

Run: python example.py
"""
import ast
import sys

FAILURES = []


def expect(label, actual, wanted):
    ok = actual == wanted
    print(f"[{'ok' if ok else 'MISMATCH'}] {label}: {actual}")
    if not ok:
        FAILURES.append(label)


# ---------------------------------------------------------------- case A ----
PROMPT = "def square(x):\n"
TEST = (
    "def check(candidate):\n"
    "    assert candidate(3) == 9\n"
    "    assert candidate(-2) == 4\n"
)


def vulnerable_exec(completion):
    program = PROMPT + completion + "\n" + TEST + "\ncheck(square)\n"
    try:
        exec(program, {})
        return True
    except BaseException:
        return False


EXPECTED_TYPE = int  # what square() returns for the int inputs in TEST


def typed(candidate):
    """Fail any return value whose type is not exactly EXPECTED_TYPE, so the
    test's == compares plain ints, not an object the submission defined."""
    def call(*args):
        result = candidate(*args)
        if type(result) is not EXPECTED_TYPE:
            raise TypeError(f"expected {EXPECTED_TYPE.__name__}, got {type(result).__name__}")
        return result
    return call


def fixed_exec(completion):
    source = PROMPT + completion
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return False  # a dangling decorator is a syntax error on its own
    allowed = (ast.FunctionDef, ast.Import, ast.ImportFrom)
    if not all(isinstance(node, allowed) for node in tree.body):
        return False
    solution_ns, test_ns = {}, {}
    try:
        exec(compile(tree, "solution", "exec"), solution_ns)
        exec(TEST, test_ns)  # fresh namespace the solution never touched
        test_ns["check"](typed(solution_ns["square"]))
        return True
    except BaseException:
        return False


DECORATOR_EXPLOIT = "    return 0\n@(lambda f: (lambda *a, **k: None))\n"
CORRECT_A = "    return x * x\n"

# ---------------------------------------------------------------- case B ----
DIRECTIVE = "# checker: off"


def toy_checker(source):
    """Flags calls to eval(). Like many real tools, it obeys a directive."""
    if source.lstrip().startswith(DIRECTIVE):
        return []
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        return [f"syntax error: {exc.msg}"]
    return [f"line {n.lineno}: eval() call" for n in ast.walk(tree)
            if isinstance(n, ast.Call) and getattr(n.func, "id", None) == "eval"]


def vulnerable_lint(source):
    return toy_checker(source) == []


def fixed_lint(source):
    if DIRECTIVE in source:
        return False  # the submission may not configure its own checker
    if not source.strip():
        return False  # nothing to check is not a pass
    return toy_checker(source) == []


EVAL_EXPLOIT = DIRECTIVE + "\ndef total(expr):\n    return eval(expr)\n"
SYNTAX_EXPLOIT = DIRECTIVE + "\nthis is not python at all\n"
CORRECT_B = "def total(values):\n    return sum(values)\n"


def main():
    expect("A: one-program grader, trailing decorator exploit", vulnerable_exec(DECORATOR_EXPLOIT), True)
    expect("A: fixed grader, same completion", fixed_exec(DECORATOR_EXPLOIT), False)
    expect("A: one-program grader, correct completion", vulnerable_exec(CORRECT_A), True)
    expect("A: fixed grader, correct completion", fixed_exec(CORRECT_A), True)

    expect("B: vulnerable, eval() behind the directive", vulnerable_lint(EVAL_EXPLOIT), True)
    expect("B: vulnerable, prose behind the directive", vulnerable_lint(SYNTAX_EXPLOIT), True)
    expect("B: vulnerable, empty submission", vulnerable_lint(""), True)
    expect("B: fixed, eval() behind the directive", fixed_lint(EVAL_EXPLOIT), False)
    expect("B: fixed, prose behind the directive", fixed_lint(SYNTAX_EXPLOIT), False)
    expect("B: fixed, empty submission", fixed_lint(""), False)
    expect("B: vulnerable, clean code", vulnerable_lint(CORRECT_B), True)
    expect("B: fixed, clean code", fixed_lint(CORRECT_B), True)


if __name__ == "__main__":
    main()
    sys.exit(1 if FAILURES else 0)
