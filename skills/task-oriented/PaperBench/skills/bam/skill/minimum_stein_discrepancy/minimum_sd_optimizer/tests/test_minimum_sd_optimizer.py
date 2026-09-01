from minimum_sd_optimizer import minimise_scalar_grid, quadratic_loss


def test_grid_optimizer_moves_toward_quadratic_target():
    result = minimise_scalar_grid(quadratic_loss(1.25), initial_theta=-2.0, lower=-3.0, upper=3.0, grid_size=49)
    assert abs(result["estimated_theta"] - 1.25) < 0.1
    assert result["loss_after"] < result["loss_before"]
    assert result["parameter_changed"] is True


def test_optimizer_records_validator_parameter_fields():
    result = minimise_scalar_grid(quadratic_loss(0.0), initial_theta=1.0, lower=-1.0, upper=1.0, grid_size=11)
    assert "params_before" in result
    assert "params_after" in result
    assert result["params_before"] != result["params_after"]
    assert len(result["trace"]) >= 12
