from objectives import denoiser_loss, score_from_denoiser, velocity_loss


def test_target_predictor_beats_zero_predictor():
    target = [2.0, -1.0, 3.0]
    zero = [0.0, 0.0, 0.0]
    assert velocity_loss(target, target) < velocity_loss(zero, target)
    noise = [1.0, -2.0]
    assert denoiser_loss(noise, noise) < denoiser_loss([0.0, 0.0], noise)


def test_score_from_denoiser_skips_endpoint_gamma():
    scores = score_from_denoiser([2.0, 3.0], [0.0, 0.5])
    assert scores[0] is None
    assert scores[1] == -6.0


def test_velocity_loss_rejects_mismatched_lengths():
    try:
        velocity_loss([1.0, 2.0], [1.0])
    except ValueError as exc:
        assert "lengths differ" in str(exc)
    else:
        raise AssertionError("expected mismatched objective inputs to fail")
