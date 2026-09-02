from validate_offline_dataset import validate_dataset


def test_valid_dataset_counts_terminals_and_timeouts():
    transitions = [
        {"observation": [0], "action": 0, "reward": 1, "next_observation": [1], "terminal": False, "timeout": False},
        {"observation": [1], "action": 1, "reward": 2, "next_observation": [2], "terminal": True, "timeout": False},
        {"observation": [2], "action": 0, "reward": 0, "next_observation": [3], "terminal": False, "timeout": True},
    ]
    report = validate_dataset(transitions, {"quality_tags": ["synthetic_proxy"]})
    assert report["ok"] is True
    assert report["transition_count"] == 3
    assert report["terminal_count"] == 1
    assert report["timeout_count"] == 1
    assert "fixed_dataset" in report["quality_tags"]


def test_missing_key_is_rejected():
    report = validate_dataset([{"observation": [0]}])
    assert report["ok"] is False
    assert "missing keys" in report["errors"][0]
