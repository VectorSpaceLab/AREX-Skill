from apt_transform import transform

def test_correction_and_normalization():
    out = transform([0.0, 1.0, -1.0], [-1.0, -1.0, -2.0], [-2.0, -1.0, -2.0])
    assert out['corrected_logits'] == [-1.0, 1.0, -1.0]
    assert abs(sum(out['probabilities']) - 1.0) < 1e-12
    assert out['probabilities'][1] > out['probabilities'][0]

from apt_transform import correction_effect

def test_correction_changes_nonprior_proposal_probabilities():
    out = correction_effect([0.0, 0.0], [-1.0, -1.0], [-0.2, -2.0])
    assert out['max_probability_shift'] > 0.1
