from robustification import evaluate_trajectory, replay_actions


GOAL_PATH = list("RURRRRRD")


def test_replay_reaches_goal_for_known_path():
    result = replay_actions(GOAL_PATH)
    assert result["goal_reached"] is True
    assert result["score"] == 1


def test_evaluation_reports_numeric_success_rate():
    result = evaluate_trajectory(GOAL_PATH, perturbation_checks=True)
    assert 0.0 <= result["success_rate"] <= 1.0
    assert result["mechanism_checks"]["deterministic_replay_executed"] is True
    assert result["mechanism_checks"]["reduced_robustification_proxy"] is True
