import tempfile
from pathlib import Path

from run_reduced_recovery import run_recovery


def test_reduced_recovery_produces_mechanism_metrics():
    with tempfile.TemporaryDirectory() as tmp:
        attempt_dir = Path(tmp)
        skills_root = Path(__file__).resolve().parents[2]
        (attempt_dir / "module_plan.json").write_text(
            '{"paper_id":"demo","fast_recovery_target":{"dataset":"synthetic_1d_gaussian_mixture_interpolant","metric":"loss_reduction_fraction","paper_value":0.0,"proxy":true}}',
            encoding="utf-8",
        )
        result = run_recovery(attempt_dir, skills_root, seed=7, sample_count=32, steps=20, lr=0.03)
        assert result["is_proxy"] is True
        assert result["metrics"]["loss_reduction_fraction"] > 0.0
        assert result["mechanism_checks"]["interpolant_constructed"] is True
        assert (attempt_dir / "recovery" / "logs" / "training_trace.json").exists()
        assert (attempt_dir / "recovery" / "logs" / "generated_data_item.json").exists()
