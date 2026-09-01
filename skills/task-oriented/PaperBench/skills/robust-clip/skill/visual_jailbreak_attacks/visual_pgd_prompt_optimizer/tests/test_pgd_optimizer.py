from pgd_optimizer import optimize_visual_prompt


def test_pgd_reduces_loss():
    result = optimize_visual_prompt([0.0, 0.0], [1.0, -1.0], steps=8, step_size=0.4)
    assert result["loss_after"] < result["loss_before"]
    assert result["params_before"] != result["params_after"]


def test_linf_projection_is_respected():
    result = optimize_visual_prompt([0.0, 0.0], [10.0, -10.0], steps=4, step_size=1.0, epsilon=0.5)
    assert result["constraint"]["within_linf"] is True
    assert max(abs(value) for value in result["params_after"]) <= 0.5 + 1e-9


def test_zero_epsilon_prevents_parameter_change():
    result = optimize_visual_prompt([0.2, -0.2], [10.0, -10.0], steps=3, step_size=10.0, epsilon=0.0)
    assert result["constraint"]["within_linf"] is True
    assert result["params_before"] == result["params_after"]
    assert result["loss_before"] == result["loss_after"]
