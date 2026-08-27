# GraphML visualization and JSON export

`NetworkXStorage` persists the knowledge graph as GraphML named `graph_chunk_entity_relation.graphml` inside a user's `GraphRAG(working_dir=...)`. Use the bundled visualization helper only on a GraphML file supplied by the user or produced in the user's own working directory.

## Safe default: JSON export only

The helper's default workflow converts GraphML to NetworkX node-link JSON and does not open a browser or start a server:

```bash
python path/to/storage-backends/scripts/visualize_graphml.py \
  --graphml ./my_nano_graphrag_store/graph_chunk_entity_relation.graphml \
  --json-output ./graph.node_link.json
```

The JSON contains:

- `nodes`: graph nodes with their GraphML attributes such as `id`, `entity_type`, `description`, `source_id`, and `clusters` when present.
- `links`: graph edges with attributes such as `source`, `target`, `description`, `weight`, and `source_id` when present.
- `graph_summary`: node count, edge count, and directedness added by the helper.

If `--json-output` is omitted, the script writes `<graphml-stem>.node_link.json` next to the input GraphML. The script refuses to overwrite existing output unless `--overwrite` is provided.

## Optional local HTML preview

To create a self-contained HTML preview without automatically opening a browser:

```bash
python path/to/storage-backends/scripts/visualize_graphml.py \
  --graphml ./my_nano_graphrag_store/graph_chunk_entity_relation.graphml \
  --json-output ./graph.node_link.json \
  --html-output ./graph.preview.html
```

The generated HTML embeds the graph data directly and uses a small vanilla-JavaScript circular layout. It does not download D3 or any other browser dependency. This is intended for quick inspection, not publication-quality graph rendering.

## Optional local serving

If the user wants to view the HTML over HTTP, add `--serve`:

```bash
python path/to/storage-backends/scripts/visualize_graphml.py \
  --graphml ./my_nano_graphrag_store/graph_chunk_entity_relation.graphml \
  --json-output ./graph.node_link.json \
  --html-output ./graph.preview.html \
  --serve \
  --port 11236
```

Serving is foreground and stops on `Ctrl+C`. The helper does not use an infinite busy-loop. It opens a browser only when `--open-browser` is explicitly supplied.

## Practical notes

- Large graphs can produce large JSON/HTML files. Use `--max-render-nodes` to limit the HTML preview while keeping the JSON export complete.
- If nodes have no `entity_type`, the preview uses a neutral type label. This can happen when the graph was manually constructed or partially inserted.
- If `community_schema()` is empty or GraphML has no cluster attributes, visualization can still show nodes and edges; clustering/report failures should be debugged separately.
- `Neo4jStorage` does not write GraphML by default. Export from Neo4j to GraphML or switch to a NetworkX-backed working directory if GraphML visualization is required.
- The helper requires `networkx` in the Python environment because it reads GraphML through `networkx.read_graphml`.
