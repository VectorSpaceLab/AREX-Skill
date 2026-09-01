from guide_policy_contract import rollout_progress


def test_invalid_guide_action_is_rejected():
    def invalid_policy(state):
        return 99

    report = rollout_progress(invalid_policy)
    assert report["valid_actions"] is False
    assert report["useful"] is False
    assert "invalid action" in report["error"]
