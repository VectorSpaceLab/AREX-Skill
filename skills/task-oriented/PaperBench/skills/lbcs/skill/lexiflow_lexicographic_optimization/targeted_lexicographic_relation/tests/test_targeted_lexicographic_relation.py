from targeted_lexicographic_relation import target_equal, target_preferred, update_decision, vanilla_preferred


def test_lower_priority_improvement_inside_target_is_accepted():
    decision = update_decision([0.11, 2.0], [0.10, 8.0], [0.12, 4.0])
    assert decision["target_equal"] is False
    assert decision["target_preferred"]
    assert decision["accept"]


def test_unsatisfied_high_priority_worsening_rejected():
    decision = update_decision([0.20, 1.0], [0.10, 8.0], [0.12, 8.0])
    assert not decision["accept"]


def test_above_target_high_priority_improvement_preferred():
    assert target_preferred([0.15, 9.0], [0.20, 1.0], [0.12, 8.0])
    assert not target_equal([0.15, 9.0], [0.20, 1.0], [0.12, 8.0])
    assert vanilla_preferred([0.15, 9.0], [0.20, 1.0])

def test_target_equivalent_vanilla_tiebreak_accepts():
    decision = update_decision([0.10, 1.5], [0.10, 2.0], [0.12, 2.0])
    assert decision["target_equal"]
    assert decision["vanilla_preferred"]
    assert decision["accept"]
