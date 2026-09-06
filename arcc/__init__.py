"""arc-agi-compressed: fast, seed-honest iteration on ARC-AGI-1, -2 and -3.

Two things, and no more:

1. A small subset of each benchmark, chosen by solver-independent structure, so
   an idea can be tried in minutes instead of hours.
2. A harness that will not report a number without a spread, and compares two
   arms paired on identical seeds.

The second is the point. The first only makes it affordable to do often.
"""

from .stats import Band, Comparison, band, paired, seeds_needed, summarize, SIGMA
from .select import Features, Subset, features, stratified, marginals
from .tasks import load_dir, score_set, score_task, identity_solver, constant_solver

__version__ = "0.1.0"

__all__ = [
    "Band", "Comparison", "band", "paired", "seeds_needed", "summarize", "SIGMA",
    "Features", "Subset", "features", "stratified", "marginals",
    "load_dir", "score_set", "score_task", "identity_solver", "constant_solver",
]
