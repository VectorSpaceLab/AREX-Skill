import tempfile
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from read_run_config import DEFAULT_ITERATION_BUDGET, main, normalize_config


def test_read_run_config_applies_defaults_and_computed_paths():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        config = root / "run.toml"
        config.write_text(
            f"""
schema_version = 1

[defaults]
workspace_root = "{root}"
iteration_budget = 10
runtime_constraints = "default runtime"

[[runs]]
paper_slug = "My Paper"
paper_source = "https://arxiv.org/abs/2604.10674"
original_repo_source = "none"
""",
            encoding="utf-8",
        )

        runs, errors = normalize_config(config)

        assert errors == []
        assert len(runs) == 1
        assert runs[0]["paper_slug"] == "my_paper"
        assert runs[0]["iteration_budget"] == DEFAULT_ITERATION_BUDGET == 10
        assert runs[0]["recovery_mode"] == "hard"
        assert runs[0]["repo_discovery_mode"] == "ask"
        assert runs[0]["run_root"] == str(root / "my_paper")
        assert runs[0]["distillation_root"] == str(root / "my_paper" / "distillation")
        assert runs[0]["test_root"] == str(root / "my_paper")
        assert runs[0]["skills_root"] == str(root / "my_paper" / "skills")
        assert runs[0]["generated_skills_root"] == str(root / "my_paper" / "skills")
        assert runs[0]["attempt_dir"] == str(root / "my_paper" / "distillation")
        assert runs[0]["paper_cache_dir"] == str(root / "my_paper" / "distillation" / "source")
        assert runs[0]["source_resolution_path"] == str(
            root / "my_paper" / "distillation" / "source" / "source_resolution.json"
        )
        assert runs[0]["runtime_constraints"] == "default runtime"


def test_read_run_config_allows_run_overrides_and_slug_selection():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        config = root / "run.toml"
        config.write_text(
            f"""
schema_version = 1

[defaults]
workspace_root = "{root}"
iteration_budget = 10
language_preference = "Chinese summary"

[[runs]]
paper_slug = "first"
paper_source = "/tmp/first.pdf"

[[runs]]
paper_slug = "second"
paper_source = "/tmp/second.pdf"
iteration_budget = 3
recovery_mode = "soft"
repo_discovery_mode = "auto"
language_preference = "English summary"
""",
            encoding="utf-8",
        )

        runs, errors = normalize_config(config, selector_slug="second")

        assert errors == []
        assert len(runs) == 1
        assert runs[0]["paper_slug"] == "second"
        assert runs[0]["iteration_budget"] == 3
        assert runs[0]["recovery_mode"] == "soft"
        assert runs[0]["repo_discovery_mode"] == "auto"
        assert runs[0]["language_preference"] == "English summary"


def test_read_run_config_rejects_missing_required_fields():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        config = root / "run.toml"
        config.write_text(
            """
schema_version = 1

[defaults]
iteration_budget = -1

[[runs]]
paper_slug = "bad"
""",
            encoding="utf-8",
        )

        runs, errors = normalize_config(config)

        assert len(runs) == 1
        assert any("workspace_root is required" in error for error in errors)
        assert any("paper_source is required" in error for error in errors)
        assert any("iteration_budget must be a non-negative integer" in error for error in errors)


def test_read_run_config_rejects_invalid_recovery_mode():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        config = root / "run.toml"
        config.write_text(
            f"""
schema_version = 1

[defaults]
workspace_root = "{root}"

[[runs]]
paper_slug = "paper"
paper_source = "/tmp/paper.pdf"
recovery_mode = "medium"
""",
            encoding="utf-8",
        )

        runs, errors = normalize_config(config)

        assert len(runs) == 1
        assert runs[0]["recovery_mode"] == "hard"
        assert any("recovery_mode must be 'hard' or 'soft'" in error for error in errors)


def test_read_run_config_rejects_invalid_repo_discovery_mode():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        config = root / "run.toml"
        config.write_text(
            f"""
schema_version = 1

[defaults]
workspace_root = "{root}"

[[runs]]
paper_slug = "paper"
paper_source = "/tmp/paper.pdf"
repo_discovery_mode = "always"
""",
            encoding="utf-8",
        )

        runs, errors = normalize_config(config)

        assert len(runs) == 1
        assert runs[0]["repo_discovery_mode"] == "ask"
        assert any("repo_discovery_mode must be 'ask', 'auto', or 'disabled'" in error for error in errors)


def test_read_run_config_run_only_writes_selected_run_json():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        config = root / "run.toml"
        output = root / "selected.json"
        config.write_text(
            f"""
schema_version = 1

[defaults]
workspace_root = "{root}"

[[runs]]
paper_slug = "first"
paper_source = "/tmp/first.pdf"

[[runs]]
paper_slug = "second"
paper_source = "/tmp/second.pdf"
""",
            encoding="utf-8",
        )

        with redirect_stdout(StringIO()):
            rc = main([str(config), "--slug", "second", "--run-only", "--output", str(output)])

        selected = __import__("json").loads(output.read_text(encoding="utf-8"))
        assert rc == 0
        assert selected["paper_slug"] == "second"
        assert "runs" not in selected
