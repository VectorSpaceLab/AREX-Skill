from classify_dataset import classify_dataset


def test_medium_expert_is_mixed_quality():
    report = classify_dataset({"name": "hopper-medium-expert-v2", "domain": "mujoco"})
    assert "mixed_quality" in report["tags"]


def test_antmaze_diverse_tags_sparse_multitask_undirected():
    report = classify_dataset({"name": "antmaze-large-diverse-v0", "reward_type": "sparse"})
    assert "sparse_reward" in report["tags"]
    assert "undirected_data" in report["tags"]
    assert "multitask" in report["tags"]


def test_empty_metadata_warns():
    report = classify_dataset({})
    assert report["warnings"]
