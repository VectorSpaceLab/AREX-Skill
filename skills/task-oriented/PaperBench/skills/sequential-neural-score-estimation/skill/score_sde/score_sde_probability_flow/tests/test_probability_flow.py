import importlib.util
import pathlib

MODULE = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "probability_flow.py"
spec = importlib.util.spec_from_file_location("probability_flow", MODULE)
probability_flow = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probability_flow)


def test_probability_flow_zero_diffusion_and_finite_divergence():
    result = probability_flow.probability_flow_step(1.0, 0.5, -1.0, -0.01)
    assert result["zero_diffusion"] is True
    assert result["ode_diffusion"] == 0.0
    assert result["finite"] is True
    assert "log_density_delta" in result
