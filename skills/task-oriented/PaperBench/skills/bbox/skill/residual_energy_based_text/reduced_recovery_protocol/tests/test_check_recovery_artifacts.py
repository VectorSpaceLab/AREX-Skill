import tempfile
from pathlib import Path

from check_recovery_artifacts import REQUIRED


def test_required_recovery_artifact_list_names_core_logs():
    assert "recovery/recovery_result.json" in REQUIRED
    assert "recovery/logs/training_trace.json" in REQUIRED
    assert "recovery/logs/generated_skill_invocations.json" in REQUIRED


def test_required_paths_are_relative():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        for rel in REQUIRED:
            assert not Path(rel).is_absolute()
            assert str(root / rel).startswith(str(root))

