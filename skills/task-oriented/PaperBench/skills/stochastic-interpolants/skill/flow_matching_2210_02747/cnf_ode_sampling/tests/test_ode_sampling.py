import importlib.util
from pathlib import Path

script = Path(__file__).resolve().parents[1] / "scripts" / "ode_sampling.py"
spec = importlib.util.spec_from_file_location("ode_sampling", script)
ode_sampling = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ode_sampling)


def test_constant_field_solvers_match_reference_and_nfe():
    x0 = [0.0, 1.0]
    velocity = [2.0, -1.0]
    expected = [2.0, 0.0]
    expected_nfe = {"euler": 4, "midpoint": 8, "rk4": 16}
    for solver, nfe in expected_nfe.items():
        result = ode_sampling.integrate(ode_sampling.constant_field(velocity), x0, 4, solver)
        assert result["final"] == expected
        assert result["nfe"] == nfe
        assert len(result["trajectory"]) == 5


def test_invalid_solver_and_mse():
    assert ode_sampling.mse([1.0, 3.0], [1.0, 1.0]) == 2.0
    try:
        ode_sampling.integrate(ode_sampling.constant_field([1.0]), [0.0], 0, "euler")
    except ValueError as exc:
        assert "steps" in str(exc)
    else:
        raise AssertionError("zero steps should fail")


if __name__ == "__main__":
    test_constant_field_solvers_match_reference_and_nfe()
    test_invalid_solver_and_mse()
