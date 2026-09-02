from dual_returns import combine_returns


def test_intrinsic_can_continue_across_done():
    result = combine_returns([1.0, 0.0, 2.0], [0.5, 0.5, 0.5], [False, True, False], gamma_e=1.0, gamma_i=1.0, intrinsic_non_episodic=True)
    assert result["extrinsic_returns"] == [1.0, 0.0, 2.0]
    assert result["intrinsic_returns"] == [1.5, 1.0, 0.5]
    assert result["combined_returns"] == [2.5, 1.0, 2.5]
