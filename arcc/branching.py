"""Branch on the first contradiction; never average one away.

The design is the repository owner's, given as answers to the five questions in
`MEMORY_DESIGN_QUESTIONS.md`, and it is implemented here rather than argued
about. In their words:

    1. cause + condition = effect, not cause = effect
    2. when the screen shows no reason, look in the history of actions
    3. one observation is enough
    4. it is conditional, not unreliable, when the same cause already has a
       different effect and nothing yet distinguishes them
    5. left open

Two of those choices matter more than they look.

**One observation is enough** dissolves the trap recorded in the questions file.
The measured sample budget is a median of four observations per situation, and
21% of situations are seen once, so any scheme that waits for statistics fires
only on the runs that are already stuck. Branching on the first contradiction
needs no statistics at all: storage is cheap, and the expensive part -- finding
what distinguishes the branches -- is deferred until there is something to
explain.

**The absence of a distinguishing feature is the trigger.** That inverts the
question this repo failed to answer before: a control that works 70% of the time
and a control with two modes are identical in aggregate, and timing does not
separate them (measured at 0.74-0.82 of chance). Here nothing has to separate
them up front. The contradiction opens a branch whose condition is `None`, and
`None` is the flag that says: go look.

What this module is: a recorder, run offline over traces. It builds no policy,
proposes no mechanism, and is not wired into any agent. Its only job is to answer
whether the structure separates a known conditional control -- g50t's gated door
-- from ordinary unreliability.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Hashable, Iterator, Optional, Sequence


@dataclass
class Branch:
    """One effect a cause has produced, and the condition under which -- unknown
    until something explains it."""

    effect: Hashable
    condition: Optional[Hashable] = None
    seen: int = 1
    first_step: int = 0
    steps: list[int] = field(default_factory=list)

    @property
    def unexplained(self) -> bool:
        return self.condition is None


@dataclass
class Memory:
    """cause -> branches. A cause with one branch is a plain fact; a cause with
    two or more is an open question."""

    branches: dict[Hashable, list[Branch]] = field(default_factory=lambda: defaultdict(list))
    opened: list[tuple[int, Hashable, Hashable, Hashable]] = field(default_factory=list)

    def observe(self, step: int, cause: Hashable, effect: Hashable) -> bool:
        """Record one (cause, effect). Returns True if this opened a new branch.

        No averaging, no decay, no overwrite: an effect that disagrees with every
        branch on record becomes a branch of its own, on its first appearance.
        """
        bs = self.branches[cause]
        for b in bs:
            if b.effect == effect:
                b.seen += 1
                b.steps.append(step)
                return False
        new = Branch(effect=effect, first_step=step, steps=[step])
        bs.append(new)
        if len(bs) > 1:
            self.opened.append((step, cause, bs[0].effect, effect))
            return True
        return False

    def conditional(self) -> list[Hashable]:
        """Causes carrying more than one effect: the open questions."""
        return [c for c, bs in self.branches.items() if len(bs) > 1]

    def stable(self) -> list[Hashable]:
        return [c for c, bs in self.branches.items() if len(bs) == 1]

    def summary(self) -> dict:
        cond = self.conditional()
        return {
            "causes": len(self.branches),
            "stable": len(self.stable()),
            "conditional": len(cond),
            "branches_opened": len(self.opened),
            "observations": sum(b.seen for bs in self.branches.values() for b in bs),
        }


def run(events: Sequence[tuple[int, Hashable, Hashable]]) -> Memory:
    """Feed a sequence of (step, cause, effect) through a fresh memory."""
    m = Memory()
    for step, cause, effect in events:
        m.observe(step, cause, effect)
    return m
