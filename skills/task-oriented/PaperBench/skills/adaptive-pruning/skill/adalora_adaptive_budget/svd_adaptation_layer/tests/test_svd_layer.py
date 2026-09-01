from svd_layer import svd_forward, active_rank

def test_zero_singular_values_preserve_base_output():
    got=svd_forward([[3,4]], [[1,0],[0,1]], None, [[1,0],[0,1]], [0,0], [[1,0],[0,1]])
    assert got['output']==[[3,4]]
    assert got['active_rank']==0

def test_nonzero_update_and_rank_count():
    got=svd_forward([[1,2]], [[1,0],[0,1]], None, [[1,0],[0,1]], [1,2], [[1,0],[0,1]], alpha=2, ranknum=2)
    assert active_rank([1,0,2])==2
    assert abs(got['output'][0][0]-2)<1e-4
    assert abs(got['output'][0][1]-6)<1e-4

def test_bias_is_preserved_with_zero_update():
    got=svd_forward([[1,1]], [[1,1]], [0.5], [[1,0]], [0], [[1]])
    assert got['output']==[[2.5]]
