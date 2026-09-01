from score_masking import compute_mask

def test_top_v_ties_and_shape():
    r=compute_mask([[1,2],[2,-1]], keep_ratio=0.5)
    assert r['mask']==[[0,1],[1,0]]
    assert r['metadata']['kept']==2

def test_threshold_strict():
    r=compute_mask([0.0,0.1,0.2], mode='threshold', threshold=0.1)
    assert r['mask']==[0,0,1]
