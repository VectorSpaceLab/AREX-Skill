from sb_coupling import bridge_std, row_normalized_gibbs


def test_lower_epsilon_concentrates_near_match():
    source = [[0.0]]
    target = [[0.0], [3.0]]
    low = row_normalized_gibbs(source, target, 0.1)["row_coupling"][0][0]
    high = row_normalized_gibbs(source, target, 10.0)["row_coupling"][0][0]
    assert low > high


def test_bridge_std_endpoint_and_midpoint():
    assert bridge_std(0.0, 2.0) == 0.0
    assert bridge_std(1.0, 2.0) == 0.0
    assert bridge_std(0.5, 2.0) > bridge_std(0.25, 2.0)
