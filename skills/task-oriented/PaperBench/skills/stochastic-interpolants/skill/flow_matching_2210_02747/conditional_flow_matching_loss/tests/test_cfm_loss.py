import importlib.util
from pathlib import Path

script = Path(__file__).resolve().parents[1] / "scripts" / "cfm_loss.py"
spec = importlib.util.spec_from_file_location("cfm_loss", script)
cfm_loss = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cfm_loss)


def test_zero_and_weighted_loss():
    targets = [[1.0, 2.0], [0.0, -1.0]]
    assert cfm_loss.mean_loss(targets, targets)["loss"] == 0.0
    result = cfm_loss.mean_loss([[0.0, 0.0], [0.0, 0.0]], targets, [2.0, 1.0])
    assert abs(result["loss"] - (11.0 / 3.0)) < 1e-12
    assert result["sample_count"] == 2


def test_one_parameter_update_decreases_loss_and_validates_inputs():
    update = cfm_loss.one_parameter_update([[1.0, 2.0], [3.0, 4.0]], 0.0, 0.05)
    assert update["updated"] is True
    assert update["loss_after"] < update["loss_before"]
    try:
        cfm_loss.mean_loss([[1.0]], [[1.0, 2.0]])
    except ValueError as exc:
        assert "dimensions" in str(exc)
    else:
        raise AssertionError("dimension mismatch should fail")


if __name__ == "__main__":
    test_zero_and_weighted_loss()
    test_one_parameter_update_decreases_loss_and_validates_inputs()
