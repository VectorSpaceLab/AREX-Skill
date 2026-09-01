import importlib.util
import pathlib

SCRIPT = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "metrics.py"
spec = importlib.util.spec_from_file_location("metrics", SCRIPT)
metrics = importlib.util.module_from_spec(spec)
spec.loader.exec_module(metrics)


def five(value):
    return {str(i): value for i in range(1, 6)}


def test_baseline_mce_is_100():
    baseline = {"gaussian_noise": five(0.5), "brightness": five(0.25)}
    result = metrics.compute_corruption_metrics(baseline, baseline, 0.1, 0.1)
    assert abs(result["mce"] - 100.0) < 1e-9
    assert abs(result["relative_mce"] - 100.0) < 1e-9


def test_half_error_model_has_mce_50():
    baseline = {"gaussian_noise": five(0.6), "brightness": five(0.4)}
    model = {"gaussian_noise": five(0.3), "brightness": five(0.2)}
    result = metrics.compute_corruption_metrics(model, baseline, 0.15, 0.1)
    assert abs(result["mce"] - 50.0) < 1e-9
    assert result["relative_mce"] != result["mce"]


def test_requires_all_severities():
    try:
        metrics.compute_corruption_metrics({"gaussian_noise": {"1": 0.1}}, {"gaussian_noise": five(0.2)}, 0.0, 0.0)
    except ValueError as exc:
        assert "severities" in str(exc)
    else:
        raise AssertionError("expected ValueError")


if __name__ == "__main__":
    test_baseline_mce_is_100()
    test_half_error_model_has_mce_50()
    test_requires_all_severities()
