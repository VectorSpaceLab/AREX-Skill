import json
import tempfile
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from validate_distillation_run import main


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def make_module_plan(attempt: Path) -> None:
    write_json(
        attempt / "module_plan.json",
        {
            "schema_version": 1,
            "paper_id": "paper",
            "title": "Paper",
            "fast_recovery_target": {"dataset": "toy", "metric": "score", "paper_value": 1.0},
            "modules": [
                {
                    "id": "core_module",
                    "name": "Core Module",
                    "skill_name": "core-module",
                    "summary": "Core method module with deterministic behavior.",
                    "inputs": ["input"],
                    "outputs": ["output"],
                    "insight": "The test fixture exercises the validator contract.",
                    "test_strategy": "Run a deterministic smoke test for the generated skill.",
                    "evidence": ["paper"],
                }
            ],
        },
    )
    (attempt / "modules").mkdir(exist_ok=True)
    (attempt / "modules" / "core_module.md").write_text("# Core Module\n", encoding="utf-8")


def make_valid_skill_validation(attempt: Path, attempted: bool = True) -> None:
    write_json(
        attempt / "generated_skills_validation" / "core_module.json",
        {
            "ok": True,
            "errors": [],
            "warnings": [],
            "tests": {"attempted": attempted, "ok": True, "runner": "simple"},
        },
    )


def make_recovery_artifacts(attempt: Path, prepare_stage: str = "complete", runtime_handoff: dict | None = None) -> None:
    write_json(
        attempt / "run_manifest.json",
        {
            "iteration_budget": 10,
            "recovery_mode": "soft",
            "stages": {"prepare_environment": prepare_stage},
        },
    )
    (attempt / "paper_profile.md").write_text("# Paper\n", encoding="utf-8")
    make_module_plan(attempt)
    make_valid_skill_validation(attempt)
    write_json(attempt / "environment" / "runtime_handoff.json", runtime_handoff or {"models": {"preferred_ready": False}})
    write_json(attempt / "environment" / "logs" / "command_log.json", {"commands": []})
    (attempt / "recovery" / "experiment_plan.md").parent.mkdir(parents=True, exist_ok=True)
    (attempt / "recovery" / "experiment_plan.md").write_text("# Plan\n", encoding="utf-8")
    write_json(
        attempt / "recovery" / "logs" / "experiment_command_log.json",
        {"commands": [{"command": "python recovery/run.py", "returncode": 0, "status": "completed"}]},
    )
    write_json(
        attempt / "recovery" / "logs" / "generated_skill_invocations.json",
        {"invocations": [{"module": "core_module", "evidence": "called script"}]},
    )
    write_json(
        attempt / "recovery" / "recovery_result.json",
        {"is_proxy": False, "metrics": {"score": 1.0}, "commands": ["python recovery/run.py"], "mechanism_checks": {}},
    )
    write_json(
        attempt / "recovery" / "source_manifest.json",
        {"forbidden_sources_detected": [], "sources": ["environment/runtime_handoff.json"]},
    )


def test_validate_distillation_run_accepts_matching_run_config_budget():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        attempt = root / "attempt"
        attempt.mkdir()
        write_json(attempt / "run_manifest.json", {"iteration_budget": 10, "recovery_mode": "hard"})
        write_json(
            attempt / "run_config.normalized.json",
            {
                "workspace_root": str(root),
                "paper_slug": "paper",
                "paper_source": "/tmp/paper.pdf",
                "iteration_budget": 10,
                "recovery_mode": "hard",
            },
        )

        with redirect_stdout(StringIO()):
            rc = main([str(attempt), "--stage", "initialized"])

        assert rc == 0


def test_validate_distillation_run_rejects_run_config_budget_mismatch():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        attempt = root / "attempt"
        attempt.mkdir()
        write_json(attempt / "run_manifest.json", {"iteration_budget": 10, "recovery_mode": "hard"})
        write_json(
            attempt / "run_config.normalized.json",
            {
                "workspace_root": str(root),
                "paper_slug": "paper",
                "paper_source": "/tmp/paper.pdf",
                "iteration_budget": 3,
                "recovery_mode": "hard",
            },
        )

        with redirect_stdout(StringIO()):
            rc = main([str(attempt), "--stage", "initialized"])

        assert rc == 2


def test_validate_distillation_run_requires_generated_skill_tests_for_skills_stage():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        attempt = root / "attempt"
        attempt.mkdir()
        write_json(attempt / "run_manifest.json", {"iteration_budget": 10, "recovery_mode": "hard"})
        (attempt / "paper_profile.md").write_text("# Paper\n", encoding="utf-8")
        make_module_plan(attempt)
        make_valid_skill_validation(attempt, attempted=False)

        with redirect_stdout(StringIO()):
            rc = main([str(attempt), "--stage", "skills"])

        assert rc == 2


def test_validate_distillation_run_recovered_requires_prepare_environment_gate():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        attempt = root / "attempt"
        attempt.mkdir()
        make_recovery_artifacts(attempt, prepare_stage="pending")

        with redirect_stdout(StringIO()):
            rc = main([str(attempt), "--stage", "recovered"])

        assert rc == 2


def test_validate_distillation_run_recovered_accepts_prepared_environment_and_tests():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        attempt = root / "attempt"
        attempt.mkdir()
        make_recovery_artifacts(attempt, prepare_stage="blocked")

        with redirect_stdout(StringIO()):
            rc = main([str(attempt), "--stage", "recovered"])

        assert rc == 0


def test_validate_distillation_run_rejects_recovery_that_ignores_private_python():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        attempt = root / "attempt"
        attempt.mkdir()
        private_python = str(root / "envs" / "paper-recovery-paper" / "bin" / "python")
        make_recovery_artifacts(
            attempt,
            prepare_stage="complete",
            runtime_handoff={
                "python": {
                    "executable": private_python,
                    "host_executable": "/shared/conda/bin/python",
                },
                "environment": {
                    "manager": "venv",
                    "python": private_python,
                    "prefix": str(root / "envs" / "paper-recovery-paper"),
                },
                "models": {"preferred_ready": False},
            },
        )

        with redirect_stdout(StringIO()):
            rc = main([str(attempt), "--stage", "recovered"])

        assert rc == 2


def test_validate_distillation_run_reported_requires_final_report_artifacts():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        attempt = root / "attempt"
        attempt.mkdir()
        make_recovery_artifacts(attempt)
        (attempt / "analysis").mkdir(exist_ok=True)
        write_json(attempt / "analysis" / "analysis_report.json", {"decision": "accept"})
        (attempt / "analysis" / "feedback.md").write_text("accepted\n", encoding="utf-8")
        write_json(attempt / "final_validation.json", {"ok": True})

        with redirect_stdout(StringIO()):
            rc = main([str(attempt), "--stage", "reported"])

        assert rc == 2


def test_validate_distillation_run_rejects_run_config_recovery_mode_mismatch():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        attempt = root / "attempt"
        attempt.mkdir()
        write_json(attempt / "run_manifest.json", {"iteration_budget": 10, "recovery_mode": "hard"})
        write_json(
            attempt / "run_config.normalized.json",
            {
                "workspace_root": str(root),
                "paper_slug": "paper",
                "paper_source": "/tmp/paper.pdf",
                "iteration_budget": 10,
                "recovery_mode": "soft",
            },
        )

        with redirect_stdout(StringIO()):
            rc = main([str(attempt), "--stage", "initialized"])

        assert rc == 2


def test_validate_distillation_run_rejects_missing_packages_without_install_attempts():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        attempt = root / "attempt"
        attempt.mkdir()
        make_recovery_artifacts(
            attempt,
            prepare_stage="blocked",
            runtime_handoff={
                "packages": {"torch": False, "transformers": False},
                "environment_mutation_allowed": True,
                "environment": {
                    "manager": "current",
                    "setup": {
                        "actions": [],
                        "blockers": ["packages still missing after environment preparation"],
                    },
                },
                "models": {"preferred_ready": False},
            },
        )

        buffer = StringIO()
        with redirect_stdout(buffer):
            rc = main([str(attempt), "--stage", "recovered"])

        assert rc == 2
        result = json.loads(buffer.getvalue())
        assert any("isolated environment creation/reuse" in error for error in result["errors"])
        assert any("missing package 'torch'" in error for error in result["errors"])


def test_validate_distillation_run_rejects_isolated_env_constraint_without_env_attempt():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        attempt = root / "attempt"
        attempt.mkdir()
        make_recovery_artifacts(
            attempt,
            prepare_stage="blocked",
            runtime_handoff={
                "packages": {"sys": True},
                "environment": {"manager": "current", "setup": {"actions": [], "blockers": []}},
                "models": {"preferred_ready": False},
            },
        )
        write_json(
            attempt / "run_config.normalized.json",
            {
                "workspace_root": str(root),
                "paper_slug": "paper",
                "paper_source": "/tmp/paper.pdf",
                "iteration_budget": 10,
                "recovery_mode": "soft",
                "runtime_constraints": "Do not mutate shared conda envs; use isolated env only.",
            },
        )

        buffer = StringIO()
        with redirect_stdout(buffer):
            rc = main([str(attempt), "--stage", "recovered"])

        assert rc == 2
        result = json.loads(buffer.getvalue())
        assert any("runtime constraints require an isolated recovery env" in error for error in result["errors"])


def test_validate_distillation_run_rejects_missing_model_without_download_or_user_request():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        attempt = root / "attempt"
        attempt.mkdir()
        make_recovery_artifacts(
            attempt,
            prepare_stage="blocked",
            runtime_handoff={
                "packages": {"torch": True, "transformers": True, "huggingface_hub": True},
                "environment": {"manager": "current", "setup": {"actions": [], "blockers": []}},
                "models": {
                    "required": True,
                    "preferred": "Qwen/QwQ-32B",
                    "preferred_ready": False,
                    "cache_hits": [],
                    "download": {"attempted": False, "blockers": []},
                    "blockers": ["no local model cache hit"],
                },
            },
        )

        buffer = StringIO()
        with redirect_stdout(buffer):
            rc = main([str(attempt), "--stage", "recovered"])

        assert rc == 2
        result = json.loads(buffer.getvalue())
        assert any("required model is unavailable" in error for error in result["errors"])


def test_validate_distillation_run_rejects_required_dataset_url_without_download_attempt():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        attempt = root / "attempt"
        attempt.mkdir()
        make_recovery_artifacts(
            attempt,
            prepare_stage="blocked",
            runtime_handoff={
                "packages": {"sys": True},
                "environment": {"manager": "current", "setup": {"actions": [], "blockers": []}},
                "models": {"preferred_ready": False},
                "datasets": {
                    "AIME2024": {
                        "required": True,
                        "paths": [],
                        "urls": ["https://example.invalid/aime.jsonl"],
                        "download_attempted": False,
                        "downloaded_files": [],
                    }
                },
            },
        )

        buffer = StringIO()
        with redirect_stdout(buffer):
            rc = main([str(attempt), "--stage", "recovered"])

        assert rc == 2
        result = json.loads(buffer.getvalue())
        assert any("required dataset 'AIME2024'" in error for error in result["errors"])
