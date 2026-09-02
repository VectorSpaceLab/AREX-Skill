from boosted_scoring import boosted_scores, predict

def test_negative_alpha_discounts_short_prior():
    full=[-1.0,-0.9]
    short=[-5.0,-0.1]
    assert predict(full, short, 0.0)["prediction"] == 1
    assert predict(full, short, -1.0)["prediction"] == 0

def test_scores_follow_formula():
    assert boosted_scores([-2.0],[-3.0],-0.5)==[-0.5]


def test_rejects_mismatched_lengths():
    try:
        boosted_scores([-1.0],[-1.0,-2.0],-1.0)
    except ValueError as exc:
        assert "equal length" in str(exc)
    else:
        raise AssertionError("expected ValueError")
