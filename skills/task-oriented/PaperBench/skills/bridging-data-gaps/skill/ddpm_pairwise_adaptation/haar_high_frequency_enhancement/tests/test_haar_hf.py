from haar_hf import haar_high_frequency, high_frequency_losses


def test_constant_image_has_zero_high_frequency():
    image = [[[[2.0, 2.0], [2.0, 2.0]]]]
    assert haar_high_frequency(image) == [[[[0.0]]]]


def test_checkerboard_has_positive_high_frequency():
    image = [[[[1.0, -1.0], [-1.0, 1.0]]]]
    hf = haar_high_frequency(image)
    assert abs(hf[0][0][0][0]) > 0.0


def test_losses_are_finite_and_zero_when_matching():
    image = [[[[1.0, -1.0], [-1.0, 1.0]]], [[[0.5, -0.5], [-0.5, 0.5]]]]
    result = high_frequency_losses(image, image, image)
    assert result["Lhf"] >= 0.0
    assert result["Lhfmse"] == 0.0
    assert result["energy"]["source"] > 0.0

def test_odd_spatial_shape_is_rejected():
    try:
        haar_high_frequency([[[[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]]]])
    except ValueError as exc:
        assert "even" in str(exc)
    else:
        raise AssertionError("odd spatial width should be rejected")
