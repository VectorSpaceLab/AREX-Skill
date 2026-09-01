import importlib.util
import math
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "sil_loss.py"
spec = importlib.util.spec_from_file_location("sil_loss", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def test_positive_advantage_gate():
    result = mod.compute_sil_loss([1.0, 0.2], [0.4, 0.5], [0.25, 0.8], beta=0.5)
    assert result["valid_mask"] == [True, False]
    assert result["positive_advantages"] == [0.6, 0.0]
    expected_policy = (-math.log(0.25) * 0.6) / 2.0
    expected_value = (0.5 * 0.6 * 0.6) / 2.0
    assert abs(result["policy_loss"] - expected_policy) < 1e-9
    assert abs(result["value_loss"] - expected_value) < 1e-9
    assert abs(result["total_loss"] - (expected_policy + 0.5 * expected_value)) < 1e-9


if __name__ == "__main__":
    test_positive_advantage_gate()
