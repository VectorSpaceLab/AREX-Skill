import math

from ranking_nce import (
    build_section_4_3_protocol,
    candidate_posterior,
    optimize_section_4_3,
    ranking_objective,
    section_4_3_score_from_params,
)


def test_candidate_posterior_normalizes():
    protocol = build_section_4_3_protocol(k_negatives=1)
    score_fn = section_4_3_score_from_params({"log_theta1": 0.0, "log_theta2": math.log(3.0)})
    posterior = candidate_posterior(protocol, score_fn, "x1", ["y1", "y2"])
    assert math.isclose(sum(posterior), 1.0)
    assert posterior[1] > posterior[0]


def test_ranking_objective_and_optimizer_recover_ratio():
    protocol = build_section_4_3_protocol(k_negatives=2)
    score_fn = section_4_3_score_from_params({"log_theta1": 0.0, "log_theta2": math.log(3.0)})
    assert ranking_objective(protocol, score_fn) < 0.0
    result = optimize_section_4_3(k_negatives=2, steps=120, learning_rate=0.25)
    assert result["loss_after"] < result["loss_before"]
    assert abs(result["ratio_x1"] - (1.0 / 3.0)) < 0.05
    assert math.isclose(result["candidate_posterior_sum"], 1.0)


def test_ranking_optimizer_is_stable_for_multiple_k_values():
    for k_negatives in (1, 3):
        result = optimize_section_4_3(k_negatives=k_negatives, steps=160, learning_rate=0.2)
        assert result["loss_after"] < result["loss_before"]
        assert abs(result["ratio_x1"] - (1.0 / 3.0)) < 0.05
