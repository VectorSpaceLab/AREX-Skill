#!/usr/bin/env python3
"""Static AST validator for Mycodo custom module files.

This tool never imports the target module. It checks conservative source-shape
contracts that Mycodo custom module import/update flows expect, then emits
warnings that still require live Mycodo review.
"""
from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set

CONTRACTS = {
    "input": {
        "dict": "INPUT_INFORMATION",
        "unique": "input_name_unique",
        "name": "input_name",
        "classes": {"InputModule"},
        "base": "AbstractInput",
        "methods": {"initialize", "get_measurement"},
        "measurement_required": True,
    },
    "output": {
        "dict": "OUTPUT_INFORMATION",
        "unique": "output_name_unique",
        "name": "output_name",
        "classes": {"OutputModule"},
        "base": "AbstractOutput",
        "methods": {"initialize", "output_switch", "is_on", "is_setup"},
        "measurement_required": True,
    },
    "function": {
        "dict": "FUNCTION_INFORMATION",
        "unique": "function_name_unique",
        "name": "function_name",
        "classes": {"CustomModule"},
        "base": "AbstractFunction",
        "methods": {"initialize"},
        "soft_methods": {"loop"},
        "measurement_required": False,
    },
    "action": {
        "dict": "ACTION_INFORMATION",
        "unique": "name_unique",
        "name": "name",
        "classes": {"ActionModule"},
        "base": "AbstractFunctionAction",
        "methods": {"initialize", "run_action", "is_setup"},
        "measurement_required": False,
    },
    "widget": {
        "dict": "WIDGET_INFORMATION",
        "unique": "widget_name_unique",
        "name": "widget_name",
        "classes": {"WidgetModule", "CustomModule", "Widget"},
        "base": "AbstractWidget",
        "methods": set(),
        "soft_methods": {"execute_refresh"},
        "measurement_required": False,
    },
}

VALID_DEP_SOURCES = {"internal", "pip-pypi", "apt"}
LIST_KEYS = ("dependencies_module", "custom_options", "custom_channel_options", "custom_commands")
WIDGET_SNIPPETS = (
    "widget_dashboard_head",
    "widget_dashboard_title_bar",
    "widget_dashboard_body",
    "widget_dashboard_js",
    "widget_dashboard_js_ready",
    "widget_dashboard_js_ready_end",
)
UNSAFE_CALLS = {
    "subprocess.run", "subprocess.Popen", "subprocess.call", "subprocess.check_call",
    "subprocess.check_output", "os.system", "os.popen", "open", "requests.get",
    "requests.post", "requests.put", "requests.patch", "requests.delete",
    "urllib.request.urlopen", "socket.create_connection", "time.sleep", "serial.Serial",
    "smbus.SMBus", "DaemonControl",
}


def string_key(node: ast.AST) -> Optional[str]:
    return node.value if isinstance(node, ast.Constant) and isinstance(node.value, str) else None


def literal(node: Optional[ast.AST]):
    if node is None:
        return None
    try:
        return ast.literal_eval(node)
    except Exception:
        return None


def type_name(node: Optional[ast.AST]) -> str:
    if node is None:
        return "missing"
    if isinstance(node, ast.List):
        return "list"
    if isinstance(node, ast.Tuple):
        return "tuple"
    if isinstance(node, ast.Dict):
        return "dict"
    if isinstance(node, ast.Constant):
        return type(node.value).__name__
    if isinstance(node, ast.Name):
        return f"name:{node.id}"
    return type(node).__name__


def call_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = call_name(node.value)
        return f"{parent}.{node.attr}" if parent else node.attr
    return ""


def dict_entries(node: ast.Dict) -> Dict[str, ast.AST]:
    out: Dict[str, ast.AST] = {}
    for key, value in zip(node.keys, node.values):
        if key is None:
            continue
        name = string_key(key)
        if name is not None:
            out[name] = value
    return out


def assignment_name(stmt: ast.AST) -> Optional[str]:
    if isinstance(stmt, ast.Assign):
        for target in stmt.targets:
            if isinstance(target, ast.Name):
                return target.id
    if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
        return stmt.target.id
    return None


def assignment_value(stmt: ast.AST) -> Optional[ast.AST]:
    if isinstance(stmt, ast.Assign):
        return stmt.value
    if isinstance(stmt, ast.AnnAssign):
        return stmt.value
    return None


def iter_without_nested_defs(node: ast.AST) -> Iterable[ast.AST]:
    stack = [node]
    while stack:
        cur = stack.pop()
        yield cur
        if cur is not node and isinstance(cur, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
            continue
        stack.extend(reversed(list(ast.iter_child_nodes(cur))))


class Validator:
    def __init__(self, kind: str, target: Path, tree: ast.Module):
        self.kind = kind
        self.target = target
        self.tree = tree
        self.contract = CONTRACTS[kind]
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.info: List[str] = []
        self.assignments: Dict[str, ast.AST] = {}
        self.classes: Dict[str, ast.ClassDef] = {}
        self.info_entries: Dict[str, ast.AST] = {}

    def run(self) -> "Validator":
        self.collect()
        self.check_info_dict()
        self.check_class()
        self.check_lists()
        self.check_measurements()
        self.check_kind_specific()
        self.check_filename_unique()
        self.check_top_level()
        return self

    def collect(self) -> None:
        for stmt in self.tree.body:
            name = assignment_name(stmt)
            value = assignment_value(stmt)
            if name and value is not None:
                self.assignments[name] = value
            if isinstance(stmt, ast.ClassDef):
                self.classes[stmt.name] = stmt

    def resolve(self, node: ast.AST) -> ast.AST:
        if isinstance(node, ast.Name) and node.id in self.assignments:
            return self.assignments[node.id]
        return node

    def check_info_dict(self) -> None:
        dict_name = self.contract["dict"]
        node = self.assignments.get(dict_name)
        if node is None:
            self.errors.append(f"missing expected metadata dictionary {dict_name}")
            return
        if not isinstance(node, ast.Dict):
            self.errors.append(f"{dict_name} should be a top-level dict literal; found {type_name(node)}")
            return
        self.info_entries = dict_entries(node)
        self.info.append(f"found {dict_name} with {len(self.info_entries)} string keys")
        for key in (self.contract["unique"], self.contract["name"]):
            if key not in self.info_entries:
                self.warnings.append(f"{dict_name} missing key {key!r}")
            elif literal(self.info_entries[key]) == "":
                self.warnings.append(f"{dict_name} key {key!r} is empty")

    def check_class(self) -> None:
        no_class = self.kind == "widget" and literal(self.info_entries.get("no_class")) is True
        present = self.contract["classes"] & set(self.classes)
        if not present:
            if no_class:
                self.info.append("widget declares no_class=True; runtime class is optional")
            else:
                self.errors.append("missing expected class: one of " + ", ".join(sorted(self.contract["classes"])))
            return
        for name in sorted(present):
            cls = self.classes[name]
            bases = {call_name(base) for base in cls.bases}
            base = self.contract["base"]
            if base and not any(b == base or b.endswith("." + base) for b in bases):
                self.warnings.append(f"class {name} does not visibly inherit {base}; bases={sorted(bases)}")
            methods = {item.name for item in cls.body if isinstance(item, ast.FunctionDef)}
            for method in sorted(self.contract.get("methods", set())):
                if method not in methods:
                    self.warnings.append(f"class {name} missing method {method}()")
            for method in sorted(self.contract.get("soft_methods", set())):
                if method not in methods:
                    self.warnings.append(f"class {name} does not define optional/common method {method}()")
            self.info.append(f"found class {name}")

    def check_lists(self) -> None:
        if not self.info_entries:
            return
        for key in LIST_KEYS:
            if key not in self.info_entries:
                if key in {"dependencies_module", "custom_options"}:
                    self.warnings.append(f"{key!r} omitted; use [] when intentionally empty")
                continue
            value = self.resolve(self.info_entries[key])
            if not isinstance(value, ast.List):
                self.warnings.append(f"{key!r} should be a list; found {type_name(value)}")
                continue
            if key == "dependencies_module":
                self.check_dependencies(value)
            elif key in {"custom_options", "custom_channel_options", "custom_commands"}:
                self.check_options(key, value)

    def check_dependencies(self, node: ast.List) -> None:
        for idx, item in enumerate(node.elts):
            if not isinstance(item, ast.Tuple):
                self.warnings.append(f"dependencies_module[{idx}] is not a tuple")
                continue
            if len(item.elts) != 3:
                self.warnings.append(f"dependencies_module[{idx}] should have 3 items, found {len(item.elts)}")
                continue
            source = literal(item.elts[0])
            if source is not None and source not in VALID_DEP_SOURCES:
                self.warnings.append(f"dependencies_module[{idx}][0] should be one of {sorted(VALID_DEP_SOURCES)}, got {source!r}")
            for subidx, elt in enumerate(item.elts):
                if literal(elt) == "":
                    self.warnings.append(f"dependencies_module[{idx}][{subidx}] is empty")

    def check_options(self, key: str, node: ast.List) -> None:
        methods: Set[str] = set()
        for cls in self.classes.values():
            methods.update(item.name for item in cls.body if isinstance(item, ast.FunctionDef))
        seen: Set[str] = set()
        for idx, item in enumerate(node.elts):
            if not isinstance(item, ast.Dict):
                self.warnings.append(f"{key}[{idx}] is not a dict")
                continue
            entry = dict_entries(item)
            typ = literal(entry.get("type"))
            option_id = literal(entry.get("id"))
            if "type" not in entry:
                self.warnings.append(f"{key}[{idx}] missing 'type'")
            if typ not in {"new_line", "message"} and "id" not in entry:
                self.warnings.append(f"{key}[{idx}] missing 'id'")
            if key != "custom_commands" and typ != "new_line" and "default_value" not in entry:
                self.warnings.append(f"{key}[{idx}] missing 'default_value'")
            if isinstance(option_id, str):
                if option_id in seen:
                    self.warnings.append(f"{key}[{idx}] duplicates id {option_id!r}")
                seen.add(option_id)
            if key == "custom_commands" and typ == "button" and isinstance(option_id, str) and methods and option_id not in methods:
                self.warnings.append(f"custom command button id {option_id!r} has no matching class method")
            if "constraints_pass" in entry and not isinstance(entry["constraints_pass"], (ast.Name, ast.Attribute)):
                self.warnings.append(f"{key}[{idx}] constraints_pass should reference a callable; found {type_name(entry['constraints_pass'])}")

    def check_measurements(self) -> None:
        if not self.info_entries:
            return
        m_node = self.info_entries.get("measurements_dict")
        variable = literal(self.info_entries.get("measurements_variable_amount")) is True
        if m_node is None:
            if self.contract.get("measurement_required"):
                self.warnings.append("measurements_dict missing; import usually requires it for this kind")
            return
        m_node = self.resolve(m_node)
        if not isinstance(m_node, ast.Dict):
            self.warnings.append(f"measurements_dict should resolve to a dict; found {type_name(m_node)}")
            return
        m_keys: Set[int] = set()
        for key, value in zip(m_node.keys, m_node.values):
            lk = literal(key)
            if isinstance(lk, int):
                m_keys.add(lk)
            if isinstance(value, ast.Dict):
                entry = dict_entries(value)
                if self.kind in {"input", "output"}:
                    for required in ("measurement", "unit"):
                        if required not in entry:
                            self.warnings.append(f"measurements_dict[{lk!r}] missing {required!r}")
            else:
                self.warnings.append(f"measurements_dict[{lk!r}] value is not a dict")
        if not m_keys and self.contract.get("measurement_required") and not variable:
            self.warnings.append("measurements_dict appears empty without measurements_variable_amount=True")
        c_node = self.info_entries.get("channels_dict")
        if c_node is None:
            if self.kind == "output":
                self.warnings.append("OUTPUT_INFORMATION usually needs channels_dict")
            return
        c_node = self.resolve(c_node)
        if not isinstance(c_node, ast.Dict):
            self.warnings.append(f"channels_dict should resolve to a dict; found {type_name(c_node)}")
            return
        for key, value in zip(c_node.keys, c_node.values):
            channel = literal(key)
            if not isinstance(value, ast.Dict):
                self.warnings.append(f"channels_dict[{channel!r}] value is not a dict")
                continue
            entry = dict_entries(value)
            if self.kind == "output" and "types" not in entry:
                self.warnings.append(f"channels_dict[{channel!r}] missing 'types' for Output channel")
            if "measurements" in entry:
                refs = literal(entry["measurements"])
                if not isinstance(refs, list):
                    self.warnings.append(f"channels_dict[{channel!r}]['measurements'] should be a list")
                else:
                    for ref in refs:
                        if isinstance(ref, int) and m_keys and ref not in m_keys:
                            self.warnings.append(f"channels_dict[{channel!r}] references missing measurement channel {ref}")

    def check_kind_specific(self) -> None:
        if not self.info_entries:
            return
        if self.kind == "input":
            for key in ("input_manufacturer", "measurements_name"):
                if key not in self.info_entries:
                    self.warnings.append(f"INPUT_INFORMATION missing {key!r}")
        elif self.kind == "output" and "output_types" not in self.info_entries:
            self.warnings.append("OUTPUT_INFORMATION missing 'output_types'")
        elif self.kind == "action" and "application" not in self.info_entries:
            self.warnings.append("ACTION_INFORMATION missing 'application' list")
        elif self.kind == "widget":
            for key in WIDGET_SNIPPETS:
                if key not in self.info_entries:
                    self.warnings.append(f"WIDGET_INFORMATION missing dashboard snippet {key!r}")

    def check_filename_unique(self) -> None:
        unique_node = self.info_entries.get(self.contract["unique"])
        unique = literal(unique_node)
        if isinstance(unique, str) and unique and self.target.stem.lower() != unique.lower():
            self.warnings.append(
                f"filename stem {self.target.stem!r} differs from unique key {unique!r}; initial import uses the lower-case unique key, supported updates compare dictionary keys"
            )

    def check_top_level(self) -> None:
        for stmt in self.tree.body:
            if isinstance(stmt, (ast.Import, ast.ImportFrom, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                continue
            if isinstance(stmt, ast.If) and self.is_main_guard(stmt):
                continue
            if isinstance(stmt, (ast.For, ast.While, ast.With, ast.AsyncWith, ast.Try)):
                self.warnings.append(f"top-level {type(stmt).__name__} executes during Mycodo import; review for side effects")
            for node in iter_without_nested_defs(stmt):
                if isinstance(node, ast.Call):
                    name = call_name(node.func)
                    if name in UNSAFE_CALLS or name.endswith(".start"):
                        self.warnings.append(f"unsafe-looking top-level call {name} executes during import/update validation")
                    elif isinstance(stmt, ast.Expr):
                        self.warnings.append(f"top-level expression call {name or '<call>'} executes during import; review necessity")

    @staticmethod
    def is_main_guard(stmt: ast.If) -> bool:
        test = stmt.test
        return (
            isinstance(test, ast.Compare)
            and isinstance(test.left, ast.Name)
            and test.left.id == "__name__"
            and any(literal(cmp) == "__main__" for cmp in test.comparators)
        )


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Statically validate a Mycodo custom module without importing it."
    )
    parser.add_argument("--kind", required=True, choices=sorted(CONTRACTS), help="Custom module kind to validate.")
    parser.add_argument("path", type=Path, help="Path to the Python module file to validate.")
    return parser.parse_args(argv)


def main(argv: List[str]) -> int:
    args = parse_args(argv)
    if not args.path.is_file():
        print(f"ERROR: file does not exist or is not a file: {args.path}", file=sys.stderr)
        return 2
    try:
        tree = ast.parse(args.path.read_text(encoding="utf-8"), filename=str(args.path))
    except UnicodeDecodeError:
        tree = ast.parse(args.path.read_text(encoding="utf-8-sig"), filename=str(args.path))
    except SyntaxError as exc:
        print(f"ERROR: syntax error in {args.path}: {exc}", file=sys.stderr)
        return 2

    result = Validator(args.kind, args.path, tree).run()
    print(f"Mycodo custom module static validation: {args.path}")
    print(f"Kind: {args.kind}")
    print("No import was performed; warnings are conservative review prompts.")
    if result.errors:
        print("\nERRORS:")
        for item in result.errors:
            print(f"  - {item}")
    if result.warnings:
        print("\nWARNINGS:")
        for item in result.warnings:
            print(f"  - {item}")
    if result.info:
        print("\nINFO:")
        for item in result.info:
            print(f"  - {item}")
    print(f"\nSummary: {len(result.errors)} error(s), {len(result.warnings)} warning(s), {len(result.info)} info note(s).")
    return 2 if result.errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
