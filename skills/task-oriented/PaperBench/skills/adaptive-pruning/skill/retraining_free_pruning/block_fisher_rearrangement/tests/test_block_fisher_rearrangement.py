from block_fisher_rearrangement import rearrange_layer

def test_objective_nonincrease_and_cardinality():
    block=[[5,0,0],[0,1,4],[0,4,1]]
    mask=[0,0,1]
    got=rearrange_layer(mask,block)
    assert got['objective_after'] <= got['objective_before']
    assert sum(got['mask']) == sum(mask)
