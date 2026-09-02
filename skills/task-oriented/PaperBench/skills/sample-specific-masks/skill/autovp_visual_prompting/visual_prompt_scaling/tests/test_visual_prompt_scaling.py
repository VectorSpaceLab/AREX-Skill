from visual_prompt_scaling import prompt_width, frame_mask, apply_prompt

def test_width_mask_and_center():
    assert prompt_width(6,2)==2
    m=frame_mask(6,2,1)[0]
    assert sum(sum(row) for row in m)==32
    out=apply_prompt([[3,4],[5,6]],6,0.0)
    assert out[2][2]==3 and out[3][3]==6
    assert abs(out[0][0]-0.5)<1e-9


def test_odd_padding_floor_is_documented():
    assert prompt_width(7,2)==2
    out=apply_prompt([[1,2],[3,4]],7,0.0)
    assert out[2][2]==1 and out[3][3]==4
