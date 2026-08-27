#!/usr/bin/env python3
"""Suggest SimpleTuner unittest/Jest/E2E targets for changed paths.

This helper is read-only. It never suggests pytest and does not print raw input
paths, so accidental absolute local paths are not echoed back into validation
notes.
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Iterable

PYTHON = ".venv/bin/python"
UNITTEST = f"{PYTHON} -m unittest -v -f"


@dataclass(frozen=True)
class AreaRule:
    area: str
    patterns: tuple[str, ...]
    commands: tuple[str, ...]
    notes: tuple[str, ...] = ()


RULES: tuple[AreaRule, ...] = (
    AreaRule(
        "config",
        (
            "st_cli.py",
            "simpletuner/cli/**",
            "simpletuner/helpers/configuration/**",
            "config/**",
            "documentation/OPTIONS*.md",
            "tests/test_config*.py",
            "tests/test_loader_boolean_handling.py",
            "tests/test_parser_type_override.py",
        ),
        (
            f"{UNITTEST} tests.test_config tests.test_config_registry tests.test_config_templates tests.test_cli_environment tests.test_parser_type_override tests.test_loader_boolean_handling",
        ),
        ("Add OPTIONS documentation/translations when a public option changes.",),
    ),
    AreaRule(
        "data-and-dataloader",
        (
            "simpletuner/helpers/data_backend/**",
            "simpletuner/helpers/caching/**",
            "simpletuner/simpletuner_sdk/server/data/**",
            "simpletuner/templates/components/dataloader/**",
            "simpletuner/simpletuner_sdk/server/routes/datasets.py",
            "documentation/DATALOADER*.md",
            "documentation/data_presets/**",
            "tests/test_backend_config.py",
            "tests/test_audio_backend_config.py",
            "tests/test_dataset*.py",
            "tests/helpers/data_backend/**",
        ),
        (
            f"{UNITTEST} tests.test_backend_config tests.test_audio_backend_config tests.test_dataset_blueprints tests.test_dataset tests.test_dataset_plan tests.helpers.data_backend.test_local_files",
        ),
        (
            "Dataloader option changes also need WebUI Dataset template/blueprint coverage and DATALOADER translations.",
        ),
    ),
    AreaRule(
        "model-and-adapters",
        (
            "simpletuner/helpers/models/**",
            "simpletuner/helpers/training/lora_format.py",
            "simpletuner/helpers/models/model_metadata.json",
            "simpletuner/helpers/models/field_registry/**",
            "simpletuner/simpletuner_sdk/server/services/field_registry/**",
            "scripts/extract_*.py",
            "scripts/merge_safetensors.py",
            "tests/test_*_model.py",
            "tests/test_*_lora*.py",
            "tests/test_lora_format.py",
            "tests/test_model_field_registry.py",
            "tests/test_pipelines/**",
            "tests/test_transformers/**",
        ),
        (
            f"{UNITTEST} tests.test_model_field_registry tests.test_lora_format tests.test_extract_adapter_scripts tests.test_extract_model_metadata",
        ),
        ("Add model-family, pipeline, or transformer tests when behavior changes beyond registry metadata.",),
    ),
    AreaRule(
        "training",
        (
            "simpletuner/train.py",
            "simpletuner/helpers/training/**",
            "simpletuner/helpers/acceleration/**",
            "documentation/DEEPSPEED*.md",
            "documentation/FSDP2*.md",
            "documentation/DISTRIBUTED*.md",
            "documentation/attention/**",
            "tests/test_trainer*.py",
            "tests/test_training*.py",
            "tests/test_attention_backend.py",
            "tests/test_context_parallel*.py",
            "tests/test_fsdp_cmd_args.py",
        ),
        (
            f"{UNITTEST} tests.test_trainer tests.test_training_service tests.test_training_checkpointing tests.test_attention_backend tests.test_context_parallel_plans tests.test_fsdp_cmd_args",
        ),
        ("Do not assume checkpoint resume supports topology, shuffling, or dataloader setting changes.",),
    ),
    AreaRule(
        "webui-server-api",
        (
            "simpletuner/simpletuner_sdk/server/app.py",
            "simpletuner/simpletuner_sdk/server/webui_app.py",
            "simpletuner/simpletuner_sdk/server/routes/**",
            "simpletuner/simpletuner_sdk/server/services/**",
            "simpletuner/templates/**",
            "tests/pages/**",
            "tests/webui_test_base.py",
            "tests/test_webui_e2e.py",
            "tests/test_api_integration.py",
            "tests/test_server*.py",
            "tests/test_*routes.py",
        ),
        (
            f"{UNITTEST} tests.test_api_integration tests.test_server_modes tests.test_server_startup_integration tests.test_dataset_routes tests.test_template_rendering",
        ),
        ("Add Selenium E2E for event flow, form dirty state, Alpine reactivity, and direct-load bugs.",),
    ),
    AreaRule(
        "cloud-queue-workers",
        (
            "simpletuner/cli/cloud/**",
            "simpletuner/cli/jobs.py",
            "simpletuner/worker_agent.py",
            "simpletuner/service_worker.py",
            "simpletuner/simpletuner_sdk/server/routes/cloud/**",
            "simpletuner/simpletuner_sdk/server/services/cloud/**",
            "documentation/experimental/cloud/**",
            "documentation/experimental/server/**",
            "documentation/JOB_QUEUE*.md",
            "tests/test_cloud*.py",
            "tests/test_cli_cloud_commands.py",
            "tests/test_local_job_queue_integration.py",
            "tests/test_queue*.py",
            "tests/test_worker*.py",
        ),
        (
            f"{UNITTEST} tests.test_cli_cloud_commands tests.test_cloud_cli tests.test_cloud_services tests.test_cloud_state_paths tests.test_local_job_queue_integration tests.test_queue_routes",
        ),
        ("Keep cloud/provider calls mocked unless the user explicitly approves credentialed external operations.",),
    ),
    AreaRule(
        "javascript",
        (
            "simpletuner/static/js/**",
            "tests/js/**",
            "package.json",
            "package-lock.json",
        ),
        ("npm test",),
        ("Jest/JSDOM does not replace Selenium E2E for real browser event propagation or Alpine template wiring.",),
    ),
    AreaRule(
        "docs",
        (
            "documentation/**",
            "mkdocs.yml",
        ),
        (),
        ("Check mkDocs nav/index updates and translations: zh, ja, pt-BR, es, hi for new docs.",),
    ),
    AreaRule(
        "publishing-privacy",
        (
            "simpletuner/helpers/publishing/**",
            "simpletuner/simpletuner_sdk/server/routes/publishing.py",
            "simpletuner/simpletuner_sdk/server/services/*publishing*",
            "documentation/publishing/**",
            "tests/test_publishing*.py",
            "tests/test_model_card*.py",
        ),
        (
            f"{UNITTEST} tests.test_publishing_config_parsing tests.test_publishing_providers tests.test_publishing_service tests.test_model_card",
        ),
        ("Scan exact public text before PR/comment/release/Hub publication.",),
    ),
    AreaRule(
        "package-ci",
        (
            "pyproject.toml",
            "setup.py",
            "MANIFEST.in",
            ".github/workflows/python-tests.yaml",
        ),
        (
            f"{UNITTEST} tests.test_setup tests.test_setup_platform_dependencies",
        ),
        ("CI also runs unittest discovery and npm tests for JS changes.",),
    ),
)

E2E_GENERAL = "SIMPLETUNER_SELENIUM_TESTS=1 .venv/bin/python -m unittest -v -f tests.test_webui_e2e"
E2E_DIRTY = (
    "SIMPLETUNER_SELENIUM_TESTS=1 .venv/bin/python -m unittest -v -f "
    "tests.test_webui_e2e.FormDirtyStateFlowTestCase tests.test_webui_e2e.EasyModeFormDirtyTestCase"
)
FULL = f"{UNITTEST}"

ANCHORS = (
    "simpletuner/",
    "tests/",
    "documentation/",
    ".github/",
    "config/",
    "scripts/",
    "AGENTS.md",
    "CLAUDE.md",
    "GEMINI.md",
    "pyproject.toml",
    "setup.py",
    "MANIFEST.in",
    "mkdocs.yml",
    "package.json",
    "package-lock.json",
    "st_cli.py",
)


def _git_changed_paths() -> list[str]:
    commands = (
        ("git", "diff", "--name-only", "--cached"),
        ("git", "diff", "--name-only"),
        ("git", "ls-files", "--others", "--exclude-standard"),
    )
    found: list[str] = []
    for cmd in commands:
        try:
            completed = subprocess.run(cmd, check=False, capture_output=True, text=True, timeout=5)
        except (OSError, subprocess.SubprocessError):
            continue
        if completed.returncode == 0:
            found.extend(line.strip() for line in completed.stdout.splitlines() if line.strip())
    return sorted(dict.fromkeys(found))


def normalize_for_matching(raw: str) -> str:
    value = raw.strip().strip('"\'').replace("\\", "/")
    while value.startswith("./"):
        value = value[2:]
    for anchor in ANCHORS:
        if value == anchor.rstrip("/") or value.startswith(anchor):
            return value
        marker = "/" + anchor
        idx = value.find(marker)
        if idx >= 0:
            return value[idx + 1 :]
    if value.startswith("/"):
        return PurePosixPath(value).name
    return value


def matches(path: str, pattern: str) -> bool:
    if fnmatch.fnmatch(path, pattern):
        return True
    if pattern.endswith("/**"):
        prefix = pattern[:-3]
        return path == prefix or path.startswith(prefix + "/")
    return False


def classify(paths: Iterable[str]) -> dict[str, object]:
    normalized = [normalize_for_matching(p) for p in paths if p.strip()]
    areas: list[str] = []
    commands: list[str] = []
    notes: list[str] = []

    for rule in RULES:
        if any(matches(path, pattern) for path in normalized for pattern in rule.patterns):
            areas.append(rule.area)
            commands.extend(rule.commands)
            notes.extend(rule.notes)

    path_blob = "\n".join(normalized).lower()
    frontend_hit = any(area in areas for area in ("javascript", "webui-server-api"))
    dirty_or_event = any(token in path_blob for token in ("dirty", "ez_mode", "easy", "form", "event", "alpine", "trainer"))
    template_or_js = any(path.startswith(("simpletuner/templates/", "simpletuner/static/js/")) for path in normalized)

    if frontend_hit and dirty_or_event:
        commands.append(E2E_DIRTY)
        notes.append("Dirty-form or event-flow changes require Selenium E2E; Jest alone is insufficient.")
    elif frontend_hit and template_or_js:
        commands.append(E2E_GENERAL)
        notes.append("If this WebUI change affects event flow, formDirty, Alpine reactivity, or direct-load behavior, run Selenium E2E.")

    if not commands and not areas:
        notes.append("No specific area matched. Inspect the change manually and consider the full unittest suite.")

    commands.append(FULL)
    notes.append("Full local suite averages about 300 seconds; run it for broad or cross-cutting changes.")

    return {
        "path_count": len(normalized),
        "areas": sorted(dict.fromkeys(areas)),
        "commands": list(dict.fromkeys(commands)),
        "notes": list(dict.fromkeys(notes)),
    }


def render_text(result: dict[str, object]) -> str:
    lines = ["SimpleTuner test target suggestions", ""]
    lines.append(f"Changed paths considered: {result['path_count']}")
    areas = result.get("areas") or []
    lines.append("Matched areas: " + (", ".join(areas) if areas else "none"))
    lines.append("")
    lines.append("Suggested commands:")
    for command in result["commands"]:  # type: ignore[index]
        lines.append(f"- {command}")
    lines.append("")
    lines.append("Notes:")
    for note in result["notes"]:  # type: ignore[index]
        lines.append(f"- {note}")
    lines.append("- Do not use pytest for SimpleTuner validation.")
    lines.append("- Preserve untracked files and do not commit or push unless explicitly asked.")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Suggest focused SimpleTuner unittest, Jest, and Selenium E2E commands for changed files.",
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help="Changed paths. If omitted, the helper reads git changed/untracked paths from the current repository.",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON without raw path names.")
    args = parser.parse_args(argv)

    paths = args.paths or _git_changed_paths()
    result = classify(paths)
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(render_text(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
