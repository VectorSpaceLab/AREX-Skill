from structured import nm_mask

def test_exact_group_counts_and_tail():
    res=nm_mask([[4,1,3,2,0]], 2, 4)
    assert res['mask'][0][:4].count(True)==2
    assert res['mask'][0][4] is False
    assert res['metadata']['tail_width']==1
