import importlib.util
import pathlib

SCRIPT = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "sim_protocol.py"
spec = importlib.util.spec_from_file_location("sim_protocol", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_gaussian_location_pairs_are_aligned():
    payload = module.gaussian_location_pairs(num_simulations=8, seed=3)
    assert len(payload["theta"]) == len(payload["x"]) == 8
    assert payload["metadata"]["likelihood_evaluated"] is False
    assert module.validate_pairs(payload) is True


def test_as_2d_promotes_scalars():
    assert module.as_2d([1, 2.5]) == [[1.0], [2.5]]
