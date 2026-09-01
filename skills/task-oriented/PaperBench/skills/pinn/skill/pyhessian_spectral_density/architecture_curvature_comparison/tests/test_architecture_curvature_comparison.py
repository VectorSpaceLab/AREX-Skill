from compare_curvature import summarize_variant, rank_by_sharpness, compare_to_baseline

def test_variant_ranking_and_direction():
    base = summarize_variant('baseline', 3.0, 4.0, [1.0, 3.0])
    sharp = summarize_variant('no_bn', 6.0, 7.0, [1.0, 6.0])
    flat = summarize_variant('no_residual', 2.5, 3.0, [1.0, 2.5])
    assert rank_by_sharpness([base, sharp, flat])[0]['name'] == 'no_bn'
    assert compare_to_baseline(base, sharp)['direction'] == 'sharper'

from compare_curvature import curvature_direction_contract

def test_curvature_direction_contract():
    assert curvature_direction_contract({'direction': 'sharper', 'top_eigen_delta': 1.0})
    assert not curvature_direction_contract({'direction': 'unknown'})
