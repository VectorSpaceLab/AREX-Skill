from fusion_ops import fuse_arrays, mean_abs_gradient

def test_fusion_preserves_shape_and_range():
    ir=[[0,1],[0,1]]; vis=[[0.2,0.4],[0.6,0.8]]
    fused,diag=fuse_arrays(ir,vis)
    assert len(fused)==2 and len(fused[0])==2
    assert all(0<=v<=1 for row in fused for v in row)
    assert diag['thermal_salience']>0.7

def test_gradient_metric_nonnegative():
    assert mean_abs_gradient([[0,1],[1,0]])>=0


def test_mismatched_shapes_raise_value_error():
    try:
        fuse_arrays([[1.0]], [[1.0, 0.0]])
    except ValueError as exc:
        assert 'equal shape' in str(exc)
    else:
        raise AssertionError('expected ValueError')
