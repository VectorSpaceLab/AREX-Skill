from lora_math import lora_forward, merge_weight, matvec, count_trainable

def test_zero_b_preserves_base_output():
    w=[[1.0,2.0],[0.5,-1.0]]; a=[[0.3,-0.2]]; b=[[0.0],[0.0]]; x=[2.0,1.0]
    assert lora_forward(w,a,b,2.0,x)==matvec(w,x)

def test_merged_matches_dynamic_forward():
    w=[[1.0,0.0],[0.0,1.0]]; a=[[1.0,2.0]]; b=[[0.5],[-0.25]]; x=[3.0,-1.0]
    dyn=lora_forward(w,a,b,2.0,x)
    merged=matvec(merge_weight(w,a,b,2.0), x)
    assert max(abs(a-b) for a,b in zip(dyn, merged)) < 1e-12

def test_count_trainable_parameters():
    assert count_trainable(4, 6, 2) == 20
