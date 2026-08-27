#!/usr/bin/env python3
"""Tiny AST-to-graph smoke check inspired by the code2 workflow."""

from __future__ import annotations

import ast


def build_smoke_graph(code: str) -> tuple[int, int]:
    tree = ast.parse(code)
    nodes = list(ast.walk(tree))
    edges = 0
    for node in nodes:
        edges += sum(1 for _ in ast.iter_child_nodes(node))
    return len(nodes), edges


def main() -> None:
    code = """

def add(x, y):
    return x + y
"""
    node_count, edge_count = build_smoke_graph(code)
    print("ast_nodes:", node_count)
    print("ast_edges:", edge_count)

    try:
        build_smoke_graph("def broken(:\n    pass")
    except SyntaxError:
        print("syntax_error_handled: yes")
    else:
        raise SystemExit("expected syntax error was not raised")


if __name__ == "__main__":
    main()
