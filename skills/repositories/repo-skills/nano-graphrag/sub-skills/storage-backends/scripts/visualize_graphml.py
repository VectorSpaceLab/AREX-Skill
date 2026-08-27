#!/usr/bin/env python3
"""Convert a nano-graphrag GraphML file to JSON and optionally preview it locally.

Safe defaults:
- Reads only the user-supplied GraphML file.
- Writes node-link JSON; refuses to overwrite unless --overwrite is used.
- Does not open a browser or start a server unless explicitly requested.
"""

from __future__ import annotations

import argparse
import json
import sys
import webbrowser
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import quote


def graphml_to_node_link(graphml_path: Path) -> dict[str, Any]:
    try:
        import networkx as nx
    except ImportError as exc:  # pragma: no cover - depends on user env
        raise SystemExit(
            "networkx is required to read GraphML. Install networkx or run in the nano-graphrag environment."
        ) from exc

    graph = nx.read_graphml(graphml_path)
    try:
        data = nx.node_link_data(graph, edges="links")
    except TypeError:  # older NetworkX
        data = nx.node_link_data(graph)
    data["graph_summary"] = {
        "nodes": graph.number_of_nodes(),
        "edges": graph.number_of_edges(),
        "directed": graph.is_directed(),
        "source_graphml": graphml_path.name,
    }
    return data


def write_text(path: Path, content: str, *, overwrite: bool) -> None:
    if path.exists() and not overwrite:
        raise SystemExit(f"Refusing to overwrite existing file: {path}. Pass --overwrite to replace it.")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def make_html(data: dict[str, Any], *, title: str, max_render_nodes: int) -> str:
    # Prevent accidental script termination if graph text contains '</script>'.
    embedded_json = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <style>
    body {{ font-family: system-ui, -apple-system, Segoe UI, sans-serif; margin: 0; color: #172033; }}
    header {{ padding: 1rem 1.25rem; border-bottom: 1px solid #d8dee9; background: #f8fafc; }}
    main {{ display: grid; grid-template-columns: minmax(320px, 1fr) 360px; gap: 1rem; padding: 1rem; }}
    svg {{ width: 100%; height: calc(100vh - 130px); min-height: 480px; border: 1px solid #d8dee9; background: #ffffff; }}
    aside {{ max-height: calc(100vh - 130px); overflow: auto; border: 1px solid #d8dee9; padding: 0.75rem; background: #fbfdff; }}
    .node {{ stroke: white; stroke-width: 1.5px; }}
    .link {{ stroke: #94a3b8; stroke-opacity: 0.65; }}
    .label {{ font-size: 10px; fill: #334155; pointer-events: none; }}
    code, pre {{ background: #f1f5f9; border-radius: 4px; }}
    pre {{ padding: 0.5rem; overflow: auto; }}
    .muted {{ color: #64748b; }}
  </style>
</head>
<body>
<header>
  <h1>{title}</h1>
  <div id="summary" class="muted"></div>
</header>
<main>
  <svg id="graph" role="img" aria-label="Graph preview"></svg>
  <aside>
    <h2>Selection</h2>
    <pre id="details">Hover or click a node/edge.</pre>
    <h2>Notes</h2>
    <p>This preview uses a deterministic circular layout and renders a bounded number of nodes. The JSON export remains complete.</p>
  </aside>
</main>
<script>
const graphData = {embedded_json};
const maxRenderNodes = {int(max_render_nodes)};
const nodesAll = graphData.nodes || [];
const linksAll = graphData.links || graphData.edges || [];
const nodes = maxRenderNodes > 0 ? nodesAll.slice(0, maxRenderNodes) : nodesAll.slice();
const nodeIds = new Set(nodes.map(n => String(n.id)));
const links = linksAll.filter(l => nodeIds.has(String(typeof l.source === 'object' ? l.source.id : l.source)) && nodeIds.has(String(typeof l.target === 'object' ? l.target.id : l.target)));
const summary = graphData.graph_summary || {{nodes: nodesAll.length, edges: linksAll.length, directed: false}};
document.getElementById('summary').textContent = `Nodes: ${{summary.nodes}} · Edges: ${{summary.edges}} · Directed: ${{summary.directed}}` + (nodes.length < nodesAll.length ? ` · Rendering first ${{nodes.length}} nodes` : '');

const svg = document.getElementById('graph');
const details = document.getElementById('details');
const width = 1000;
const height = 760;
svg.setAttribute('viewBox', `0 0 ${{width}} ${{height}}`);
const cx = width / 2;
const cy = height / 2;
const radius = Math.max(80, Math.min(width, height) * 0.42);
const palette = ['#2563eb', '#16a34a', '#dc2626', '#9333ea', '#d97706', '#0891b2', '#4f46e5', '#be123c'];
const typeToColor = new Map();
function nodeType(n) {{ return String(n.entity_type || n.type || 'UNKNOWN'); }}
function colorFor(type) {{
  if (!typeToColor.has(type)) typeToColor.set(type, palette[typeToColor.size % palette.length]);
  return typeToColor.get(type);
}}
function endpointId(value) {{ return String(typeof value === 'object' && value !== null ? value.id : value); }}
function show(obj) {{ details.textContent = JSON.stringify(obj, null, 2); }}

nodes.forEach((node, i) => {{
  const angle = nodes.length <= 1 ? 0 : (2 * Math.PI * i / nodes.length) - Math.PI / 2;
  node._x = cx + radius * Math.cos(angle);
  node._y = cy + radius * Math.sin(angle);
}});
const nodeById = new Map(nodes.map(n => [String(n.id), n]));

for (const link of links) {{
  const s = nodeById.get(endpointId(link.source));
  const t = nodeById.get(endpointId(link.target));
  if (!s || !t) continue;
  const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
  line.setAttribute('x1', s._x); line.setAttribute('y1', s._y);
  line.setAttribute('x2', t._x); line.setAttribute('y2', t._y);
  line.setAttribute('class', 'link');
  const weight = Number(link.weight || link.value || 1);
  line.setAttribute('stroke-width', String(Math.max(1, Math.min(6, Math.sqrt(Math.abs(weight))))));
  line.addEventListener('mouseenter', () => show(link));
  line.addEventListener('click', () => show(link));
  svg.appendChild(line);
}}

for (const node of nodes) {{
  const group = document.createElementNS('http://www.w3.org/2000/svg', 'g');
  const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
  circle.setAttribute('cx', node._x); circle.setAttribute('cy', node._y);
  circle.setAttribute('r', '7'); circle.setAttribute('class', 'node');
  circle.setAttribute('fill', colorFor(nodeType(node)));
  circle.addEventListener('mouseenter', () => show(node));
  circle.addEventListener('click', () => show(node));
  const label = document.createElementNS('http://www.w3.org/2000/svg', 'text');
  label.setAttribute('x', node._x + 10); label.setAttribute('y', node._y + 4);
  label.setAttribute('class', 'label');
  label.textContent = String(node.id).slice(0, 48);
  group.appendChild(circle); group.appendChild(label); svg.appendChild(group);
}}
</script>
</body>
</html>
"""


def serve_directory(directory: Path, html_path: Path, host: str, port: int, open_browser: bool) -> None:
    handler = partial(SimpleHTTPRequestHandler, directory=str(directory))
    url = f"http://{host}:{port}/{quote(html_path.name)}"
    with ThreadingHTTPServer((host, port), handler) as httpd:
        print(f"Serving {directory} at http://{host}:{port}/")
        print(f"Preview URL: {url}")
        if open_browser:
            webbrowser.open(url)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nStopping server.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Convert a GraphML knowledge graph to node-link JSON and optionally create/serve an HTML preview.",
    )
    parser.add_argument("--graphml", required=True, type=Path, help="Input GraphML file to read.")
    parser.add_argument("--json-output", type=Path, help="Output JSON path. Defaults to <graphml-stem>.node_link.json next to the input.")
    parser.add_argument("--html-output", type=Path, help="Optional self-contained HTML preview path.")
    parser.add_argument("--max-render-nodes", type=int, default=500, help="Maximum nodes rendered in HTML preview; <=0 renders all. JSON export is never truncated.")
    parser.add_argument("--overwrite", action="store_true", help="Allow replacing existing JSON/HTML output files.")
    parser.add_argument("--serve", action="store_true", help="Serve the HTML output directory in the foreground until Ctrl+C.")
    parser.add_argument("--host", default="127.0.0.1", help="Host for --serve. Default: 127.0.0.1.")
    parser.add_argument("--port", type=int, default=8000, help="Port for --serve. Default: 8000.")
    parser.add_argument("--open-browser", action="store_true", help="Open a browser only after generating HTML; with --serve, open the served URL.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    graphml_path = args.graphml.expanduser()
    if not graphml_path.exists():
        parser.error(f"GraphML file does not exist: {graphml_path}")
    if not graphml_path.is_file():
        parser.error(f"GraphML path is not a file: {graphml_path}")

    json_output = args.json_output.expanduser() if args.json_output else graphml_path.with_suffix(".node_link.json")
    html_output = args.html_output.expanduser() if args.html_output else None
    if args.serve and html_output is None:
        html_output = json_output.with_suffix(".html")
    if args.open_browser and html_output is None:
        parser.error("--open-browser requires --html-output or --serve")

    data = graphml_to_node_link(graphml_path)
    write_text(json_output, json.dumps(data, indent=2, ensure_ascii=False), overwrite=args.overwrite)
    print(f"Wrote JSON: {json_output}")
    summary = data.get("graph_summary", {})
    print(f"Graph summary: nodes={summary.get('nodes')} edges={summary.get('edges')} directed={summary.get('directed')}")

    if html_output is not None:
        html = make_html(data, title=f"GraphML preview: {graphml_path.name}", max_render_nodes=args.max_render_nodes)
        write_text(html_output, html, overwrite=args.overwrite)
        print(f"Wrote HTML preview: {html_output}")
        if args.open_browser and not args.serve:
            webbrowser.open(html_output.resolve().as_uri())

    if args.serve:
        assert html_output is not None
        serve_directory(html_output.resolve().parent, html_output.resolve(), args.host, args.port, args.open_browser)

    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main(sys.argv[1:]))
