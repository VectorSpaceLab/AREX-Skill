from frequency_mapping import compute_frequency_mapping

def test_duplicate_best_uses_next_best_unused():
    grouped={'a':['s1','s1','s2'], 'b':['s1','s2','s2']}
    out=compute_frequency_mapping(grouped, ['a','b'], ['s1','s2'])
    assert out['mapping']=={'a':'s1','b':'s2'}
    assert not out['audit'][1]['duplicate_assignment']

def test_empty_target_rejected():
    try:
        compute_frequency_mapping({'a':[]}, ['a'], ['s1'])
    except ValueError:
        return
    assert False, 'expected ValueError'

def test_tie_breaks_by_source_label_order():
    grouped={'a':['s2','s1']}
    out=compute_frequency_mapping(grouped, ['a'], ['s1','s2'])
    assert out['mapping']['a']=='s1'
