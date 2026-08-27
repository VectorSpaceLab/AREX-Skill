#!/usr/bin/env python3
"""Summarize a Pydantic AI checkout for maintainer validation planning.

Usage:
    python scripts/check_repo_context.py [--root PATH]

The script is read-only, makes no network requests, does not import provider SDKs,
and does not print absolute checkout paths. It can run from any current working
directory as long as the repository root is discoverable from `--root` or a parent
of the current directory.
"""

from __future__ import annotations

import argparse
import ast
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

WORKSPACE_MARKERS = (
    'pyproject.toml',
    'AGENTS.md',
    'pydantic_ai_slim',
    'pydantic_graph',
    'pydantic_evals',
    'clai',
)
PACKAGE_ROOTS = (
    'pydantic_ai_slim',
    'pydantic_graph',
    'pydantic_evals',
    'clai',
    'examples',
)
AREA_HINTS = {
    'agent core': (
        'pydantic_ai_slim/pydantic_ai/agent',
        'pydantic_ai_slim/pydantic_ai/_agent_graph.py',
        'pydantic_ai_slim/pydantic_ai/run.py',
        'pydantic_ai_slim/pydantic_ai/result.py',
        'tests/test_agent.py',
        'tests/test_deps.py',
    ),
    'tools and toolsets': (
        'pydantic_ai_slim/pydantic_ai/tools.py',
        'pydantic_ai_slim/pydantic_ai/toolsets',
        'pydantic_ai_slim/pydantic_ai/_function_schema.py',
        'tests/test_tools.py',
        'tests/test_toolsets.py',
        'tests/test_function_schema.py',
    ),
    'outputs and messages': (
        'pydantic_ai_slim/pydantic_ai/output.py',
        'pydantic_ai_slim/pydantic_ai/messages.py',
        'pydantic_ai_slim/pydantic_ai/_output.py',
        'tests/test_messages.py',
        'tests/test_agent_output_schemas.py',
    ),
    'models and providers': (
        'pydantic_ai_slim/pydantic_ai/models',
        'pydantic_ai_slim/pydantic_ai/providers',
        'pydantic_ai_slim/pydantic_ai/profiles',
        'pydantic_ai_slim/pydantic_ai/native_tools',
        'tests/models',
        'tests/providers',
        'tests/profiles',
    ),
    'mcp and integrations': (
        'pydantic_ai_slim/pydantic_ai/mcp.py',
        'pydantic_ai_slim/pydantic_ai/capabilities',
        'pydantic_ai_slim/pydantic_ai/durable_exec',
        'pydantic_ai_slim/pydantic_ai/ui',
        'tests/test_mcp.py',
        'tests/test_capabilities.py',
        'tests/test_ag_ui.py',
    ),
    'evals and graph': (
        'pydantic_evals',
        'pydantic_graph',
        'tests/evals',
        'tests/graph',
    ),
    'cli and apps': (
        'clai',
        'pydantic_ai_slim/pydantic_ai/_cli',
        'examples',
        'tests/test_cli.py',
        'tests/test_examples.py',
    ),
    'repo development': (
        'AGENTS.md',
        'agent_docs',
        'CONTRIBUTING.md',
        'Makefile',
        '.pre-commit-config.yaml',
        'scripts',
        '.claude/skills',
    ),
}


@dataclass(frozen=True)
class VcrInventory:
    cassette_dirs: int
    cassette_files: int
    vcr_marked_tests: int
    test_modules_with_vcr: int


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Summarize Pydantic AI repo context without side effects.')
    parser.add_argument('--root', type=Path, default=None, help='Repository root or a path inside the repository.')
    parser.add_argument(
        '--check-cassettes',
        action='store_true',
        help='Also report cassette files that do not appear to match VCR-marked tests.',
    )
    return parser.parse_args()


def find_repo_root(start: Path) -> Path:
    current = start.resolve()
    if current.is_file():
        current = current.parent
    for candidate in (current, *current.parents):
        if all((candidate / marker).exists() for marker in WORKSPACE_MARKERS):
            return candidate
    raise SystemExit('Could not find a Pydantic AI repository root from the supplied path.')


def rel(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.name


def count_files(root: Path, pattern: str) -> int:
    return sum(1 for path in root.glob(pattern) if path.is_file())


def package_status(root: Path) -> list[str]:
    rows: list[str] = []
    for package_root in PACKAGE_ROOTS:
        path = root / package_root
        pyproject = path / 'pyproject.toml'
        rows.append(f'- {package_root}: {"present" if pyproject.exists() else "missing pyproject.toml"}')
    return rows


def read_git_value(root: Path, *args: str) -> str | None:
    try:
        result = subprocess.run(
            ('git', *args),
            cwd=root,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def git_summary(root: Path) -> list[str]:
    branch = read_git_value(root, 'branch', '--show-current') or '<unknown>'
    commit = read_git_value(root, 'rev-parse', '--short=12', 'HEAD') or '<unknown>'
    porcelain = read_git_value(root, 'status', '--short')
    changed_count = 0 if porcelain is None else len([line for line in porcelain.splitlines() if line.strip()])
    return [f'- branch: {branch}', f'- commit: {commit}', f'- changed files: {changed_count}']


def has_vcr_marker(decorator_list: list[ast.expr]) -> bool:
    for decorator in decorator_list:
        if isinstance(decorator, ast.Attribute) and decorator.attr == 'vcr':
            return True
        if isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute) and decorator.func.attr == 'vcr':
            return True
    return False


def module_has_vcr_marker(tree: ast.Module) -> bool:
    for node in ast.iter_child_nodes(tree):
        if not isinstance(node, ast.Assign):
            continue
        if any(isinstance(target, ast.Name) and target.id == 'pytestmark' for target in node.targets):
            return 'vcr' in ast.dump(node.value)
    return False


def count_vcr_tests(test_file: Path) -> int:
    try:
        tree = ast.parse(test_file.read_text(encoding='utf-8'))
    except (OSError, SyntaxError, UnicodeDecodeError):
        return 0
    module_marked = module_has_vcr_marker(tree)
    count = 0
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name.startswith('test_') and (module_marked or has_vcr_marker(node.decorator_list)):
                count += 1
        elif isinstance(node, ast.ClassDef):
            class_marked = has_vcr_marker(node.decorator_list)
            for method in ast.iter_child_nodes(node):
                if isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if method.name.startswith('test_') and (module_marked or class_marked or has_vcr_marker(method.decorator_list)):
                        count += 1
    return count


def vcr_inventory(root: Path) -> VcrInventory:
    cassette_dirs = [path for path in (root / 'tests').rglob('cassettes') if path.is_dir()] if (root / 'tests').exists() else []
    cassette_files = count_files(root, 'tests/**/cassettes/**/*.yaml')
    vcr_counts = [count_vcr_tests(path) for path in (root / 'tests').rglob('test_*.py')]
    return VcrInventory(
        cassette_dirs=len(cassette_dirs),
        cassette_files=cassette_files,
        vcr_marked_tests=sum(vcr_counts),
        test_modules_with_vcr=sum(1 for count in vcr_counts if count),
    )


def sanitize_cassette_name(name: str) -> str:
    for char in r'''<>?%*:|"'/\\''':
        name = name.replace(char, '-')
    return name


def collect_vcr_test_names(test_file: Path) -> set[str]:
    try:
        tree = ast.parse(test_file.read_text(encoding='utf-8'))
    except (OSError, SyntaxError, UnicodeDecodeError):
        return set()
    module_marked = module_has_vcr_marker(tree)
    names: set[str] = set()
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name.startswith('test_') and (module_marked or has_vcr_marker(node.decorator_list)):
                names.add(sanitize_cassette_name(node.name))
        elif isinstance(node, ast.ClassDef):
            class_marked = has_vcr_marker(node.decorator_list)
            for method in ast.iter_child_nodes(node):
                if isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if method.name.startswith('test_') and (module_marked or class_marked or has_vcr_marker(method.decorator_list)):
                        names.add(sanitize_cassette_name(f'{node.name}.{method.name}'))
    return names


def cassette_orphans(root: Path) -> list[str]:
    tests: dict[str, set[str]] = {}
    for test_file in (root / 'tests').rglob('test_*.py'):
        names = collect_vcr_test_names(test_file)
        if names:
            tests.setdefault(test_file.stem, set()).update(names)

    orphans: list[str] = []
    for cassette_dir in (root / 'tests').rglob('cassettes'):
        if not cassette_dir.is_dir():
            continue
        for test_dir in sorted(path for path in cassette_dir.iterdir() if path.is_dir()):
            expected = tests.get(test_dir.name, set())
            for cassette in sorted(test_dir.glob('*.yaml')):
                stem = cassette.stem[:-4] if cassette.stem.endswith('.xai') else cassette.stem
                base_name = stem.split('[', 1)[0]
                if stem not in expected and base_name not in expected:
                    orphans.append(rel(cassette, root))
    return orphans


def existing_paths(root: Path, paths: tuple[str, ...]) -> list[str]:
    existing: list[str] = []
    for item in paths:
        if (root / item).exists():
            existing.append(item)
    return existing


def area_summary(root: Path) -> list[str]:
    rows: list[str] = []
    for area, paths in AREA_HINTS.items():
        matched = existing_paths(root, paths)
        if matched:
            rows.append(f'- {area}: {len(matched)} evidence path(s), e.g. {", ".join(matched[:3])}')
        else:
            rows.append(f'- {area}: no expected evidence paths found')
    return rows


def validation_hints(root: Path) -> list[str]:
    hints = [
        '- Target a changed test first: uv run pytest path/to/test.py::test_name -q',
        '- Target typecheck for source edits: PYRIGHT_PYTHON_IGNORE_WARNINGS=1 uv run pyright path/to/file.py',
        '- Target lint/format for Python edits: uv run ruff format path/to/file.py && uv run ruff check path/to/file.py',
    ]
    if (root / 'tests/test_examples.py').exists():
        hints.append('- For docs examples: uv run pytest tests/test_examples.py -k "path_or_title" -q')
    if (root / 'tests').exists():
        hints.append('- For cassette churn from this sub-skill directory: python scripts/check_repo_context.py --check-cassettes')
    if (root / 'Makefile').exists():
        hints.append('- For broad final gates: make lint, make typecheck, make test, or make testcov as scope requires')
    return hints


def main() -> int:
    args = parse_args()
    try:
        root = find_repo_root(args.root or Path.cwd())
    except SystemExit:
        if args.root is not None:
            raise
        root = find_repo_root(Path(__file__))
    inventory = vcr_inventory(root)

    print('Pydantic AI repository context')
    print('==============================')
    print(f'repository root: {rel(root, root) or "."}')
    print()

    print('Git')
    print('\n'.join(git_summary(root)))
    print()

    print('Workspace packages')
    print('\n'.join(package_status(root)))
    print()

    print('Key files')
    key_files = (
        'AGENTS.md',
        'agent_docs/index.md',
        'CONTRIBUTING.md',
        'Makefile',
        '.pre-commit-config.yaml',
        'docs/AGENTS.md',
        'tests/AGENTS.md',
    )
    for key_file in key_files:
        print(f'- {key_file}: {"present" if (root / key_file).exists() else "missing"}')
    print()

    print('Tests and cassettes')
    print(f'- test files: {count_files(root, "tests/**/test_*.py")}')
    print(f'- cassette directories: {inventory.cassette_dirs}')
    print(f'- cassette YAML files: {inventory.cassette_files}')
    print(f'- VCR-marked tests found by AST scan: {inventory.vcr_marked_tests}')
    print(f'- test modules with VCR markers: {inventory.test_modules_with_vcr}')
    print()

    print('Generated skill context')
    print(f'- runtime skill root in this checkout: {"present" if (root / "skills/pydantic-ai").exists() else "missing"}')
    print(f'- review artifact root: {"present" if (root / "skills/tests/pydantic-ai").exists() else "missing"}')
    print(f'- package user skill: {"present" if (root / "pydantic_ai_slim/pydantic_ai/.agents/skills/building-pydantic-ai-agents/SKILL.md").exists() else "missing"}')
    print()

    print('Area evidence')
    print('\n'.join(area_summary(root)))
    print()

    print('Validation hints')
    print('\n'.join(validation_hints(root)))

    if args.check_cassettes:
        print()
        print('Cassette pairing check')
        orphans = cassette_orphans(root)
        if orphans:
            print(f'- orphaned cassette candidates: {len(orphans)}')
            for orphan in orphans[:50]:
                print(f'  - {orphan}')
            if len(orphans) > 50:
                print(f'  - ... {len(orphans) - 50} more')
            return 1
        print('- orphaned cassette candidates: 0')
    return 0


if __name__ == '__main__':
    sys.exit(main())
