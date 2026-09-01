from prompt_ops import prepend_prompts, replace_deep_prompts


def test_prepend_preserves_cls_and_images():
    tokens = [[[1, 1], [2, 2], [3, 3]]]
    prompts = [[9, 9], [8, 8]]
    result = prepend_prompts(tokens, prompts)
    assert result["tokens"] == [[[1, 1], [9, 9], [8, 8], [2, 2], [3, 3]]]
    assert result["metadata"]["prompt_count"] == 2


def test_deep_replaces_prompt_slots_only():
    prompted = [[[1], [9], [8], [2], [3]]]
    layers = [[[7], [6]], [[5], [4]]]
    result = replace_deep_prompts(prompted, layers, 1)
    assert result["tokens"] == [[[1], [5], [4], [2], [3]]]


def test_rejects_unsupported_location():
    try:
        prepend_prompts([[[1], [2]]], [[3]], location="pad")
    except ValueError as exc:
        assert "prepend" in str(exc)
    else:
        raise AssertionError("expected ValueError")
