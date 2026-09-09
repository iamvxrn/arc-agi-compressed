# Branch-on-first-contradiction works, and g50t's door is not a memory problem

The design is the repo owner's, from their answers to
`MEMORY_DESIGN_QUESTIONS.md`: cause + condition = effect, branch on the **first**
contradiction rather than accumulating statistics, leave the condition `None`
until something explains it, and look for the explanation in the history.

Implemented in `arcc/branching.py`, probed offline in `arcc/g50t_probe.py` over
16 recorded g50t traces. No agent was changed and no new mechanism proposed.

    cause  = (control, avatar position before the press)
    effect = the avatar's displacement

## It does what it was designed to do

| | conditional causes | branches at (k2, barrier) |
|---|---|---|
| the 5 seeds that clear level 1 | 11.0 | **2.00** — all five |
| the 11 that do not | 4.6 | 1.09 — one of eleven |

**It is selective.** Of 60-143 causes per run, 2-13 become conditional: 3-10%.
The other 90-97% stay single-branch and pooled. That is the trap in Q1 avoided —
resolution is refined only where a contradiction was actually seen, so the data
is not shattered into cells too small to support anything.

**It needs no statistics.** Branches open on the first disagreement, so the
measured budget of a median four observations per situation, 21% seen once, never
binds. Q3 is satisfied by construction rather than by tuning a threshold.

**It finds the door.** Every seed that passes through the barrier flags
`(k2, (34,16))` as carrying two effects, on the first press that disagrees.

## And it cannot help the seeds that need it

The eleven stuck seeds press k2 into the barrier 13-17 times and observe
`(0, 0)` every time. One branch, no contradiction, nothing to flag.

The door is invisible to them not because the memory is the wrong shape but
because **the contradiction is absent from their experience**. No record can hold
what was never observed.

## The consequence

g50t's door is not a memory-design problem. It is an exploration problem: eleven
seeds of sixteen never generate the observation that would make the door
noticeable, and the five that do have already solved the level by the time they
do.

This does not refute the design. It relocates the question the design was built
to answer. Whether branching pays off is now a question about environments where
the contradiction *is* observed and currently gets averaged away, and g50t is not
one of them.

Status: DESIGN IMPLEMENTED AND BEHAVES AS SPECIFIED. WRONG TEST CASE.
THE BLOCKER ON g50t IS UPSTREAM OF MEMORY.
