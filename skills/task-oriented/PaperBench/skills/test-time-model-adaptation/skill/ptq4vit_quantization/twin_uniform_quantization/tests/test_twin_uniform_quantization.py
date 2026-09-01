from twin_quant import twin_quantize, power_of_two_alignment

def test_softmax_uses_two_ranges():
    r=twin_quantize([0.01,0.9], bits=4, kind='softmax')
    assert set(r['range_flags']) == {0,1}

def test_gelu_splits_signs():
    r=twin_quantize([-0.2,0.5], bits=4, kind='gelu')
    assert r['range_flags']==[0,1]
    assert power_of_two_alignment({'r1':0.125,'r2':0.5})['aligned']


def test_zero_and_large_softmax_stability():
    r=twin_quantize([0.0, 1.0], bits=4, kind='softmax')
    assert r['values'][0] == 0.0
    assert r['values'][1] <= 1.0
