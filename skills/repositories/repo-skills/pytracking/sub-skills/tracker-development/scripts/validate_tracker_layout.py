#!/usr/bin/env python3
"""Static PyTracking tracker/parameter layout validator.

This helper only reads files under --repo-root. It does not import PyTracking,
load checkpoints, download data, run tracking, or run training.
"""

from __future__ import annotations

import argparse
import ast
import difflib
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


MODULE_RE = re.compile(r"^[A-Za-z_]\w*$")


class Report:
    def __init__(self) -> None:
        self.entries: List[Dict[str, str]] = []
        self.meta: Dict[str, Any] = {}

    def add(self, level: str, message: str, hint: Optional[str] = None) -> None:
        entry = {"level": level, "message": message}
        if hint:
            entry["hint"] = hint
        self.entries.append(entry)

    def ok(self, message: str, hint: Optional[str] = None) -> None:
        self.add("OK", message, hint)

    def info(self, message: str, hint: Optional[str] = None) -> None:
        self.add("INFO", message, hint)

    def warn(self, message: str, hint: Optional[str] = None) -> None:
        self.add("WARNING", message, hint)

    def error(self, message: str, hint: Optional[str] = None) -> None:
        self.add("ERROR", message, hint)

    @property
    def has_errors(self) -> bool:
        return any(e["level"] == "ERROR" for e in self.entries)

    def print_human(self) -> None:
        for entry in self.entries:
            print(f"{entry['level']}: {entry['message']}")
            if "hint" in entry:
                print(f"  HINT: {entry['hint']}")

    def as_json(self) -> Dict[str, Any]:
        return {"ok": not self.has_errors, "meta": self.meta, "entries": self.entries}


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate a PyTracking tracker package and parameter module layout without importing heavy code.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python validate_tracker_layout.py --repo-root /path/to/pytracking --tracker-name dimp --param-name dimp50
  python validate_tracker_layout.py --repo-root . --tracker-name mytracker --param-name default --json

If --tracker-name and --param-name are omitted, the helper lists available tracker and parameter modules.
""",
    )
    parser.add_argument(
        "--repo-root",
        default=".",
        help="Repository root containing pytracking/tracker and pytracking/parameter (default: current directory).",
    )
    parser.add_argument("--tracker-name", help="Tracker package name under pytracking/tracker.")
    parser.add_argument("--param-name", help="Parameter module name under pytracking/parameter/<tracker-name>.")
    parser.add_argument("--json", action="store_true", help="Emit a machine-readable JSON report.")
    return parser.parse_args(argv)


def parse_python(path: Path, label: str, report: Report) -> Optional[ast.Module]:
    try:
        return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except FileNotFoundError:
        report.error(f"Missing {label}: {path}")
    except SyntaxError as exc:
        report.error(f"Syntax error in {label}: {path}:{exc.lineno}:{exc.offset}: {exc.msg}")
    except OSError as exc:
        report.error(f"Could not read {label}: {path} ({exc})")
    return None


def module_name_ok(name: str) -> bool:
    return bool(MODULE_RE.match(name)) and Path(name).name == name


def close_hint(name: str, candidates: Iterable[str]) -> Optional[str]:
    matches = difflib.get_close_matches(name, list(candidates), n=3)
    if matches:
        return "Did you mean: {}?".format(", ".join(matches))
    return None


def list_dirs(root: Path, exclude: Iterable[str] = ()) -> List[str]:
    excluded = set(exclude)
    if not root.is_dir():
        return []
    return sorted(p.name for p in root.iterdir() if p.is_dir() and p.name not in excluded)


def list_param_files(param_root: Path, tracker_name: Optional[str] = None) -> Dict[str, List[str]]:
    out: Dict[str, List[str]] = {}
    roots = [param_root / tracker_name] if tracker_name else [p for p in sorted(param_root.iterdir()) if p.is_dir()] if param_root.is_dir() else []
    for folder in roots:
        if folder.is_dir():
            out[folder.name] = sorted(p.stem for p in folder.glob("*.py") if p.name != "__init__.py")
    return out


def extract_name(node: ast.AST) -> Optional[str]:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = extract_name(node.value)
        return f"{base}.{node.attr}" if base else node.attr
    return None


def find_function(tree: ast.Module, name: str) -> Optional[ast.FunctionDef]:
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    return None


def required_positional_count(fn: ast.FunctionDef) -> int:
    positional = list(fn.args.posonlyargs) + list(fn.args.args)
    defaults = list(fn.args.defaults)
    return max(0, len(positional) - len(defaults))


def relative_imports(tree: ast.Module) -> Dict[str, Tuple[Optional[str], str]]:
    imports: Dict[str, Tuple[Optional[str], str]] = {}
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.level >= 1:
            for alias in node.names:
                local_name = alias.asname or alias.name
                imports[local_name] = (node.module, alias.name)
    return imports


def class_defs(tree: ast.Module) -> Dict[str, ast.ClassDef]:
    return {node.name: node for node in tree.body if isinstance(node, ast.ClassDef)}


def base_names(cls: ast.ClassDef) -> List[str]:
    return [extract_name(base) or ast.dump(base) for base in cls.bases]


def class_method_names(cls: ast.ClassDef) -> List[str]:
    return [node.name for node in cls.body if isinstance(node, ast.FunctionDef)]


def class_attr_string(cls: ast.ClassDef, attr_name: str) -> Optional[str]:
    for node in cls.body:
        target: Optional[ast.AST] = None
        value: Optional[ast.AST] = None
        if isinstance(node, ast.Assign):
            for candidate in node.targets:
                if isinstance(candidate, ast.Name) and candidate.id == attr_name:
                    target = candidate
                    value = node.value
                    break
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.target.id == attr_name:
            target = node.target
            value = node.value
        if target is not None and isinstance(value, ast.Constant) and isinstance(value.value, str):
            return value.value
    return None


def call_names(tree_or_node: ast.AST) -> List[str]:
    names: List[str] = []
    for node in ast.walk(tree_or_node):
        if isinstance(node, ast.Call):
            name = extract_name(node.func)
            if name:
                names.append(name.split(".")[-1])
    return names


def net_path_values(tree_or_node: ast.AST) -> List[str]:
    values: List[str] = []
    for node in ast.walk(tree_or_node):
        if isinstance(node, ast.Call):
            for kw in node.keywords:
                if kw.arg == "net_path" and isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                    values.append(kw.value.value)
    return sorted(set(values))


def returns_value(fn: ast.FunctionDef) -> bool:
    return any(isinstance(node, ast.Return) and node.value is not None for node in ast.walk(fn))


def validate_tracker(tracker_dir: Path, tracker_name: str, report: Report) -> None:
    init_file = tracker_dir / "__init__.py"
    if not init_file.exists():
        report.error(
            f"Tracker package '{tracker_name}' is missing __init__.py",
            "Add pytracking/tracker/<tracker>/__init__.py with get_tracker_class().",
        )
        return

    tree = parse_python(init_file, "tracker __init__.py", report)
    if tree is None:
        return

    report.ok(f"Found tracker package: {tracker_dir}")
    get_cls = find_function(tree, "get_tracker_class")
    if get_cls is None:
        report.error(
            "Tracker __init__.py does not define get_tracker_class()",
            "Use: from .mytracker import MyTracker; def get_tracker_class(): return MyTracker",
        )
        return

    if required_positional_count(get_cls) != 0:
        report.error("get_tracker_class() must take no required arguments")
    else:
        report.ok("get_tracker_class() exists and takes no required arguments")

    return_names = [extract_name(node.value) for node in ast.walk(get_cls) if isinstance(node, ast.Return) and node.value]
    return_names = [name for name in return_names if name]
    if not return_names:
        report.error("get_tracker_class() does not return a class object")
        return

    returned = return_names[0].split(".")[-1]
    report.ok(f"get_tracker_class() returns: {returned}")

    imports = relative_imports(tree)
    impl_path: Optional[Path] = None
    class_name = returned
    if returned in imports:
        module, imported_name = imports[returned]
        class_name = imported_name
        if module:
            impl_path = tracker_dir.joinpath(*module.split(".")).with_suffix(".py")
            if not impl_path.exists():
                report.error(
                    f"Returned class '{returned}' is imported from .{module}, but {impl_path.name} is missing",
                    "Fix the relative import or add the implementation file.",
                )
                return
            if imported_name != returned:
                report.info(f"Returned name '{returned}' is an alias for imported class '{imported_name}'")
        else:
            report.warn(
                f"Returned class '{returned}' uses a package-level relative import that cannot be resolved statically",
                "Prefer an explicit import such as from .mytracker import MyTracker.",
            )
    else:
        report.warn(
            f"Could not find a relative import for returned class '{returned}' in __init__.py",
            "Ensure the returned class is imported at package level without heavy side effects.",
        )

    if impl_path is None:
        candidates = [p for p in tracker_dir.glob("*.py") if p.name != "__init__.py"]
        if len(candidates) == 1:
            impl_path = candidates[0]
            report.info(f"Using sole implementation candidate for static class checks: {impl_path.name}")
        elif candidates:
            report.info("Implementation candidates: " + ", ".join(p.name for p in candidates))
        return

    impl_tree = parse_python(impl_path, "tracker implementation", report)
    if impl_tree is None:
        return

    classes = class_defs(impl_tree)
    if class_name not in classes:
        report.error(
            f"Implementation file {impl_path.name} does not define class '{class_name}'",
            "Make get_tracker_class() return the actual class defined in the implementation file.",
        )
        return

    cls = classes[class_name]
    bases = base_names(cls)
    if any(base.endswith("BaseTracker") for base in bases):
        report.ok(f"Class '{class_name}' inherits BaseTracker")
    else:
        report.warn(
            f"Class '{class_name}' bases are {bases or 'empty'}; BaseTracker inheritance was not detected",
            "Custom trackers should inherit pytracking.tracker.base.BaseTracker or a compatible subclass.",
        )

    methods = set(class_method_names(cls))
    for method in ("initialize", "track"):
        if method in methods:
            report.ok(f"Class '{class_name}' defines {method}()")
        else:
            report.warn(
                f"Class '{class_name}' does not define {method}() directly",
                "This is only safe if the method is inherited from a compatible tracker subclass.",
            )

    mode = class_attr_string(cls, "multiobj_mode")
    if mode is None:
        report.info("No class-level multiobj_mode found; evaluator will fall back to parameter/default behavior")
    elif mode in {"default", "parallel"}:
        report.ok(f"multiobj_mode = {mode!r}")
    else:
        report.warn(
            f"Unusual multiobj_mode value: {mode!r}",
            "Expected 'parallel' for wrapper-per-object mode or 'default' for tracker-managed multi-object mode.",
        )


def validate_parameters(param_file: Path, param_name: str, report: Report) -> None:
    tree = parse_python(param_file, "parameter file", report)
    if tree is None:
        return

    report.ok(f"Found parameter file: {param_file}")
    params_fn = find_function(tree, "parameters")
    if params_fn is None:
        report.error(
            "Parameter file does not define parameters()",
            "Add def parameters(): params = TrackerParams(); ...; return params",
        )
        return

    if required_positional_count(params_fn) != 0:
        report.error("parameters() must take no required arguments")
    else:
        report.ok("parameters() exists and takes no required arguments")

    if returns_value(params_fn):
        report.ok("parameters() contains a return value")
    else:
        report.error("parameters() does not return a value")

    calls = call_names(params_fn)
    if "TrackerParams" in calls:
        report.ok("parameters() constructs TrackerParams")
    else:
        report.warn(
            "No TrackerParams() call detected inside parameters()",
            "Returning a plain dict or custom object will break trackers that call params.get() or params.has().",
        )

    if "FeatureParams" in calls:
        report.info("FeatureParams() usage detected")
    if "Choice" in calls:
        report.warn("Choice() usage detected; document nondeterminism and seed evaluation if reproducibility matters")

    paths = net_path_values(params_fn)
    if paths:
        report.info("net_path values referenced in parameters(): " + ", ".join(paths))
    else:
        report.info("No explicit net_path keyword detected in parameters(); this is fine for feature-only or checkpoint-free trackers")


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    report = Report()

    repo_root = Path(args.repo_root).expanduser().resolve()
    pytracking_root = repo_root / "pytracking"
    tracker_root = pytracking_root / "tracker"
    param_root = pytracking_root / "parameter"

    report.meta.update(
        {
            "repo_root": str(repo_root),
            "tracker_name": args.tracker_name,
            "param_name": args.param_name,
        }
    )

    if not tracker_root.is_dir():
        report.error(
            f"Missing tracker root: {tracker_root}",
            "Pass --repo-root as the repository root that contains pytracking/tracker.",
        )
    if not param_root.is_dir():
        report.error(
            f"Missing parameter root: {param_root}",
            "Pass --repo-root as the repository root that contains pytracking/parameter.",
        )

    trackers = list_dirs(tracker_root, exclude={"base", "__pycache__"})
    param_catalog = list_param_files(param_root)
    report.meta["available_trackers"] = trackers
    report.meta["available_parameters"] = param_catalog

    if report.has_errors:
        if args.json:
            print(json.dumps(report.as_json(), indent=2, sort_keys=True))
        else:
            report.print_human()
        return 1

    if not args.tracker_name and not args.param_name:
        report.info("No tracker/parameter pair supplied; listing available modules only")
        report.info("Available trackers: " + (", ".join(trackers) if trackers else "<none>"))
        for tracker, params in param_catalog.items():
            report.info(f"Parameters for {tracker}: " + (", ".join(params) if params else "<none>"))
        if args.json:
            print(json.dumps(report.as_json(), indent=2, sort_keys=True))
        else:
            report.print_human()
        return 0

    if not args.tracker_name or not args.param_name:
        report.error("Both --tracker-name and --param-name are required for validation")
        if args.json:
            print(json.dumps(report.as_json(), indent=2, sort_keys=True))
        else:
            report.print_human()
        return 1

    tracker_name = args.tracker_name
    param_name = args.param_name

    for label, value in (("tracker name", tracker_name), ("parameter name", param_name)):
        if not module_name_ok(value):
            report.error(
                f"Invalid {label}: {value!r}",
                "Use a Python module identifier such as mytracker, keep_track, or dimp50; do not include slashes or .py.",
            )

    tracker_dir = tracker_root / tracker_name
    param_dir = param_root / tracker_name
    param_file = param_dir / f"{param_name}.py"

    if not tracker_dir.is_dir():
        report.error(
            f"Tracker directory not found: {tracker_dir}",
            close_hint(tracker_name, trackers) or "Create pytracking/tracker/<tracker_name>/.",
        )
    if not param_dir.is_dir():
        report.error(
            f"Parameter directory not found: {param_dir}",
            close_hint(tracker_name, param_catalog.keys()) or "Create pytracking/parameter/<tracker_name>/.",
        )
    elif not param_file.is_file():
        available = param_catalog.get(tracker_name, [])
        report.error(
            f"Parameter file not found: {param_file}",
            close_hint(param_name, available) or f"Available parameter names for {tracker_name}: {', '.join(available) if available else '<none>'}",
        )

    if not report.has_errors:
        validate_tracker(tracker_dir, tracker_name, report)
        validate_parameters(param_file, param_name, report)

    if args.json:
        print(json.dumps(report.as_json(), indent=2, sort_keys=True))
    else:
        report.print_human()
        if report.has_errors:
            print("\nValidation failed. Fix ERROR entries before running tracker commands.")
        else:
            print("\nValidation passed with no ERROR entries. Review WARNING entries before running tracker commands.")

    return 1 if report.has_errors else 0


if __name__ == "__main__":
    sys.exit(main())
