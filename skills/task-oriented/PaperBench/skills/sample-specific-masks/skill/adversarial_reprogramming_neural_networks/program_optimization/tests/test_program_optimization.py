from program_optimization import train_universal_program

def test_program_changes_and_loss_finite():
    r=train_universal_program([(-2,0),(-1,0),(1,1),(2,1)], init_program=-1, steps=5)
    assert r['params_before']['program'] != r['params_after']['program']
    assert r['loss_after'] < 10
    assert r['mechanism_checks']['frozen_model_unchanged'] is True
