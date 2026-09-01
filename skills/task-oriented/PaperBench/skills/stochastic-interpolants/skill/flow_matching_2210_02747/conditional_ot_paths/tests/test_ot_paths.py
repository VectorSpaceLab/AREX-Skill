import importlib.util
from pathlib import Path

script = Path(__file__).resolve().parents[1] / "scripts" / "ot_paths.py"
spec = importlib.util.spec_from_file_location("ot_paths", script)
ot_paths = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ot_paths)


def test_interpolation_and_target_formula():
    x0 = [1.0, -2.0]
    x1 = [3.0, 4.0]
    sigma_min = 0.5
    assert ot_paths.interpolate_ot(x0, x1, 0.0, sigma_min) == x0
    assert ot_paths.interpolate_ot(x0, x1, 1.0, sigma_min) == [3.5, 3.0]
    assert ot_paths.target_ot(x0, x1, sigma_min) == [2.5, 5.0]


def test_diagnostics_and_invalid_inputs():
    diagnostics = ot_paths.path_diagnostics([0.0, 1.0], [2.0, 3.0], 0.1)
    assert diagnostics["finite"] is True
    assert diagnostics["target_time_invariant"] is True
    try:
        ot_paths.interpolate_ot([0.0], [1.0], 1.2)
    except ValueError as exc:
        assert "t must be" in str(exc)
    else:
        raise AssertionError("invalid time should fail")


if __name__ == "__main__":
    test_interpolation_and_target_formula()
    test_diagnostics_and_invalid_inputs()
