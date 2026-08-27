#!/usr/bin/env python3
"""Read-only static checker for ClawBio skill assets.

The checker intentionally does not import or execute a skill, regenerate the
catalog, or write a report. It inspects source metadata, the static CLI registry,
INTENTS.json, and (optionally) skills/catalog.json from an explicit repository
root.
"""
from __future__ import annotations

import argparse
import ast
from dataclasses import asdict, dataclass
import json
import re
import sys
from pathlib import Path
from typing import Any

SCHEMA = "clawbio.skill_intents.v1"
IDENT_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,79}$")
SLOT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,63}$")
SECTION_NAMES = (
    "Trigger",
    "Scope",
    "Input Formats",
    "Workflow",
    "Example Output",
    "Output Structure",
    "Gotchas",
    "Safety",
    "Agent Boundary",
    "Maintenance",
)
EXCLUDED_FOLDERS = {"pr-audit", "wes-clinical-report-es"}
BLOCKED_FLAGS = {
    "--input",
    "--output",
    "--profile",
    "--profile-path",
    "--demo",
    "--help",
    "-h",
}
BLOCKED_FRAGMENTS = (
    "credential", "password", "secret", "token", "profile", "output",
    "input", "config", "path", "file", "dir", "weights", "pop-map",
    "reference", "vcf", "counts", "metadata", "reads", "genome", "adata",
    "sheet",
)


@dataclass
class Finding:
    level: str
    code: str
    path: str
    message: str


@dataclass
class RegistryEntry:
    alias: str
    folder: str | None
    script: str | None
    value_flags: set[str]
    boolean_flags: set[str]


class Checker:
    def __init__(self, root: Path, *, strict: bool = False, operating: bool = False) -> None:
        self.root = root
        self.strict = strict
        self.operating = operating
        self.findings: list[Finding] = []
        self.registry: dict[str, RegistryEntry] = {}

    def add(self, level: str, code: str, path: Path | str, message: str) -> None:
        rendered = str(path)
        try:
            rendered = str(Path(path).resolve().relative_to(self.root))
        except (ValueError, OSError):
            pass
        self.findings.append(Finding(level, code, rendered, message))

    def error(self, code: str, path: Path | str, message: str) -> None:
        self.add("error", code, path, message)

    def warning(self, code: str, path: Path | str, message: str) -> None:
        self.add("warning", code, path, message)

    def run(self, skill_dirs: list[Path], catalog_path: Path | None) -> None:
        selected_folders = {path.name for path in skill_dirs} if skill_dirs else None
        self.registry = load_registry(self.root, self, check_missing_folders=selected_folders)
        for skill_dir in skill_dirs:
            self.check_skill(skill_dir)
        if catalog_path is not None:
            self.check_catalog(catalog_path, skill_dirs)

    def check_skill(self, skill_dir: Path) -> None:
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.is_file():
            self.error("missing-skill-md", skill_dir, "skill directory has no SKILL.md")
            return
        try:
            text = skill_md.read_text(encoding="utf-8")
        except OSError as exc:
            self.error("unreadable-skill-md", skill_md, f"cannot read SKILL.md: {exc}")
            return
        frontmatter, body = parse_frontmatter(text)
        if frontmatter is None:
            self.error("invalid-frontmatter", skill_md, "expected YAML frontmatter between --- delimiters")
            return
        name = frontmatter.get("name")
        if name != skill_dir.name:
            self.error("name-folder-mismatch", skill_md, f"name {name!r} must match directory {skill_dir.name!r}")
        description = frontmatter.get("description", "")
        if not description:
            self.error("missing-description", skill_md, "frontmatter requires a non-empty description")
        if self.operating:
            self.check_operating_frontmatter(skill_md, frontmatter)
        else:
            self.check_contributor_sections(skill_md, body)

        scripts = [
            path for path in skill_dir.rglob("*.py")
            if "tests" not in path.relative_to(skill_dir).parts
            and "__pycache__" not in path.parts
            and path.name != "__init__.py"
        ]
        has_tests = any((skill_dir / "tests").glob("test_*.py")) if (skill_dir / "tests").is_dir() else False
        has_demo_marker = "--demo" in text or "demo_data" in text or any(
            "demo" in path.name.lower() for path in skill_dir.iterdir()
        )
        if not self.operating and scripts and not has_tests:
            self.error("missing-tests", skill_dir, "executable skill needs tests/test_*.py")
        if not self.operating and scripts and not has_demo_marker:
            self.warning("missing-demo-signal", skill_md, "executable skill has no visible --demo, demo_data, or demo-named fixture")
        if not self.operating and scripts and "report.md" not in text and "result.json" not in text:
            self.warning("unclear-output-contract", skill_md, "document the primary report/result output or explain why this skill is non-reporting")
        for descriptor_name in ("INTENTS.json", "skill_intents.json"):
            descriptor = skill_dir / descriptor_name
            if descriptor.is_file():
                self.check_descriptor(descriptor, skill_dir)

    def check_operating_frontmatter(self, skill_md: Path, frontmatter: dict[str, Any]) -> None:
        expected = {"name", "description", "disable-model-invocation", "metadata"}
        actual = set(frontmatter) - {"_raw_description"}
        if actual != expected:
            self.error("operating-frontmatter-keys", skill_md, f"operating SKILL.md keys must be {sorted(expected)}, found {sorted(actual)}")
        if frontmatter.get("disable-model-invocation") is not True:
            self.error("operating-invocation", skill_md, "disable-model-invocation must be true")
        metadata = frontmatter.get("metadata")
        if not isinstance(metadata, dict) or metadata.get("disco-role") != "operating":
            self.error("operating-role", skill_md, "metadata.disco-role must be operating")
        raw_description = frontmatter.get("_raw_description", "")
        if not (isinstance(raw_description, str) and raw_description.startswith('"') and raw_description.endswith('"')):
            self.error("operating-description-quote", skill_md, "description must use a double-quoted YAML scalar")

    def check_contributor_sections(self, skill_md: Path, body: str) -> None:
        headings = set(re.findall(r"^##\s+(.+?)\s*$", body, flags=re.MULTILINE))
        for section in SECTION_NAMES:
            if section not in headings:
                self.error("missing-section", skill_md, f"SKILL.md must include ## {section}")
        if "Fire this skill when" not in body or "Do NOT fire when" not in body:
            self.error("weak-trigger-section", skill_md, "Trigger must contain both fire and do-not-fire guidance")
        if "trigger_keywords" not in body and "trigger_keywords" not in skill_md.read_text(encoding="utf-8"):
            self.warning("missing-trigger-keywords", skill_md, "declare metadata.openclaw.trigger_keywords")
        if "ClawBio is a research and educational tool." not in body:
            self.warning("missing-disclaimer", skill_md, "document the exact ClawBio medical disclaimer for report-producing skills")

    def check_descriptor(self, path: Path, skill_dir: Path) -> None:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            self.error("invalid-descriptor-json", path, f"cannot parse descriptor JSON: {exc}")
            return
        if not isinstance(data, dict):
            self.error("descriptor-object", path, "descriptor root must be an object")
            return
        if data.get("schema") != SCHEMA:
            self.error("descriptor-schema", path, f"schema must equal {SCHEMA!r}")
        descriptor_skill = data.get("skill") or skill_dir.name
        if not isinstance(descriptor_skill, str) or not IDENT_RE.fullmatch(descriptor_skill):
            self.error("descriptor-skill", path, "skill must be a conservative identifier")
        elif descriptor_skill != skill_dir.name and not self._alias_maps_to_folder(descriptor_skill, skill_dir.name):
            self.error("descriptor-alias", path, f"descriptor skill {descriptor_skill!r} is not the folder or a registered alias for it")
        for field in ("entrypoint", "script"):
            if field in data:
                self.check_confined_path(data[field], skill_dir, path, field, must_exist=True)
        execution = data.get("execution")
        if execution is not None:
            if not isinstance(execution, dict):
                self.error("descriptor-execution", path, "execution must be an object")
            else:
                for field in ("entrypoint", "script"):
                    if field in execution:
                        self.check_confined_path(execution[field], skill_dir, path, f"execution.{field}", must_exist=True)
        routes = data.get("routes")
        if not isinstance(routes, list) or not routes:
            self.error("descriptor-routes", path, "routes must be a non-empty list")
            return
        for route_index, route in enumerate(routes):
            self.check_route(route, path, skill_dir, descriptor_skill, route_index)

    def check_route(self, route: Any, descriptor_path: Path, skill_dir: Path, descriptor_skill: str, index: int) -> None:
        label = f"route[{index}]"
        if not isinstance(route, dict):
            self.error("descriptor-route", descriptor_path, f"{label} must be an object")
            return
        intent_id = route.get("intent_id")
        if not isinstance(intent_id, str) or not IDENT_RE.fullmatch(intent_id):
            self.error("descriptor-intent-id", descriptor_path, f"{label}.intent_id must be a conservative identifier")
        terms = route.get("trigger_terms", route.get("aliases", []))
        if not isinstance(terms, list) or not terms or not all(isinstance(item, str) and item.strip() for item in terms):
            self.error("descriptor-triggers", descriptor_path, f"{label} needs non-empty trigger_terms or aliases")
        if route.get("demo_policy", "never_unless_explicit") not in {"never_unless_explicit", "only_when_explicit"}:
            self.error("descriptor-demo-policy", descriptor_path, f"{label}.demo_policy is unsupported")
        plan = route.get("plan")
        if not isinstance(plan, list) or not plan:
            self.error("descriptor-plan", descriptor_path, f"{label}.plan must be a non-empty list")
            return
        for step_index, step in enumerate(plan):
            self.check_step(step, descriptor_path, skill_dir, descriptor_skill, f"{label}.plan[{step_index}]")

    def check_step(self, step: Any, descriptor_path: Path, skill_dir: Path, descriptor_skill: str, label: str) -> None:
        if not isinstance(step, dict) or step.get("kind", "skill_run") != "skill_run":
            self.error("descriptor-step", descriptor_path, f"{label} must be a skill_run object")
            return
        step_skill = step.get("skill") or descriptor_skill
        if not isinstance(step_skill, str) or not IDENT_RE.fullmatch(step_skill):
            self.error("descriptor-step-skill", descriptor_path, f"{label}.skill is invalid")
        for field in ("input", "output"):
            if field in step:
                self.check_confined_path(step[field], skill_dir, descriptor_path, f"{label}.{field}", must_exist=False)
        if "input_template" in step and not isinstance(step["input_template"], dict):
            self.error("descriptor-template", descriptor_path, f"{label}.input_template must be an object")
        slots = step.get("slots", {})
        if not isinstance(slots, dict):
            self.error("descriptor-slots", descriptor_path, f"{label}.slots must be an object")
        else:
            self.check_slots(slots, descriptor_path, label)
        args = step.get("args")
        if args is not None:
            self.check_args(args, descriptor_path, step_skill, slots, label)
        if "demo" in step and not isinstance(step["demo"], bool):
            self.error("descriptor-demo", descriptor_path, f"{label}.demo must be boolean")

    def check_slots(self, slots: dict[str, Any], path: Path, label: str) -> None:
        for name, spec in slots.items():
            if not isinstance(name, str) or not SLOT_RE.fullmatch(name) or not isinstance(spec, dict):
                self.error("descriptor-slot", path, f"{label} has an invalid slot {name!r}")
                continue
            pattern = spec.get("pattern")
            if pattern is not None:
                if not isinstance(pattern, str) or len(pattern) > 256:
                    self.error("descriptor-slot-pattern", path, f"{label}.{name} pattern is missing/too long")
                else:
                    try:
                        re.compile(pattern)
                    except re.error as exc:
                        self.error("descriptor-slot-pattern", path, f"{label}.{name} pattern does not compile: {exc}")
            if "required" in spec and not isinstance(spec["required"], bool):
                self.error("descriptor-slot-required", path, f"{label}.{name}.required must be boolean")

    def check_args(self, args: Any, path: Path, skill: str, slots: dict[str, Any], label: str) -> None:
        if not isinstance(args, list):
            self.error("descriptor-args", path, f"{label}.args must be a list")
            return
        registry = self.registry.get(skill)
        allowed = registry.value_flags | registry.boolean_flags if registry else set()
        i = 0
        while i < len(args):
            arg_value = args[i]
            if not isinstance(arg_value, str) or not arg_value.startswith("-"):
                self.error("descriptor-arg-value", path, f"{label}.args[{i}] must follow an allowed flag")
                i += 1
                continue
            flag, inline = arg_value.split("=", 1) if "=" in arg_value else (arg_value, None)
            lowered = flag.lower()
            if flag in BLOCKED_FLAGS or any(fragment in lowered for fragment in BLOCKED_FRAGMENTS):
                self.error("descriptor-blocked-arg", path, f"{label} uses blocked descriptor flag {flag}")
            elif registry is None:
                self.error("descriptor-unregistered-args", path, f"{label} uses args for unregistered skill {skill!r}")
            elif flag not in allowed:
                self.error("descriptor-arg-not-allowlisted", path, f"{label} flag {flag} is not in the static allowlist for {skill}")
            if inline is not None:
                self.check_arg_value(inline, path, label, i, slots)
                i += 1
                continue
            if flag not in (registry.boolean_flags if registry else set()):
                if i + 1 >= len(args):
                    self.error("descriptor-arg-missing-value", path, f"{label} flag {flag} has no value")
                else:
                    value = args[i + 1]
                    if isinstance(value, str) and value.startswith("-"):
                        self.error("descriptor-arg-missing-value", path, f"{label} flag {flag} is followed by another flag")
                    else:
                        self.check_arg_value(value, path, label, i + 1, slots)
                    i += 1
            i += 1

    def check_arg_value(self, value: Any, path: Path, label: str, index: int, slots: dict[str, Any]) -> None:
        if not isinstance(value, str):
            self.error("descriptor-arg-value", path, f"{label}.args[{index}] must be a string")
            return
        if re.fullmatch(r"\{[A-Za-z_][A-Za-z0-9_]*\}", value):
            name = value[1:-1]
            if name not in slots:
                self.error("descriptor-unknown-slot", path, f"{label} references unknown slot {name!r}")
            return
        if "\x00" in value or "\n" in value or "\r" in value or len(value) > 512:
            self.error("descriptor-unsafe-value", path, f"{label}.args[{index}] contains unsafe text")
        if Path(value).is_absolute() or value.startswith("~") or any(part == ".." for part in Path(value).parts) or "/" in value or "\\" in value:
            self.error("descriptor-path-value", path, f"{label}.args[{index}] looks like a path; use input/template/output instead")

    def check_confined_path(self, value: Any, skill_dir: Path, descriptor_path: Path, label: str, *, must_exist: bool) -> None:
        if not isinstance(value, str) or not value or len(value) > 512:
            self.error("descriptor-path", descriptor_path, f"{label} must be a non-empty relative path")
            return
        raw = Path(value)
        if raw.is_absolute() or any(part == ".." for part in raw.parts):
            self.error("descriptor-path-escape", descriptor_path, f"{label} must not be absolute or traverse with ..")
            return
        resolved = (skill_dir / raw).resolve()
        try:
            resolved.relative_to(skill_dir.resolve())
        except ValueError:
            self.error("descriptor-path-escape", descriptor_path, f"{label} resolves outside the skill directory")
            return
        if must_exist and not resolved.is_file():
            self.error("descriptor-entrypoint-missing", descriptor_path, f"{label} does not exist: {value}")

    def _alias_maps_to_folder(self, alias: str, folder: str) -> bool:
        entry = self.registry.get(alias)
        return bool(entry and entry.folder == folder)

    def check_catalog(self, catalog_path: Path, selected_dirs: list[Path]) -> None:
        if not catalog_path.is_file():
            self.error("missing-catalog", catalog_path, "catalog file is missing; generate it from source metadata instead of hand-writing it")
            return
        try:
            catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            self.error("invalid-catalog", catalog_path, f"cannot parse catalog JSON: {exc}")
            return
        entries = catalog.get("skills") if isinstance(catalog, dict) else None
        if not isinstance(entries, list):
            self.error("catalog-shape", catalog_path, "catalog.skills must be a list")
            return
        if catalog.get("skill_count") != len(entries):
            self.error("catalog-count", catalog_path, "skill_count does not equal the number of skills entries")
        by_name: dict[str, dict[str, Any]] = {}
        for entry in entries:
            if not isinstance(entry, dict) or not isinstance(entry.get("name"), str):
                self.error("catalog-entry", catalog_path, "every catalog skill entry needs a name")
                continue
            name = entry["name"]
            if name in by_name:
                self.error("catalog-duplicate", catalog_path, f"duplicate catalog skill {name!r}")
            by_name[name] = entry
        skills_root = self.root / "skills"
        all_dirs = [
            path for path in skills_root.iterdir() if path.is_dir() and path.name not in EXCLUDED_FOLDERS and (path / "SKILL.md").is_file()
        ] if skills_root.is_dir() else []
        # A targeted --skill check validates only those catalog entries. A full
        # run validates inventory as well, matching generate_catalog.py's scope.
        dirs = selected_dirs or all_dirs
        if not selected_dirs:
            expected_names = {path.name for path in all_dirs}
            for name in sorted(expected_names - set(by_name)):
                self.error("catalog-missing-skill", catalog_path, f"catalog has no entry for {name!r}; regenerate from source")
            for name in sorted(set(by_name) - expected_names):
                self.error("catalog-stale-skill", catalog_path, f"catalog contains {name!r}, but no matching non-excluded skills/<name>/SKILL.md exists")
        selected_names = {path.name for path in dirs}
        for name in sorted(selected_names - set(by_name)):
            self.error("catalog-missing-skill", catalog_path, f"catalog has no entry for selected skill {name!r}; regenerate from source")
        for name, entry in by_name.items():
            if selected_dirs and name not in selected_names:
                continue
            skill_dir = skills_root / name
            if not skill_dir.is_dir():
                continue
            has_script = any(
                p.suffix == ".py" and p.name != "__init__.py" and "tests" not in p.relative_to(skill_dir).parts
                for p in skill_dir.rglob("*.py") if "__pycache__" not in p.parts
            )
            has_tests = (skill_dir / "tests").is_dir() and any((skill_dir / "tests").glob("test_*.py"))
            alias = next((a for a, reg in self.registry.items() if reg.folder == name), None)
            expected_demo = bool(alias or has_script)
            for field, expected in (("has_script", has_script), ("has_tests", has_tests), ("has_demo", expected_demo)):
                if field in entry and bool(entry[field]) != expected:
                    self.error("catalog-stale-field", catalog_path, f"{name}.{field}={entry[field]!r} disagrees with current files ({expected!r}); regenerate")
            if "cli_alias" in entry and entry["cli_alias"] != alias:
                self.error("catalog-alias", catalog_path, f"{name}.cli_alias={entry['cli_alias']!r} should be {alias!r}; fix registry/source and regenerate")


def parse_frontmatter(text: str) -> tuple[dict[str, Any] | None, str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, text
    try:
        end = next(index for index in range(1, len(lines)) if lines[index].strip() == "---")
    except StopIteration:
        return None, text
    raw = lines[1:end]
    fields: dict[str, Any] = {}
    for line in raw:
        match = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if match:
            key, value = match.groups()
            if value.startswith('"') and value.endswith('"'):
                try:
                    fields[key] = json.loads(value)
                except json.JSONDecodeError:
                    fields[key] = value
            elif value in {"true", "false"}:
                fields[key] = value == "true"
            elif value in {"null", "~"}:
                fields[key] = None
            elif value:
                fields[key] = value
            else:
                fields[key] = {}
            if key == "description":
                fields["_raw_description"] = value
    # Parse the only nested key needed by the operating contract.
    for index, line in enumerate(raw):
        if line == "metadata:":
            nested: dict[str, Any] = {}
            for nested_line in raw[index + 1 :]:
                match = re.match(r"^\s{2}([A-Za-z0-9_-]+):\s*(.*)$", nested_line)
                if match:
                    key, value = match.groups()
                    nested[key] = value.strip('"') if value else {}
            fields["metadata"] = nested
            break
    return fields, "\n".join(lines[end + 1 :])


def path_string_parts(node: ast.AST | None) -> list[str]:
    """Return string fragments from a static ``Path / 'folder' / 'file'`` expression."""
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
        return path_string_parts(node.left) + path_string_parts(node.right)
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return [node.value]
    return []


def literal_string_set(node: ast.AST | None) -> set[str]:
    if not isinstance(node, (ast.Set, ast.List, ast.Tuple)):
        return set()
    return {item.value for item in node.elts if isinstance(item, ast.Constant) and isinstance(item.value, str)}


def load_registry(root: Path, checker: Checker, *, check_missing_folders: set[str] | None = None) -> dict[str, RegistryEntry]:
    path = root / "clawbio" / "cli.py"
    if not path.is_file():
        checker.warning("missing-cli-registry", path, "clawbio/cli.py not found; static alias and allowlist checks skipped")
        return {}
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (OSError, SyntaxError) as exc:
        checker.error("invalid-cli-registry", path, f"cannot parse static CLI registry: {exc}")
        return {}
    result: dict[str, RegistryEntry] = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign) or not any(isinstance(t, ast.Name) and t.id == "SKILLS" for t in node.targets):
            continue
        if not isinstance(node.value, ast.Dict):
            checker.error("registry-shape", path, "SKILLS must be a literal dictionary for static inspection")
            return result
        for key_node, value_node in zip(node.value.keys, node.value.values):
            if not isinstance(key_node, ast.Constant) or not isinstance(key_node.value, str) or not isinstance(value_node, ast.Dict):
                continue
            values: dict[str, ast.AST] = {}
            for field_node, field_value in zip(value_node.keys, value_node.values):
                if isinstance(field_node, ast.Constant) and isinstance(field_node.value, str):
                    values[field_node.value] = field_value
            constants = path_string_parts(values.get("script"))
            folder = constants[-2] if len(constants) >= 2 else None
            script = constants[-1] if constants else None
            entry = RegistryEntry(
                alias=key_node.value,
                folder=folder,
                script=script,
                value_flags=literal_string_set(values.get("allowed_extra_flags")),
                boolean_flags=literal_string_set(values.get("allowed_extra_flags_without_values")),
            )
            result[entry.alias] = entry
            if not folder or not script:
                checker.warning("registry-path-unresolved", path, f"could not statically resolve script path for alias {entry.alias!r}")
            else:
                script_path = root / "skills" / folder / script
                if (check_missing_folders is None or entry.folder in check_missing_folders) and not script_path.is_file():
                    try:
                        shown_script = script_path.relative_to(checker.root)
                    except ValueError:
                        shown_script = script_path
                    checker.warning("registry-script-missing", path, f"alias {entry.alias!r} points to missing script {shown_script}; fix the registry before claiming CLI registration")
        break
    return result


def choose_skill_dirs(root: Path, raw_skills: list[str] | None, checker: Checker) -> list[Path]:
    if raw_skills:
        result: list[Path] = []
        for raw in raw_skills:
            candidate = (root / raw).resolve() if not Path(raw).is_absolute() else Path(raw).resolve()
            try:
                candidate.relative_to(root)
            except ValueError:
                checker.error("skill-root-escape", raw, "--skill must resolve inside --root")
                continue
            if not candidate.is_dir():
                checker.error("missing-skill-dir", candidate, "--skill directory does not exist")
                continue
            result.append(candidate)
        return result
    skills_root = root / "skills"
    if not skills_root.is_dir():
        checker.error("missing-skills-root", skills_root, "repository root has no skills directory")
        return []
    return [path for path in sorted(skills_root.iterdir()) if path.is_dir() and path.name not in EXCLUDED_FOLDERS and (path / "SKILL.md").is_file()]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Read-only static checker for ClawBio skill, registry, catalog, and INTENTS.json contracts.",
        epilog="Example: %(prog)s --root . --skill skills/my-skill --catalog skills/catalog.json",
    )
    parser.add_argument("--root", required=True, type=Path, help="repository root to inspect (required; no files are written)")
    parser.add_argument("--skill", action="append", dest="skills", help="skill directory relative to root; repeat to check selected skills (default: all)")
    parser.add_argument("--catalog", type=Path, help="catalog JSON relative to root (default: skills/catalog.json)")
    parser.add_argument("--skip-catalog", action="store_true", help="do not inspect the catalog")
    parser.add_argument("--operating", action="store_true", help="enforce the generated operating SKILL.md four-field frontmatter contract")
    parser.add_argument("--strict", action="store_true", help="treat selected authoring warnings as errors where applicable")
    parser.add_argument("--json", action="store_true", dest="as_json", help="print machine-readable findings")
    args = parser.parse_args(argv)

    root = args.root.expanduser().resolve()
    checker = Checker(root, strict=args.strict, operating=args.operating)
    if not root.is_dir():
        checker.error("missing-root", root, "--root must be an existing directory")
    else:
        skill_dirs = choose_skill_dirs(root, args.skills, checker)
        catalog = None if args.skip_catalog else (args.catalog or Path("skills/catalog.json"))
        if catalog is not None:
            catalog = catalog if catalog.is_absolute() else root / catalog
            checker.run(skill_dirs, catalog)
        else:
            checker.run(skill_dirs, None)

    findings = checker.findings
    if args.strict:
        for finding in findings:
            if finding.level == "warning":
                finding.level = "error"
    errors = [finding for finding in findings if finding.level == "error"]
    if args.as_json:
        print(json.dumps([asdict(item) for item in findings], indent=2, sort_keys=True))
    else:
        for finding in findings:
            print(f"{finding.level.upper():7} {finding.code:30} {finding.path}: {finding.message}")
        print(f"Checked {len(skill_dirs) if 'skill_dirs' in locals() else 0} skill director{'y' if len(skill_dirs if 'skill_dirs' in locals() else []) == 1 else 'ies'}; {len(errors)} error(s), {len(findings) - len(errors)} warning(s).")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
