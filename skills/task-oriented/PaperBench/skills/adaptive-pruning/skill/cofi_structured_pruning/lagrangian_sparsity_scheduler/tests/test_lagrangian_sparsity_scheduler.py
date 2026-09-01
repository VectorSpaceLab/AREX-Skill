
from cofi_lagrangian import warmup_target, lagrangian_penalty, update_lambda, expected_sparsity

def test_warmup_target_is_monotone_and_capped():
    vals=[warmup_target(s, 10, 0.8) for s in [0,5,10,20]]
    assert vals == [0.0,0.4,0.8,0.8]

def test_penalty_and_lambda_update_direction():
    assert lagrangian_penalty(0.7,0.7,2.0,3.0) == 0.0
    assert lagrangian_penalty(0.9,0.7,1.0,0.0) > 0
    assert update_lambda(1.0,0.9,0.7,0.1) > 1.0
    assert expected_sparsity(2,10) == 0.8
