from evaluate_bar_recovery import build_recovery_result


def test_proxy_result_contains_commands_and_artifacts_for_boundary_audit():
    target = {"dataset":"proxy", "metric":"accuracy", "paper_value":0.7, "proxy":True}
    trace = {"params_before":[0], "params_after":[1], "loss_before":0.2, "loss_after":0.1, "query_count":2}
    result = build_recovery_result("pid", target, [0, 1], [0, 1], trace, "python run.py", ["recovery/logs/training_trace.json"])
    assert result["commands"] == ["python run.py"]
    assert result["artifacts"]
    assert result["is_proxy"] is True
