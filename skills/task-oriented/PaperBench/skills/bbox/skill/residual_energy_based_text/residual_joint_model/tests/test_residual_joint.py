from residual_joint import logsumexp, score_candidates


def test_joint_score_and_selection():
    result = score_candidates(
        [
            {"id": "a", "lm_logprob": -2.0, "energy": -1.0},
            {"id": "b", "lm_logprob": -1.0, "energy": 1.0},
        ]
    )
    by_id = {item["id"]: item for item in result["candidates"]}
    assert by_id["a"]["joint_logscore"] == -1.0
    assert by_id["b"]["joint_logscore"] == -2.0
    assert result["selected_id"] == "a"
    assert abs(sum(item["importance_weight"] for item in result["candidates"]) - 1.0) < 1e-12


def test_logsumexp_is_stable():
    value = logsumexp([-1000.0, -1001.0])
    assert -1000.0 < value < -999.0

