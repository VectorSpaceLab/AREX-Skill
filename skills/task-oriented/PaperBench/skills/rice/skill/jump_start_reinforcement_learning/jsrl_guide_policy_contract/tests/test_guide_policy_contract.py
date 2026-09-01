from guide_policy_contract import compare_to_baseline, right_guide, stationary_or_bad_guide


def test_right_guide_is_useful():
    report = compare_to_baseline(right_guide)
    assert report["useful"] is True
    assert report["guide"]["success"] is True


def test_stationary_guide_is_not_useful_against_right_baseline():
    report = compare_to_baseline(stationary_or_bad_guide, baseline=right_guide)
    assert report["useful"] is False
