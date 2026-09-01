from train_reprogramming import run

def test_training_improves_and_freezes_source():
    r=run(steps=20)
    assert r['source_unchanged'] is True
    assert r['params_before'] != r['params_after']
    assert r['loss_after'] < r['loss_before']
