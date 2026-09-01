import importlib.util
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "msfm_synthetic_recovery" / "scripts" / "run_synthetic_recovery.py"
spec = importlib.util.spec_from_file_location("run_synthetic_recovery", MODULE_PATH)
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


def test_synthetic_recovery_writes_mechanism_evidence():
    with tempfile.TemporaryDirectory() as tmpdir:
        result = runner.run_experiment(
            ROOT / "msfm_batch_coupling" / "scripts" / "coupling.py",
            ROOT / "msfm_joint_cfm_loss" / "scripts" / "joint_cfm.py",
            tmpdir,
            seed=5,
            batch_size=4,
        )
        assert result["is_proxy"] is True
        assert result["metrics"]["batchot_transport_cost_reduction"] > 0.0
        assert result["mechanism_checks"]["batchot_coupling_evaluated"] is True
        assert result["mechanism_checks"]["optimizer_step_executed"] is True
        assert (Path(tmpdir) / "training_trace.json").exists()
