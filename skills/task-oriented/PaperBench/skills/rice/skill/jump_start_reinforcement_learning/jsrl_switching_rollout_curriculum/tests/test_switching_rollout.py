from switching_rollout import ChainEnv, left_policy, maybe_advance_curriculum, right_policy, rollout_switching, select_guide_steps


def test_handoff_controller_counts():
    report = rollout_switching(ChainEnv(), right_policy, left_policy, horizon=6, guide_steps=3)
    assert report["summary"]["guide_action_count"] == 3
    assert report["summary"]["exploration_action_count"] == 3
    assert [row["controller"] for row in report["trajectory"]][:4] == ["guide", "guide", "guide", "exploration"]


def test_curriculum_advances_only_after_threshold():
    schedule = [6, 4, 2, 0]
    assert maybe_advance_curriculum(schedule, 0, evaluation=0.4, beta=0.5) == 0
    assert maybe_advance_curriculum(schedule, 0, evaluation=0.5, beta=0.5) == 1


def test_random_strategy_selects_from_schedule():
    schedule = [6, 4, 2, 0]
    assert select_guide_steps(schedule, strategy="random", seed=3) in schedule
