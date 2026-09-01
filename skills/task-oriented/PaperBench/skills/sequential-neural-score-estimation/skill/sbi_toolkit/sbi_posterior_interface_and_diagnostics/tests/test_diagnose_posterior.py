import importlib.util
import pathlib

SCRIPT = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "diagnose_posterior.py"
spec = importlib.util.spec_from_file_location("diagnose_posterior", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_diagnose_accepts_finite_uncertain_samples():
    result = module.diagnose([0.8, 1.0, 1.2, 1.1], reference_mean=1.0)
    assert result["ok"] is True
    assert result["checks"]["no_fabricated_density_score"] is True


def test_degenerate_samples_fail_uncertainty_check():
    result = module.diagnose([1.0, 1.0, 1.0], reference_mean=1.0)
    assert result["ok"] is False
    assert result["checks"]["nonzero_uncertainty"] is False


def test_reference_mean_threshold_failure_is_reported():
    result = module.diagnose([2.0, 2.1, 1.9], reference_mean=0.0, max_mean_error=0.5)
    assert result["ok"] is False
    assert result["checks"]["reference_mean_within_threshold"] is False
