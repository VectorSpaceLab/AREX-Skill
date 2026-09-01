import importlib.util
from pathlib import Path

script = Path(__file__).resolve().parents[1] / "scripts" / "energy_loss.py"
spec = importlib.util.spec_from_file_location("energy_loss", script)
energy_loss = importlib.util.module_from_spec(spec)
spec.loader.exec_module(energy_loss)


def test_exact_solution_and_relative_l2():
    point = [1.0] * 10
    assert energy_loss.poisson_10d_exact_python(point) == 5.0
    assert energy_loss.relative_l2_python([1.0, 2.0], [1.0, 2.0]) == 0.0
    assert energy_loss.relative_l2_python([0.0, 0.0], [1.0, 1.0]) > 0.0


def test_torch_loss_if_available():
    try:
        import torch
    except Exception:
        return

    class LinearTrial(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.layer = torch.nn.Linear(2, 1)

        def forward(self, values):
            return self.layer(values)

    torch.manual_seed(0)
    model = LinearTrial()
    interior = torch.rand(4, 2)
    boundary = torch.zeros(4, 2)
    loss, diagnostics = energy_loss.poisson_energy_loss_torch(model, interior, boundary, beta=10.0)
    assert loss.requires_grad
    assert diagnostics["boundary_penalty"] >= 0.0


if __name__ == "__main__":
    test_exact_solution_and_relative_l2()
    test_torch_loss_if_available()
