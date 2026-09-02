import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "scalar_sil_train.py"
spec = importlib.util.spec_from_file_location("scalar_sil_train", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def test_scalar_sil_update_improves_high_return_action():
    records = [{"state": "s2", "action": 1, "return": 1.0}]
    trace = mod.train_scalar_sil(records, learning_rate=0.2, updates=20, beta=0.1)
    assert trace["optimizer_step_executed"] is True
    assert trace["loss_after"] < trace["loss_before"]
    before_prob = trace["details_before"][0]["probability"]
    after_prob = trace["details_after"][0]["probability"]
    assert after_prob > before_prob
    assert "params_before" in trace and "params_after" in trace


if __name__ == "__main__":
    test_scalar_sil_update_improves_high_return_action()
