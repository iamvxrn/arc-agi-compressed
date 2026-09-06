"""Choosing the subset, reproducibly, without looking at any solver.

The temptation is to pick "hard" or "representative" tasks. Both need solver
scores to define, and a subset chosen by what some solver found hard is a subset
fitted to that solver -- it will flatter its sibling and mislead about anything
built differently.

So selection here uses only what can be computed from the task files themselves:

    n_train         how many demonstration pairs
    shape_change    does the output grid have the same shape as the input
    scale           the size band of the largest grid
    n_colors        the size band of the palette actually used
    grid_ratio      whether output is smaller, same, or larger by area

These are structural, cheap, and solver-independent. Tasks are bucketed by the
tuple of those features, and the subset takes from each bucket in proportion to
its share of the full set, so the subset's marginal distribution over these
features matches the original.

What this does license: a subset whose *composition* mirrors the full set on
named, checkable axes, drawn by a stated seed, reproducible from the data alone.

What it does NOT license: any claim that scores on the subset predict scores on
the full set, or that solver *rankings* are preserved. That is a different claim,
it needs several solvers measured on both, and it is the open item in
docs/METHOD.md. Until it is done, treat a compressed score as a fast development
signal and never as a reported result.
"""

from __future__ import annotations

import json
import pathlib
import random
from collections import defaultdict
from dataclasses import dataclass, asdict
from typing import Iterable


def _band(n: int, edges: tuple[int, ...]) -> int:
    """Index of the first edge n does not exceed; len(edges) if it exceeds all."""
    for i, e in enumerate(edges):
        if n <= e:
            return i
    return len(edges)


@dataclass(frozen=True)
class Features:
    """Solver-independent structure of one task."""

    n_train: int
    shape_change: bool
    scale: int
    n_colors: int
    area_ratio: int

    def key(self) -> tuple:
        return (self.n_train, self.shape_change, self.scale, self.n_colors, self.area_ratio)


def features(task: dict) -> Features:
    """Structural features of an ARC-AGI-1/2 style task dict."""
    train = task.get("train", [])
    grids = [p[k] for p in train for k in ("input", "output") if k in p]
    if not grids:
        raise ValueError("task has no train grids")

    largest = max(len(g) * len(g[0]) for g in grids if g and g[0])
    colors = {c for g in grids for row in g for c in row}

    changed = any(
        len(p["input"]) != len(p["output"]) or len(p["input"][0]) != len(p["output"][0])
        for p in train
        if p.get("input") and p.get("output")
    )

    in_area = sum(len(p["input"]) * len(p["input"][0]) for p in train if p.get("input"))
    out_area = sum(len(p["output"]) * len(p["output"][0]) for p in train if p.get("output"))
    ratio = 1 if out_area == in_area else (0 if out_area < in_area else 2)

    return Features(
        n_train=min(len(train), 5),
        shape_change=changed,
        scale=_band(largest, (100, 400, 900)),
        n_colors=_band(len(colors), (2, 4, 6)),
        area_ratio=ratio,
    )


@dataclass
class Subset:
    """A selection, carrying enough provenance to be re-derived from scratch."""

    name: str
    source: str
    seed: int
    size: int
    task_ids: list[str]
    strata: dict[str, int]

    def save(self, path: pathlib.Path) -> None:
        path.write_text(json.dumps(asdict(self), indent=1, sort_keys=True) + "\n")

    @classmethod
    def load(cls, path: pathlib.Path) -> "Subset":
        return cls(**json.loads(pathlib.Path(path).read_text()))


def stratified(tasks: dict[str, dict], size: int, seed: int, name: str,
               source: str) -> Subset:
    """Draw `size` tasks preserving the marginal distribution over Features.

    Buckets are filled by largest-remainder apportionment, so the subset totals
    exactly `size` and no bucket with any share is silently rounded out of
    existence.
    """
    if size > len(tasks):
        raise ValueError(f"asked for {size} of {len(tasks)} tasks")

    buckets: dict[tuple, list[str]] = defaultdict(list)
    for tid, task in sorted(tasks.items()):
        buckets[features(task).key()].append(tid)

    total = len(tasks)
    exact = {k: len(v) * size / total for k, v in buckets.items()}
    take = {k: min(int(v), len(buckets[k])) for k, v in exact.items()}

    # Largest remainder, deterministic on ties by bucket key.
    short = size - sum(take.values())
    order = sorted(exact, key=lambda k: (-(exact[k] - int(exact[k])), k))
    i = 0
    while short > 0 and i < len(order) * 2:
        k = order[i % len(order)]
        if take[k] < len(buckets[k]):
            take[k] += 1
            short -= 1
        i += 1

    rng = random.Random(seed)
    chosen: list[str] = []
    for k in sorted(buckets):
        ids = sorted(buckets[k])
        rng.shuffle(ids)
        chosen.extend(ids[: take[k]])

    return Subset(
        name=name,
        source=source,
        seed=seed,
        size=len(chosen),
        task_ids=sorted(chosen),
        strata={str(k): take[k] for k in sorted(buckets) if take[k]},
    )


def marginals(tasks: dict[str, dict], ids: Iterable[str] | None = None) -> dict[str, dict]:
    """Per-feature distribution, for checking that a subset matches its source."""
    keep = set(ids) if ids is not None else set(tasks)
    out: dict[str, dict] = defaultdict(lambda: defaultdict(int))
    n = 0
    for tid, task in tasks.items():
        if tid not in keep:
            continue
        n += 1
        for field, value in asdict(features(task)).items():
            out[field][str(value)] += 1
    return {f: {k: v / n for k, v in sorted(d.items())} for f, d in out.items()} if n else {}
