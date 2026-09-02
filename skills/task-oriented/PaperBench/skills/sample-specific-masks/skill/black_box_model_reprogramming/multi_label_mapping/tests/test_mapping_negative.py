from mapping import apply_mapping


def test_overlapping_source_groups_are_rejected():
    try:
        apply_mapping([[0.25, 0.25, 0.25, 0.25]], {0: [0, 1], 1: [1, 2]})
    except ValueError as exc:
        assert "overlap" in str(exc)
    else:
        raise AssertionError("overlapping groups should be rejected")
