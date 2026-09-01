from evaluate_recovery import evaluate_bundle


def test_missing_random_switch_ablation_blocks_core_acceptance():
    bundle = {
        "guide_policy_validated": True,
        "source_boundary_ok": True,
        "curriculum_guide_steps": [6, 0],
        "jsrl_episodes": [{"success": True}],
        "vanilla_episodes": [{"success": False}],
        "random_switch_episodes": [],
        "jsrl_trajectories": [{"trajectory": [{"controller": "guide"}, {"controller": "exploration"}]}],
        "training_trace": {"params_before": {}, "params_after": {"s5_a1": 1.0}, "optimizer_state_changed": True},
    }
    report = evaluate_bundle(bundle)
    assert report["metrics"]["success_rate_gain"] == 1.0
    assert report["mechanism_checks"]["random_switching_ablation_executed"] is False
    assert report["mechanism_checks"]["all_core_checks_passed"] is False
