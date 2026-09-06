"""Tests that would fail if the honesty machinery quietly stopped working."""

import math
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from arcc import stats, select, tasks


def test_single_seed_is_not_a_measurement():
    b = stats.band([1.7087])
    assert b.n == 1 and b.se == 0.0
    assert "not a measurement" in str(b)


def test_band_matches_hand_computed():
    b = stats.band([1.0, 3.0])
    assert b.mean == 2.0 and b.sd == 1.0
    assert math.isclose(b.se, 1.0 / math.sqrt(2))


def test_pairing_sees_what_independent_means_cannot():
    # A real +0.30 effect buried under a spread of about 1.7.
    base = {s: float(s % 5) for s in range(16)}
    new = {s: base[s] + 0.30 for s in range(16)}
    assert stats.band(list(new.values())).sd > 1.0     # each arm is very noisy
    c = stats.paired(new, base)
    assert c.verdict == "IMPROVED"                      # pairing cancels it
    assert math.isclose(c.delta.mean, 0.30)


def test_noise_is_reported_as_noise():
    base = {s: float(s % 7) for s in range(12)}
    new = {s: base[s] + (0.4 if s % 2 else -0.4) for s in range(12)}
    assert stats.paired(new, base).verdict == "INSIDE THE NOISE"


def test_unpaired_seeds_are_refused():
    try:
        stats.paired({1: 1.0}, {2: 1.0})
    except ValueError:
        return
    raise AssertionError("comparing arms with no shared seed must fail")


def test_seeds_needed_grows_with_noise():
    assert stats.seeds_needed(sd=0.83, effect=0.30) > stats.seeds_needed(sd=0.83, effect=1.0)
    assert stats.seeds_needed(sd=0.0, effect=1.0) == 1


def _task(n_train=2, shape=(3, 3), out=(3, 3), colors=(0, 1)):
    grid = lambda h, w, c: [[c[(r + col) % len(c)] for col in range(w)] for r in range(h)]
    pairs = [{"input": grid(*shape, colors), "output": grid(*out, colors)}
             for _ in range(n_train)]
    return {"train": pairs, "test": [{"input": grid(*shape, colors),
                                      "output": grid(*out, colors)}]}


def test_features_are_solver_independent_and_stable():
    f1 = select.features(_task())
    f2 = select.features(_task())
    assert f1 == f2
    assert select.features(_task(out=(5, 5))).shape_change is True
    assert select.features(_task()).shape_change is False


def test_stratified_is_reproducible_and_exact_size():
    pool = {f"t{i:03d}": _task(n_train=1 + i % 4, out=(3, 3) if i % 2 else (5, 5))
            for i in range(60)}
    a = select.stratified(pool, size=17, seed=7, name="x", source="mem")
    b = select.stratified(pool, size=17, seed=7, name="x", source="mem")
    assert a.task_ids == b.task_ids
    assert len(a.task_ids) == 17
    assert select.stratified(pool, size=17, seed=8, name="x", source="mem").task_ids != a.task_ids


def test_identity_floor_is_not_zero_on_identity_tasks():
    t = _task()
    assert tasks.score_task(t, tasks.identity_solver) == 1.0


def test_constant_solver_declines_when_outputs_differ():
    t = {"train": [{"input": [[0]], "output": [[1]]}, {"input": [[0]], "output": [[2]]}],
         "test": [{"input": [[0]], "output": [[1]]}]}
    assert tasks.constant_solver(t["train"], [[0]]) is None
    assert tasks.score_task(t, tasks.constant_solver) == 0.0


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"ok  {fn.__name__}")
    print(f"\n{len(fns)} passed")
