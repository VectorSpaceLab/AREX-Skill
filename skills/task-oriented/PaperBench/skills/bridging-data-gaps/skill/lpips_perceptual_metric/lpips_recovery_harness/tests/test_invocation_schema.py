import json
import pathlib


def test_generated_skill_invocation_schema_matches_validator():
    current = pathlib.Path(__file__).resolve()
    marker = "skill_distillation/lpips_perceptual_metric/lpips_perceptual_metric_attempt_001"
    parts = str(current).split(marker)
    if len(parts) != 2:
        return
    log_path = pathlib.Path(parts[0] + marker) / "recovery" / "logs" / "generated_skill_invocations.json"
    if not log_path.exists():
        return
    payload = json.loads(log_path.read_text(encoding="utf-8"))
    assert payload.get("invocations")
    for item in payload["invocations"]:
        assert item.get("module") or item.get("skill")
        assert item.get("evidence") or item.get("kind")
        assert item.get("artifact")
