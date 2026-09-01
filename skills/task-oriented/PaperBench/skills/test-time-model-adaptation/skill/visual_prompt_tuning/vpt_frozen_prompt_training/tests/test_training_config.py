from training_config import build_trainability, verify_frozen_unchanged


def test_only_prompt_and_head_trainable():
    params = [
        {"name": "backbone.block0.attn", "count": 100},
        {"name": "prompt_embeddings", "count": 4},
        {"name": "classifier_head.weight", "count": 6},
    ]
    result = build_trainability(params)
    assert result["optimizer_group_names"] == ["prompt_embeddings", "classifier_head.weight"]
    assert result["summary"]["trainable_parameters"] == 10


def test_ambiguous_parameters_are_frozen():
    result = build_trainability([{"name": "mystery", "count": 5}])
    assert result["parameters"][0]["trainable"] is False


def test_detects_backbone_mutation():
    params = [{"name": "backbone.weight", "before": 1.0, "after": 1.1}]
    result = verify_frozen_unchanged(params)
    assert result["ok"] is False
    assert result["violations"] == ["backbone.weight"]
