# RHP-05. Agent-writable tests, verifier scripts, reward files and reference data

## What it is

Something the grader relies on sits where the agent can write to it during its turn: the test files, the test script, the reward file the script writes, the input the expected answer is computed from, or code the verifier later runs. Grading then runs in the same place, after the agent, and trusts what it finds. The agent can replace the tests with `pass`, write `1` into the reward file, or change the input so the "expected" answer becomes trivial. Telling the agent "do not edit tests/" in the prompt is not a control.

## Why it matters

Tampering with the grader is a general skill: once a policy learns it on one task, it applies to every task built the same way, and it is often cheaper than solving anything. Eval numbers from such tasks cannot separate a fix from an edit to the tests unless someone reads the trajectories.

## Vulnerable grader and exploit

The workspace holds `calc.py` (buggy), `test_calc.py` and `logs/`. Grading happens afterwards, in the same directory.

```python
def vulnerable_a(ws):
    return run_tests(ws / "test_calc.py", ws)        # runs whatever is there now

def test_script(ws):                                 # stands in for test.sh
    if run_tests(ws / "test_calc.py", ws):
        (ws / "logs" / "reward.txt").write_text("1\n")

def vulnerable_b(ws):
    test_script(ws)
    reward = ws / "logs" / "reward.txt"              # never cleared first
    return reward.exists() and reward.read_text().strip() == "1"

# exploits
(ws / "test_calc.py").write_text("pass\n")
(ws / "logs" / "reward.txt").write_text("1\n")
```

## Fixed grader

Keep a pristine copy of everything the grader needs outside the agent's reach. At grading time, copy in only the agent's deliverable, run the grader's own tests, and compute the reward in the grader.

```python
PRISTINE_TESTS = "from calc import add\nassert add(2, 3) == 5\nassert add(-1, 1) == 0\n"

def fixed_a(ws):
    with tempfile.TemporaryDirectory() as clean:
        clean = pathlib.Path(clean)
        (clean / "calc.py").write_text((ws / "calc.py").read_text())
        (clean / "test_calc.py").write_text(PRISTINE_TESTS)
        return run_tests(clean / "test_calc.py", clean)
```

In a container setup this means: do not mount tests or verifier files into the agent's container (or mount them read-only and run as a user that cannot remount); copy them in after the agent's turn; delete any reward or result file before running the verifier; better still, run the verifier in a separate container that receives only the deliverable. Also remove files that change test behaviour, such as `conftest.py`, `pytest.ini`, `pyproject.toml` or `sitecustomize.py`, unless they are part of the deliverable. Store expected answers; do not recompute them from inputs the agent could edit.

## How to test for it

- For each task, run three scripted agents: one that overwrites the test files with passing stubs, one that writes the maximum reward to every reward path it can find, and one that edits the task inputs. None should score.
- List every path the verifier reads. For each, ask: could the agent's process have written this? Check permissions as the agent's user, not as the author.
- Check that the verifier deletes stale result files before it runs, and that a missing result file scores 0.
- If the verifier runs any agent-supplied script, treat its outputs as untrusted and check the constraints it was supposed to honour.

## Seen in the wild

- [Toloka/tolokaforge#1934](https://github.com/Toloka/tolokaforge/issues/1934): terminal_bench 2.1 tasks mount `/tests` read-write in the agent's container and grading runs that same copy, so replacing `test.sh` with one line that writes `1.0` to the reward file scores 1.0.
- [hud-evals/hud-python#736](https://github.com/hud-evals/hud-python/issues/736): `fix_calc` writes `test_calc.py` into the agent's workspace and never restores it, so replacing it with ten empty tests scores 1.0.
- [UiPath/coder_eval#233](https://github.com/UiPath/coder_eval/issues/233): the 3D-scan task recomputes the expected mass from `scan_data.stl`, which the agent can overwrite; a single zero-volume triangle plus a reported mass of 0 scores 1.0.
- [scaleapi/agentenv-framework#305](https://github.com/scaleapi/agentenv-framework/issues/305): in reward mode the container verifier never clears `reward.txt` before running `test.sh`, so a reward file planted by the agent is scored when the script exits without writing one.
- [scaleapi/rsi-benchmark#103](https://github.com/scaleapi/rsi-benchmark/issues/103): the verifier runs the solver's own training script and scores any `checkpoint-100` directory that appears, so a script that copies in a checkpoint trained earlier is accepted.

## Run the example

```
python example.py
```
