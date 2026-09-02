from output_remapping import remap_scores

def test_many_to_one_sum():
    r=remap_scores([0.1,2.0,0.5,0.6], {'zero':[0], 'one':[2,3]})
    assert r['adversarial_scores']['one']==1.1
    assert r['prediction']=='one'
