from group_pruning import aggregate_groups, broadcast_mask, structured_pruning_mask


def test_row_aggregation_and_mask():
    imp = [[1.0, 1.0], [0.1, 0.2], [3.0, 0.0]]
    out = structured_pruning_mask(imp, "row", 1)
    assert out["group_scores"] == [2.0, 0.30000000000000004, 3.0]
    assert out["group_mask"] == [1, 0, 1]
    assert out["element_mask"] == [[1, 1], [0, 0], [1, 1]]


def test_column_aggregation_and_mask():
    imp = [[1.0, 0.1, 2.0], [1.0, 0.2, 3.0]]
    assert aggregate_groups(imp, "column") == [2.0, 0.30000000000000004, 5.0]
    assert broadcast_mask([1, 0, 1], (2, 3), "column") == [[1, 0, 1], [1, 0, 1]]


def test_tie_break_is_deterministic():
    out = structured_pruning_mask([[1.0], [1.0], [2.0]], "row", 1)
    assert out["group_mask"] == [0, 1, 1]
