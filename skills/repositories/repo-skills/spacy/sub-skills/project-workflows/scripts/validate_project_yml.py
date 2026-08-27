#!/usr/bin/env python3
"""Validate a spaCy project.yml file without network access.

The check is intentionally local only: it inspects project structure, command and
workflow names, path references, and remote-risk signals. It does not clone
repos, fetch assets, push outputs, or contact any remote storage.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any, Iterable, List, Sequence, Tuple

import spacy
import srsly

try:
    from packaging.requirements import Requirement
    from packaging.specifiers import SpecifierSet
    from packaging.version import Version
except Exception:  # pragma: no cover - fallback for minimal environments
    Requirement = None  # type: ignore[assignment]
    SpecifierSet = None  # type: ignore[assignment]
    Version = None  # type: ignore[assignment]

PROJECT_FILENAMES = ("project.yml", "project.yaml")
TOP_LEVEL_KEYS = {
    "title",
    "description",
    "vars",
    "env",
    "directories",
    "assets",
    "commands",
    "workflows",
    "remotes",
    "spacy_version",
    "check_requirements",
}
COMMAND_KEYS = {
    "name",
    "help",
    "script",
    "deps",
    "outputs",
    "outputs_no_cache",
    "no_skip",
}
ASSET_KEYS = {
    "dest",
    "url",
    "git",
    "checksum",
    "extra",
    "description",
}


def is_url(value: str) -> bool:
    return bool(re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", value))


def is_absolute_like(value: str) -> bool:
    path = Path(value)
    if path.is_absolute():
        return True
    return bool(re.match(r"^[A-Za-z]:[\\/]", value))


def has_parent_segments(value: str) -> bool:
    return any(part == ".." for part in Path(value).parts)


def coerce_sequence(
    value: Any,
    *,
    location: str,
    issues: List[Tuple[str, str]],
    allow_scalar: bool = False,
) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if allow_scalar and isinstance(value, str):
        issues.append(
            (
                "warning",
                f"{location} should be a list; treating the single string as one item.",
            )
        )
        return [value]
    issues.append(("error", f"{location} must be a list."))
    return []


def add_issue(
    issues: List[Tuple[str, str]], severity: str, message: str
) -> None:
    issues.append((severity, message))


def load_project_file(raw_path: str) -> Tuple[Path, Path, Any]:
    path = Path(raw_path).expanduser()
    if path.is_dir():
        for filename in PROJECT_FILENAMES:
            candidate = path / filename
            if candidate.is_file():
                path = candidate
                break
        else:
            raise FileNotFoundError(
                f"No project.yml or project.yaml found in {path}"
            )
    elif not path.is_file():
        raise FileNotFoundError(f"Project file not found: {path}")

    data = srsly.read_yaml(path)
    if data is None:
        data = {}
    if not isinstance(data, dict):
        raise TypeError("The project file must parse to a mapping/object.")
    return path, path.parent, data


def validate_paths(
    values: Sequence[Any], *, location: str, issues: List[Tuple[str, str]]
) -> None:
    for index, value in enumerate(values):
        item_location = f"{location}[{index}]"
        if not isinstance(value, str) or not value.strip():
            add_issue(issues, "error", f"{item_location} must be a non-empty string.")
            continue
        if is_absolute_like(value):
            add_issue(
                issues,
                "warning",
                f"{item_location} uses an absolute path; project files work best with relative paths.",
            )
        if has_parent_segments(value):
            add_issue(
                issues,
                "warning",
                f"{item_location} contains '..' segments and may escape the project tree.",
            )


def validate_assets(project_dir: Path, assets: Any, issues: List[Tuple[str, str]]) -> None:
    asset_items = coerce_sequence(assets, location="assets", issues=issues)
    for index, asset in enumerate(asset_items):
        location = f"assets[{index}]"
        if not isinstance(asset, dict):
            add_issue(issues, "error", f"{location} must be a mapping/object.")
            continue

        unknown = sorted(set(asset) - ASSET_KEYS)
        if unknown:
            add_issue(
                issues,
                "warning",
                f"{location} contains unrecognized keys: {', '.join(unknown)}.",
            )

        dest = asset.get("dest")
        if not isinstance(dest, str) or not dest.strip():
            add_issue(issues, "error", f"{location}.dest must be a non-empty string.")
        else:
            validate_paths([dest], location=f"{location}.dest", issues=issues)

        url = asset.get("url")
        git = asset.get("git")
        has_url = isinstance(url, str) and bool(url.strip())
        has_git = isinstance(git, dict)

        if url is not None and not has_url:
            add_issue(issues, "error", f"{location}.url must be a non-empty string.")

        if git is not None and not has_git:
            add_issue(issues, "error", f"{location}.git must be a mapping/object.")

        if has_url and has_git:
            add_issue(
                issues,
                "warning",
                f"{location} defines both url and git; keep a single source of truth.",
            )

        if has_url:
            if is_url(url):
                add_issue(
                    issues,
                    "warning",
                    f"{location} uses a network URL; asset fetching may need network access or credentials.",
                )
            else:
                local_source = (project_dir / url).expanduser()
                if not local_source.exists():
                    add_issue(
                        issues,
                        "warning",
                        f"{location}.url points to a local path that does not exist yet.",
                    )

        if has_git:
            repo = git.get("repo")
            path = git.get("path")
            branch = git.get("branch", "master")
            if not isinstance(repo, str) or not repo.strip():
                add_issue(issues, "error", f"{location}.git.repo must be a non-empty string.")
            if not isinstance(path, str):
                add_issue(issues, "error", f"{location}.git.path must be a string.")
            elif is_absolute_like(path) or has_parent_segments(path):
                add_issue(
                    issues,
                    "warning",
                    f"{location}.git.path should stay within the remote repo and avoid absolute or parent paths.",
                )
            if branch is not None and not isinstance(branch, str):
                add_issue(issues, "warning", f"{location}.git.branch should be a string.")
            add_issue(
                issues,
                "warning",
                f"{location} is Git-backed; fetching it may require network access, repo permissions, and sparse-checkout support.",
            )

        extra = asset.get("extra")
        if extra not in (None, False) and not isinstance(extra, bool):
            add_issue(issues, "error", f"{location}.extra must be a boolean.")
        elif extra:
            add_issue(
                issues,
                "warning",
                f"{location} is opt-in and will only download when project assets runs with --extra.",
            )

        checksum = asset.get("checksum")
        if checksum is not None and not isinstance(checksum, str):
            add_issue(issues, "error", f"{location}.checksum must be a string when provided.")
        if not has_url and not has_git:
            if checksum is None:
                add_issue(
                    issues,
                    "warning",
                    f"{location} has no url or git source and no checksum; it is a private/local placeholder.",
                )
            else:
                add_issue(
                    issues,
                    "warning",
                    f"{location} is a private/local asset placeholder; place the file locally before running assets.",
                )


def validate_commands(commands: Any, issues: List[Tuple[str, str]]) -> List[str]:
    command_items = coerce_sequence(commands, location="commands", issues=issues)
    names: List[str] = []
    seen = set()
    for index, command in enumerate(command_items):
        location = f"commands[{index}]"
        if not isinstance(command, dict):
            add_issue(issues, "error", f"{location} must be a mapping/object.")
            continue

        unknown = sorted(set(command) - COMMAND_KEYS)
        if unknown:
            add_issue(
                issues,
                "warning",
                f"{location} contains unrecognized keys: {', '.join(unknown)}.",
            )

        name = command.get("name")
        if not isinstance(name, str) or not name.strip():
            add_issue(issues, "error", f"{location}.name must be a non-empty string.")
            continue
        if name in seen:
            add_issue(issues, "error", f"Command name '{name}' is duplicated.")
        seen.add(name)
        names.append(name)

        help_text = command.get("help")
        if help_text is not None and not isinstance(help_text, str):
            add_issue(issues, "warning", f"{location}.help should be a string.")

        script = coerce_sequence(
            command.get("script"),
            location=f"{location}.script",
            issues=issues,
            allow_scalar=True,
        )
        if not script:
            add_issue(issues, "error", f"{location}.script must contain at least one step.")
        else:
            for step_index, step in enumerate(script):
                if not isinstance(step, str) or not step.strip():
                    add_issue(
                        issues,
                        "error",
                        f"{location}.script[{step_index}] must be a non-empty string.",
                    )

        deps = coerce_sequence(
            command.get("deps"), location=f"{location}.deps", issues=issues, allow_scalar=True
        )
        if deps:
            validate_paths(deps, location=f"{location}.deps", issues=issues)

        outputs = coerce_sequence(
            command.get("outputs"),
            location=f"{location}.outputs",
            issues=issues,
            allow_scalar=True,
        )
        if outputs:
            validate_paths(outputs, location=f"{location}.outputs", issues=issues)
        else:
            add_issue(
                issues,
                "warning",
                f"{location} has no outputs; it will never be skipped.",
            )

        outputs_no_cache = coerce_sequence(
            command.get("outputs_no_cache"),
            location=f"{location}.outputs_no_cache",
            issues=issues,
            allow_scalar=True,
        )
        if outputs_no_cache:
            validate_paths(
                outputs_no_cache, location=f"{location}.outputs_no_cache", issues=issues
            )

        no_skip = command.get("no_skip")
        if no_skip is not None and not isinstance(no_skip, bool):
            add_issue(issues, "error", f"{location}.no_skip must be a boolean.")

    return names


def validate_workflows(
    workflows: Any, command_names: Sequence[str], issues: List[Tuple[str, str]]
) -> None:
    workflow_map = workflows or {}
    if not isinstance(workflow_map, dict):
        add_issue(issues, "error", "workflows must be a mapping/object.")
        return

    for workflow_name, steps in workflow_map.items():
        location = f"workflows.{workflow_name}"
        if not isinstance(workflow_name, str) or not workflow_name.strip():
            add_issue(issues, "error", "Workflow names must be non-empty strings.")
            continue
        if workflow_name in command_names:
            add_issue(
                issues,
                "error",
                f"Workflow name '{workflow_name}' must not shadow a command name.",
            )
        workflow_steps = coerce_sequence(
            steps, location=location, issues=issues, allow_scalar=True
        )
        if not workflow_steps:
            add_issue(issues, "warning", f"{location} is empty.")
        for step_index, step in enumerate(workflow_steps):
            if not isinstance(step, str) or not step.strip():
                add_issue(
                    issues,
                    "error",
                    f"{location}[{step_index}] must be a non-empty string.",
                )
            elif step not in command_names:
                add_issue(
                    issues,
                    "error",
                    f"{location}[{step_index}] references unknown command '{step}'.",
                )


def validate_remotes(remotes: Any, issues: List[Tuple[str, str]]) -> None:
    remote_map = remotes or {}
    if not isinstance(remote_map, dict):
        add_issue(issues, "error", "remotes must be a mapping/object.")
        return

    for remote_name, remote_target in remote_map.items():
        location = f"remotes.{remote_name}"
        if not isinstance(remote_name, str) or not remote_name.strip():
            add_issue(issues, "error", "Remote names must be non-empty strings.")
            continue
        if not isinstance(remote_target, str) or not remote_target.strip():
            add_issue(issues, "error", f"{location} must be a non-empty string.")
            continue
        if is_url(remote_target):
            add_issue(
                issues,
                "warning",
                f"{location} points to networked storage; push and pull may need credentials or protocol dependencies.",
            )
        elif is_absolute_like(remote_target):
            add_issue(
                issues,
                "warning",
                f"{location} uses a local absolute path; confirm the storage location is reachable on this machine.",
            )


def validate_requirements(
    project_dir: Path, data: dict[str, Any], issues: List[Tuple[str, str]]
) -> None:
    spacy_version = data.get("spacy_version")
    if spacy_version is not None:
        if not isinstance(spacy_version, str) or not spacy_version.strip():
            add_issue(issues, "error", "spacy_version must be a non-empty string when provided.")
        elif SpecifierSet is None or Version is None:
            add_issue(
                issues,
                "warning",
                "spacy_version is present, but packaging is unavailable so the version specifier was not checked.",
            )
        else:
            try:
                spec = SpecifierSet(spacy_version)
            except Exception as exc:
                add_issue(issues, "error", f"spacy_version is not a valid version specifier: {exc}")
            else:
                if Version(spacy.__version__) not in spec:
                    add_issue(
                        issues,
                        "error",
                        f"Installed spaCy {spacy.__version__} does not satisfy spacy_version '{spacy_version}'.",
                    )

    requirements_file = project_dir / "requirements.txt"
    if not requirements_file.is_file():
        return

    check_requirements = data.get("check_requirements", True)
    if check_requirements is False:
        add_issue(
            issues,
            "warning",
            "requirements.txt exists but check_requirements is false; runtime dependency alignment checks are disabled.",
        )
        return
    if Requirement is None or Version is None:
        add_issue(
            issues,
            "warning",
            "requirements.txt exists, but packaging is unavailable so installed version checks were skipped.",
        )
        return

    found_spacy_requirement = False
    for raw_line in requirements_file.read_text(encoding="utf-8").splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line or line.startswith(("-", "--")):
            continue
        try:
            req = Requirement(line)
        except Exception:
            continue
        if req.name.lower() == "spacy":
            found_spacy_requirement = True
            if req.specifier and Version(spacy.__version__) not in req.specifier:
                add_issue(
                    issues,
                    "warning",
                    f"Installed spaCy {spacy.__version__} does not satisfy requirements.txt entry '{req}'.",
                )
            break
    if not found_spacy_requirement:
        add_issue(
            issues,
            "warning",
            "requirements.txt is present but does not declare a spaCy requirement; the environment check may be incomplete.",
        )


def validate_project(project_dir: Path, data: dict[str, Any]) -> List[Tuple[str, str]]:
    issues: List[Tuple[str, str]] = []

    unknown_top_level = sorted(set(data) - TOP_LEVEL_KEYS)
    if unknown_top_level:
        add_issue(
            issues,
            "warning",
            f"project.yml contains unrecognized top-level keys: {', '.join(unknown_top_level)}.",
        )

    for key in ("title", "description", "spacy_version"):
        value = data.get(key)
        if value is not None and not isinstance(value, str):
            add_issue(issues, "error", f"{key} must be a string when provided.")

    if "check_requirements" in data and not isinstance(data.get("check_requirements"), bool):
        add_issue(issues, "error", "check_requirements must be a boolean when provided.")

    if "vars" in data and not isinstance(data.get("vars"), dict):
        add_issue(issues, "error", "vars must be a mapping/object.")
    if "env" in data and not isinstance(data.get("env"), dict):
        add_issue(issues, "error", "env must be a mapping/object.")

    directories = data.get("directories")
    if directories is not None:
        validate_paths(
            coerce_sequence(directories, location="directories", issues=issues, allow_scalar=True),
            location="directories",
            issues=issues,
        )

    validate_assets(project_dir, data.get("assets"), issues)
    command_names = validate_commands(data.get("commands"), issues)
    validate_workflows(data.get("workflows"), command_names, issues)
    validate_remotes(data.get("remotes"), issues)
    validate_requirements(project_dir, data, issues)

    return issues


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate a spaCy project.yml locally without network access."
    )
    parser.add_argument(
        "project_path",
        nargs="?",
        default="project.yml",
        help="Path to project.yml, project.yaml, or the directory that contains it.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as errors.",
    )
    args = parser.parse_args(argv)

    try:
        project_file, project_dir, data = load_project_file(args.project_path)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    issues = validate_project(project_dir, data)
    errors = [message for severity, message in issues if severity == "error"]
    warnings = [message for severity, message in issues if severity == "warning"]

    print(f"spaCy {spacy.__version__} project validation: {project_file.name}")
    for severity, message in issues:
        stream = sys.stderr if severity == "error" else sys.stdout
        print(f"{severity.upper()}: {message}", file=stream)

    if errors or (args.strict and warnings):
        if args.strict and warnings:
            print("STRICT mode: warnings were treated as errors.", file=sys.stderr)
        return 1

    if warnings:
        print(f"OK with {len(warnings)} warning(s).")
    else:
        print("OK.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
