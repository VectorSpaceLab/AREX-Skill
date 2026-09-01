from invalid_correction import estimate_validity, correct_scores

def test_validity_estimate_and_correction():
    est=estimate_validity([(0.0,True),(0.1,False),(1.0,True)], bins=2)
    assert len(est)==2
    scores=correct_scores([1.0,1.0],[0.25,0.75])
    assert scores[1]>scores[0]
