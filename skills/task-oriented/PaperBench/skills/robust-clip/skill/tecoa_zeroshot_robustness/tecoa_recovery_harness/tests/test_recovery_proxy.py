from pathlib import Path
from recovery_proxy import run_proxy_experiment


def test_proxy_experiment_runs_and_changes_parameters():
    skills_root = Path(__file__).resolve().parents[2]
    result = run_proxy_experiment(skills_root, steps=3, learning_rate=0.2)
    checks = result["mechanism_checks"]
    assert checks["prompt_protocol_invoked"]
    assert checks["contrastive_objective_invoked"]
    assert checks["adversarial_attack_invoked"]
    assert checks["optimizer_step_executed"]
    assert result["trace"]["params_before"] != result["trace"]["params_after"]
    assert result["metrics"]["loss_after"] < result["metrics"]["loss_before"]
    assert result["metrics"]["tecoa_proxy_success_rate"] >= 0.8


def test_proxy_records_positive_loss_and_margin_improvement():
    skills_root = Path(__file__).resolve().parents[2]
    result = run_proxy_experiment(skills_root, steps=1, learning_rate=0.2)
    assert result["metrics"]["loss_before"] - result["metrics"]["loss_after"] > 0
    assert result["metrics"]["mean_margin_after"] > result["metrics"]["mean_margin_before"]
