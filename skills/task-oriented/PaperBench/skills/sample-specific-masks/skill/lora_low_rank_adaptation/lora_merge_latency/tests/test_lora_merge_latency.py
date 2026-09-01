import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))

def test_skill_smoke():
    from merge_lora import merged_weight, forward_merged
    W=[[1,0],[0,1]]; A=[[1,2]]; B=[[0.5],[0.0]]
    assert merged_weight(W,A,B,1.0)==[[1.5,1.0],[0.0,1.0]]
    assert forward_merged(W,A,B,[2,1])==[4.0,1.0]


def test_merge_respects_alpha_over_rank_scaling():
    from merge_lora import merged_weight
    W=[[0.0,0.0],[0.0,0.0]]; A=[[1.0,0.0],[0.0,1.0]]; B=[[2.0,0.0],[0.0,4.0]]
    assert merged_weight(W,A,B,alpha=4.0) == [[4.0,0.0],[0.0,8.0]]
