from mapping import apply_mapping, frequency_mapping


def test_apply_mapping_averages_and_renormalizes():
    rows = [[0.4, 0.2, 0.1, 0.3]]
    mapped = apply_mapping(rows, {0: [0, 1], 1: [2, 3]})
    assert abs(mapped[0][0] - 0.6) < 1e-12
    assert abs(mapped[0][1] - 0.4) < 1e-12


def test_frequency_mapping_is_deterministic_and_nonoverlapping():
    rows = [[0.8,0.1,0.05,0.05], [0.7,0.2,0.05,0.05], [0.05,0.05,0.7,0.2], [0.05,0.05,0.8,0.1]]
    mapping = frequency_mapping(rows, [0,0,1,1], group_size=1)
    assert mapping == {0: [0], 1: [2]}
