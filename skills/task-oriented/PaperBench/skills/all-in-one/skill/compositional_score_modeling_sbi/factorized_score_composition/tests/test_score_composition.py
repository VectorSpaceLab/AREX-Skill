from score_composition import compose_f_npse_score, compose_pf_npse_score, prior_coefficient


def close_vec(a, b, tol=1e-9):
    return all(abs(x - y) <= tol for x, y in zip(a, b))


def test_f_npse_equation_matches_manual_sum():
    theta = [0.25, -0.5]
    observations = [[1.0, 0.0], [0.5, -1.0], [-0.2, 0.3]]

    def score_fn(th, t, obs):
        return [obs_i - th_i for th_i, obs_i in zip(th, obs)]

    score, meta = compose_f_npse_score(theta, 2, 5, observations, score_fn)
    coeff = ((1 - 3) * (5 - 2)) / 5
    manual = [coeff * (-theta[i]) + sum(obs[i] - theta[i] for obs in observations) for i in range(2)]
    assert close_vec(score, manual)
    assert meta["prior_coefficient"] == coeff


def test_single_observation_prior_correction_is_zero():
    assert prior_coefficient(1, 3, 10) == 0.0


def test_pf_npse_group_order_invariance_for_additive_group_scores():
    theta = [0.1, -0.1]
    observations = [[1.0, 0.0], [0.0, 1.0], [0.2, -0.4], [-0.3, 0.5]]

    def group_score(th, t, group):
        return [sum(row[i] for row in group) - len(group) * th[i] for i in range(2)]

    score_a, meta_a = compose_pf_npse_score(theta, 1, 4, observations, 2, group_score)
    score_b, meta_b = compose_pf_npse_score(theta, 1, 4, [observations[2], observations[3], observations[0], observations[1]], 2, group_score)
    assert close_vec(score_a, score_b)
    assert meta_a["group_count"] == meta_b["group_count"] == 2
