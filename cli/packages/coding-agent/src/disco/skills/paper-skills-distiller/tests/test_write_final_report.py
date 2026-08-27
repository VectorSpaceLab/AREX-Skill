import json
import tempfile
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from write_final_report import main


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def test_write_final_report_creates_organized_json_and_markdown():
    with tempfile.TemporaryDirectory() as tmp:
        attempt = Path(tmp)
        write_json(
            attempt / "run_manifest.json",
            {"slug": "paper", "generated_skills_root": str(attempt / "skills"), "recovery_mode": "soft"},
        )
        write_json(
            attempt / "run_config.normalized.json",
            {"language_preference": "Chinese summary", "paper_slug": "paper"},
        )
        write_json(
            attempt / "module_plan.json",
            {
                "paper_id": "paper",
                "fast_recovery_target": {"dataset": "toy", "metric": "score", "paper_value": 1.0},
                "modules": [{"id": "core_module", "skill_name": "core-module"}],
            },
        )
        write_json(
            attempt / "generated_skills_validation" / "core_module.json",
            {"ok": True, "warnings": [], "errors": [], "tests": {"attempted": True, "ok": True}},
        )
        write_json(attempt / "environment" / "runtime_handoff.json", {"blockers": []})
        write_json(attempt / "environment" / "logs" / "command_log.json", {"commands": []})
        write_json(
            attempt / "recovery" / "recovery_result.json",
            {"is_proxy": True, "metrics": {"score": 1.0}, "paper_target": {"metric": "score"}},
        )
        write_json(attempt / "recovery" / "experiment_validation.json", {"ok": True, "errors": []})
        write_json(attempt / "analysis" / "analysis_report.json", {"decision": "accept", "feedback": []})
        write_json(attempt / "final_validation.json", {"ok": True, "errors": [], "warnings": [], "missing": []})

        with redirect_stdout(StringIO()):
            rc = main([str(attempt)])

        report_json = attempt / "reports" / "final" / "final_report.json"
        report_md = attempt / "reports" / "final" / "final_report.md"
        report = json.loads(report_json.read_text(encoding="utf-8"))
        assert rc == 0
        assert report["ok"] is True
        assert report["distillation_dir"] == str(attempt.resolve())
        assert report["module_skill_validations"][0]["tests_attempted"] is True
        markdown = report_md.read_text(encoding="utf-8")
        assert "Paper2Skills 最终报告" in markdown
        assert "Distillation directory" in markdown
        assert "Attempt:" not in markdown
