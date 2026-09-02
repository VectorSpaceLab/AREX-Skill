import importlib.util
from pathlib import Path

script = Path(__file__).resolve().parents[1] / "scripts" / "residual_network.py"
spec = importlib.util.spec_from_file_location("residual_network", script)
residual_network = importlib.util.module_from_spec(spec)
spec.loader.exec_module(residual_network)


def test_parameter_count_matches_residual_formula():
    expected = (2 * 10 + 10) + 3 * (2 * (10 * 10 + 10)) + (10 + 1)
    assert residual_network.estimate_parameter_count(2, 10, 3) == expected
    assert residual_network.estimate_parameter_count(2, 10, 4) == expected + 2 * (10 * 10 + 10)


def test_torch_forward_and_input_gradient_if_available():
    try:
        import torch
    except Exception:
        return
    torch.manual_seed(0)
    model = residual_network.build_torch_model(3, width=4, blocks=2)
    points = torch.rand(5, 3, requires_grad=True)
    values = model(points)
    assert tuple(values.shape) == (5, 1)
    gradient = torch.autograd.grad(values.sum(), points, create_graph=True)[0]
    assert tuple(gradient.shape) == (5, 3)


if __name__ == "__main__":
    test_parameter_count_matches_residual_formula()
    test_torch_forward_and_input_gradient_if_available()
