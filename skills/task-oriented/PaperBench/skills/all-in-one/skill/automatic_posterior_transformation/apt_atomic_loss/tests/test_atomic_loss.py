from atomic_loss import atomic_loss, atomic_probabilities, ratio_diagnostic


def test_atomic_probabilities_sum_to_one():
    result = atomic_probabilities([-2.0, -0.5, -1.0], [-1.0, -1.0, -1.0])
    assert abs(result["probability_sum"] - 1.0) < 1e-12
    assert result["probabilities"][1] > result["probabilities"][2] > result["probabilities"][0]


def test_atomic_probabilities_are_shift_invariant():
    base = atomic_probabilities([-2.0, -0.5, -1.0], [-1.0, -1.0, -1.0])["probabilities"]
    shifted = atomic_probabilities([8.0, 9.5, 9.0], [-1.0, -1.0, -1.0])["probabilities"]
    assert all(abs(a - b) < 1e-12 for a, b in zip(base, shifted))


def test_targeted_update_reduces_loss():
    before = atomic_loss([-2.0, -0.5, -1.0], [-1.0, -1.0, -1.0], true_index=0)
    after = atomic_loss([-0.2, -0.5, -1.0], [-1.0, -1.0, -1.0], true_index=0)
    assert after["loss"] < before["loss"]
    assert after["true_probability"] > before["true_probability"]


def test_ratio_diagnostic_matches_scores():
    diagnostic = ratio_diagnostic([-2.0, -0.5, -1.0], [-1.0, -1.5, -1.0], 1, 2)
    assert diagnostic["abs_error"] < 1e-12


def test_true_atom_outside_prior_support_is_rejected():
    try:
        atomic_loss([-1.0, -2.0], [float("-inf"), -1.0], true_index=0)
    except ValueError as exc:
        assert "prior support" in str(exc)
    else:
        raise AssertionError("expected true atom outside prior support to fail")
