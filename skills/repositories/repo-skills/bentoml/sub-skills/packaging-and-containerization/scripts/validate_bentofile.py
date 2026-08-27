#!/usr/bin/env python3
"""Validate common BentoML bentofile.yaml mistakes without building a Bento."""

from __future__ import annotations

import argparse
import fnmatch
import re
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None


def parse_scalar(value: str) -> Any:
    value = value.strip()
    if not value:
        return ""
    if value in {"null", "Null", "NULL", "~"}:
        return None
    if value in {"true", "True", "TRUE"}:
        return True
    if value in {"false", "False", "FALSE"}:
        return False
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        return value[1:-1]
    return value


def simple_yaml_load(text: str) -> Any:
    prepared: list[tuple[int, str]] = []
    for raw_line in text.splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        indent = len(raw_line) - len(raw_line.lstrip(" "))
        prepared.append((indent, raw_line.strip()))

    def parse_block(index: int, indent: int) -> tuple[Any, int]:
        if index >= len(prepared):
            return None, index
        if prepared[index][0] < indent:
            return None, index
        if prepared[index][1].startswith("- "):
            return parse_list(index, indent)
        return parse_map(index, indent)

    def parse_map(index: int, indent: int) -> tuple[dict[str, Any], int]:
        result: dict[str, Any] = {}
        while index < len(prepared):
            line_indent, content = prepared[index]
            if line_indent < indent or content.startswith("- "):
                break
            if line_indent > indent:
                raise ValueError(f"unexpected indentation near: {content}")
            key, separator, rest = content.partition(":")
            if not separator:
                raise ValueError(f"expected key: value near: {content}")
            key = key.strip()
            rest = rest.strip()
            index += 1
            if rest:
                result[key] = parse_scalar(rest)
            elif index < len(prepared) and (
                prepared[index][0] > line_indent
                or (prepared[index][0] == line_indent and prepared[index][1].startswith("- "))
            ):
                result[key], index = parse_block(index, prepared[index][0])
            else:
                result[key] = None
        return result, index

    def parse_list(index: int, indent: int) -> tuple[list[Any], int]:
        result: list[Any] = []
        while index < len(prepared):
            line_indent, content = prepared[index]
            if line_indent < indent or not content.startswith("- "):
                break
            if line_indent > indent:
                raise ValueError(f"unexpected indentation near: {content}")
            item = content[2:].strip()
            index += 1
            if not item:
                if index < len(prepared) and prepared[index][0] > line_indent:
                    value, index = parse_block(index, prepared[index][0])
                else:
                    value = None
            elif ":" in item and not item.startswith(("'", '"')):
                key, _, rest = item.partition(":")
                value = {key.strip(): parse_scalar(rest.strip()) if rest.strip() else None}
                if index < len(prepared) and prepared[index][0] > line_indent:
                    extra, index = parse_block(index, prepared[index][0])
                    if isinstance(extra, dict):
                        value.update(extra)
                result.append(value)
                continue
            else:
                value = parse_scalar(item)
            result.append(value)
        return result, index

    if not prepared:
        return None
    parsed, final_index = parse_block(0, prepared[0][0])
    if final_index != len(prepared):
        raise ValueError("could not parse complete YAML document")
    return parsed


def load_yaml_text(text: str) -> Any:
    if yaml is not None:
        return yaml.safe_load(text)
    return simple_yaml_load(text)

TOP_LEVEL_KEYS = {
    "service",
    "name",
    "description",
    "labels",
    "include",
    "exclude",
    "docker",
    "python",
    "conda",
    "models",
    "envs",
    "args",
}
PYTHON_KEYS = {
    "requirements_txt",
    "packages",
    "lock_packages",
    "pack_git_packages",
    "index_url",
    "no_index",
    "trusted_host",
    "find_links",
    "extra_index_url",
    "pip_args",
    "wheels",
    "is_src_layout",
}
DOCKER_KEYS = {
    "distro",
    "python_version",
    "cuda_version",
    "env",
    "system_packages",
    "setup_script",
    "base_image",
    "dockerfile_template",
}
CONDA_KEYS = {"environment_yml", "channels", "dependencies", "pip"}
SUPPORTED_DISTROS = {"debian", "alpine", "ubi8", "amazonlinux"}
ENV_STAGES = {"all", "build", "runtime"}
SERVICE_RE = re.compile(r"^[A-Za-z_][\w.]*:[A-Za-z_][\w.]*$")
PYTHON_VERSION_RE = re.compile(r"^\d+\.\d+(?:\.\w+)?$")


def add_error(errors: list[str], message: str) -> None:
    errors.append(f"ERROR: {message}")


def add_warning(warnings: list[str], message: str) -> None:
    warnings.append(f"WARN: {message}")


def require_mapping(value: Any, key: str, errors: list[str]) -> bool:
    if value is None:
        return True
    if not isinstance(value, dict):
        add_error(errors, f"{key} must be a mapping/object")
        return False
    return True


def require_string_list(value: Any, key: str, errors: list[str], *, allow_string: bool = False) -> bool:
    if value is None:
        return True
    if allow_string and isinstance(value, str):
        return True
    if not isinstance(value, list):
        add_error(errors, f"{key} must be a list of strings")
        return False
    bad = [item for item in value if not isinstance(item, str)]
    if bad:
        add_error(errors, f"{key} must contain only strings")
        return False
    return True


def path_exists(project_dir: Path, relative_path: str) -> bool:
    return (project_dir / relative_path).expanduser().exists()


def description_file(description: Any) -> str | None:
    if isinstance(description, str) and description.startswith("file:"):
        return description.partition(":")[2].strip()
    return None


def check_unknown_keys(mapping: dict[str, Any], allowed: set[str], context: str, errors: list[str]) -> None:
    for key in sorted(set(mapping) - allowed):
        add_error(errors, f"unknown key {context}.{key}" if context else f"unknown key {key}")


def check_patterns(data: dict[str, Any], project_dir: Path, warnings: list[str], errors: list[str]) -> None:
    include = data.get("include")
    exclude = data.get("exclude")
    require_string_list(include, "include", errors)
    require_string_list(exclude, "exclude", errors)

    for key, patterns in (("include", include), ("exclude", exclude)):
        if not isinstance(patterns, list):
            continue
        for pattern in patterns:
            if not pattern or pattern.strip() != pattern:
                add_warning(warnings, f"{key} pattern {pattern!r} is empty or has surrounding whitespace")
            matches = list(project_dir.glob(pattern)) if not any(ch in pattern for ch in "[]") else []
            if not matches and not any(ch in pattern for ch in "*?") and not path_exists(project_dir, pattern.rstrip("/")):
                add_warning(warnings, f"{key} pattern {pattern!r} does not currently match an existing path")
            if fnmatch.fnmatch(pattern, "*.key") or "secret" in pattern.lower():
                add_warning(warnings, f"{key} pattern {pattern!r} mentions sensitive files; ensure secrets are excluded, not included")


def check_python(python_cfg: Any, project_dir: Path, warnings: list[str], errors: list[str]) -> None:
    if not require_mapping(python_cfg, "python", errors) or not isinstance(python_cfg, dict):
        return
    check_unknown_keys(python_cfg, PYTHON_KEYS, "python", errors)
    require_string_list(python_cfg.get("packages"), "python.packages", errors)
    require_string_list(python_cfg.get("trusted_host"), "python.trusted_host", errors, allow_string=True)
    require_string_list(python_cfg.get("find_links"), "python.find_links", errors, allow_string=True)
    require_string_list(python_cfg.get("extra_index_url"), "python.extra_index_url", errors, allow_string=True)
    require_string_list(python_cfg.get("wheels"), "python.wheels", errors)

    requirements_txt = python_cfg.get("requirements_txt")
    if requirements_txt is not None:
        if not isinstance(requirements_txt, str):
            add_error(errors, "python.requirements_txt must be a string path")
        elif not path_exists(project_dir, requirements_txt):
            add_error(errors, f"python.requirements_txt does not exist: {requirements_txt}")
        if python_cfg.get("packages"):
            add_warning(warnings, "python.requirements_txt is set; BentoML ignores python.packages content")

    for bool_key in ("lock_packages", "pack_git_packages", "no_index", "is_src_layout"):
        if bool_key in python_cfg and python_cfg[bool_key] is not None and not isinstance(python_cfg[bool_key], bool):
            add_error(errors, f"python.{bool_key} must be true or false")

    if python_cfg.get("no_index") and (python_cfg.get("index_url") or python_cfg.get("extra_index_url")):
        add_warning(warnings, "python.no_index ignores index_url and extra_index_url")

    for wheel in python_cfg.get("wheels") or []:
        if not path_exists(project_dir, wheel):
            add_warning(warnings, f"python.wheels entry does not exist yet: {wheel}")


def check_docker(docker_cfg: Any, project_dir: Path, warnings: list[str], errors: list[str]) -> None:
    if not require_mapping(docker_cfg, "docker", errors) or not isinstance(docker_cfg, dict):
        return
    check_unknown_keys(docker_cfg, DOCKER_KEYS, "docker", errors)

    distro = docker_cfg.get("distro")
    if distro is not None and distro not in SUPPORTED_DISTROS:
        add_error(errors, f"docker.distro {distro!r} is not one of {sorted(SUPPORTED_DISTROS)}")

    python_version = docker_cfg.get("python_version")
    if python_version is not None and not PYTHON_VERSION_RE.match(str(python_version)):
        add_error(errors, "docker.python_version must look like 3.11 or 3.11.9")

    require_string_list(docker_cfg.get("system_packages"), "docker.system_packages", errors)

    for path_key in ("setup_script", "dockerfile_template"):
        value = docker_cfg.get(path_key)
        if value is not None:
            if not isinstance(value, str):
                add_error(errors, f"docker.{path_key} must be a string path")
            elif not path_exists(project_dir, value):
                add_error(errors, f"docker.{path_key} does not exist: {value}")

    if docker_cfg.get("base_image"):
        ignored = [key for key in ("distro", "python_version", "cuda_version", "system_packages") if docker_cfg.get(key)]
        if ignored:
            add_warning(warnings, f"docker.base_image overrides these fields: {', '.join(ignored)}")


def check_conda(conda_cfg: Any, project_dir: Path, warnings: list[str], errors: list[str]) -> None:
    if not require_mapping(conda_cfg, "conda", errors) or not isinstance(conda_cfg, dict):
        return
    check_unknown_keys(conda_cfg, CONDA_KEYS, "conda", errors)
    require_string_list(conda_cfg.get("channels"), "conda.channels", errors)
    require_string_list(conda_cfg.get("pip"), "conda.pip", errors)

    env_yml = conda_cfg.get("environment_yml")
    if env_yml is not None:
        if not isinstance(env_yml, str):
            add_error(errors, "conda.environment_yml must be a string path")
        elif not path_exists(project_dir, env_yml):
            add_error(errors, f"conda.environment_yml does not exist: {env_yml}")
        overridden = [key for key in ("channels", "dependencies", "pip") if conda_cfg.get(key)]
        if overridden:
            add_warning(warnings, f"conda.environment_yml overrides these fields: {', '.join(overridden)}")

    dependencies = conda_cfg.get("dependencies")
    if dependencies is not None and not isinstance(dependencies, list):
        add_error(errors, "conda.dependencies must be a list")


def check_models(models: Any, errors: list[str]) -> None:
    if models is None:
        return
    if not isinstance(models, list):
        add_error(errors, "models must be a list")
        return
    for index, item in enumerate(models):
        if isinstance(item, str):
            continue
        if isinstance(item, dict) and isinstance(item.get("tag"), str):
            extra = set(item) - {"tag", "filter", "alias"}
            if extra:
                add_error(errors, f"models[{index}] has unknown keys: {sorted(extra)}")
            continue
        add_error(errors, f"models[{index}] must be a string tag or mapping with tag")


def check_envs(envs: Any, errors: list[str]) -> None:
    if envs is None:
        return
    if not isinstance(envs, list):
        add_error(errors, "envs must be a list")
        return
    for index, item in enumerate(envs):
        if not isinstance(item, dict):
            add_error(errors, f"envs[{index}] must be a mapping")
            continue
        if not isinstance(item.get("name"), str) or not item.get("name"):
            add_error(errors, f"envs[{index}].name must be a non-empty string")
        if "stage" in item and item["stage"] not in ENV_STAGES:
            add_error(errors, f"envs[{index}].stage must be one of {sorted(ENV_STAGES)}")


def validate(path: Path, project_dir: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    data = load_yaml_text(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return ["ERROR: bentofile must contain a YAML mapping/object"], warnings

    check_unknown_keys(data, TOP_LEVEL_KEYS, "", errors)

    service = data.get("service")
    if not isinstance(service, str) or not service.strip():
        add_error(errors, "service is required and must be a non-empty string")
    elif not SERVICE_RE.match(service):
        add_warning(warnings, "service usually has the form module:object, for example service:MyService")

    if "labels" in data and not isinstance(data.get("labels"), dict):
        add_error(errors, "labels must be a mapping")
    if "args" in data and not isinstance(data.get("args"), dict):
        add_error(errors, "args must be a mapping")

    desc_path = description_file(data.get("description"))
    if desc_path and not path_exists(project_dir, desc_path):
        add_error(errors, f"description file does not exist: {desc_path}")

    check_patterns(data, project_dir, warnings, errors)
    check_python(data.get("python"), project_dir, warnings, errors)
    check_docker(data.get("docker"), project_dir, warnings, errors)
    check_conda(data.get("conda"), project_dir, warnings, errors)
    check_models(data.get("models"), errors)
    check_envs(data.get("envs"), errors)
    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bentofile", type=Path, help="Path to bentofile.yaml")
    parser.add_argument("--project-dir", type=Path, default=None, help="Build context for resolving relative paths")
    args = parser.parse_args()

    bentofile = args.bentofile.resolve()
    if not bentofile.exists():
        print(f"ERROR: bentofile does not exist: {bentofile}", file=sys.stderr)
        return 2
    project_dir = (args.project_dir or bentofile.parent).resolve()
    if not project_dir.exists():
        print(f"ERROR: project directory does not exist: {project_dir}", file=sys.stderr)
        return 2

    try:
        errors, warnings = validate(bentofile, project_dir)
    except Exception as exc:
        print(f"ERROR: invalid YAML: {exc}", file=sys.stderr)
        return 1

    for message in warnings:
        print(message, file=sys.stderr)
    for message in errors:
        print(message, file=sys.stderr)

    if errors:
        return 1
    print(f"OK: {bentofile.name} passed static BentoML build-file checks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
