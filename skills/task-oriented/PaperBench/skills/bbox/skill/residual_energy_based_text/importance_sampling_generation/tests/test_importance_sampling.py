from importance_sampling import importance_weights, logsumexp


def test_lower_energy_gets_higher_weight():
    result = importance_weights(
        [
            {"id": "low", "energy": -2.0, "lm_logprob": -3.0},
            {"id": "high", "energy": 2.0, "lm_logprob": -1.0},
        ]
    )
    by_id = {item["id"]: item for item in result["candidates"]}
    assert by_id["low"]["importance_weight"] > by_id["high"]["importance_weight"]
    assert abs(sum(item["importance_weight"] for item in result["candidates"]) - 1.0) < 1e-12
    assert result["mode"] == "energy_importance_generation"


def test_logsumexp_large_negative_values():
    value = logsumexp([-10000.0, -10001.0])
    assert -10000.0 < value < -9999.0


def test_generation_selection_uses_energy_not_proposal_logprob():
    result = importance_weights(
        [
            {"id": "positive_low_energy", "energy": -2.0, "lm_logprob": -3.0},
            {"id": "negative_high_proposal", "energy": 1.5, "lm_logprob": -0.1},
        ]
    )
    assert result["selected_id"] == "positive_low_energy"


def test_equal_energy_tie_uses_proposal_logprob_not_label_id():
    result = importance_weights(
        [
            {"id": "positive_low_proposal", "energy": 0.0, "lm_logprob": -3.0},
            {"id": "negative_high_proposal", "energy": 0.0, "lm_logprob": -0.1},
        ]
    )
    assert result["selected_id"] == "negative_high_proposal"
