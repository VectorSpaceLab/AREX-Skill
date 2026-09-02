
from prompt_training_loop import train_scalar_prompt

def test_prompt_training_reduces_loss_and_freezes_weight():
    trace=train_scalar_prompt(xs=[-0.2,0.0,0.1], ys=[1,1,1], weight=2.0, prompt=-1.0, lr=0.3, steps=15)
    assert trace['loss_after'] < trace['loss_before']
    assert trace['frozen_weights_unchanged']
    assert trace['params_before']['prompt'] != trace['params_after']['prompt']


def test_trace_has_validator_compatible_parameter_fields():
    from prompt_training_loop import train_scalar_prompt
    trace=train_scalar_prompt(xs=[0.0], ys=[1], steps=2)
    assert 'params_before' in trace and 'params_after' in trace
    assert trace['weight_before'] == trace['weight_after']
