from mmd_recovery import build_recovery_result, squared_mmd


def test_identical_samples_have_zero_mmd():
    samples = [0.0, 1.0, 2.0]
    assert squared_mmd(samples, samples) < 1e-12


def test_shifted_samples_have_positive_mmd():
    assert squared_mmd([0.0, 0.1, 0.2], [2.0, 2.1, 2.2]) > 0.1


def test_recovery_result_preserves_target():
    target = {"dataset": "analytic_gaussian_sbi_proxy", "metric": "squared_mmd", "paper_value": 0.0, "proxy": True}
    result = build_recovery_result("paper", target, [0.0, 0.1], [0.0, 0.1], 0.25, {"score_composition_executed": True}, ["cmd"], ["artifact"])
    assert result["paper_target"] == target
    assert result["metrics"]["passes_threshold"] == 1.0
