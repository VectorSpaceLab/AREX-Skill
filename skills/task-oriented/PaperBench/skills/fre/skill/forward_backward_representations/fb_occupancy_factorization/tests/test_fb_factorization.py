from fb_factorization import run

def test_factorization_reduces_loss_and_changes_params():
    out = run(rank=3)
    assert out['loss_after'] < out['loss_before']
    assert out['params_before'] != out['params_after']
    assert len(out['F']) == 36
    assert len(out['B']) == 9
