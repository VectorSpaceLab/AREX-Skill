import tempfile
from pathlib import Path

from run_proxy_recovery import run_experiment


def test_proxy_experiment_reduces_loss_and_updates_param():
    repo_root = Path(__file__).resolve().parents[2]
    skills_root = repo_root
    with tempfile.TemporaryDirectory() as d:
        result = run_experiment(Path(d), skills_root, epochs=4, seed=5, variant="layerwise", lr=0.8)
    assert result["loss_reduction_fraction"] > 0.0
    assert result["params_before"] != result["params_after"]
    checks = result["mechanism_checks"]
    assert checks["random_mapping_executed"] is True
    assert checks["combined_objective_executed"] is True
    assert checks["optimizer_step_executed"] is True


def test_concatenated_variant_runs():
    skills_root = Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory() as d:
        result = run_experiment(Path(d), skills_root, epochs=3, seed=9, variant="concatenated", lr=0.5)
    assert result["mechanism_checks"]["rail_loss_variant"] == "concatenated"
    assert result["final_loss"] >= 0.0
