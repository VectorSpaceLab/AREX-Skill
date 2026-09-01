import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
from latent_perturbation import perturb_logits, softmax

def test_perturbation_increases_target_and_freezes_base():
    base=[0.0,0.0,0.0]
    final,trace=perturb_logits(base,[2],steps=6,step_size=1.0)
    assert final[2] > softmax(base)[2]
    assert trace['base_logits_after']==base
    assert trace['params_before'] != trace['params_after']
