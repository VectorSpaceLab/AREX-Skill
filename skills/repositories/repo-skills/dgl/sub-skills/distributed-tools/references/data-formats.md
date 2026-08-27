# Distributed Data Formats

## `ip_config.txt`

`ip_config.txt` lists cluster machines, one host per non-empty line:

```text
172.31.19.1
172.31.23.205 30060
worker-03.example.net
```

Rules:

- First token is the host or IP address.
- Optional second token is the port for DGL server communication.
- Lines with more than two tokens are invalid for DGL launchers.
- Blank lines and comments are best avoided; the bundled checker ignores blank/comment lines for preflight, but DGL launchers may be stricter.
- The number of host lines must equal `num_parts` in the partition JSON for `tools/launch.py`.

Do not invent hostnames or ports. Ask the user for cluster information if `ip_config.txt` is absent or unconfirmed.

## Partition Config JSON Essentials

A partition metadata JSON produced by `dgl.distributed.partition_graph()` is commonly named `graph_name.json` and lives next to `part0/`, `part1/`, ... directories.

Essential top-level fields:

```json
{
  "graph_name": "mygraph",
  "part_method": "metis",
  "num_parts": 2,
  "halo_hops": 1,
  "node_map": {"_N": [[0, 10], [10, 20]]},
  "edge_map": {"_N:_E:_N": [[0, 50], [50, 100]]},
  "ntypes": {"_N": 0},
  "etypes": {"_N:_E:_N": 0},
  "num_nodes": 20,
  "num_edges": 100,
  "part-0": {
    "node_feats": "part0/node_feats.dgl",
    "edge_feats": "part0/edge_feats.dgl",
    "part_graph": "part0/graph.dgl"
  },
  "part-1": {
    "node_feats": "part1/node_feats.dgl",
    "edge_feats": "part1/edge_feats.dgl",
    "part_graph": "part1/graph.dgl"
  }
}
```

Field meanings:

- `graph_name`: the exact name used by `DistGraph(graph_name)`.
- `part_method`: partition algorithm, commonly `metis` or `random`.
- `num_parts`: number of partitions; normally equals number of machines for `tools/launch.py`.
- `halo_hops`: number of HALO hops stored in each partition.
- `node_map`: per-node-type ranges for each partition after ID reshuffling.
- `edge_map`: per-canonical-edge-type ranges for each partition after ID reshuffling.
- `ntypes`: map of node type string to type ID.
- `etypes`: map of canonical edge type string to type ID.
- `num_nodes` and `num_edges`: global graph counts.
- `part-N`: file references for partition `N`.

Common `part-N` keys include:

- `part_graph`: partition graph structure, usually `partN/graph.dgl`.
- `node_feats`: node feature shard, usually `partN/node_feats.dgl`.
- `edge_feats`: edge feature shard, usually `partN/edge_feats.dgl`.
- GraphBolt-specific keys may point to sampled/CSC graph assets or metadata; preserve them and validate only their path shape unless the runtime checker understands the exact DGL version.

Prefer relative paths in `part-N` entries. Absolute paths may work in a local workflow but are fragile for shared workspaces and should not appear in reusable instructions.

## `node_map` and `edge_map` Range Rules

`node_map` and `edge_map` values should be lists with length `num_parts`. Each element is a two-integer range `[start, end]`.

Preflight expectations:

- `start <= end` for every range.
- Adjacent ranges are usually contiguous for each type: next `start` equals previous `end`.
- Final `end` values should be compatible with `num_nodes`/`num_edges` when maps cover the whole graph.
- `edge_map` keys should be canonical etype strings for heterographs.

Range preflight cannot prove graph correctness. Full correctness requires loading partition graphs and comparing `dgl.NID`, `dgl.EID`, `inner_node`, `inner_edge`, partition book metadata, and features.

## Canonical Edge-Type Strings

DGL canonical edge types are triples `(src_type, relation, dst_type)`. Partition metadata serializes them with colon separators:

```text
user:follows:user
user:plays:game
paper:cites:paper
_N:_E:_N
```

Use canonical strings in `edge_map` and `etypes`. Old partition configs may use relation-only keys such as `plays`; those are ambiguous when multiple node-type pairs share the same relation name.

Migration guidance:

- Homogeneous old configs can often map relation-only `etype` to `_N:etype:_N` or the single configured node type.
- Heterogeneous old configs require inspecting partition graph structure to infer source and destination node types. Do not guess.
- Native migration utilities may overwrite the partition JSON. Use the bundled checker first because it is read-only.

## Chunked Graph Metadata for Large Preprocessing

The distributed preprocessing pipeline accepts chunked graph metadata rather than an in-memory `DGLGraph`. Its `metadata.json` describes:

- `graph_name`
- `node_type`
- `num_nodes_per_chunk`
- `edge_type` using canonical strings like `author:writes:paper`
- `num_edges_per_chunk`
- `edges` chunk file specs
- `node_data` and `edge_data` chunk file specs

Chunk file specs contain `format` and `data` keys. Formats include CSV, NumPy, and Parquet depending on the pipeline. This format belongs to preprocessing and dispatch; it is not the same as the partition config consumed by `DistGraph`/`launch.py`.
