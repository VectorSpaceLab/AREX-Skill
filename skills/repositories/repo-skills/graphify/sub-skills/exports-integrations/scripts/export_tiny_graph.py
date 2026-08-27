#!/usr/bin/env python3
"""Create a tiny Graphify graph and exercise safe local export formats.

This helper is self-contained: it does not read the Graphify source checkout, it
requires only an installed ``graphify`` package, and it never contacts Neo4j,
FalkorDB, GitHub, or other external services. It writes into a temporary
``graphify-export-smoke-*`` directory by default and prints validation results.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


def _fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    sys.exit(1)


def _imports() -> dict[str, Any]:
    try:
        import networkx as nx
        from graphify.export import (
            to_canvas,
            to_cypher,
            to_graphml,
            to_html,
            to_json,
            to_obsidian,
            to_svg,
        )
        from graphify.tree_html import write_tree_html
        from graphify.wiki import to_wiki
        from graphify.callflow_html import write_callflow_html
    except Exception as exc:  # pragma: no cover - depends on user's environment
        _fail(
            "Could not import Graphify export dependencies. Install the package "
            "first, for example: pip install graphifyy. Original error: "
            f"{exc}"
        )
    return locals()


def _build_graph(nx: Any) -> tuple[Any, dict[int, list[str]], dict[int, str], dict[int, float], list[dict[str, Any]]]:
    graph = nx.DiGraph()
    graph.add_node(
        "api_client",
        label="ApiClient",
        source_file="src/api.py",
        source_location="L10",
        file_type="code",
        community=0,
    )
    graph.add_node(
        "run",
        label="run()",
        source_file="src/main.py",
        source_location="L4",
        file_type="code",
        community=0,
    )
    graph.add_node(
        "write_html",
        label="write_html()",
        source_file="src/export.py",
        source_location="L22",
        file_type="code",
        community=1,
    )
    graph.add_node(
        "test_export_html",
        label="test_export_html",
        source_file="tests/test_export.py",
        source_location="L5",
        file_type="code",
        community=1,
    )
    graph.add_edge(
        "run",
        "api_client",
        relation="calls",
        confidence="EXTRACTED",
        confidence_score=1.0,
        source_file="src/main.py",
        source_location="L8",
    )
    graph.add_edge(
        "api_client",
        "write_html",
        relation="uses",
        confidence="EXTRACTED",
        confidence_score=1.0,
        source_file="src/api.py",
        source_location="L15",
    )
    graph.add_edge(
        "test_export_html",
        "write_html",
        relation="references",
        confidence="INFERRED",
        confidence_score=0.5,
        source_file="tests/test_export.py",
        source_location="L12",
    )
    communities = {0: ["api_client", "run"], 1: ["write_html", "test_export_html"]}
    labels = {0: "Runtime API", 1: "Export Surface"}
    cohesion = {0: 0.91, 1: 0.82}
    gods = [{"id": "write_html", "label": "write_html()", "degree": 2}]
    return graph, communities, labels, cohesion, gods


def _write_sidecars(out_dir: Path, graph: Any, communities: dict[int, list[str]], labels: dict[int, str], cohesion: dict[int, float], gods: list[dict[str, Any]], to_json: Any) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    graph_path = out_dir / "graph.json"
    ok = to_json(graph, communities, str(graph_path), force=True, community_labels=labels)
    if not ok:
        _fail(f"Graphify refused to write {graph_path}")
    (out_dir / ".graphify_analysis.json").write_text(
        json.dumps(
            {
                "communities": {str(k): v for k, v in communities.items()},
                "cohesion": {str(k): v for k, v in cohesion.items()},
                "gods": gods,
                "surprises": [],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (out_dir / ".graphify_labels.json").write_text(
        json.dumps({str(k): v for k, v in labels.items()}, indent=2),
        encoding="utf-8",
    )
    (out_dir / "GRAPH_REPORT.md").write_text(
        "# Graph Report - tiny export smoke\n\n"
        "## Summary\n"
        "- 4 nodes · 3 edges · 2 communities detected\n\n"
        "## God Nodes\n"
        "1. `write_html()` - 2 edges\n",
        encoding="utf-8",
    )
    return graph_path


def _require_file(path: Path, *, contains: str | None = None) -> None:
    if not path.exists():
        _fail(f"Expected output does not exist: {path}")
    if path.stat().st_size <= 0:
        _fail(f"Expected output is empty: {path}")
    if contains is not None and contains not in path.read_text(encoding="utf-8", errors="replace"):
        _fail(f"Expected {path} to contain {contains!r}")


def _run_cli(args: list[str], cwd: Path) -> str:
    proc = subprocess.run(
        [sys.executable, "-m", "graphify", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=60,
    )
    output = (proc.stdout + proc.stderr).strip()
    if proc.returncode != 0:
        _fail(f"CLI command failed: graphify {' '.join(args)}\n{output}")
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=None,
        help="Directory to create/use. Defaults to a persistent temp directory.",
    )
    parser.add_argument(
        "--api-only",
        action="store_true",
        help="Run Python export APIs only; skip CLI command smoke checks.",
    )
    parser.add_argument(
        "--include-svg",
        action="store_true",
        help="Also try SVG export. This requires the optional graphifyy[svg] extra.",
    )
    args = parser.parse_args()

    symbols = _imports()
    nx = symbols["nx"]

    work_root = args.out_dir or Path(tempfile.mkdtemp(prefix="graphify-export-smoke-"))
    work_root = work_root.expanduser().resolve()
    out_dir = work_root / "graphify-out"

    graph, communities, labels, cohesion, gods = _build_graph(nx)
    graph_path = _write_sidecars(
        out_dir,
        graph,
        communities,
        labels,
        cohesion,
        gods,
        symbols["to_json"],
    )

    # Python API exports: no external services.
    symbols["to_html"](graph, communities, str(out_dir / "graph-api.html"), community_labels=labels, node_limit=50)
    notes = symbols["to_obsidian"](graph, communities, str(out_dir / "obsidian-api"), community_labels=labels, cohesion=cohesion)
    symbols["to_canvas"](graph, communities, str(out_dir / "obsidian-api" / "graph.canvas"), community_labels=labels)
    articles = symbols["to_wiki"](graph, communities, out_dir / "wiki-api", community_labels=labels, cohesion=cohesion, god_nodes_data=gods)
    symbols["to_graphml"](graph, communities, str(out_dir / "graph-api.graphml"))
    symbols["to_cypher"](graph, str(out_dir / "cypher-api.txt"))
    symbols["write_tree_html"](graph_path=graph_path, output_path=out_dir / "GRAPH_TREE-api.html")
    symbols["write_callflow_html"](project=work_root, output=out_dir / "callflow-api.html", max_sections=4)

    svg_status = "skipped"
    if args.include_svg:
        try:
            symbols["to_svg"](graph, communities, str(out_dir / "graph-api.svg"), community_labels=labels)
            svg_status = "written"
        except ImportError as exc:
            svg_status = f"skipped ({exc})"

    cli_outputs: list[str] = []
    if not args.api_only:
        cli_commands = [
            ["export", "html"],
            ["export", "obsidian"],
            ["export", "wiki"],
            ["export", "graphml"],
            ["export", "neo4j"],
            ["export", "falkordb"],
            ["export", "callflow-html", "--output", "graphify-out/callflow-cli.html", "--max-sections", "4"],
            ["tree", "--output", "graphify-out/GRAPH_TREE-cli.html"],
        ]
        for command in cli_commands:
            cli_outputs.append(f"graphify {' '.join(command)} -> {_run_cli(command, work_root).splitlines()[-1]}")
        if args.include_svg:
            cli_outputs.append(f"graphify export svg -> {_run_cli(['export', 'svg'], work_root).splitlines()[-1]}")

    # Validations.
    _require_file(graph_path, contains='"nodes"')
    _require_file(out_dir / "graph-api.html", contains="vis-network")
    _require_file(out_dir / "obsidian-api" / "graph.canvas", contains='"nodes"')
    _require_file(out_dir / "wiki-api" / "index.md")
    _require_file(out_dir / "graph-api.graphml", contains="<graphml")
    _require_file(out_dir / "cypher-api.txt", contains="MERGE")
    _require_file(out_dir / "GRAPH_TREE-api.html", contains="graphify tree viewer")
    _require_file(out_dir / "callflow-api.html", contains="mermaid")
    if not args.api_only:
        _require_file(out_dir / "graph.html")
        _require_file(out_dir / "obsidian" / "graph.canvas")
        _require_file(out_dir / "wiki" / "index.md")
        _require_file(out_dir / "graph.graphml", contains="<graphml")
        _require_file(out_dir / "cypher.txt", contains="MERGE")
        _require_file(out_dir / "callflow-cli.html", contains="mermaid")
        _require_file(out_dir / "GRAPH_TREE-cli.html", contains="graphify tree viewer")

    print("Graphify export smoke passed")
    print(f"Output root: {work_root}")
    print(f"API Obsidian notes/articles: {notes} notes, {articles} wiki articles")
    print(f"SVG: {svg_status}")
    if cli_outputs:
        print("CLI checks:")
        for line in cli_outputs:
            print(f"  - {line}")
    print("No database push, GitHub access, or external service check was performed.")


if __name__ == "__main__":
    main()
