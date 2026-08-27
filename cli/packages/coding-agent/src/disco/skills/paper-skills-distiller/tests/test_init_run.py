import json
import os
import tempfile
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from init_run import DEFAULT_ITERATION_BUDGET, main


def test_init_run_records_default_iteration_budget():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        paper = root / "paper.txt"
        paper.write_text("paper", encoding="utf-8")

        with redirect_stdout(StringIO()):
            rc = main(
                [
                    "--paper",
                    str(paper),
                    "--slug",
                    "My Paper",
                    "--test-root",
                    str(root / "test"),
                    "--skills-root",
                    str(root / "skills"),
                    "--distiller-skills-root",
                    str(root / "Distiller" / "skills"),
                ]
            )

        manifest = json.loads((root / "test" / "distillation" / "run_manifest.json").read_text(encoding="utf-8"))
        assert rc == 0
        assert manifest["iteration_budget"] == DEFAULT_ITERATION_BUDGET == 10
        assert manifest["recovery_mode"] == "hard"


def test_init_run_allows_iteration_budget_override():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        paper = root / "paper.txt"
        paper.write_text("paper", encoding="utf-8")

        with redirect_stdout(StringIO()):
            rc = main(
                [
                    "--paper",
                    str(paper),
                    "--slug",
                    "paper",
                    "--test-root",
                    str(root / "test"),
                    "--skills-root",
                    str(root / "skills"),
                    "--distiller-skills-root",
                    str(root / "Distiller" / "skills"),
                    "--iteration-budget",
                    "3",
                ]
            )

        manifest = json.loads((root / "test" / "distillation" / "run_manifest.json").read_text(encoding="utf-8"))
        assert rc == 0
        assert manifest["iteration_budget"] == 3


def test_init_run_allows_recovery_mode_override():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        paper = root / "paper.txt"
        paper.write_text("paper", encoding="utf-8")

        with redirect_stdout(StringIO()):
            rc = main(
                [
                    "--paper",
                    str(paper),
                    "--slug",
                    "paper",
                    "--test-root",
                    str(root / "test"),
                    "--skills-root",
                    str(root / "skills"),
                    "--distiller-skills-root",
                    str(root / "Distiller" / "skills"),
                    "--recovery-mode",
                    "soft",
                ]
            )

        manifest = json.loads((root / "test" / "distillation" / "run_manifest.json").read_text(encoding="utf-8"))
        assert rc == 0
        assert manifest["recovery_mode"] == "soft"


def test_init_run_copies_normalized_run_config():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        paper = root / "paper.txt"
        paper.write_text("paper", encoding="utf-8")
        run_config = root / "run.normalized.json"
        run_config.write_text('{"paper_slug": "paper", "iteration_budget": 5}\n', encoding="utf-8")

        with redirect_stdout(StringIO()):
            rc = main(
                [
                    "--paper",
                    str(paper),
                    "--slug",
                    "paper",
                    "--test-root",
                    str(root / "test"),
                    "--skills-root",
                    str(root / "skills"),
                    "--distiller-skills-root",
                    str(root / "Distiller" / "skills"),
                    "--run-config",
                    str(run_config),
                ]
            )

        copied = json.loads((root / "test" / "distillation" / "run_config.normalized.json").read_text(encoding="utf-8"))
        assert rc == 0
        assert copied["paper_slug"] == "paper"
        assert copied["iteration_budget"] == 5


def test_init_run_accepts_exact_attempt_and_generated_skills_dirs():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        paper = root / "paper.txt"
        paper.write_text("paper", encoding="utf-8")
        attempt_dir = root / "custom_attempt"
        generated_skills_root = root / "custom_skills" / "paper"

        with redirect_stdout(StringIO()):
            rc = main(
                [
                    "--paper",
                    str(paper),
                    "--slug",
                    "paper",
                    "--test-root",
                    str(root / "test"),
                    "--skills-root",
                    str(root / "skills"),
                    "--generated-skills-root",
                    str(generated_skills_root),
                    "--distiller-skills-root",
                    str(root / "Distiller" / "skills"),
                    "--attempt-dir",
                    str(attempt_dir),
                ]
            )

        manifest = json.loads((attempt_dir / "run_manifest.json").read_text(encoding="utf-8"))
        assert rc == 0
        assert manifest["attempt_dir"] == str(attempt_dir.resolve())
        assert manifest["generated_skills_root"] == str(generated_skills_root.resolve())
        assert manifest["paper_skill_root"] == str(generated_skills_root.resolve())


def test_init_run_defaults_to_flat_run_tree():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        paper = root / "paper.txt"
        paper.write_text("paper", encoding="utf-8")
        old_cwd = Path.cwd()
        os.chdir(root)
        try:
            with redirect_stdout(StringIO()):
                rc = main(
                    [
                        "--paper",
                        str(paper),
                        "--slug",
                        "My Paper",
                        "--distiller-skills-root",
                        str(root / "bundled" / "skills"),
                    ]
                )
        finally:
            os.chdir(old_cwd)

        attempt = root / "my_paper" / "distillation"
        manifest = json.loads((attempt / "run_manifest.json").read_text(encoding="utf-8"))
        assert rc == 0
        assert manifest["run_root"] == str(root / "my_paper")
        assert manifest["attempt_dir"] == str(root / "my_paper" / "distillation")
        assert manifest["distillation_root"] == str(root / "my_paper" / "distillation")
        assert manifest["generated_skills_root"] == str(root / "my_paper" / "skills")
        assert (root / "my_paper" / "skills").is_dir()
        assert (attempt / "reports" / "generated-skills").is_dir()
        assert (attempt / "reports" / "verification").is_dir()
        assert (attempt / "reports" / "final").is_dir()
        assert not (root / "Distiller").exists()
