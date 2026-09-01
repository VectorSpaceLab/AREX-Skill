from pathlib import Path

from proxy_step import run_proxy


def test_proxy_step_changes_params_and_checks_mechanisms():
    skills_root = str(Path(__file__).resolve().parents[2])
    result = run_proxy(skills_root)
    checks = result["mechanism_checks"]
    assert checks["proxy_declared"] is True
    assert checks["x0_reconstruction_executed"] is True
    assert checks["image_pairwise_kl_executed"] is True
    assert checks["high_frequency_mse_executed"] is True
    assert checks["optimizer_step_executed"] is True
    assert checks["finite_losses"] is True
    assert result["trace"]["params_before"] != result["trace"]["params_after"]


def test_ablation_weights_change_loss_components():
    skills_root = str(Path(__file__).resolve().parents[2])
    baseline = run_proxy(skills_root, lambda2=0.5, lambda3=0.5, lambda4=0.04)
    ablated = run_proxy(skills_root, lambda2=0.0, lambda3=0.0, lambda4=0.0)
    assert baseline["trace"]["loss_before"] != ablated["trace"]["loss_before"]
