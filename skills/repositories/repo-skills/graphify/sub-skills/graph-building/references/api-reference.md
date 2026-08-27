# Graph-building API and schema reference

## Purpose

Use this when you need verified function signatures, graph JSON schema facts, confidence labels, cache/manifest behavior, or CLI/API boundaries for Graphify graph construction. Prefer CLI workflows for ordinary users; use Python APIs for diagnostics, custom embedding in scripts, or assertion-backed validation.

## Verified CLI commands for this route

The main `graphify --help` route advertises these graph-building commands and options:

| Command | Purpose | Important options |
|---|---|---|
| `graphify extract <path>` | Headless full extraction from local files. Writes `<out>/graphify-out/graph.json` and sidecars. `graphify <path>` is treated as this command for convenience. | `--backend`, `--model`, `--mode deep`, `--force`, `--max-workers`, `--token-budget`, `--max-concurrency`, `--api-timeout`, `--out DIR`, `--output DIR`, `--google-workspace`, `--no-gitignore`, `--no-cluster`, `--code-only`, `--postgres DSN`, `--cargo`, `--global`, `--as TAG`, `--dedup-llm`, `--allow-partial`, `--timing`, source-backed `--exclude PATTERN`, `--resolution`, `--exclude-hubs`. |
| `graphify update [path]` | Re-extract code files and update an existing graph without LLM calls. | `--force`, `--no-cluster`. With no path, reads the saved `.graphify_root` when available. |
| `graphify cluster-only <path>` | Recluster an existing `graph.json` and regenerate report/JSON/HTML. | `--graph PATH`, `--no-viz`, `--no-label`, `--backend`, `--model`, `--max-concurrency`, `--batch-size`, `--resolution`, `--exclude-hubs`. |
| `graphify label <path>` | Regenerate or complete community names. | `--missing-only`, `--backend`, `--model`, `--max-concurrency`, `--batch-size`. |
| `graphify add <url>` | Fetch a URL into `./raw` or another directory for later graph update. | `--author`, `--contributor`, `--dir`. |
| `graphify watch <path>` | Watch code changes and update graph artifacts automatically. | Public CLI takes a path; `python -m graphify.watch <path> --debounce N` supports custom debounce. |
| `graphify check-update <path>` | Report pending semantic update flag from watch mode. | No graph mutation; cron-safe status helper. |

Notes:

- Command-specific `--help` currently routes back to the main help for many subcommands. Treat main help and source-backed parser inspection as the command catalog.
- `--output` is an alias of `--out` for `extract`.
- `--exclude` is parsed by `extract` and persisted even though it is not prominent in main help output.

## Verified Python signatures

These signatures were inspected from the installed package and are safe public surfaces for graph-building helpers:

```text
graphify.detect.detect(root: Path, *, follow_symlinks: bool | None = None, google_workspace: bool | None = None, extra_excludes: list[str] | None = None, cache_root: Path | None = None, gitignore: bool = True) -> dict

graphify.detect.detect_incremental(root: Path, manifest_path: str = 'graphify-out/manifest.json', *, follow_symlinks: bool | None = None, google_workspace: bool | None = None, kind: str = 'semantic', extra_excludes: list[str] | None = None, gitignore: bool = True) -> dict

graphify.extract.collect_files(target: Path, *, follow_symlinks: bool = False, root: Path | None = None) -> list[Path]

graphify.extract.extract(paths: list[Path], cache_root: Path | None = None, *, root: Path | None = None, parallel: bool = True, max_workers: int | None = None, resolution_context_nodes: list[dict] | None = None, resolution_context_edges: list[dict] | None = None) -> dict

graphify.build.build_from_json(extraction: dict, *, directed: bool = False, root: str | Path | None = None) -> nx.Graph

graphify.build.build_merge(new_chunks: list[dict], graph_path: str | Path | None = None, prune_sources: list[str] | None = None, *, directed: bool | None = None, dedup: bool = True, dedup_llm_backend: str | None = None, root: str | Path | None = None) -> nx.Graph

graphify.cluster.cluster(G: nx.Graph, resolution: float = 1.0, exclude_hubs_percentile: float | None = None) -> dict[int, list[str]]

graphify.analyze.god_nodes(G: nx.Graph, top_n: int = 10) -> list[dict]

graphify.report.generate(G, communities, cohesion_scores, community_labels, god_node_list, surprise_list, detection_result, token_cost, root, suggested_questions=None, min_community_size=3, built_at_commit=None, learning=None, obsidian=False) -> str

graphify.cache.check_semantic_cache(files: list[str], root: Path = Path('.'), mode: str | None = None, prompt: str | Path | None = None, prompt_file: str | Path | None = None, cache_root: Path | None = None) -> tuple[list[dict], list[dict], list[dict], list[str]]

graphify.cache.save_semantic_cache(nodes: list[dict], edges: list[dict], hyperedges: list[dict] | None = None, root: Path = Path('.'), merge_existing: bool = False, allowed_source_files: Iterable[str | Path] | None = None, mode: str | None = None, prompt: str | Path | None = None, prompt_file: str | Path | None = None, partial_source_files: Iterable[str | Path] | None = None, cache_root: Path | None = None) -> int

graphify.detect.save_manifest(files: dict[str, list[str]], manifest_path: str = 'graphify-out/manifest.json', *, kind: str = 'both', root: Path | None = None, scan_corpus: set[str] | list[str] | None = None, clear_semantic: set[str] | list[str] | None = None, clear_ast: set[str] | list[str] | None = None) -> None

graphify.detect.load_manifest(manifest_path: str = 'graphify-out/manifest.json', *, root: Path | None = None) -> dict

graphify.transcribe.transcribe(video_path: Path | str, output_dir: Path | None = None, initial_prompt: str | None = None, force: bool = False) -> Path
```

## Detection result shape

`detect(root)` returns a dictionary used by both CLI and custom scripts. Important keys:

```json
{
  "files": {
    "code": ["..."],
    "document": ["..."],
    "paper": ["..."],
    "image": ["..."],
    "video": ["..."]
  },
  "total_files": 0,
  "total_words": 0,
  "needs_graph": false,
  "warning": null,
  "skipped_sensitive": [],
  "unclassified": [],
  "walk_errors": [],
  "ignored": [],
  "pruned_noise_dirs": [],
  "graphifyignore_patterns": 0,
  "scan_root": "..."
}
```

`detect_incremental(...)` adds:

```json
{
  "incremental": true,
  "new_files": {"code": [], "document": [], "paper": [], "image": [], "video": []},
  "unchanged_files": {"code": [], "document": [], "paper": [], "image": [], "video": []},
  "new_total": 0,
  "deleted_files": [],
  "excluded_files": []
}
```

Use `kind='ast'` when reproducing code/update behavior and `kind='semantic'` when reproducing semantic extraction gates. CLI `graphify update` handles this internally.

## Extraction dict shape

AST extraction and semantic extraction ultimately merge into this shape:

```json
{
  "nodes": [
    {
      "id": "stable_node_id",
      "label": "Human label",
      "file_type": "code",
      "source_file": "repo-relative/path.py",
      "source_location": "L42"
    }
  ],
  "edges": [
    {
      "source": "caller_id",
      "target": "callee_id",
      "relation": "calls",
      "confidence": "EXTRACTED",
      "confidence_score": 1.0,
      "source_file": "repo-relative/path.py",
      "source_location": "L42",
      "weight": 1.0
    }
  ],
  "hyperedges": [
    {
      "id": "shared_flow",
      "label": "Shared flow",
      "nodes": ["a", "b", "c"],
      "relation": "participate_in",
      "confidence": "INFERRED",
      "confidence_score": 0.75,
      "source_file": "docs/flow.md"
    }
  ],
  "input_tokens": 0,
  "output_tokens": 0
}
```

Valid `file_type` values accepted by the build path are `code`, `document`, `paper`, `image`, `rationale`, and `concept`. Builders normalize legacy aliases such as `links` to `edges` and may coerce numeric IDs to strings.

## Persisted `graph.json` schema

`graphify-out/graph.json` is NetworkX node-link JSON. Current writers use `links` for edges, while readers accept both `links` and `edges`.

Common top-level keys:

```json
{
  "directed": false,
  "multigraph": false,
  "graph": {},
  "nodes": [],
  "links": [],
  "hyperedges": [],
  "built_at_commit": "optional-git-sha"
}
```

Node fields usually include:

- `id`: stable identifier.
- `label`: human-readable name.
- `file_type`: one of `code`, `document`, `paper`, `image`, `rationale`, `concept`.
- `source_file`: normalized source file path, intended to be portable/repo-relative when the build had a root.
- `source_location`: often `L<number>` for AST extraction, `null`/missing for semantic concepts.
- `community`: community id after clustering.
- `community_name`: present when labels were supplied.
- `norm_label`: lowercased/diacritic-stripped label used by query/navigation.

Edge fields usually include:

- `source`, `target`: endpoint node ids. Direction is restored on export using internal `_src`/`_tgt`; persisted graph JSON should have the true direction.
- `relation`: relation string such as `calls`, `imports`, `references`, `contains`, `semantically_similar_to`, or `rationale_for`.
- `confidence`, `confidence_score`, `source_file`, `source_location`, `weight`.

## Confidence labels

| Label | Meaning | Default score behavior |
|---|---|---|
| `EXTRACTED` | Directly observed in source, e.g. imports, call relationships, package manifests, explicit citations/links. | `1.0`. |
| `INFERRED` | Reasonable inference from context, shared structure, semantic similarity, or resolver logic. | Semantic extraction uses a discrete rubric such as `0.95`, `0.85`, `0.75`, `0.65`, `0.55`; code resolvers may use other explicit scores for local inference. |
| `AMBIGUOUS` | Uncertain relationship flagged for review rather than silently dropped. | Low score, typically in the `0.1`-`0.3` range for semantic output. |

`GRAPH_REPORT.md` summarizes confidence percentages and average inferred confidence. When a downstream answer depends on `AMBIGUOUS` or low-confidence `INFERRED` edges, surface that uncertainty.

## Cache and manifest contracts

### AST cache

- AST extraction caches per-file results under `graphify-out/cache/ast/` unless a custom output root is provided.
- AST cache entries are versioned by the installed `graphifyy` version so extractor fixes invalidate stale AST entries.
- Empty or failed extractor results are not stamped as successful; future runs retry them after missing extras or parser failures are fixed.

### Semantic cache

- Semantic cache entries are content-hash keyed and prompt-fingerprinted when the caller supplies the extraction prompt or prompt file.
- Standard and `--mode deep` semantic extraction use separate namespaces.
- Failed or partial semantic files are left unstamped/cleared in the manifest so the next incremental run requeues them.
- The cache is an optimization, not a source of truth. If cache behavior is suspect, rerun with `--force` to skip cache reads.

### Manifest

`manifest.json` records file mtime plus `ast_hash` and `semantic_hash` fields. When `root` is supplied, keys are stored as relative, forward-slash paths so the manifest can be committed and moved across clones. Important behaviors:

- `save_manifest(..., kind='ast')` stamps AST hashes and preserves compatible semantic hashes.
- `save_manifest(..., kind='semantic')` stamps semantic hashes and preserves AST hashes.
- `save_manifest(..., kind='both')` stamps both.
- `scan_corpus` lets full scans drop in-root files that are alive on disk but newly excluded.
- `clear_semantic` and `clear_ast` prevent failed files from being frozen as up-to-date.

## Build and merge behavior

- `build_from_json(extraction, directed=False, root=None)` creates an undirected NetworkX `Graph` by default; `directed=True` returns a `DiGraph` preserving source-to-target semantics.
- `build(...)` merges extraction chunks, deduplicates entities by default, normalizes source paths, removes invalid/dangling edges, merges known AST/semantic ghost duplicates, and stores hyperedges in graph metadata.
- `build_merge(new_chunks, graph_path=..., prune_sources=..., root=...)` loads an existing graph, replaces the re-extracted source tier, preserves unchanged files, prunes deleted/excluded sources, preserves hyperedges when appropriate, and honors the existing graph's `directed` flag when `directed=None`.
- Existing graph corruption should stop an incremental merge; do not overwrite a possibly recoverable graph with a partial one.

## Community/report APIs

- `cluster(G, resolution=1.0, exclude_hubs_percentile=None)` returns `{community_id: [node_id, ...]}`. Leiden is used when `graspologic` is installed; otherwise NetworkX Louvain is used. Directed graphs are converted to undirected for clustering.
- `score_all(G, communities)` returns cohesion per community.
- `god_nodes(G, top_n=10)` filters file-level/noise nodes and returns high-degree architectural hubs.
- `report.generate(...)` returns Markdown for `GRAPH_REPORT.md` with corpus check, summary, community hubs, god nodes, surprising connections, confidence audit, suggested questions, and optional freshness/work-memory sections.

## Safe API smoke snippet

This snippet builds a graph from a temporary file using public APIs only. Prefer the bundled script for routine checks, but this is useful when you need to embed assertions in another test.

```python
from pathlib import Path
from tempfile import TemporaryDirectory
from graphify.detect import detect
from graphify.extract import extract
from graphify.build import build_from_json
from graphify.cluster import cluster

with TemporaryDirectory() as td:
    root = Path(td)
    (root / "app.py").write_text("def hello():\n    return 1\n", encoding="utf-8")
    detection = detect(root)
    code_files = [Path(p) for p in detection["files"]["code"]]
    extraction = extract(code_files, cache_root=root, root=root, parallel=False)
    graph = build_from_json(extraction, root=root)
    communities = cluster(graph)
    assert graph.number_of_nodes() > 0
    assert communities
```
