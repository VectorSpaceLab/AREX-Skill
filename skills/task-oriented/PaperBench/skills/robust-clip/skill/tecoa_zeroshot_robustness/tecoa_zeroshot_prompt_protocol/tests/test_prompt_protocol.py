from prompt_protocol import build_prompts


def test_build_prompts_preserves_order_and_normalizes():
    payload = build_prompts(["tabby_cat", "  fire   truck  "], "a photo of a {}")
    assert payload["prompts"] == ["a photo of a tabby cat", "a photo of a fire truck"]
    assert [row["index"] for row in payload["mapping"]] == [0, 1]
    assert payload["metadata"]["count"] == 2


def test_rejects_bad_template_and_empty_labels():
    for labels, template in [([], "a photo of a {}"), (["cat"], "no field"), (["cat"], "{} {}")]:
        try:
            build_prompts(labels, template)
        except ValueError:
            pass
        else:
            raise AssertionError("invalid prompt inputs should fail")


def test_output_has_no_downstream_control_markers():
    payload = build_prompts(["hummingbird"])
    joined = "\n".join(payload["prompts"])
    assert "Final Answer:" not in joined
    assert "prediction" not in payload
