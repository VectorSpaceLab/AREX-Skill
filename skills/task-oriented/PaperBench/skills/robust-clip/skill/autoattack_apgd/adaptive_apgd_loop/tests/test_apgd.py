import sys, pathlib
base=pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(base/'threat_model_projection'/'scripts'))
sys.path.insert(0, str(base/'dlr_margin_loss'/'scripts'))
from apgd import run_apgd

def logits(x):
    return [x[0]-0.35, 0.35-x[0], 0.1*x[1]]

def test_apgd_succeeds_and_adapts():
    result=run_apgd(logits, [[0.55,0.5]], [0], eps=0.35, iterations=12, step_size=0.2, window=3)
    assert result['successes'][0] is True
    assert result['step_events']
    assert max(abs(a-b) for a,b in zip(result['adversarial_examples'][0],[0.55,0.5])) <= 0.35 + 1e-9
