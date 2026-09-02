import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))

def test_skill_smoke():
    from budget import budget_report, lora_params
    assert lora_params(768,8,24)==2*24*768*8
    assert budget_report(4,1,2)['reduction_vs_dense']==2.0


def test_transformer_scale_reduction_is_large():
    from budget import budget_report
    r=budget_report(768,8,24)
    assert r['lora_trainable_params'] == 294912
    assert r['reduction_vs_dense'] == 48.0
