import importlib.util
import pathlib

SCRIPT = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "corruptions.py"
spec = importlib.util.spec_from_file_location("corruptions", SCRIPT)
corruptions = importlib.util.module_from_spec(spec)
spec.loader.exec_module(corruptions)


def sample_image():
    return [
        [[0.1, 0.2, 0.3], [0.3, 0.4, 0.5], [0.5, 0.6, 0.7]],
        [[0.2, 0.3, 0.4], [0.4, 0.5, 0.6], [0.6, 0.7, 0.8]],
        [[0.3, 0.4, 0.5], [0.5, 0.6, 0.7], [0.7, 0.8, 0.9]],
    ]


def test_reproducible_shape_and_range():
    image = sample_image()
    first = corruptions.apply_corruption(image, "gaussian_noise", 2, seed=7)
    second = corruptions.apply_corruption(image, "gaussian_noise", 2, seed=7)
    assert first == second
    assert first["metadata"]["shape"] == [3, 3, 3]
    for row in first["image"]:
        for pixel in row:
            for value in pixel:
                assert 0.0 <= value <= 1.0


def test_gaussian_severity_increases_distortion():
    image = sample_image()
    low = corruptions.apply_corruption(image, "gaussian_noise", 1, seed=3)["metadata"]["mean_abs_difference"]
    high = corruptions.apply_corruption(image, "gaussian_noise", 5, seed=3)["metadata"]["mean_abs_difference"]
    assert high > low


def test_rejects_unknown_corruption():
    try:
        corruptions.apply_corruption(sample_image(), "adversarial_noise", 1)
    except ValueError as exc:
        assert "unknown corruption" in str(exc)
    else:
        raise AssertionError("expected ValueError")


if __name__ == "__main__":
    test_reproducible_shape_and_range()
    test_gaussian_severity_increases_distortion()
    test_rejects_unknown_corruption()
