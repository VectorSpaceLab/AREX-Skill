from protocol_checks import mechanism_checks_complete, source_manifest_has_no_original_repo


def test_source_manifest_rejects_original_repo():
    assert source_manifest_has_no_original_repo({"sources": [{"kind": "paper", "path": "paper.pdf"}]}) is True
    assert source_manifest_has_no_original_repo({"sources": [{"kind": "original_repo", "path": "/tmp/repo"}]}) is False


def test_mechanism_checks_require_core_booleans():
    checks = {
        "score_only_model_used": True,
        "stein_kernel_u_statistic_executed": True,
        "diffusion_factor_validated": True,
        "minimum_discrepancy_optimized": True,
        "reduced_training_executed": True,
        "optimizer_step_executed": True,
    }
    assert mechanism_checks_complete(checks) is True
    checks["optimizer_step_executed"] = False
    assert mechanism_checks_complete(checks) is False
