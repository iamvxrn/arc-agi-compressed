"""Run branch-on-first-contradiction over any game's traces.

`g50t_probe` answered one question about one game and found the wrong test case:
the seeds that need the door never observe it, so there is no contradiction to
branch on. This asks the general version.

    Where contradictions ARE observed, how much does the current memory throw
    away, and is what it throws away concentrated or scattered?

The comparison is the point. Today's memory keeps one value per key and the
second observation replaces the first, so every contradiction is a fact that was
recorded and then deleted. This counts them.

Run: python3 -m arcc.trace_probe <dir> [game ...]
"""

from __future__ import annotations

import json
import pathlib
import statistics as st
import sys
from collections import Counter

from .branching import run


def events(path: pathlib.Path):
    fired = [e for e in (json.loads(l) for l in path.open())
             if e.get("event") == "fired" and e.get("pos")]
    out = []
    for i, e in enumerate(fired[:-1]):
        here, nxt = tuple(e["pos"]), tuple(fired[i + 1]["pos"])
        out.append((i, (e["tok"], here), (nxt[0] - here[0], nxt[1] - here[1])))
    return out


def probe(path: pathlib.Path) -> dict | None:
    ev = events(path)
    if not ev:
        return None
    m = run(ev)
    s = m.summary()
    cond = m.conditional()
    # An observation is DISCARDED by today's memory when its effect disagrees
    # with the effect already stored for that cause. Count them.
    discarded = 0
    for c in cond:
        bs = m.branches[c]
        first = max(bs, key=lambda b: b.first_step == min(x.first_step for x in bs))
        discarded += sum(b.seen for b in bs if b is not first)
    return {
        "causes": s["causes"],
        "observations": s["observations"],
        "conditional": len(cond),
        "share_conditional": len(cond) / max(s["causes"], 1),
        "discarded": discarded,
        "share_discarded": discarded / max(s["observations"], 1),
        "branches": st.mean([len(m.branches[c]) for c in cond]) if cond else 1.0,
    }


def main(argv=None) -> int:
    a = argv or sys.argv[1:]
    d = pathlib.Path(a[0])
    games = a[1:] or sorted({p.stem.split("_s")[0] for p in d.glob("*_s*.jsonl")})
    print(f"{'игра':6} {'seed':>5} {'причин':>7} {'наблюд.':>8} {'условных':>9} "
          f"{'доля':>6} {'ВЫБРОШЕНО':>10} {'доля':>6} {'ветвей':>7}")
    for g in games:
        rows = [r for r in (probe(p) for p in sorted(d.glob(f"{g}_s*.jsonl"))) if r]
        if not rows:
            continue
        f = lambda k: st.mean([r[k] for r in rows])
        print(f"{g:6} {len(rows):5} {f('causes'):7.0f} {f('observations'):8.0f} "
              f"{f('conditional'):9.1f} {f('share_conditional'):6.1%} "
              f"{f('discarded'):10.1f} {f('share_discarded'):6.1%} {f('branches'):7.2f}")
    print("\nВЫБРОШЕНО = наблюдений, которые сегодняшняя память затирает как противоречащие")
    return 0


if __name__ == "__main__":
    sys.exit(main())
