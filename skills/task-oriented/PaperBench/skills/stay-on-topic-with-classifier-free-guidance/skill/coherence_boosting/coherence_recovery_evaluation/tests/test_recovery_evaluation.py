from recovery_evaluation import evaluate, source_boundary_ok

def test_metrics_and_checks():
    out=evaluate([0,1],[1,1],[0,1],-1.0,["paper_profile.md"],["/repo/"])
    assert out["metrics"]["boosted_accuracy"] == 1.0
    assert out["metrics"]["accuracy_gain_over_full_context"] == 0.5
    assert out["mechanism_checks"]["selected_alpha_is_negative"]

def test_source_boundary_marker():
    assert not source_boundary_ok(["/tmp/repo/file.py"],["/repo/"])


def test_accuracy_rejects_empty_inputs():
    from recovery_evaluation import accuracy
    try:
        accuracy([],[])
    except ValueError as exc:
        assert "non-empty" in str(exc)
    else:
        raise AssertionError("expected ValueError")
