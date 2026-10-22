"""Run every patterns/*/example.py and check that it exits cleanly.

Each example exits non-zero if any of its expectations does not hold, so a
passing run means: the vulnerable grader accepts the exploit, the fixed
grader rejects it, and the correct answer passes both.

Usage:
    python -m pytest tests/
    python tests/test_examples.py
"""
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
EXAMPLES = sorted(ROOT.glob("patterns/*/example.py"))


def run_example(path):
    return subprocess.run(
        [sys.executable, str(path)],
        cwd=path.parent,
        capture_output=True,
        text=True,
        timeout=120,
    )


def test_examples_found():
    assert len(EXAMPLES) >= 14, f"expected at least 14 examples, found {len(EXAMPLES)}"


def test_every_pattern_has_readme_and_example():
    for d in sorted((ROOT / "patterns").iterdir()):
        if d.is_dir():
            assert (d / "README.md").is_file(), f"{d.name} has no README.md"
            assert (d / "example.py").is_file(), f"{d.name} has no example.py"


try:
    import pytest
except ImportError:  # plain-python mode
    pytest = None

if pytest is not None:

    @pytest.mark.parametrize("path", EXAMPLES, ids=[p.parent.name for p in EXAMPLES])
    def test_example(path):
        proc = run_example(path)
        assert proc.returncode == 0, f"{path.parent.name} failed:\n{proc.stdout}\n{proc.stderr}"
        assert "MISMATCH" not in proc.stdout


def main():
    failed = 0
    for path in EXAMPLES:
        proc = run_example(path)
        ok = proc.returncode == 0 and "MISMATCH" not in proc.stdout
        print(f"{'PASS' if ok else 'FAIL'}  {path.parent.name}")
        if not ok:
            failed += 1
            print(proc.stdout)
            print(proc.stderr)
    print(f"\n{len(EXAMPLES) - failed}/{len(EXAMPLES)} examples passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
