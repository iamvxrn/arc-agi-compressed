# Three independent tests, all decided by representation granularity

## What was being asked

The owner's answer to Q2: when the screen shows no reason for a contradiction,
look in the history of actions. Tested on g50t, the only game with both a
reliable avatar detector and real contradictions.

## What happened

| test | feature | result |
|---|---|---|
| history, local | the immediately preceding action | 1.12x chance |
| history, cumulative | was control X ever pressed before | 0.00x chance |
| map | avatar size, shape-found flag | 0 of 63 separated |
| history, coarsest | step index within the play | 0 of 6, below chance |
| map, full | board hash without the clock | 5 of 6 "separated" -- **and vacuous** |

The last row is the important one. On g50t the door press is seen 9-16 times
across 7-11 *distinct* board hashes, so nearly every press has a board of its
own. Under that granularity the two outcome groups are disjoint almost by
construction, and the test answers nothing.

One seed is informative in the other direction. `s11` presses 16 times across 11
boards, boards therefore repeat, and one board appears with **both** outcomes.
That is a genuine same-board-different-outcome: hidden state, on at least one
seed.

## The pattern

    effect fine    -> ls20, measured near-deterministic, is the most flagged
    effect coarse  -> re86, tagged stateful-mode, shows 0.1%

    feature local  -> previous action: nothing
    feature coarse -> ever-pressed: nothing

    board as hash  -> too fine to be falsifiable

Every one of these was settled by how finely the representation carves the world,
not by anything the world did. Three independent routes, the same outcome.

## Consequence

Q6 -- what counts as the same effect, the same state, the same situation -- is
not the sixth item on a list. It is prior to all of them. Until it is answered,
no experiment of this shape can return information: too fine and everything
differs, too coarse and nothing does, and the analyst chooses which by choosing
the encoding.

This is also why the earlier refutations in the parent repo took the shape they
did. Conditioning on position, then on body configuration, each partitioned the
same data more finely and lost support without buying truth (g50t: 43 repeated
pairs to 13). That was read as "these variables are wrong". It is at least as
consistent with "no fixed granularity can be right", which is a different problem
with a different repair.

## What is established

- The branching structure is selective at every granularity tried (3-13%).
- The door on g50t is real, and it does **not** latch: every winning seed passes
  once and fails again afterwards, so "open it and it stays open" is refuted.
- Successes cluster at 24-38 actions into a play but a threshold on that does not
  separate them, so earliness correlates with the cause without being it.
- At least one seed shows the same board producing both outcomes.

## What is not

Where the condition lives. Every instrument used to ask returned an artefact of
its own resolution.

Status: Q2 UNANSWERED. Q6 PROMOTED TO PRIOR. THE DOOR DOES NOT LATCH.
