"""Does branch-on-first-contradiction separate g50t's gated door?

g50t is the test case because its failure is known from measurement, not guessed:
all eleven seeds that fail stop at exactly (34, 16), pressing k2 into a barrier
13-17 times without moving, while all five that clear the level pass straight
through. So there is a control whose effect is genuinely conditional, its cause
is known, and the question is only whether the structure notices.

    cause  = (control, avatar position before the press)
    effect = the avatar's displacement

Run: python3 -m arcc.g50t_probe <dir of g50t_s*.jsonl>
"""

from __future__ import annotations

import json
import pathlib
import sys
from collections import Counter

from .branching import run

BARRIER = (34, 16)


def events(path: pathlib.Path):
    """(step, cause, effect) from one trace, effect = displacement to next pos."""
    fired = [e for e in (json.loads(l) for l in path.open())
             if e.get("event") == "fired" and e.get("pos")]
    out = []
    for i, e in enumerate(fired[:-1]):
        here, nxt = tuple(e["pos"]), tuple(fired[i + 1]["pos"])
        out.append((i, (e["tok"], here), (nxt[0] - here[0], nxt[1] - here[1])))
    return out


def main(argv=None) -> int:
    d = pathlib.Path((argv or sys.argv[1:])[0])
    rows = []
    for p in sorted(d.glob("g50t_s*.jsonl")):
        seed = int(p.stem.split("_s")[1])
        res = json.loads((p.parent / f"{p.stem}.json").read_text())
        won = res["games"]["g50t"]["levels_completed"] > 0
        m = run(events(p))
        s = m.summary()
        cond = m.conditional()
        at_barrier = [c for c in cond if c[1] == BARRIER]
        k2_barrier = ("k2", BARRIER)
        rows.append((seed, won, s, len(cond), at_barrier, k2_barrier in m.branches,
                     len(m.branches.get(k2_barrier, []))))

    print(f"{'seed':5} {'ур':>3} {'причин':>7} {'стабильных':>11} {'УСЛОВНЫХ':>9} "
          f"{'у барьера':>10} {'ветвей у (k2,барьер)':>21}")
    for seed, won, s, ncond, at_b, has_k2, nb in rows:
        print(f"{seed:5} {int(won):3} {s['causes']:7} {s['stable']:11} {ncond:9} "
              f"{len(at_b):10} {nb if has_k2 else '-':>21}")

    W = [r for r in rows if r[1]]
    L = [r for r in rows if not r[1]]
    f = lambda g, i: sum(r[i] for r in g) / len(g) if g else 0.0
    print(f"\nпобедители  ({len(W)}): условных причин {f(W,3):.1f}, ветвей у (k2,барьер) {f(W,6):.2f}")
    print(f"проигравшие ({len(L)}): условных причин {f(L,3):.1f}, ветвей у (k2,барьер) {f(L,6):.2f}")

    flagged = sum(1 for r in rows if r[6] > 1)
    print(f"\n(k2, {BARRIER}) помечена как условная на {flagged} из {len(rows)} seed'ов")
    return 0


if __name__ == "__main__":
    sys.exit(main())
