# arc-agi-compressed

Fast, seed-honest iteration on ARC-AGI-1, -2 and -3.

Two things, and no more:

1. **A small subset of each benchmark**, chosen by solver-independent structure,
   so an idea can be tried in minutes instead of hours.
2. **A harness that will not report a number without a spread**, and that
   compares two arms paired on identical seeds.

The second is the point. The first only makes it affordable to do often.

## Why

Most reported deltas on these benchmarks are inside their own noise, and nothing
in the usual tooling says so. This is not a hypothetical worry — it is what the
repository this grew out of looks like when you audit it:

- 21 recorded results at a **single seed**
- four of them at **exactly 1.7087** — four different changes that did nothing,
  filed as four separate findings
- a headline **"+27%"** that is one seed against one seed
- measured spread on that same set: **sd 0.83**, eight seeds of unmodified code
  ranging 2.32 to 4.58

A sibling branch had already had to retract one headline result and five
"rejected" conclusions that had all been living inside its own noise band.

So `arcc` refuses to hand back a bare number, and every comparison is paired.

## Install

No dependencies beyond the standard library. Python 3.10+.

```sh
git clone https://github.com/iamvxrn/arc-agi-compressed
cd arc-agi-compressed
python3 tests/test_arcc.py      # 10 tests, ~1s
```

## Data

**No benchmark data ships here.** The upstream sets are Apache-2.0 and are better
fetched from their own homes, where they stay current and correctly attributed:

| | source |
|---|---|
| ARC-AGI-1 | `github.com/fchollet/ARC-AGI` → `data/{training,evaluation}` |
| ARC-AGI-2 | `github.com/arcprize/ARC-AGI-2` → `data/{training,evaluation}` |
| ARC-AGI-3 | the ARC Prize starter kit (interactive; needs its engine) |

This repository ships **task id lists** and the harness, nothing else.

## Use

```sh
# draw a structure-matched subset
python3 -m arcc.cli select /path/to/ARC-AGI/data/evaluation --size 100 --seed 0 \
    --name arc1-evaluation-100

# score a solver on it  (module:function, or the built-in floors)
python3 -m arcc.cli run /path/to/ARC-AGI/data/evaluation \
    --subset subsets/arc1-evaluation-100.json --solver mysolver:solve --out runs/new.json

# paired difference against a previous run
python3 -m arcc.cli compare runs/new.json runs/base.json
```

A solver is any callable `solve(train_pairs, test_input) -> grid | [grid, grid] | None`.

For the interactive arm, `arcc.arc3` runs any seed-taking command once per seed in
parallel and applies the same statistics — see its docstring.

## What is established, and what is not

**Established.** The subsets preserve the source set's marginal distribution over
five solver-independent structural features (`n_train`, `shape_change`, `scale`,
`n_colors`, `area_ratio`). Measured on ARC-AGI-1, 100 drawn from 400, seed 0:

| split | strata | largest marginal drift |
|---|---|---|
| training | 46 | 0.0575 |
| evaluation | 54 | 0.0425 |

Most cells drift under 0.025. Reproduce with `arcc.select.marginals`.

**Not established — the open item.** That a score on the compressed subset
predicts the score on the full set, or preserves the *ranking* of two solvers.
That claim needs several real solvers measured on both, and it has not been done.

An attempt using the two built-in floors was **uninformative**: `identity` and
`constant` both score exactly 0.0000 on all four full and compressed sets, so
there was no signal to compare. That is recorded here rather than omitted.

Until that validation exists, **treat a compressed score as a development signal
and never as a reported result.** Report full-set numbers.

## The vocabulary

`arcc.stats` returns one of five verdicts, and only two of them are wins:

    IMPROVED                 cleared 2 standard errors upward
    REGRESSED                cleared 2 standard errors downward
    INSIDE THE NOISE         the number moved; the explanation is unsupported
    ONE SEED -- NOT A RESULT
    IDENTICAL

`INSIDE THE NOISE` is the common outcome and a publishable one.

`seeds_needed(sd, effect)` answers the question worth asking *before* spending a
run: at this spread, is the effect I am hoping for even detectable at this budget?

## Licence

Code: MIT, see `LICENSE`. Benchmark data is not redistributed here and remains
under its own upstream licence.
