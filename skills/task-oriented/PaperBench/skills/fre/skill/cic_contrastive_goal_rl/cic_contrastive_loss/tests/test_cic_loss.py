from cic_loss import evaluate_cic_loss, finite_difference_update, identity_weights


def _fixtures():
    tau = [[1, 0, 1.2, 0.1], [0, 1, 0.2, 1.1], [1, 1, 1.3, 1.2]]
    skills = [[1, 0], [0, 1], [1, 1]]
    query_w = identity_weights(2, 2)
    key_w = [[1, 0], [0, 1], [1, 0], [0, 1]]
    return tau, skills, query_w, key_w


def test_loss_outputs_are_finite():
    tau, skills, query_w, key_w = _fixtures()
    result = evaluate_cic_loss(tau, skills, query_w, key_w, temperature=0.5)
    assert result["loss"] > 0
    assert len(result["logits"]) == 3
    assert isinstance(result["positive_logit_margin"], float)


def test_rejects_nonpositive_temperature():
    tau, skills, query_w, key_w = _fixtures()
    try:
        evaluate_cic_loss(tau, skills, query_w, key_w, temperature=0)
    except ValueError as exc:
        assert "temperature" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_update_changes_params_and_does_not_increase_loss():
    tau, skills, query_w, key_w = _fixtures()
    trace = finite_difference_update(tau, skills, query_w, key_w, learning_rate=0.05)
    assert trace["params_before"] != trace["params_after"]
    assert trace["loss_after"] <= trace["loss_before"] + 1e-6
