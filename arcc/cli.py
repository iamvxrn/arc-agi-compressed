"""One command, three verbs: select, run, compare."""

from __future__ import annotations

import argparse
import importlib
import json
import pathlib
import sys

from . import select as sel
from . import stats, tasks

HERE = pathlib.Path(__file__).resolve().parent.parent
SUBSETS = HERE / "subsets"


def _load_solver(spec: str):
    """`module:function`, or one of the built-in floors."""
    builtin = {"identity": tasks.identity_solver, "constant": tasks.constant_solver}
    if spec in builtin:
        return builtin[spec]
    if ":" not in spec:
        raise SystemExit(f"solver must be module:function or one of {sorted(builtin)}")
    mod, _, fn = spec.partition(":")
    return getattr(importlib.import_module(mod), fn)


def cmd_select(a) -> int:
    t = tasks.load_dir(a.data)
    sub = sel.stratified(t, size=a.size, seed=a.seed, name=a.name, source=str(a.data))
    out = pathlib.Path(a.out) if a.out else SUBSETS / f"{a.name}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    sub.save(out)

    full, part = sel.marginals(t), sel.marginals(t, sub.task_ids)
    worst = max(
        (abs(part.get(f, {}).get(k, 0.0) - v), f, k)
        for f, d in full.items() for k, v in d.items()
    )
    print(f"{sub.size} of {len(t)} tasks -> {out}")
    print(f"{len(sub.strata)} strata, seed {sub.seed}")
    print(f"largest marginal drift: {worst[0]:.4f} on {worst[1]}={worst[2]}")
    return 0


def cmd_run(a) -> int:
    t = tasks.load_dir(a.data)
    ids = sel.Subset.load(pathlib.Path(a.subset)).task_ids if a.subset else None
    solver = _load_solver(a.solver)

    scores = tasks.score_set(t, solver, ids)
    per_task = {k: v for k, v in scores.items()}
    b = stats.band(list(per_task.values()))

    if a.out:
        pathlib.Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        pathlib.Path(a.out).write_text(json.dumps(
            {"solver": a.solver, "data": str(a.data), "subset": a.subset,
             "n": len(per_task), "mean": b.mean, "scores": per_task}, indent=1) + "\n")

    solved = sum(1 for v in per_task.values() if v >= 1.0)
    print(f"solver   {a.solver}")
    print(f"tasks    {len(per_task)}")
    print(f"solved   {solved} fully ({solved / max(len(per_task), 1):.1%})")
    print(f"mean     {b.mean:.4f}")
    print("\ndeterministic solver: one run is the answer. A STOCHASTIC solver must be")
    print("run at several seeds and compared with `arcc compare`, never like this.")
    return 0


def cmd_compare(a) -> int:
    def load(p):
        d = json.loads(pathlib.Path(p).read_text())
        return d["scores"] if "scores" in d else d

    new, base = load(a.new), load(a.base)
    shared = sorted(set(new) & set(base))
    if not shared:
        print("no shared tasks between the two runs", file=sys.stderr)
        return 1

    # Tasks play the role seeds play for a stochastic agent: the same task in both
    # arms cancels that task's difficulty, so the per-task difference is paired.
    idx = {i: t for i, t in enumerate(shared)}
    c = stats.paired({i: new[t] for i, t in idx.items()},
                     {i: base[t] for i, t in idx.items()})

    gained = [t for t in shared if new[t] > base[t]]
    lost = [t for t in shared if new[t] < base[t]]
    print(f"paired on {len(shared)} shared tasks")
    print(f"delta    {c}")
    print(f"gained   {len(gained)}   lost {len(lost)}")
    if lost and a.verbose:
        print("regressions: " + ", ".join(lost[:20]) + (" ..." if len(lost) > 20 else ""))
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="arcc", description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("select", help="draw a structure-matched subset")
    s.add_argument("data", help="directory of ARC task .json files")
    s.add_argument("--size", type=int, default=100)
    s.add_argument("--seed", type=int, default=0)
    s.add_argument("--name", default="compressed")
    s.add_argument("--out")
    s.set_defaults(fn=cmd_select)

    r = sub.add_parser("run", help="score a solver")
    r.add_argument("data")
    r.add_argument("--subset", help="a subsets/*.json; omit to run the full set")
    r.add_argument("--solver", default="identity")
    r.add_argument("--out")
    r.set_defaults(fn=cmd_run)

    c = sub.add_parser("compare", help="paired difference between two runs")
    c.add_argument("new")
    c.add_argument("base")
    c.add_argument("-v", "--verbose", action="store_true")
    c.set_defaults(fn=cmd_compare)

    a = p.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
