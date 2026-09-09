# The trade was relocated, not avoided: what counts as the same effect?

## What was claimed

`BRANCHING_RESULT.md` reported that branch-on-first-contradiction avoids the trap
recorded in Q1 -- that local refinement shatters the data -- because it refines
only where a contradiction was actually seen. That is true and it holds: across
four games the structure flags 3-13% of causes and leaves the rest pooled.

It is also incomplete. The trade did not disappear. It moved from the **key** to
the **value**.

## Measured

Same traces, same structure, one change: what counts as "the same effect".

| game | effect = exact displacement | effect = moved / did not |
|---|---|---|
| ls20 | 12.9% | 6.1% |
| m0r0 | 11.3% | 8.2% |
| re86 | **3.1%** | **0.1%** |
| sp80 | 9.9% | 9.5% |

`re86` is tagged `stateful-mode` in the census, with responses alternating on a
period of five -- it is known to be conditional. Under the coarse effect the
structure sees essentially nothing there: 0.1%, a thirtyfold drop.

`ls20` was measured earlier as near-deterministic: 58 repeated `(control,
position)` pairs, one contradictory. Under the fine effect it is the most flagged
game of the four.

So the fine effect flags a game known to be lawful, and the coarse effect hides a
game known to be conditional. **No single granularity is right for both**, and
nothing in the design chooses one.

## Q6

    What makes two outcomes the same effect?

This is not a detail of implementation. Every property of the structure depends
on it: which causes become conditional, how much is flagged, and whether a real
mode is visible at all. The design specifies when to branch and says nothing
about what a branch is a branch of.

Three shapes an answer could take, none of them tested:

1. **Fixed granularity, chosen per environment.** Cheap, and it needs a chooser,
   which is the same problem one level up.
2. **Coarse first, refined on demand.** Start with moved/not, and split a branch
   further only when the coarse version has already proved conditional. Keeps the
   selectivity argument intact at both levels.
3. **Granularity as part of the branch.** A branch carries its own notion of
   sameness, and the condition search may propose a finer one.

## Status

The design survives. Its selectivity claim is measured and holds at both
granularities, so the Q1 trap really is avoided on the key side.

What is now open is a question the design did not ask, reached by measurement
rather than argument, and it is prior to Q2's "where is the condition": there is
no point searching for what distinguishes two branches before deciding what made
them two branches.

Status: SELECTIVITY CONFIRMED. TRADE RELOCATED TO THE VALUE. Q6 OPEN.
