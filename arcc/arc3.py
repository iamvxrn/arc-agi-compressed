"""The ARC-AGI-3 arm: interactive games, where the seeds are the agent's own.

ARC-AGI-1 and -2 are static -- a task is a task, and a deterministic solver run
twice gives the same answer, so pairing is over *tasks*. ARC-AGI-3 is interactive
and its agents explore stochastically, so the same code scores differently every
run and pairing is over *seeds*. The statistics in `arcc.stats` are the same; only
what a "unit" is changes.

Measured on one such agent: eight seeds of the same unmodified code scored
2.32 to 4.58 on a four-game set, sd 0.83. Any single-seed comparison on that set
is therefore blind to anything smaller than about one whole point.

This module does not ship an engine or an agent. It runs a command you supply,
once per seed, and reads a JSON file back. The command is expected to write

    {"games": {"<id>": {"score": <float>, "levels_completed": <int>}, ...}}

which is the shape the public ARC-AGI-3 starter harnesses already emit.
"""

from __future__ import annotations

import concurrent.futures as cf
import json
import os
import pathlib
import subprocess
from typing import Mapping, Sequence

from .stats import band, paired, summarize

SUBSETS = pathlib.Path(__file__).resolve().parent.parent / "subsets"


def run_seeds(command: Sequence[str], seeds: Sequence[int], out_dir: str | pathlib.Path,
              seed_flag: str = "--seed", out_flag: str = "--out",
              jobs: int | None = None) -> dict[int, dict]:
    """Run `command` once per seed in parallel; return seed -> parsed result.

    Seeds are independent processes, so this is embarrassingly parallel and the
    default leaves one core free so the machine stays usable.
    """
    out = pathlib.Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    jobs = jobs or max(1, (os.cpu_count() or 2) - 1)

    def one(seed: int):
        path = out / f"seed{seed}.json"
        cmd = [*command, seed_flag, str(seed), out_flag, str(path)]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0 or not path.exists():
            return seed, None
        return seed, json.loads(path.read_text())

    results: dict[int, dict] = {}
    with cf.ThreadPoolExecutor(max_workers=jobs) as ex:
        for seed, data in ex.map(one, seeds):
            if data is not None:
                results[seed] = data
    return results


def group(runs: Mapping[int, dict], games: Sequence[str]) -> dict[int, float]:
    """Seed -> mean score over a named set of games."""
    out = {}
    for seed, r in runs.items():
        vals = [r["games"][g]["score"] for g in games if g in r.get("games", {})]
        if vals:
            out[seed] = sum(vals) / len(vals)
    return out


def report(runs: Mapping[int, dict], groups: Mapping[str, Sequence[str]],
           base: Mapping[str, Mapping[int, float]] | None = None) -> str:
    """Bands per group, and the paired verdict against a baseline if given.

    A change is a win only when the group carrying the open problem improves and
    the guard group does not regress. Both halves are required: on the agent this
    was built against, a fix that left the keyboard games untouched still cost the
    two scoring games 0.28 each with every one of 16 seeds negative.
    """
    lines = [summarize({k: list(group(runs, g).values()) for k, g in groups.items()})]
    if base:
        lines.append("")
        for name, games in groups.items():
            now = group(runs, games)
            if name not in base:
                continue
            c = paired(now, base[name])
            lines.append(f"{name:12} {c}  on {len(c.seeds)} shared seeds")
    return "\n".join(lines)


def load_subset(name: str = "arc3c") -> dict:
    """The probe set definition: groups, settings and the recorded baseline."""
    path = pathlib.Path(name)
    if not path.exists():
        path = SUBSETS / (name if name.endswith(".json") else f"{name}.json")
    return json.loads(path.read_text())


def games(subset: dict) -> list[str]:
    """Every game in the subset, probe group first."""
    out: list[str] = []
    for g in subset["groups"].values():
        out.extend(x for x in g["games"] if x not in out)
    return out


def verdict(runs: Mapping[int, dict], subset: dict,
            base: Mapping[str, Mapping[int, float]] | None = None) -> str:
    """The full report, and the two-sided rule a change has to satisfy.

    A win requires BOTH halves: the probe group improves and the guard group does
    not regress. Reporting only the first is how a keyboard fix that costs the
    scoring games gets recorded as progress.
    """
    groups = {k: v["games"] for k, v in subset["groups"].items()}
    lines = [report(runs, groups, base)]

    if base:
        probe = paired(group(runs, groups["probe"]), base["probe"])
        guard = paired(group(runs, groups["guard"]), base["guard"])
        won = probe.verdict == "IMPROVED" and guard.verdict != "REGRESSED"
        lines += ["", f"probe {probe.verdict}, guard {guard.verdict}"
                      f"  ->  {'A WIN' if won else 'NOT A WIN'}"]
        if probe.verdict == "IMPROVED" and guard.verdict == "REGRESSED":
            lines.append("the probe moved and the guard broke -- this is the exact"
                         " shape the guard group exists to catch")
    return "\n".join(lines)
