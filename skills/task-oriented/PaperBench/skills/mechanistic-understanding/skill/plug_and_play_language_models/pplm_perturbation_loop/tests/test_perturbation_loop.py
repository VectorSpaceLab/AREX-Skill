from perturbation_loop import run_perturbation
import math

def _softmax(logits):
    m=max(logits); e=[math.exp(x-m) for x in logits]; s=sum(e); return [x/s for x in e]

def _objective(logits):
    p=_softmax(logits); mass=p[1]
    grad=[pj for pj in p]
    grad[1] -= 1.0
    return {'loss': -math.log(mass), 'gradient': grad, 'target_mass': mass}

def test_loop_changes_params_and_improves_mass():
    res=run_perturbation([0.0,0.0,0.0], _objective, steps=3, step_size=0.5)
    assert res['optimizer_step_executed']
    assert res['trace'][-1]['target_mass_after'] > res['trace'][0]['target_mass_before']
