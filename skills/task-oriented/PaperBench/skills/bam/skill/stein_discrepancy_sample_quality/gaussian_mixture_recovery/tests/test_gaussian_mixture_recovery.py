import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "mixture_recovery.py"
spec = importlib.util.spec_from_file_location("mixture_recovery", SCRIPT)
mixture_recovery = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mixture_recovery)


def test_single_component_score_points_to_mean():
    samples = [[-1.0], [0.0], [2.0]]
    scores = mixture_recovery.mixture_score(samples, [0.0], [1.0], 1.0)
    assert scores[0][0] > 0.0
    assert abs(scores[1][0]) < 1e-12
    assert scores[2][0] < 0.0


def test_tiny_recovery_invokes_generated_skills():
    skill_root = Path(__file__).resolve().parents[2]
    result = mixture_recovery.run_trials(skill_root, sample_size=24, trials=2, num_bootstrap=10, seed=5)
    assert result["mechanism_checks"]["generated_stein_kernel_skill_invoked"] is True
    assert result["mechanism_checks"]["generated_bootstrap_skill_invoked"] is True
    assert len(result["trial_records"]) == 4
    assert "alternative_rejection_rate_minus_null_rejection_rate" in result["metrics"]
