from burgers_residual import QuadraticSurrogate, burgers_residual, mean_squared_residual


def test_burgers_residual_reports_derivatives():
    model = QuadraticSurrogate(bias=0.1, t_weight=0.2, x_weight=-0.3, tx_weight=0.04, xx_weight=0.05)
    result = burgers_residual({"t": 0.5, "x": -0.25}, model, nu=0.01)
    assert set(["u", "u_t", "u_x", "u_xx", "residual"]).issubset(result)
    assert isinstance(result["residual"], float)
    assert result["u_xx"] == 0.1


def test_mean_squared_residual_is_positive():
    model = QuadraticSurrogate()
    loss = mean_squared_residual([{"t": 0.0, "x": -1.0}, {"t": 1.0, "x": 1.0}], model, nu=0.01)
    assert loss >= 0.0
