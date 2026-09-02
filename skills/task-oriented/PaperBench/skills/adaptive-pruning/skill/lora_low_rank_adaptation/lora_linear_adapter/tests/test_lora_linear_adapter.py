
from lora_core import LoRALinear, rank_leq

def test_zero_b_and_merge_equivalence():
    m=LoRALinear([[1.0,2.0],[0.0,1.0]], r=1, alpha=2.0)
    x=[3.0,4.0]
    assert m.forward(x)==[11.0,4.0]
    m.B[0][0]=0.5
    assert all(abs(a-b)<1e-9 for a,b in zip(m.forward(x), m.forward(x, merged=True)))
    ok, rank = rank_leq(m.delta(), 1)
    assert ok and rank <= 1
