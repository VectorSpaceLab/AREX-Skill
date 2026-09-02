
from lora_core import LoRALinear, rank_leq

def test_zero_b_and_merge_equivalence():
    m=LoRALinear([[1.0,2.0],[0.0,1.0]], r=1, alpha=2.0)
    x=[3.0,4.0]
    assert m.forward(x)==[11.0,4.0]
    m.B[0][0]=0.5
    assert all(abs(a-b)<1e-9 for a,b in zip(m.forward(x), m.forward(x, merged=True)))
    ok, rank = rank_leq(m.delta(), 1)
    assert ok and rank <= 1

from lora_core import lora_parameter_count, validate_trace

def test_efficiency_and_trace_validation():
    assert lora_parameter_count(768, 8, 24) == 294912
    assert validate_trace({'loss_before':2.0,'loss_after':1.0,'params_before':{'a':0},'params_after':{'a':1}},0.4)['passes']
