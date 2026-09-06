"""Seed discipline: the part most benchmark harnesses leave out.

A benchmark number without a spread is not a measurement, and the failure is not
hypothetical. The repository this grew out of carries 21 recorded results at a
single seed, four of which sit at exactly 1.7087 -- four different changes that
did nothing, filed as four separate findings -- and a headline "+27%" that is one
seed against one seed inside a band of sd 0.83. A sibling branch had to retract a
headline result and five "rejected" conclusions that had all been living inside
its own noise.

So every entry point here refuses to hand back a bare number.

Two ideas do the work.

**Bands.** n runs give a mean, a standard deviation, and a standard error
sd/sqrt(n). The standard error, not the standard deviation, is what a difference
of means has to clear.

**Pairing.** Stochastic agents differ far more across seeds than across small
code changes. Comparing two independent means therefore hides any effect smaller
than the spread. Running both arms on the *same* seed makes the exploration path
common to both, so the per-seed difference cancels it, and the spread of those
differences is typically several times tighter than the spread of either arm.
Always pair. It is free and it is the difference between seeing a real 0.3 and
calling it noise.

The verdict vocabulary is deliberately small and includes an outcome that is not
a win: `INSIDE THE NOISE` is a valid, common, publishable result.
"""

from __future__ import annotations

import math
import statistics as st
from dataclasses import dataclass
from typing import Iterable, Mapping, Sequence

# A difference must clear this many standard errors to be called real. Two is the
# usual convention and is stated here rather than buried at a call site, so that
# raising it after seeing a result is a visible edit to a named constant.
SIGMA = 2.0


@dataclass(frozen=True)
class Band:
    """A measurement: what it was, how much it moved around, and over how many runs."""

    mean: float
    sd: float
    se: float
    n: int

    def __str__(self) -> str:
        if self.n < 2:
            return f"{self.mean:.4f} (n=1 -- not a measurement)"
        return f"{self.mean:.4f} +/- {self.se:.4f} (sd {self.sd:.4f}, n={self.n})"


def band(values: Sequence[float]) -> Band:
    """Mean, spread and standard error of a set of per-seed scores."""
    vals = list(values)
    if not vals:
        raise ValueError("band() needs at least one value")
    n = len(vals)
    mean = st.mean(vals)
    if n == 1:
        return Band(mean, 0.0, 0.0, 1)
    sd = st.pstdev(vals)
    return Band(mean, sd, sd / math.sqrt(n), n)


@dataclass(frozen=True)
class Comparison:
    """A paired difference between two arms, with the verdict it actually supports."""

    delta: Band
    verdict: str
    seeds: tuple[int, ...]

    @property
    def moved(self) -> bool:
        return self.verdict in ("IMPROVED", "REGRESSED")

    def __str__(self) -> str:
        return f"{self.delta.mean:+.4f} +/- {self.delta.se:.4f}  {self.verdict}"


def paired(new: Mapping[int, float], base: Mapping[int, float]) -> Comparison:
    """Compare two arms on the seeds they share.

    Both arguments map seed -> score. Seeds present in only one arm are dropped:
    an unpaired seed contributes the exploration-path variance that pairing exists
    to remove, so including it would silently undo the method.
    """
    shared = tuple(sorted(set(new) & set(base)))
    if not shared:
        raise ValueError("no shared seeds -- the two arms cannot be paired")

    deltas = [new[s] - base[s] for s in shared]
    d = band(deltas)

    if d.n < 2:
        verdict = "ONE SEED -- NOT A RESULT"
    elif d.se == 0.0:
        # Every seed moved by exactly the same amount. Real, and usually means the
        # change was deterministic rather than that the estimate is infinitely sharp.
        verdict = "IMPROVED" if d.mean > 0 else ("REGRESSED" if d.mean < 0 else "IDENTICAL")
    elif abs(d.mean) < SIGMA * d.se:
        verdict = "INSIDE THE NOISE"
    else:
        verdict = "IMPROVED" if d.mean > 0 else "REGRESSED"

    return Comparison(d, verdict, shared)


def seeds_needed(sd: float, effect: float, sigma: float = SIGMA) -> int:
    """How many paired seeds before an effect of this size could clear the band.

    Answers the question that should be asked *before* a run, not after a
    disappointing one: with this much spread, is the effect I am hoping for even
    detectable at the budget I am about to spend? Returns 1 for a zero spread.
    """
    if sd <= 0:
        return 1
    if effect <= 0:
        raise ValueError("effect must be positive")
    return max(2, math.ceil((sigma * sd / effect) ** 2))


def summarize(groups: Mapping[str, Sequence[float]]) -> str:
    """A fixed-width report of several named groups. Used by every CLI path."""
    width = max((len(k) for k in groups), default=5)
    lines = [f"{'group'.ljust(width)} {'mean':>9} {'sd':>8} {'se':>8} {'n':>4}"]
    for name, vals in groups.items():
        b = band(vals)
        lines.append(f"{name.ljust(width)} {b.mean:9.4f} {b.sd:8.4f} {b.se:8.4f} {b.n:4d}")
    return "\n".join(lines)
