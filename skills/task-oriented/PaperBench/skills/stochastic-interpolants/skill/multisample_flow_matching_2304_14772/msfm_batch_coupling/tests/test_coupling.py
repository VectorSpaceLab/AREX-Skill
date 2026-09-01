import importlib.util
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "coupling.py"
spec = importlib.util.spec_from_file_location("coupling", MODULE_PATH)
coupling = importlib.util.module_from_spec(spec)
spec.loader.exec_module(coupling)


def test_batch_ot_reduces_transport_cost_and_preserves_marginals():
    source = [[0.0], [10.0]]
    target = [[9.0], [1.0]]
    uniform = coupling.build_coupling(source, target, "uniform")
    batch_ot = coupling.build_coupling(source, target, "batch_ot")
    assert batch_ot["pairs"] == [(0, 1), (1, 0)]
    assert batch_ot["transport_cost"] < uniform["transport_cost"]
    assert batch_ot["row_sums"] == [1.0, 1.0]
    assert batch_ot["column_sums"] == [1.0, 1.0]


def test_invalid_method_is_rejected():
    try:
        coupling.build_coupling([[0.0]], [[1.0]], "bad")
    except ValueError as exc:
        assert "method" in str(exc)
    else:
        raise AssertionError("invalid method should fail")
