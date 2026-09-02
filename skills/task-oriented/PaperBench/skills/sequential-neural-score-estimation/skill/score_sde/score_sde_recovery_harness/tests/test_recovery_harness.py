import importlib.util
import json
import pathlib
import shutil
import tempfile

MODULE = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "run_recovery.py"
skills_root = pathlib.Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("run_recovery", MODULE)
run_recovery = importlib.util.module_from_spec(spec)
spec.loader.exec_module(run_recovery)


def test_recovery_harness_writes_core_artifacts():
    with tempfile.TemporaryDirectory() as tmp:
        attempt = pathlib.Path(tmp) / "attempt"
        attempt.mkdir()
        source_attempt = pathlib.Path(__file__).resolve().parents[5] / "skill_distillation" / "score_sde" / "score_sde_attempt_001"
        if not source_attempt.exists():
            source_attempt = pathlib.Path("/share/project/yuyang/workspace/Paperbench/record/case1/skill_distillation/score_sde/score_sde_attempt_001")
        shutil.copy(source_attempt / "module_plan.json", attempt / "module_plan.json")
        (attempt / "modules").mkdir()
        (attempt / "paper_profile.md").write_text("profile", encoding="utf-8")
        (attempt / "paper_text.txt").write_text("paper", encoding="utf-8")
        (attempt / "environment").mkdir()
        (attempt / "environment" / "runtime_handoff.json").write_text(json.dumps({"environment_modified": False}), encoding="utf-8")
        result = run_recovery.run_recovery(attempt, skills_root)
        assert result["is_proxy"] is True
        assert result["mechanism_checks"]["loss_decreased"] is True
        assert (attempt / "recovery" / "recovery_result.json").exists()
        assert (attempt / "recovery" / "logs" / "generated_skill_invocations.json").exists()
