from rail_mapping import coverage_report, mapping_pairs, sample_teacher_layers


def test_sample_is_unique_sorted_and_reproducible():
    a = sample_teacher_layers(12, 6, seed=7, epoch=2)
    b = sample_teacher_layers(12, 6, seed=7, epoch=2)
    assert a == b
    assert a == sorted(a)
    assert len(a) == 6
    assert len(set(a)) == 6


def test_epoch_changes_mapping_and_coverage_counts():
    report = coverage_report(12, 6, epochs=8, seed=3)
    assert report["unique_layers_visited"] >= 10
    assert len({tuple(m) for m in report["mappings"]}) > 1
    assert sum(report["coverage_counts"].values()) == 48


def test_pairs_align_student_order():
    pairs = mapping_pairs(8, 4, seed=1)
    assert [p["student_layer"] for p in pairs] == [0, 1, 2, 3]
    assert [p["teacher_layer"] for p in pairs] == sorted(p["teacher_layer"] for p in pairs)


def test_invalid_counts_raise():
    try:
        sample_teacher_layers(3, 4, seed=0)
        assert False, "expected ValueError"
    except ValueError:
        pass
