import importlib.util
import pathlib

MODULE = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "score_loss.py"
spec = importlib.util.spec_from_file_location("score_loss", MODULE)
score_loss = importlib.util.module_from_spec(spec)
spec.loader.exec_module(score_loss)


def test_optimizer_step_reduces_dsm_loss():
    data = [-1.0, -0.5, 0.5, 1.0]
    noise = [0.2, -0.1, 0.1, -0.2]
    result = score_loss.optimizer_step(data, 0.4, noise, {"weight": 0.0, "time_weight": 0.0, "bias": 0.0}, 0.05)
    assert result["optimizer_step_executed"] is True
    assert result["loss_after"] < result["loss_before"]
    assert result["params_before"] != result["params_after"]
    assert len(result["perturbation_before"]["target_score"]) == len(data)
