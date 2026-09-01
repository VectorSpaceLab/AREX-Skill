from select_coreset import monotonic_selection, select_coverage_coreset


def test_stratified_selection_covers_more_bins_than_monotonic():
    table = {
        'indices': list(range(20)),
        'targets': [0] * 10 + [1] * 10,
        'accumulated_margin': [i / 19 for i in range(20)],
    }
    ccs = select_coverage_coreset(table, coreset_ratio=0.2, mis_ratio=0.0, strata=4, seed=3)
    mono = monotonic_selection(table, 'accumulated_margin', 0.2, descending=True)
    mono_bins = set(min(3, int((table['accumulated_margin'][i]) / 0.25)) for i in mono)
    assert ccs['coreset_size'] == 4
    assert len(ccs['represented_bins']) > len(mono_bins)
    assert set(ccs['class_counts']) == {'0', '1'}
