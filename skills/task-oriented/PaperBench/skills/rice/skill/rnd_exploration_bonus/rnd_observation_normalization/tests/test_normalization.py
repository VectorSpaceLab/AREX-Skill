from normalization import normalize, normalize_with_update


def test_running_stats_and_clip_bounds():
    result = normalize_with_update([[0.0, 10.0], [2.0, 14.0]])
    assert result["stats"]["count"] == 2
    assert all(-5.0 <= value <= 5.0 for row in result["normalized"] for value in row)
    clipped = normalize([[1000.0, -1000.0]], result["stats"], clip=5.0)
    assert clipped == [[5.0, -5.0]]
