from prompt_eval import evaluate


def test_accuracy_and_template_metrics():
    rec=[{'example_id':'1','template_id':'a','prediction':'yes','target':'yes'}, {'example_id':'2','template_id':'a','prediction':'no','target':'yes'}, {'example_id':'1','template_id':'b','prediction':'yes','target':'yes'}]
    m=evaluate(rec)
    assert round(m['accuracy'],3)==0.667
    assert m['per_template_accuracy']['b']==1.0
    assert m['prompt_consistency']==1.0


def test_empty_records_are_defined():
    m=evaluate([])
    assert m['accuracy']==0.0
    assert m['prompt_consistency']==1.0
    assert m['count']==0
