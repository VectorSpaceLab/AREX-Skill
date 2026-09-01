from attribute_objectives import bow_loss_and_grad

def test_bow_gradient_increases_target_when_descended():
    tokens=['cat','space','rocket','table']
    logits=[0.0,0.0,0.0,0.0]
    out=bow_loss_and_grad(tokens, logits, ['space','rocket'])
    assert abs(out['target_mass']-0.5) < 1e-9
    assert out['gradient'][1] < 0 and out['gradient'][2] < 0
    new=[x-0.5*g for x,g in zip(logits,out['gradient'])]
    out2=bow_loss_and_grad(tokens, new, ['space','rocket'])
    assert out2['target_mass'] > out['target_mass']

def test_missing_target_words_raise():
    try:
        bow_loss_and_grad(['cat'], [0.0], ['rocket'])
        assert False
    except ValueError:
        assert True
