import math

from mixture_protocol import build_protocol, log_likelihood, log_posterior


def test_protocol_is_deterministic_and_normalized():
    first = build_protocol(seed=7, n_observations=12, grid_size=11)
    second = build_protocol(seed=7, n_observations=12, grid_size=11)
    assert first["observations"] == second["observations"]
    density = first["grid"]["density"]
    mass = sum(sum(row) for row in density) * first["grid"]["cell_area"]
    assert abs(mass - 1.0) < 1e-6


def test_symmetric_modes_are_finite():
    protocol = build_protocol(seed=3, n_observations=20, grid_size=9)
    observations = protocol["observations"]
    for mode in protocol["expected_modes"]:
        assert math.isfinite(log_posterior(mode, observations))
        assert math.isfinite(log_likelihood(mode, observations[0]))
