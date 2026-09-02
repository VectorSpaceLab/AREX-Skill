from visual_prompt import apply_prompt, run_frozen_linear_batch

def test_prompt_changes_logits_without_changing_source():
    weights=[[1,0],[0,1]]; bias=[0,0]
    out0=run_frozen_linear_batch([[1,0]],[0,0],weights,bias)
    out1=run_frozen_linear_batch([[1,0]],[0,2],weights,bias)
    assert out0['logits'] != out1['logits']
    assert out1['frozen_source_unchanged']

def test_mask_blocks_prompt_position():
    assert apply_prompt([1,1],[5,5],[1,0]) == [6,1]

def test_shape_mismatch_rejected():
    try:
        apply_prompt([1,2], [1])
    except ValueError:
        return
    assert False, 'expected ValueError for mismatched prompt shape'
