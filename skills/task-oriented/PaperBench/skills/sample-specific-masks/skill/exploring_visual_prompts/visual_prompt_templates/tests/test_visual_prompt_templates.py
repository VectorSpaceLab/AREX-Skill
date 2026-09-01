
from visual_prompt_templates import apply_padding_prompt

def test_padding_changes_only_border():
    image=[[[1.0 for _ in range(4)] for _ in range(4)]]
    prompt=[[[0.5 for _ in range(4)] for _ in range(4)]]
    out, mask=apply_padding_prompt(image,prompt,1)
    assert out[0][0][0] == 1.5
    assert out[0][1][1] == 1.0
    assert mask[0][1][1] == 0.0
    assert mask[0][3][2] == 1.0


def test_invalid_padding_rejected():
    from visual_prompt_templates import apply_padding_prompt
    image=[[[1.0 for _ in range(4)] for _ in range(4)]]
    try:
        apply_padding_prompt(image, image, 2)
    except ValueError:
        return
    raise AssertionError('invalid padding was not rejected')
