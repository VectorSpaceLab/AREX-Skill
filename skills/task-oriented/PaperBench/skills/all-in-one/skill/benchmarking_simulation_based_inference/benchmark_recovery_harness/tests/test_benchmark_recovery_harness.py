import tempfile
from pathlib import Path

from run_recovery import write_json, run


def test_recovery_harness_writes_core_artifacts():
    with tempfile.TemporaryDirectory() as tmp:
        attempt = Path(tmp) / "attempt"
        skill_root = Path(__file__).resolve().parents[2]
        (attempt / "environment").mkdir(parents=True)
        (attempt / "recovery" / "logs").mkdir(parents=True)
        write_json(
            attempt / "module_plan.json",
            {
                "schema_version": 1,
                "paper_id": "benchmarking_simulation_based_inference",
                "title": "Benchmarking Simulation-Based Inference",
                "fast_recovery_target": {
                    "dataset": "gaussian_linear_proxy",
                    "split": "test",
                    "metric": "c2st_accuracy",
                    "paper_value": 0.5,
                    "proxy": True,
                    "rationale": "test proxy"
                },
                "modules": []
            },
        )
        write_json(
            attempt / "environment" / "runtime_handoff.json",
            {"schema_version": 1, "runtime_ready": False, "blockers": ["test blocker"]},
        )
        result = run(
            attempt_dir=attempt,
            skill_root=skill_root,
            num_simulations=12,
            sample_count=12,
            learning_rate=0.04,
            steps=20,
            seed=3,
        )
        assert result["mechanism_checks"]["reduced_training_executed"] is True
        assert "c2st_distance_to_ideal" in result["metrics"]
        assert (attempt / "recovery" / "recovery_result.json").exists()
        assert (attempt / "recovery" / "logs" / "training_trace.json").exists()
        assert (attempt / "recovery" / "logs" / "generated_skill_invocations.json").exists()
