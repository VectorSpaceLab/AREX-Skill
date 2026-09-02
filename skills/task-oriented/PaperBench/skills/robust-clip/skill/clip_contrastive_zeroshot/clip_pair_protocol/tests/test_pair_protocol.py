from pair_protocol import render_prompts, validate_pairs


def test_render_prompts_and_validate_pairs():
    prompts = render_prompts(["cat"], ["a photo of a {}"])
    assert prompts["cat"] == ["a photo of a cat"]
    pairs = validate_pairs([{"id":"x","class_name":"cat","image_embedding":[1,0],"text_embedding":[1,0]}])
    assert pairs[0]["embedding_dim"] == 2


def test_reject_bad_template():
    try:
        render_prompts(["cat"], ["bad template"])
    except ValueError as exc:
        assert "placeholder" in str(exc)
    else:
        raise AssertionError("bad template accepted")
