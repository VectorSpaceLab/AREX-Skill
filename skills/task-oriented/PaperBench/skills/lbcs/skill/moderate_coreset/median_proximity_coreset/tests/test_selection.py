from select_median_coreset import select_by_median_proximity

def test_even_median_selection():
    out=select_by_median_proximity([{'id':'a','score':0},{'id':'b','score':2},{'id':'c','score':4},{'id':'d','score':10}],2)
    assert out['median']==3.0
    assert out['selected_ids']==['b','c']

def test_invalid_size_fails():
    try:
        select_by_median_proximity([{'id':'a','score':1}],2)
    except ValueError as exc:
        assert 'size' in str(exc)
    else:
        raise AssertionError('expected ValueError')
