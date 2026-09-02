from tiny_train import train, predict


def test_training_changes_params_and_loss():
    rec=[{'source':'Review good excellent','target':'positive'}, {'source':'Review bad awful','target':'negative'}]
    m=train(rec, ['negative','positive'], epochs=10)
    assert m['params_before'] != m['params_after']
    assert m['loss_after'] < m['loss_before']


def test_predict_returns_label():
    rec=[{'source':'good','target':'yes'}, {'source':'bad','target':'no'}]
    m=train(rec, ['no','yes'], epochs=5)
    assert predict(m, 'good') in {'no','yes'}
