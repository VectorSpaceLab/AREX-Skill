from zeroshot import render_prompts, classify, accuracy

def test_prompt_render_and_classify():
    prompts=render_prompts(["cat","dog"], ["a photo of a {label}."])
    assert prompts["cat"] == ["a photo of a cat."]
    result=classify([[1,0],[0,1]], ["cat","dog"], {"cat":[[1,0]], "dog":[[0,1]]})
    assert result["predictions"] == ["cat", "dog"]
    assert accuracy(result["predictions"], ["cat","dog"]) == 1.0

def test_template_requires_label_slot():
    try:
        render_prompts(["cat"], ["a photo"])
    except ValueError as exc:
        assert "{label}" in str(exc)
    else:
        raise AssertionError("bad template accepted")


def test_prototypes_are_unit_normalized():
    result=classify([[1,0]], ["cat"], {"cat":[[2,0],[4,0]]})
    proto=result["prototypes"][0]
    assert abs(sum(x*x for x in proto) - 1.0) < 1e-9
