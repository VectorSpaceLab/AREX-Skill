import tempfile
from pathlib import Path

from reduced_benchmark import run_reduced_benchmark


def test_reduced_benchmark_decreases_loss_and_writes_logs():
    contract = {"valid": True, "posterior_name": "demo", "reference_posterior_name": "ref", "linked_paths": {"posterior": "posterior.json"}}
    summary = {"valid": True, "values": {"a": 1.0, "b": -1.0}}
    target = {"dataset": "demo", "metric": "mean_rmse_reduction", "paper_value": 0.0, "proxy": True}
    with tempfile.TemporaryDirectory() as tmp:
        result = run_reduced_benchmark(contract, summary, target, "python run.py", tmp)
        assert result["metrics"]["mean_rmse_reduction"] > 0
        assert result["mechanism_checks"]["optimizer_step_executed"] is True
        assert (Path(tmp) / "training_trace.json").exists()
        assert (Path(tmp) / "generated_data_item.json").exists()
