from score_masking import compute_mask

def test_zero_and_full_keep_ratio():
    assert compute_mask([3, 2, 1], keep_ratio=0)['mask'] == [0, 0, 0]
    assert compute_mask([3, 2, 1], keep_ratio=1)['mask'] == [1, 1, 1]
