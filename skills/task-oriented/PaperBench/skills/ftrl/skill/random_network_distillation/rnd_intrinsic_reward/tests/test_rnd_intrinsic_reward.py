import importlib.util
from pathlib import Path

script = Path(__file__).resolve().parents[1] / "scripts" / "rnd_core.py"
spec = importlib.util.spec_from_file_location("rnd_core", script)
rnd_core = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rnd_core)


def test_rnd_training_reduces_seen_error_and_marks_rare_as_novel():
    frequent = [[0.0, 0.1], [0.1, 0.0], [0.05, 0.05], [0.0, -0.1]]
    rare = [[1.0, 1.1], [0.9, 1.0], [1.1, 0.9]]
    target = [[0.7, -0.2], [0.3, 0.5]]
    predictor = [[-0.4, 0.1], [0.2, -0.3]]
    result = rnd_core.run_probe(frequent, frequent, rare, target, predictor, lr=0.2, steps=80)
    assert result["loss_after"] < result["loss_before"]
    assert result["novelty_margin"] > 0.01
    assert result["params_after"] != result["params_before"]
    assert result["target_unchanged"] is True
