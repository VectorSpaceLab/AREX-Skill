import importlib.util
from pathlib import Path

script_path = Path(__file__).resolve().parents[1] / "scripts" / "subset_protocol.py"
spec = importlib.util.spec_from_file_location("subset_protocol", script_path)
subset_protocol = importlib.util.module_from_spec(spec)
spec.loader.exec_module(subset_protocol)


def test_generate_alpha_subsets_reproducible():
    first = subset_protocol.generate_alpha_subsets(8, 0.5, 4, 7)
    second = subset_protocol.generate_alpha_subsets(8, 0.5, 4, 7)
    assert first == second
    assert first["metadata"]["subset_size"] == 4
    for row in first["matrix"]:
        assert set(row).issubset({0, 1})
        assert sum(row) == 4


def test_invalid_alpha_rejected():
    try:
        subset_protocol.generate_alpha_subsets(8, 0.0, 4, 7)
    except ValueError:
        return
    raise AssertionError("invalid alpha should fail")


if __name__ == "__main__":
    test_generate_alpha_subsets_reproducible()
    test_invalid_alpha_rejected()
