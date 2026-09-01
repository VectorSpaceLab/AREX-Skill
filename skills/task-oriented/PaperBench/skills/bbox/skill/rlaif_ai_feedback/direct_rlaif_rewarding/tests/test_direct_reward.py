from direct_reward import HeuristicDirectScorer, score_direct_reward, stable_softmax


class UniformScorer:
    def logits(self, context, response):
        return {str(score): 0.0 for score in range(1, 11)}


class HighScorer:
    def logits(self, context, response):
        return {str(score): float(score) for score in range(1, 11)}


class MissingScoreScorer:
    def logits(self, context, response):
        return {str(score): 0.0 for score in range(1, 10)}


def test_uniform_scores_map_to_zero_reward():
    result = score_direct_reward("summarization", "context", "response", UniformScorer())
    assert abs(result["expected_score"] - 5.5) < 1e-9
    assert abs(result["normalized_reward"]) < 1e-9


def test_high_score_distribution_has_positive_reward():
    result = score_direct_reward("summarization", "context", "response", HighScorer())
    assert result["expected_score"] > 8.0
    assert result["normalized_reward"] > 0.0
    assert result["normalized_reward"] <= 1.0


def test_heuristic_rewards_better_overlap_more():
    context = "alpha beta gamma delta epsilon"
    good = score_direct_reward("summarization", context, "alpha beta gamma delta", HeuristicDirectScorer())
    weak = score_direct_reward("summarization", context, "unrelated", HeuristicDirectScorer())
    assert good["normalized_reward"] > weak["normalized_reward"]


def test_softmax_normalizes():
    probs = stable_softmax([0.0] * 10)
    assert len(probs) == 10
    assert abs(sum(probs) - 1.0) < 1e-9


def test_missing_score_token_logits_raise_clear_error():
    try:
        score_direct_reward("summarization", "context", "response", MissingScoreScorer())
    except ValueError as exc:
        assert "missing score-token logits" in str(exc)
        assert "10" in str(exc)
    else:
        raise AssertionError("missing score-token logits should raise ValueError")
