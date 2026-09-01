import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "variance_reduction.py"
spec = importlib.util.spec_from_file_location("variance_reduction", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_variance_reduction_reports_lower_proxy_variance():
    score = [[-2.0], [-1.0], [0.0], [1.0], [2.0], [3.0]]
    local_signal = [1.0, 1.1, 1.2, 1.1, 1.0, 0.9]
    full_signal = [6.0, -5.0, 7.0, -6.0, 8.0, -7.0]
    result = module.reduce_variance(score, local_signal, full_signal)
    assert result["variance"]["naive"] > result["variance"]["control_variate"]
    assert result["variance_reduction_ratio"] > 1.0
    assert result["diagnostics"]["finite"] is True


def test_zero_score_variance_uses_zero_scale():
    result = module.reduce_variance([[1.0], [1.0]], [2.0, 3.0])
    assert result["control_variate_scale"] == 0.0
