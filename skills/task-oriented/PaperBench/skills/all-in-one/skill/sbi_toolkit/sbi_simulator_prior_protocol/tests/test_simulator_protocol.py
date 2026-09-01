from simulator_protocol import deterministic_prior_grid, run_protocol


def test_protocol_filters_failed_records():
    def simulator(theta):
        if theta[0] == 0.0:
            return None
        return theta[0] + 1.0

    result = run_protocol([[-1.0], [0.0], [1.0]], simulator)
    assert result["metadata"]["num_requested"] == 3
    assert result["metadata"]["num_valid"] == 2
    assert result["metadata"]["num_failed"] == 1
    assert all(item["status"] == "ok" for item in result["valid_records"])
    assert result["metadata"]["theta_dim"] == 1
    assert result["metadata"]["x_dim"] == 1


def test_prior_grid_is_deterministic_and_bounded():
    grid = deterministic_prior_grid(5, low=-2.0, high=2.0)
    assert grid == [[-2.0], [-1.0], [0.0], [1.0], [2.0]]
