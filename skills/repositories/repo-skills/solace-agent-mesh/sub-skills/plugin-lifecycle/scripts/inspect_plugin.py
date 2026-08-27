#!/usr/bin/env python3
"""Safely inspect a Solace Agent Mesh plugin package directory.

This helper performs read-only structural checks for a plugin root or installed
plugin package directory. It does not import the plugin, install packages, build
artifacts, contact registries, start catalog servers, or run SAM applications.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
import textwrap
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

ALLOWED_TYPES = {"agent", "gateway", "tool", "workflow", "custom"}
COMPONENT_PLACEHOLDERS = {
    "__COMPONENT_SNAKE_CASE_NAME__",
    "__COMPONENT_UPPER_SNAKE_CASE_NAME__",
    "__COMPONENT_KEBAB_CASE_NAME__",
    "__COMPONENT_PASCAL_CASE_NAME__",
    "__COMPONENT_SPACED_NAME__",
    "__COMPONENT_SPACED_CAPITALIZED_NAME__",
}
PLUGIN_TOKEN_RE = re.compile(r"__PLUGIN_[A-Z0-9_]+__")
COMPONENT_TOKEN_RE = re.compile(r"__COMPONENT_[A-Z0-9_]+__")
PEP508_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*[A-Za-z0-9]$|^[A-Za-z0-9]$")


def add(result: Dict[str, Any], kind: str, message: str) -> None:
    result.setdefault(kind, []).append(message)


def parse_scalar(value: str) -> Any:
    """Tiny TOML scalar fallback for simple SAM plugin pyproject files."""
    value = value.strip()
    if not value:
        return ""
    if value.startswith(("'", '"')) and value.endswith(("'", '"')) and len(value) >= 2:
        return value[1:-1]
    if value.lower() in {"true", "false"}:
        return value.lower() == "true"
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        parts: List[str] = []
        current = []
        quote: Optional[str] = None
        for ch in inner:
            if quote:
                current.append(ch)
                if ch == quote:
                    quote = None
            elif ch in {"'", '"'}:
                quote = ch
                current.append(ch)
            elif ch == ",":
                parts.append("".join(current).strip())
                current = []
            else:
                current.append(ch)
        if current:
            parts.append("".join(current).strip())
        return [parse_scalar(part) for part in parts if part]
    try:
        return int(value)
    except ValueError:
        return value.strip('"\'')


def strip_inline_comment(line: str) -> str:
    quote: Optional[str] = None
    escaped = False
    out: List[str] = []
    for ch in line:
        if escaped:
            out.append(ch)
            escaped = False
            continue
        if ch == "\\" and quote == '"':
            out.append(ch)
            escaped = True
            continue
        if quote:
            out.append(ch)
            if ch == quote:
                quote = None
            continue
        if ch in {"'", '"'}:
            quote = ch
            out.append(ch)
            continue
        if ch == "#":
            break
        out.append(ch)
    return "".join(out).strip()


def tiny_toml_parse(text: str) -> Dict[str, Any]:
    root: Dict[str, Any] = {}
    current: Dict[str, Any] = root
    for raw_line in text.splitlines():
        line = strip_inline_comment(raw_line.strip())
        if not line:
            continue
        if line.startswith("[") and line.endswith("]"):
            section = line.strip("[]").strip()
            current = root
            for part in section.split("."):
                key = part.strip().strip('"\'')
                if not key:
                    continue
                current = current.setdefault(key, {})
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        current[key.strip().strip('"\'')] = parse_scalar(value)
    return root


def load_toml(path: Path) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    try:
        import tomllib  # type: ignore[attr-defined]

        with path.open("rb") as handle:
            return tomllib.load(handle), None
    except ModuleNotFoundError:
        try:
            import tomli  # type: ignore[import-not-found]

            with path.open("rb") as handle:
                return tomli.load(handle), None
        except ModuleNotFoundError:
            try:
                return tiny_toml_parse(path.read_text(encoding="utf-8")), (
                    "Python TOML parser not available; used limited fallback parser."
                )
            except Exception as exc:  # pragma: no cover - defensive
                return None, f"Could not parse TOML with fallback parser: {exc}"
        except Exception as exc:
            return None, f"Could not parse TOML: {exc}"
    except Exception as exc:
        return None, f"Could not parse TOML: {exc}"


def load_yaml_if_possible(text: str) -> Tuple[Optional[Any], Optional[str]]:
    try:
        import yaml  # type: ignore[import-not-found]
    except ModuleNotFoundError:
        return None, "PyYAML not available; skipped full YAML parsing."
    try:
        return yaml.safe_load(text), None
    except Exception as exc:
        return None, f"Could not parse YAML: {exc}"


def get_nested(data: Dict[str, Any], keys: Iterable[str]) -> Any:
    node: Any = data
    for key in keys:
        if not isinstance(node, dict):
            return None
        node = node.get(key)
    return node


def formatted_names(name: str) -> Dict[str, str]:
    normalized = re.sub(r"[\s\-_]+", "_", name.strip())
    camel_case_split = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", normalized)
    acronym_split = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", camel_case_split)
    raw_parts = [part for part in acronym_split.split("_") if part]
    parts = [part.lower() for part in raw_parts]
    spaced_capitalized_parts = [part if part.isupper() else part.capitalize() for part in raw_parts]
    return {
        "KEBAB_CASE_NAME": "-".join(parts),
        "PASCAL_CASE_NAME": "".join(word.capitalize() for word in parts),
        "SNAKE_CASE_NAME": "_".join(parts),
        "SNAKE_UPPER_CASE_NAME": "_".join(word.upper() for word in parts),
        "SPACED_NAME": " ".join(parts),
        "SPACED_CAPITALIZED_NAME": " ".join(spaced_capitalized_parts),
    }


def replacement_map(component_name: str) -> Dict[str, str]:
    names = formatted_names(component_name)
    return {
        "__COMPONENT_SNAKE_CASE_NAME__": names["SNAKE_CASE_NAME"],
        "__COMPONENT_UPPER_SNAKE_CASE_NAME__": names["SNAKE_UPPER_CASE_NAME"],
        "__COMPONENT_KEBAB_CASE_NAME__": names["KEBAB_CASE_NAME"],
        "__COMPONENT_PASCAL_CASE_NAME__": names["PASCAL_CASE_NAME"],
        "__COMPONENT_SPACED_NAME__": names["SPACED_NAME"],
        "__COMPONENT_SPACED_CAPITALIZED_NAME__": names["SPACED_CAPITALIZED_NAME"],
    }


def replace_component_placeholders(text: str, component_name: str) -> str:
    result = text
    for placeholder, value in replacement_map(component_name).items():
        result = result.replace(placeholder, value)
    return result


def target_dir_for_type(plugin_type: Optional[str]) -> str:
    if plugin_type in {"agent", "tool"}:
        return "configs/agents"
    if plugin_type == "gateway":
        return "configs/gateways"
    if plugin_type == "workflow":
        return "configs/workflows"
    return "configs/plugins"


def find_package_candidates(root: Path, module_name: Optional[str]) -> List[Path]:
    candidates: List[Path] = []
    if not module_name:
        return candidates
    for candidate in [root / "src" / module_name, root / module_name, root]:
        if (candidate / "__init__.py").exists():
            candidates.append(candidate)
    return candidates


def inspect_plugin(
    plugin_path: Path,
    component_name: Optional[str] = None,
    project_dir: Optional[Path] = None,
    strict: bool = False,
) -> Dict[str, Any]:
    root = plugin_path.expanduser().resolve()
    result: Dict[str, Any] = {
        "path": str(root),
        "status": "pass",
        "errors": [],
        "warnings": [],
        "facts": {},
        "target": None,
    }

    if not root.exists():
        add(result, "errors", f"Path does not exist: {root}")
        result["status"] = "fail"
        return result
    if not root.is_dir():
        add(result, "errors", f"Path is not a directory: {root}")
        result["status"] = "fail"
        return result

    pyproject_path = root / "pyproject.toml"
    config_path = root / "config.yaml"
    readme_path = root / "README.md"

    if not pyproject_path.exists():
        add(result, "errors", "Missing pyproject.toml at plugin root/installed package directory.")
    if not config_path.exists():
        add(result, "errors", "Missing config.yaml at plugin root/installed package directory.")
    if not readme_path.exists():
        add(result, "warnings", "README.md is missing; generated plugins include it and catalog display can use it.")

    data: Dict[str, Any] = {}
    project_name: Optional[str] = None
    module_name: Optional[str] = None
    plugin_type: Optional[str] = None

    if pyproject_path.exists():
        parsed, parse_warning = load_toml(pyproject_path)
        if parse_warning:
            add(result, "warnings", parse_warning)
        if parsed is None:
            add(result, "errors", "Could not parse pyproject.toml.")
        else:
            data = parsed
            project = data.get("project", {}) if isinstance(data.get("project"), dict) else {}
            raw_project_name = project.get("name")
            if isinstance(raw_project_name, str) and raw_project_name.strip():
                project_name = raw_project_name.strip()
                module_name = project_name.replace("-", "_")
                result["facts"]["project.name"] = project_name
                result["facts"]["module_name_expected_by_sam"] = module_name
                if not PEP508_NAME_RE.match(project_name):
                    add(
                        result,
                        "warnings",
                        f"Project name {project_name!r} is unusual for Python packaging; prefer letters/digits plus '.', '_' or '-'.",
                    )
            else:
                add(result, "errors", "pyproject.toml is missing [project].name.")

            if project_name:
                metadata = get_nested(data, ["tool", project_name.replace("-", "_"), "metadata"])
                if isinstance(metadata, dict):
                    raw_type = metadata.get("type")
                    if isinstance(raw_type, str) and raw_type.strip():
                        plugin_type = raw_type.strip().lower()
                        result["facts"]["plugin_type"] = plugin_type
                        if plugin_type not in ALLOWED_TYPES:
                            add(
                                result,
                                "warnings",
                                f"Unknown plugin metadata type {plugin_type!r}; sam plugin add will route it like a custom plugin.",
                            )
                    else:
                        add(result, "warnings", "Plugin metadata table exists but has no non-empty type field.")
                else:
                    add(
                        result,
                        "warnings",
                        "Missing [tool.<project_name_with_underscores>.metadata] table; sam plugin add will route to configs/plugins.",
                    )

            if not isinstance(data.get("build-system"), dict):
                add(result, "warnings", "pyproject.toml has no [build-system]; builds may fail or use tool defaults.")

            force_include = get_nested(data, ["tool", "hatch", "build", "targets", "wheel", "force-include"])
            if isinstance(force_include, dict):
                included_sources = set(force_include.keys())
                for required in ["config.yaml", "pyproject.toml"]:
                    if required not in included_sources:
                        add(result, "warnings", f"Wheel force-include does not list {required}; installed plugin add may not find it.")
                if "README.md" not in included_sources and readme_path.exists():
                    add(result, "warnings", "Wheel force-include does not list README.md; catalog/readme content may be absent after install.")
            elif get_nested(data, ["tool", "hatch", "build", "targets", "wheel"]):
                add(result, "warnings", "Hatch wheel target has no force-include table for plugin metadata/config files.")

    package_candidates = find_package_candidates(root, module_name)
    if module_name:
        result["facts"]["package_candidates"] = [str(path.relative_to(root)) if path != root else "." for path in package_candidates]
        if not package_candidates:
            add(
                result,
                "warnings",
                f"No package directory with __init__.py found for expected module {module_name!r} under root, src/, or installed layout.",
            )
        else:
            package_dir = package_candidates[0]
            rel_package_dir = Path(".") if package_dir == root else package_dir.relative_to(root)
            result["facts"]["primary_package_dir"] = str(rel_package_dir)
            if plugin_type in {"agent", "tool"} and not (package_dir / "tools.py").exists():
                add(result, "warnings", f"{plugin_type} plugin package has no tools.py in {rel_package_dir}.")
            if plugin_type == "gateway":
                for filename in ["app.py", "component.py"]:
                    if not (package_dir / filename).exists():
                        add(result, "warnings", f"Gateway plugin package has no {filename} in {rel_package_dir}.")
            if plugin_type == "custom" and not (package_dir / "app.py").exists():
                add(result, "warnings", f"Custom plugin package has no app.py in {rel_package_dir}.")

    if config_path.exists():
        config_text = config_path.read_text(encoding="utf-8", errors="replace")
        plugin_tokens = sorted(set(PLUGIN_TOKEN_RE.findall(config_text)))
        if plugin_tokens:
            add(result, "warnings", f"Unreplaced plugin template tokens remain in config.yaml: {', '.join(plugin_tokens)}")
        component_tokens = sorted(set(COMPONENT_TOKEN_RE.findall(config_text)))
        result["facts"]["component_placeholders_found"] = component_tokens
        unknown_component_tokens = sorted(set(component_tokens) - COMPONENT_PLACEHOLDERS)
        if unknown_component_tokens:
            add(
                result,
                "warnings",
                f"Unsupported component placeholders remain in config.yaml: {', '.join(unknown_component_tokens)}",
            )
        if not component_tokens:
            add(result, "warnings", "config.yaml contains no __COMPONENT_*__ placeholders; generated component names may not appear in the added config.")

        parsed_yaml, yaml_warning = load_yaml_if_possible(config_text)
        if yaml_warning:
            add(result, "warnings", f"config.yaml: {yaml_warning}")
        elif parsed_yaml is not None and not isinstance(parsed_yaml, dict):
            add(result, "warnings", "config.yaml parsed successfully but top-level YAML is not a mapping.")

        if component_name:
            replacements = replacement_map(component_name)
            if not replacements["__COMPONENT_KEBAB_CASE_NAME__"]:
                add(result, "errors", f"Component name {component_name!r} normalizes to an empty name.")
            processed_text = replace_component_placeholders(config_text, component_name)
            remaining_component_tokens = sorted(set(COMPONENT_TOKEN_RE.findall(processed_text)))
            if remaining_component_tokens:
                add(
                    result,
                    "warnings",
                    "After component-name substitution, component tokens remain: " + ", ".join(remaining_component_tokens),
                )
            processed_yaml, processed_warning = load_yaml_if_possible(processed_text)
            if processed_warning and "PyYAML not available" not in processed_warning:
                add(result, "warnings", f"Processed component config YAML issue: {processed_warning}")
            elif processed_yaml is not None and not isinstance(processed_yaml, dict):
                add(result, "warnings", "Processed component config top-level YAML is not a mapping.")

    route_type = plugin_type if plugin_type in ALLOWED_TYPES else None
    if component_name:
        names = formatted_names(component_name)
        target_rel = Path(target_dir_for_type(route_type)) / f"{names['KEBAB_CASE_NAME']}.yaml"
        result["target"] = {
            "component_name": component_name,
            "component_kebab": names["KEBAB_CASE_NAME"],
            "target_relative_path": str(target_rel),
            "route_reason": route_type or "custom/unknown fallback",
        }
        if project_dir:
            project_root = project_dir.expanduser().resolve()
            result["target"]["project_dir"] = str(project_root)
            target_abs = project_root / target_rel
            result["target"]["target_absolute_path"] = str(target_abs)
            if not project_root.exists():
                add(result, "warnings", f"Project directory does not exist: {project_root}")
            elif target_abs.exists():
                add(
                    result,
                    "warnings",
                    f"Target config already exists and sam plugin add would overwrite it: {target_abs}",
                )

    if result["errors"]:
        result["status"] = "fail"
    elif strict and result["warnings"]:
        result["status"] = "fail"
    elif result["warnings"]:
        result["status"] = "warn"
    else:
        result["status"] = "pass"
    return result


def print_human(result: Dict[str, Any]) -> None:
    print(f"SAM plugin inspection: {result['path']}")
    print(f"status: {result['status']}")
    facts = result.get("facts") or {}
    if facts:
        print("\nfacts:")
        for key in sorted(facts):
            value = facts[key]
            if isinstance(value, list):
                value = ", ".join(value) if value else "(none)"
            print(f"  - {key}: {value}")
    if result.get("target"):
        print("\ntarget preview:")
        for key, value in result["target"].items():
            print(f"  - {key}: {value}")
    for label, key in [("errors", "errors"), ("warnings", "warnings")]:
        items = result.get(key) or []
        if items:
            print(f"\n{label}:")
            for item in items:
                print(f"  - {item}")
    if result["status"] == "pass":
        print("\nNo structural issues detected by this read-only helper.")
    elif result["status"] == "warn":
        print("\nWarnings require review before running side-effectful SAM CLI commands.")
    else:
        print("\nFix errors before running install/add/build commands.")


def make_self_test_fixture(base: Path) -> Path:
    root = base / "demo-plugin"
    package_dir = root / "src" / "demo_plugin"
    package_dir.mkdir(parents=True)
    (package_dir / "__init__.py").write_text("", encoding="utf-8")
    (package_dir / "tools.py").write_text("async def demo_tool():\n    return {'status': 'ok'}\n", encoding="utf-8")
    (root / "README.md").write_text("# Demo Plugin\n", encoding="utf-8")
    (root / "config.yaml").write_text(
        textwrap.dedent(
            """
            apps:
              - name: __COMPONENT_KEBAB_CASE_NAME__-app
                app_module: solace_agent_mesh.agent.sac.app
                app_config:
                  agent_name: "__COMPONENT_PASCAL_CASE_NAME__"
                  agent_card:
                    description: "Demo plugin"
                    skills: []
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )
    (root / "pyproject.toml").write_text(
        textwrap.dedent(
            """
            [build-system]
            requires = ["hatchling"]
            build-backend = "hatchling.build"

            [project]
            name = "demo_plugin"
            version = "0.1.0"
            description = "Demo plugin"

            [tool.demo_plugin.metadata]
            type = "agent"

            [tool.hatch.build.targets.wheel]
            packages = ["src/demo_plugin"]

            [tool.hatch.build.targets.wheel.force-include]
            "src/demo_plugin" = "demo_plugin/"
            "config.yaml" = "demo_plugin/config.yaml"
            "README.md" = "demo_plugin/README.md"
            "pyproject.toml" = "demo_plugin/pyproject.toml"
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )
    return root


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Read-only structural inspector for Solace Agent Mesh plugin package directories.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("path", nargs="?", default=".", help="Plugin root or installed plugin package directory to inspect.")
    parser.add_argument("--component-name", help="Preview component placeholder substitution and target config path.")
    parser.add_argument("--project-dir", type=Path, help="SAM project root to check for existing target config files.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of human-readable text.")
    parser.add_argument("--strict", action="store_true", help="Return non-zero when warnings are present.")
    parser.add_argument("--self-test", action="store_true", help="Run an embedded tiny fixture through the inspector.")
    args = parser.parse_args(argv)

    if args.self_test:
        with tempfile.TemporaryDirectory(prefix="sam-plugin-inspect-") as tmp:
            base = Path(tmp)
            project_dir = base / "project"
            project_dir.mkdir()
            fixture = make_self_test_fixture(base)
            result = inspect_plugin(fixture, component_name="demo-agent", project_dir=project_dir, strict=args.strict)
            if args.json:
                print(json.dumps(result, indent=2, sort_keys=True))
            else:
                print_human(result)
                print("\nself-test fixture completed.")
            return 0 if result["status"] in {"pass", "warn"} and not (args.strict and result["warnings"]) else 2

    result = inspect_plugin(Path(args.path), component_name=args.component_name, project_dir=args.project_dir, strict=args.strict)
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print_human(result)
    return 0 if result["status"] in {"pass", "warn"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
