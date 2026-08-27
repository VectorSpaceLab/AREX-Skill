#!/usr/bin/env python3
"""Extract LangBot HTTP routes and MCP tool names from a checkout.

This is a static parser; it does not import or start LangBot.
"""
from __future__ import annotations

import argparse
import ast
import json
import pathlib


def literal(node):
    try:
        return ast.literal_eval(node)
    except Exception:
        return ast.unparse(node) if hasattr(ast, 'unparse') else '?'


def extract_routes(repo: pathlib.Path) -> list[dict]:
    base_dir = repo / 'src/langbot/pkg/api/http/controller/groups'
    routes = []
    for path in sorted(base_dir.rglob('*.py')) if base_dir.exists() else []:
        tree = ast.parse(path.read_text(encoding='utf-8'))
        for cls in [n for n in tree.body if isinstance(n, ast.ClassDef)]:
            base = ''
            group_name = cls.name
            for dec in cls.decorator_list:
                if isinstance(dec, ast.Call) and getattr(dec.func, 'attr', '') == 'group_class':
                    if len(dec.args) >= 2:
                        group_name = str(literal(dec.args[0]))
                        base = str(literal(dec.args[1]))
            for node in ast.walk(cls):
                if not isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef)):
                    continue
                for dec in node.decorator_list:
                    if not (isinstance(dec, ast.Call) and getattr(dec.func, 'attr', '') == 'route'):
                        continue
                    rule = str(literal(dec.args[0])) if dec.args else ''
                    methods = ['GET']
                    auth = 'USER_TOKEN'
                    permission = None
                    for kw in dec.keywords:
                        if kw.arg == 'methods':
                            methods = [str(literal(e)) for e in getattr(kw.value, 'elts', [])]
                        elif kw.arg == 'auth_type':
                            auth = ast.unparse(kw.value).split('.')[-1]
                        elif kw.arg == 'permission':
                            permission = ast.unparse(kw.value).replace('Permission.', '')
                    routes.append({
                        'methods': methods,
                        'path': base + rule,
                        'auth': auth,
                        'permission': permission,
                        'group': group_name,
                        'source': str(path.relative_to(repo)),
                    })
    return routes


def extract_mcp_tools(repo: pathlib.Path) -> list[dict]:
    path = repo / 'src/langbot/pkg/api/mcp/server.py'
    if not path.exists():
        return []
    tree = ast.parse(path.read_text(encoding='utf-8'))
    tools = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef)):
            continue
        desc = None
        for dec in node.decorator_list:
            if isinstance(dec, ast.Call) and getattr(dec.func, 'attr', '') == 'tool':
                for kw in dec.keywords:
                    if kw.arg == 'description':
                        desc = str(literal(kw.value))
                tools.append({'name': node.name, 'description': desc, 'source': str(path.relative_to(repo))})
    return tools


def print_markdown(routes: list[dict], tools: list[dict]) -> None:
    print('# LangBot Route and MCP Tool Map')
    print('\n## HTTP Routes\n')
    print('| Methods | Path | Auth | Permission | Source |')
    print('|---|---|---|---|---|')
    for r in routes:
        print(f"| {'/'.join(r['methods'])} | `{r['path']}` | `{r['auth']}` | `{r['permission'] or '-'}` | `{r['source']}` |")
    print('\n## MCP Tools\n')
    print('| Tool | Description | Source |')
    print('|---|---|---|')
    for t in tools:
        print(f"| `{t['name']}` | {t['description'] or ''} | `{t['source']}` |")


def main() -> int:
    parser = argparse.ArgumentParser(description='Statically extract LangBot HTTP routes and MCP tools.')
    parser.add_argument('--repo-root', default='.', help='LangBot checkout root')
    parser.add_argument('--format', choices=['markdown', 'json'], default='markdown')
    args = parser.parse_args()
    repo = pathlib.Path(args.repo_root).resolve()
    data = {'routes': extract_routes(repo), 'mcp_tools': extract_mcp_tools(repo)}
    if args.format == 'json':
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        print_markdown(data['routes'], data['mcp_tools'])
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
