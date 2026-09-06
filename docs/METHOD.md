# Method

## Selection

The temptation is to pick "hard" or "representative" tasks. Both need solver
scores to define, and a subset chosen by what some solver found hard is a subset
fitted to that solver — it will flatter its siblings and mislead about anything
built differently.

So selection uses only what is computable from the task files:

| feature | what it is |
|---|---|
| `n_train` | number of demonstration pairs, capped at 5 |
| `shape_change` | does any demonstration change the grid's shape |
| `scale` | size band of the largest grid (≤100, ≤400, ≤900, more) |
| `n_colors` | band of the palette actually used (≤2, ≤4, ≤6, more) |
| `area_ratio` | total output area smaller / equal / larger than input |

Tasks are bucketed by the tuple of these, and each bucket contributes in
proportion to its share of the full set, by largest-remainder apportionment so
the subset totals exactly the requested size and no non-empty bucket is rounded
out of existence. Within a bucket the draw is a seeded shuffle, so the whole
selection is reproducible from the data and the seed alone.

## Statistics

**Bands.** `n` runs give a mean, a standard deviation, and a standard error
`sd/sqrt(n)`. A difference of means has to clear the standard error, not the
standard deviation.

**Pairing.** Stochastic agents differ far more across seeds than across small
code changes, so comparing two independent means hides any effect smaller than
the spread. Running both arms on the same seed makes the exploration path common
to both; the per-seed difference cancels it, and the spread of those differences
is typically several times tighter than either arm's.

For the static benchmarks the same argument applies with *tasks* in the role of
seeds: the same task in both arms cancels that task's difficulty.

`SIGMA = 2.0` is a named module constant precisely so that raising it after
seeing a disappointing result is a visible edit rather than a quiet one.

## Open items

1. **Proxy fidelity.** Does a compressed score predict the full score, and does
   it preserve solver rankings? Needs several real solvers on both. Not done.
   The floor-solver attempt was uninformative — both floors are 0.0 everywhere.
2. **ARC-AGI-2 subsets.** Not yet drawn; the data is not vendored and the
   selection has only been exercised on ARC-AGI-1.
3. **A stratification for the interactive arm.** ARC-AGI-3 games have mechanic
   tags (`click`, `keyboard`, `keyboard_click`) that are the obvious axis, but
   the tags come from probing the games, which is not solver-independent in the
   way the static features are. Unresolved.
