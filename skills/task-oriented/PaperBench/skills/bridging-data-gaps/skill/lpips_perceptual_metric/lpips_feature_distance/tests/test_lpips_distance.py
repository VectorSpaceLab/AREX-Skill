import importlib.util
import pathlib

script_path = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "lpips_distance.py"
spec = importlib.util.spec_from_file_location("lpips_distance", script_path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_identical_distance_is_zero():
    image = [[[0.0, 0.2], [0.3, 0.4]], [[0.1, 0.2], [0.3, 0.4]], [[0.2, 0.2], [0.3, 0.5]]]
    result = module.lpips_distance(image, image)
    assert result["distance"] < 1e-9


def test_stronger_distortion_has_larger_distance():
    ref = [[[0.0, 0.1], [0.2, 0.3]], [[0.0, 0.1], [0.2, 0.3]], [[0.0, 0.1], [0.2, 0.3]]]
    mild = [[[0.01, 0.11], [0.21, 0.31]], [[0.0, 0.1], [0.2, 0.3]], [[0.0, 0.1], [0.2, 0.3]]]
    severe = [[[1.0, -1.0], [-1.0, 1.0]], [[-1.0, 1.0], [1.0, -1.0]], [[1.0, 1.0], [-1.0, -1.0]]]
    assert module.lpips_distance(ref, mild)["distance"] < module.lpips_distance(ref, severe)["distance"]


def test_negative_weights_rejected():
    image = [[[0.0, 0.2], [0.3, 0.4]], [[0.1, 0.2], [0.3, 0.4]], [[0.2, 0.2], [0.3, 0.5]]]
    try:
        module.lpips_distance(image, image, weights=[1.0, -0.1, 1.0])
    except ValueError:
        return
    raise AssertionError("negative weights must be rejected")
