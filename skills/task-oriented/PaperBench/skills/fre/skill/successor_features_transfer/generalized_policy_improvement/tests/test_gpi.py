import importlib.util
import pathlib

SCRIPT = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "gpi.py"
spec = importlib.util.spec_from_file_location("gpi", SCRIPT)
gpi = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gpi)


def test_gpi_mixes_source_policy_values():
    values = {
        "a": {"s0": {"left": 4.0, "right": 0.0}, "s1": {"left": 1.0, "right": 1.0}},
        "b": {"s0": {"left": 2.0, "right": 3.0}, "s1": {"left": 0.0, "right": 5.0}},
    }
    result = gpi.generalized_policy_improvement(values, states=["s0", "s1"], actions=["left", "right"])
    assert result["policy"] == {"s0": "left", "s1": "right"}
    assert result["diagnostics"]["unique_winning_sources"] == ["a", "b"]


if __name__ == "__main__":
    test_gpi_mixes_source_policy_values()


def test_gpi_uses_deterministic_tie_breaking():
    values = {
        "a": {"s0": {"left": 1.0, "right": 1.0}},
        "b": {"s0": {"left": 1.0, "right": 1.0}},
    }
    result = gpi.generalized_policy_improvement(values, states=["s0"], actions=["left", "right"])
    assert result["policy"]["s0"] == "left"
    assert result["diagnostics"]["states"]["s0"]["winning_source"] == "a"

