from mapping_diagnostics import diagnose

def test_diagnose_change_and_shared_attribute():
    hist=[{'flower':'dog'},{'flower':'cardoon'}]
    out=diagnose(hist, {'flower':['purple','spiky']}, {'cardoon':['purple','spiky'], 'dog':['fur']})
    assert out['changed_count']==1
    assert out['stability']==0.0
    assert out['explanations'][0]['shared_attributes']==['purple','spiky']

def test_missing_descriptors_do_not_fail():
    out=diagnose([{'a':'s1'}])
    assert out['changed_count']==0
    assert out['explanations'][0]['explanation']=='no descriptor overlap available'
