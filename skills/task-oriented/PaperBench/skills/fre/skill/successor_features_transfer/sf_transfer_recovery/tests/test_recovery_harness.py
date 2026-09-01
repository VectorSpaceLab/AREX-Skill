import importlib.util
import pathlib
import tempfile
import json

SCRIPT = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "run_sf_transfer_recovery.py"
spec = importlib.util.spec_from_file_location("run_sf_transfer_recovery", SCRIPT)
harness = importlib.util.module_from_spec(spec)
spec.loader.exec_module(harness)


def test_recovery_harness_reports_positive_transfer_advantage():
    with tempfile.TemporaryDirectory() as tmp:
        attempt = pathlib.Path(tmp)
        (attempt / "module_plan.json").write_text(json.dumps({"fast_recovery_target": {"metric": "mean_transfer_advantage", "paper_value": 0.0}}))
        skills_root = pathlib.Path(__file__).resolve().parents[2]
        result, data_item, trace = harness.run_experiment(attempt, skills_root)
        assert result["metrics"]["mean_transfer_advantage"] > 0.0
        assert result["mechanism_checks"]["successor_features_computed"]
        assert result["mechanism_checks"]["successor_feature_bellman_residual_ok"]
        assert result["mechanism_checks"]["gpi_policy_selected_from_multiple_sources"]
        assert data_item["transfer_weights"]
        assert trace["source_policies"]


if __name__ == "__main__":
    test_recovery_harness_reports_positive_transfer_advantage()
