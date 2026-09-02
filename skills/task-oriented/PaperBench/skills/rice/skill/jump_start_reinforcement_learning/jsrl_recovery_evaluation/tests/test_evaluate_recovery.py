from evaluate_recovery import evaluate_bundle


def test_evaluate_bundle_reports_gain_and_mechanisms():
    bundle = {
        "guide_policy_validated": True,
        "source_boundary_ok": True,
        "curriculum_guide_steps": [6, 3, 0],
        "jsrl_episodes": [{"success": True}, {"success": True}],
        "vanilla_episodes": [{"success": False}, {"success": True}],
        "random_switch_episodes": [{"success": True}],
        "jsrl_trajectories": [{"trajectory": [{"controller": "guide"}, {"controller": "exploration"}]}],
        "training_trace": {"params_before": {}, "params_after": {"s5_a1": 0.5}, "optimizer_state_changed": True},
    }
    report = evaluate_bundle(bundle)
    assert report["metrics"]["success_rate_gain"] == 0.5
    assert report["mechanism_checks"]["all_core_checks_passed"] is True


def test_missing_handoff_fails_core_checks():
    report = evaluate_bundle({"guide_policy_validated": True, "training_trace": {"params_before": {}, "params_after": {"x": 1}}})
    assert report["mechanism_checks"]["all_core_checks_passed"] is False
