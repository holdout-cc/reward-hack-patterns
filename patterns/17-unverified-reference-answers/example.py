"""Pattern 17: reference answers that nobody verified.

Self-play: a proposer writes a problem and its answer. Four solvers attempt
it, and the proposer is rewarded for problems that are neither too easy nor
too hard: 4 * p * (1 - p), where p is the share of solvers that match the
proposer's answer. Nothing checks that the proposer's answer is right.

Problems here are integer arithmetic expressions so the toy grader can
compute the true answer itself.

Run: python example.py
"""
import ast
import operator
import sys

FAILURES = []


def expect(label, actual, wanted):
    ok = actual == wanted
    print(f"[{'ok' if ok else 'MISMATCH'}] {label}: {actual}")
    if not ok:
        FAILURES.append(label)


OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.FloorDiv: operator.floordiv}


def evaluate(expr):
    """Tiny safe evaluator for + - * // on integers."""
    def walk(node):
        if isinstance(node, ast.Expression):
            return walk(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, int):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in OPS:
            return OPS[type(node.op)](walk(node.left), walk(node.right))
        raise ValueError("unsupported expression")
    return walk(ast.parse(expr, mode="eval"))


def learnability(label, solver_answers):
    p = sum(a == label for a in solver_answers) / len(solver_answers)
    return 4 * p * (1 - p)


# --- vulnerable: the proposer's label is trusted ----------------------------
def vulnerable(problem, label, solver_answers):
    return learnability(label, solver_answers)


# --- fixed: the label must be confirmed independently before it counts -----
def fixed(problem, label, solver_answers):
    try:
        truth = evaluate(problem)
    except (ValueError, SyntaxError, ZeroDivisionError):
        return 0.0
    if truth != label:
        return 0.0  # wrong label: no proposer reward, and no solver training on it
    return learnability(label, solver_answers)


# Easy problem with a false label: half the solvers copy a common slip.
FALSE_LABEL = ("7 + 8", 16, [15, 15, 16, 16])
# Harder problem with a true label; solvers split for real.
HARD_TRUE = ("(37 * 41) - (18 * 23)", 1103, [1103, 1103, 1093, 1113])


def main():
    expect("vulnerable, false label earns max learnability", vulnerable(*FALSE_LABEL), 1.0)
    expect("fixed, false label", fixed(*FALSE_LABEL), 0.0)
    expect("vulnerable, hard problem with true label", vulnerable(*HARD_TRUE), 1.0)
    expect("fixed, hard problem with true label", fixed(*HARD_TRUE), 1.0)


if __name__ == "__main__":
    main()
    sys.exit(1 if FAILURES else 0)
