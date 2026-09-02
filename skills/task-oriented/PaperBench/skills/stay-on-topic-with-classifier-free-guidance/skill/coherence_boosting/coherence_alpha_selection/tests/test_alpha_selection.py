from alpha_selection import select_alpha

def test_selects_negative_alpha_on_fixture():
    examples=[{"full_logprobs":[-1.0,-0.9],"short_logprobs":[-5.0,-0.1],"label":0}]
    result=select_alpha(examples,[0.0,-0.5,-1.0])
    assert result["best_alpha"] < 0
    assert result["best_accuracy"] == 1.0


def test_tie_prefers_smaller_absolute_alpha():
    examples=[{"full_logprobs":[-1.0,-2.0],"short_logprobs":[-1.0,-2.0],"label":0}]
    result=select_alpha(examples,[-1.0,-0.25,0.0])
    assert result["best_alpha"] == 0.0
