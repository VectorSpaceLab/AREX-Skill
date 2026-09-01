from fusion_generation import geometric_fuse

def test_fusion_endpoints_and_normalization():
    base=[2.0,0.0]; pert=[0.0,2.0]
    assert geometric_fuse(base, pert, 0.0)['selected_index'] == 0
    assert geometric_fuse(base, pert, 1.0)['selected_index'] == 1
    mid=geometric_fuse(base, pert, 0.5)['fused_probs']
    assert abs(sum(mid)-1.0) < 1e-9
