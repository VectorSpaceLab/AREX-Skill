from recovery_harness import authoritative_target, build_source_manifest, invocation, reduced_recovery_allowed


def test_authoritative_target_copies_module_plan_target():
    plan = {"fast_recovery_target": {"dataset": "proxy", "metric": "accuracy", "paper_value": 0.868}}
    target = authoritative_target(plan)
    assert target["metric"] == "accuracy"
    assert target["paper_value"] == 0.868


def test_reduced_recovery_requires_soft_mode_and_blocker():
    manifest = {"recovery_mode": "soft"}
    handoff = {"reduced_recovery_recommended": True, "blockers": ["torch missing"]}
    assert reduced_recovery_allowed(manifest, handoff) is True
    assert reduced_recovery_allowed({"recovery_mode": "hard"}, handoff) is False
    assert reduced_recovery_allowed(manifest, {"reduced_recovery_recommended": True, "blockers": []}) is False


def test_source_manifest_excludes_original_repo_and_invocation_has_artifact():
    manifest = build_source_manifest("attempt", "skills", "paper_text.txt", "environment/runtime_handoff.json")
    assert manifest["forbidden_sources_detected"] == []
    assert manifest["original_repo_used"] is False
    entry = invocation("module", "skill", "called script", "recovery/logs/file.json")
    assert entry["artifact"].endswith(".json")
