#!/usr/bin/env python3
"""Statically compare two OpenCompass Python config files.

The script parses Python AST without importing the configs. It is safe for
configs that would otherwise import optional model backends, but it can only
summarize literal assignments visible in the file being parsed.
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set


class Unknown:
    pass


UNKNOWN = Unknown()


def _safe_literal(node: ast.AST) -> Any:
    try:
        return ast.literal_eval(node)
    except Exception:
        return UNKNOWN


def _name_of_type(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        inner = value.get('type')
        return _name_of_type(inner) if inner is not None else '<dict>'
    if value is UNKNOWN:
        return '<dynamic>'
    return repr(value)


def _call_or_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = _call_or_name(node.value)
        return f'{parent}.{node.attr}' if parent else node.attr
    if isinstance(node, ast.Call):
        return _call_or_name(node.func)
    if isinstance(node, ast.Constant):
        return repr(node.value)
    return '<dynamic>'


def _dict_from_ast(node: ast.AST) -> Any:
    if not isinstance(node, ast.Dict):
        return _safe_literal(node)
    result: Dict[str, Any] = {}
    for key_node, value_node in zip(node.keys, node.values):
        if key_node is None:
            continue
        key = _safe_literal(key_node)
        if key is UNKNOWN:
            key = _call_or_name(key_node)
        if isinstance(value_node, ast.Dict):
            value = _dict_from_ast(value_node)
        elif isinstance(value_node, ast.List):
            value = [_dict_from_ast(item) if isinstance(item, ast.Dict) else _safe_literal(item) for item in value_node.elts]
        elif isinstance(value_node, (ast.Name, ast.Attribute, ast.Call)):
            value = _call_or_name(value_node)
        else:
            value = _safe_literal(value_node)
        result[str(key)] = value
    return result


def _list_of_dicts(node: ast.AST) -> List[Dict[str, Any]]:
    if not isinstance(node, ast.List):
        return []
    items = []
    for item in node.elts:
        value = _dict_from_ast(item)
        if isinstance(value, dict):
            items.append(value)
    return items


def _targets(node: ast.Assign) -> Iterable[str]:
    for target in node.targets:
        if isinstance(target, ast.Name):
            yield target.id
        elif isinstance(target, ast.Tuple):
            for element in target.elts:
                if isinstance(element, ast.Name):
                    yield element.id


def _import_name(node: ast.AST) -> List[str]:
    names: List[str] = []
    if isinstance(node, ast.Import):
        names.extend(alias.asname or alias.name for alias in node.names)
    elif isinstance(node, ast.ImportFrom):
        module = '.' * node.level + (node.module or '')
        for alias in node.names:
            imported = alias.asname or alias.name
            names.append(f'{module}:{imported}')
    return names


def _entry_summary(entry: Dict[str, Any]) -> Dict[str, Any]:
    reader_cfg = entry.get('reader_cfg') if isinstance(entry.get('reader_cfg'), dict) else {}
    infer_cfg = entry.get('infer_cfg') if isinstance(entry.get('infer_cfg'), dict) else {}
    eval_cfg = entry.get('eval_cfg') if isinstance(entry.get('eval_cfg'), dict) else {}
    evaluator = eval_cfg.get('evaluator') if isinstance(eval_cfg.get('evaluator'), dict) else {}
    inferencer = infer_cfg.get('inferencer') if isinstance(infer_cfg.get('inferencer'), dict) else {}
    return {
        'abbr': entry.get('abbr', '<missing>'),
        'type': _name_of_type(entry.get('type', '<missing>')),
        'path': entry.get('path', '<missing>'),
        'reader_input_columns': reader_cfg.get('input_columns', '<missing>'),
        'reader_output_column': reader_cfg.get('output_column', '<missing>'),
        'inferencer': _name_of_type(inferencer.get('type', '<missing>')),
        'evaluator': _name_of_type(evaluator.get('type', '<missing>')),
    }


def _model_summary(entry: Dict[str, Any]) -> Dict[str, Any]:
    return {
        'abbr': entry.get('abbr', '<missing>'),
        'type': _name_of_type(entry.get('type', '<missing>')),
        'path': entry.get('path', '<missing>'),
        'run_cfg': entry.get('run_cfg', '<missing>'),
    }


def analyze(path: Path) -> Dict[str, Any]:
    source = path.read_text(encoding='utf-8')
    tree = ast.parse(source, filename=str(path))
    assigned: Set[str] = set()
    imports: List[str] = []
    datasets: List[Dict[str, Any]] = []
    models: List[Dict[str, Any]] = []

    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            imports.extend(_import_name(node))
        if isinstance(node, ast.Assign):
            names = list(_targets(node))
            assigned.update(names)
            for name in names:
                if name == 'datasets' or name.endswith('_datasets'):
                    datasets.extend(_entry_summary(item) for item in _list_of_dicts(node.value))
                if name == 'models' or name.endswith('_models'):
                    models.extend(_model_summary(item) for item in _list_of_dicts(node.value))

    return {
        'path': str(path),
        'assigned_names': sorted(assigned),
        'imports': sorted(set(imports)),
        'datasets': datasets,
        'models': models,
    }


def _diff(left: Sequence[str], right: Sequence[str]) -> Dict[str, List[str]]:
    left_set = set(left)
    right_set = set(right)
    return {
        'only_left': sorted(left_set - right_set),
        'only_right': sorted(right_set - left_set),
    }


def _abbrs(entries: Sequence[Dict[str, Any]]) -> List[str]:
    return sorted(str(entry.get('abbr', '<missing>')) for entry in entries)


def compare(left: Dict[str, Any], right: Dict[str, Any]) -> Dict[str, Any]:
    return {
        'left': left['path'],
        'right': right['path'],
        'assigned_names': _diff(left['assigned_names'], right['assigned_names']),
        'imports': _diff(left['imports'], right['imports']),
        'dataset_abbrs': _diff(_abbrs(left['datasets']), _abbrs(right['datasets'])),
        'model_abbrs': _diff(_abbrs(left['models']), _abbrs(right['models'])),
        'left_datasets': left['datasets'],
        'right_datasets': right['datasets'],
        'left_models': left['models'],
        'right_models': right['models'],
    }


def _print_diff(title: str, left_name: str, right_name: str, diff: Dict[str, List[str]]) -> None:
    print(title)
    print(f'  Only in {left_name}: {diff["only_left"] or []}')
    print(f'  Only in {right_name}: {diff["only_right"] or []}')


def _print_entries(title: str, entries: Sequence[Dict[str, Any]]) -> None:
    print(title)
    if not entries:
        print('  <none statically visible>')
        return
    for index, entry in enumerate(entries, 1):
        parts = [f'{key}={value!r}' for key, value in entry.items()]
        print(f'  {index}. ' + ', '.join(parts))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Statically compare two OpenCompass config files.')
    parser.add_argument('left', type=Path)
    parser.add_argument('right', type=Path)
    parser.add_argument('--json', action='store_true', help='Emit machine-readable JSON')
    parser.add_argument('--show', default='', help='Comma-separated extra sections: datasets,models,imports,assigned')
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    left = analyze(args.left)
    right = analyze(args.right)
    result = compare(left, right)

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0

    left_name = Path(result['left']).name
    right_name = Path(result['right']).name
    _print_diff('Assigned names', left_name, right_name, result['assigned_names'])
    _print_diff('Dataset abbrs', left_name, right_name, result['dataset_abbrs'])
    _print_diff('Model abbrs', left_name, right_name, result['model_abbrs'])

    sections = {section.strip() for section in args.show.split(',') if section.strip()}
    if 'imports' in sections:
        _print_diff('Imports', left_name, right_name, result['imports'])
    if 'assigned' in sections:
        print(f'{left_name} assigned: {left["assigned_names"]}')
        print(f'{right_name} assigned: {right["assigned_names"]}')
    if 'datasets' in sections:
        _print_entries(f'{left_name} datasets', left['datasets'])
        _print_entries(f'{right_name} datasets', right['datasets'])
    if 'models' in sections:
        _print_entries(f'{left_name} models', left['models'])
        _print_entries(f'{right_name} models', right['models'])
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except SyntaxError as exc:
        print(f'syntax error: {exc}', file=sys.stderr)
        raise SystemExit(2)
    except Exception as exc:
        print(f'error: {exc}', file=sys.stderr)
        raise SystemExit(2)
