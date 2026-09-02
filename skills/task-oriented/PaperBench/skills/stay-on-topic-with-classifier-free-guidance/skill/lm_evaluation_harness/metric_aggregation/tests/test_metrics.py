from metrics import compute_metrics

def test_accuracy_and_em():
    out=compute_metrics(['The Cat!','dog'], ['the cat','cat'], ['exact_match','accuracy'])
    assert out['exact_match']==0.5 and out['accuracy']==0.0

def test_f1_partial():
    assert compute_metrics(['red cat'], ['red big cat'], ['f1'])['f1'] > 0.79

def test_empty_metric_inputs_are_zero():
    assert compute_metrics([], [], ['accuracy','exact_match','f1']) == {'accuracy':0.0,'exact_match':0.0,'f1':0.0}
