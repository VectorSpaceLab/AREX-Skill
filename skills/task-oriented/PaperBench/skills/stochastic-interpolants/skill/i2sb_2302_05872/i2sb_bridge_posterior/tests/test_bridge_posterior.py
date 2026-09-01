import importlib.util
import os

SCRIPT = os.path.join(os.path.dirname(__file__), "..", "scripts", "bridge_posterior.py")
spec = importlib.util.spec_from_file_location("bridge_posterior", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def approx(a, b, tol=1e-9):
    return abs(a - b) <= tol


def test_midpoint_mean_and_variance():
    stats = mod.posterior_stats([0.0], [2.0], 0.5, beta=1.0)
    assert approx(stats["mean"][0], 1.0)
    assert approx(stats["variance"], 0.25)


def test_endpoints_collapse():
    start = mod.posterior_stats([4.0], [9.0], 0.0)
    end = mod.posterior_stats([4.0], [9.0], 1.0)
    assert start["mean"] == [4.0]
    assert end["mean"] == [9.0]
    assert start["variance"] == 0.0
    assert end["variance"] == 0.0


def test_seeded_sampling_reproducible():
    first = mod.sample_xt([0.0, 1.0], [2.0, 3.0], 0.25, seed=7)["sample"]
    second = mod.sample_xt([0.0, 1.0], [2.0, 3.0], 0.25, seed=7)["sample"]
    assert first == second


def test_shape_mismatch_rejected():
    try:
        mod.posterior_stats([0.0], [1.0, 2.0], 0.5)
    except ValueError as exc:
        assert "same length" in str(exc)
    else:
        raise AssertionError("expected ValueError")


if __name__ == "__main__":
    test_midpoint_mean_and_variance()
    test_endpoints_collapse()
    test_seeded_sampling_reproducible()
    test_shape_mismatch_rejected()
