from output_map import aggregate, linear_head

def test_aggregate_normalizes_and_rejects_overlap():
    y=aggregate([.1,.2,.3,.4], [[0,1],[2,3]])
    assert len(y)==2 and abs(sum(y)-1)<1e-9 and y[1]>y[0]
    try: aggregate([.1,.9], [[0,1],[1]])
    except ValueError: return
    assert False

def test_linear_head_shape():
    y=linear_head([1,2], [[1,0],[0,1]], [0,0])
    assert len(y)==2 and y[1]>y[0]
