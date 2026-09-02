from score_representations import compute_class_centers, score_records

def test_centers_and_distances():
    records=[{'id':'a','label':'x','representation':[0,0]},{'id':'b','label':'x','representation':[2,0]},{'id':'c','label':'y','representation':[5,5]}]
    out=score_records(records)
    assert out['centers']['x']==[1.0,0.0]
    assert [round(item['score'],3) for item in out['scores']]==[1.0,1.0,0.0]

def test_bad_dimensions_fail():
    try:
        compute_class_centers([{'id':'a','label':0,'representation':[1]},{'id':'b','label':0,'representation':[1,2]}])
    except ValueError as exc:
        assert 'same dimension' in str(exc)
    else:
        raise AssertionError('expected ValueError')
