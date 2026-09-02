import importlib.util
import pathlib

script_path = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "lpips_distance.py"
spec = importlib.util.spec_from_file_location("lpips_distance", script_path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_zero_to_one_normalization_matches_minus_one_to_one():
    zero_ref = [[[0.5, 0.6], [0.7, 0.8]], [[0.4, 0.5], [0.6, 0.7]], [[0.3, 0.4], [0.5, 0.6]]]
    zero_alt = [[[0.55, 0.65], [0.75, 0.85]], [[0.4, 0.5], [0.6, 0.7]], [[0.3, 0.4], [0.5, 0.6]]]
    minus_ref = [[[2 * value - 1 for value in row] for row in channel] for channel in zero_ref]
    minus_alt = [[[2 * value - 1 for value in row] for row in channel] for channel in zero_alt]
    a = module.lpips_distance(zero_ref, zero_alt, input_range="zero_to_one")["distance"]
    b = module.lpips_distance(minus_ref, minus_alt, input_range="minus_one_to_one")["distance"]
    assert abs(a - b) < 1e-12
