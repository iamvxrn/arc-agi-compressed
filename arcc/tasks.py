"""Loading and scoring ARC-AGI-1 / -2 style tasks, and the solver interface.

No data ships in this repository. The upstream sets are Apache-2.0 and are
better fetched from their own homes, where they stay current and correctly
attributed:

    ARC-AGI-1   https://github.com/fchollet/ARC-AGI          data/{training,evaluation}
    ARC-AGI-2   https://github.com/arcprize/ARC-AGI-2        data/{training,evaluation}

A solver is any callable

    solve(train_pairs, test_input) -> grid | None

`None` means "no answer", which scores zero and is distinct from a wrong grid
only in the report, never in the score. Two attempts are allowed per test input,
matching the upstream convention; a solver that wants one simply returns one.
"""

from __future__ import annotations

import json
import pathlib
from typing import Callable, Iterable, Sequence

Grid = list[list[int]]
Solver = Callable[[list[dict], Grid], Grid | list[Grid] | None]


def load_dir(path: str | pathlib.Path) -> dict[str, dict]:
    """Every *.json task in a directory, keyed by task id (the filename stem)."""
    d = pathlib.Path(path)
    if not d.is_dir():
        raise NotADirectoryError(f"{d} is not a directory of task files")
    tasks = {p.stem: json.loads(p.read_text()) for p in sorted(d.glob("*.json"))}
    if not tasks:
        raise ValueError(f"no .json tasks in {d}")
    return tasks


def _as_attempts(answer: Grid | list[Grid] | None) -> list[Grid]:
    """Normalise a solver's return into at most two attempts."""
    if answer is None:
        return []
    if answer and isinstance(answer[0], list) and answer[0] and isinstance(answer[0][0], list):
        return list(answer)[:2]  # already a list of grids
    return [answer]  # a single grid


def score_task(task: dict, solver: Solver) -> float:
    """Fraction of this task's test inputs solved exactly. 1.0 only if all are."""
    tests = task.get("test", [])
    if not tests:
        return 0.0
    got = 0
    for case in tests:
        attempts = _as_attempts(solver(task["train"], case["input"]))
        if any(a == case["output"] for a in attempts):
            got += 1
    return got / len(tests)


def score_set(tasks: dict[str, dict], solver: Solver,
              ids: Iterable[str] | None = None) -> dict[str, float]:
    """Per-task scores. The headline number is the mean of these."""
    keep = list(ids) if ids is not None else sorted(tasks)
    return {t: score_task(tasks[t], solver) for t in keep if t in tasks}


def identity_solver(train: list[dict], test_input: Grid) -> Grid:
    """Return the input unchanged.

    The floor every real solver has to clear. It is not zero -- some tasks have
    identity-shaped answers -- and a mechanism scoring at or below it has shown
    nothing, however good the absolute number looks.
    """
    return test_input


def constant_solver(train: list[dict], test_input: Grid) -> Grid | None:
    """Return the single output grid if every demonstration shares one.

    The second floor, and a sharper one than identity: it catches the tasks whose
    answer never depends on the input at all.
    """
    outs = [p["output"] for p in train if "output" in p]
    if outs and all(o == outs[0] for o in outs):
        return outs[0]
    return None
