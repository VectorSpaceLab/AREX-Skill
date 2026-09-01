import json
import pathlib


def test_recovery_source_manifest_excludes_original_repo():
    attempt_dir = pathlib.Path(__file__).resolve()
    marker = "skill_distillation/lpips_perceptual_metric/lpips_perceptual_metric_attempt_001"
    parts = str(attempt_dir).split(marker)
    if len(parts) != 2:
        return
    manifest_path = pathlib.Path(parts[0] + marker) / "recovery" / "source_manifest.json"
    if not manifest_path.exists():
        return
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest.get("original_repo_used") is False
    serialized = json.dumps(manifest)
    assert "/paper/lpips_perceptual_metric/repo" not in serialized
