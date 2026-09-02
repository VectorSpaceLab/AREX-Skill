from group_pruning import structured_pruning_mask


def test_invalid_prune_count_rejected():
    try:
        structured_pruning_mask([[1.0, 2.0]], "column", 3)
    except ValueError:
        return
    raise AssertionError("expected ValueError for pruning more groups than available")
