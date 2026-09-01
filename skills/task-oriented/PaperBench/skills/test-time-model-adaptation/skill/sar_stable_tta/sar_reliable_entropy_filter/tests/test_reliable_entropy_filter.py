from reliable_entropy_filter import filter_reliable, default_margin

def test_entropy_filter_selects_confident_samples():
    logits = [[5.0,0.0,0.0], [1.0,1.0,1.0]]
    result = filter_reliable(logits, class_count=3)
    assert result['margin'] == default_margin(3)
    assert result['selected_indices'] == [0]
    assert result['mean_entropy'] is not None


def test_empty_batch_is_explicit():
    result = filter_reliable([], class_count=3, margin=0.5)
    assert result['entropies'] == []
    assert result['selected_indices'] == []
    assert result['mean_entropy'] is None
