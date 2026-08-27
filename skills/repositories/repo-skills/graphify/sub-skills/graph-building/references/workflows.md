# Graph-building workflows

## Purpose

Use this reference to build or refresh Graphify artifacts from local files without reopening the original repository docs. It covers install checks, code-only versus semantic extraction decisions, ignore/exclude behavior, update/cluster-only/label/add/watch commands, expected outputs, and artifact validation.

## Package and command identity

- Public package/distribution: `graphifyy`.
- Python import package: `graphify`.
- CLI entry point: `graphify`; fallback invocation: `python -m graphify`.
- `graphify <path>` is a supported shorthand for `graphify extract <path>`; use explicit `extract` in scripts when you want clearer logs and parser errors.
- Python requirement: `>=3.10`.

Safe install/check sequence:

```bash
# Recommended isolated installs; choose one.
uv tool install graphifyy
pipx install graphifyy
python -m pip install graphifyy

# Verify the installed package and CLI.
graphify --help
python -m graphify --help
python - <<'PY'
import graphify
from graphify import detect, extract, build
print('graphify import ok')
PY
```

If `graphify` is not on `PATH`, use `python -m graphify ...` until PATH is fixed. If using `uvx` or `uv tool run`, name the package explicitly: `uvx --from graphifyy graphify --help`.

## Build-mode decision tree

1. **Only code, or mixed repo with no provider key and the user only needs code structure:** use code-only extraction.
   ```bash
   graphify extract <path> --code-only
   graphify cluster-only <path> --no-viz   # create GRAPH_REPORT.md and refresh graph.json; omit --no-viz when graph.html is wanted
   ```
   `--code-only` skips docs, papers, and images with an explicit message. Code is processed locally with AST extraction and no API key.

2. **Mixed code/docs/media where semantic relationships matter:** use semantic extraction with an explicit backend or configured environment.
   ```bash
   graphify extract <path> --backend gemini
   graphify cluster-only <path>
   ```
   Providers are optional; see [optional-dependencies.md](optional-dependencies.md). If no provider key is available and the docs/media are not essential, switch to `--code-only` rather than blocking.

3. **Fast raw graph smoke or CI preflight:** skip clustering first, then cluster only if needed.
   ```bash
   graphify extract <path> --code-only --no-cluster
   # Later, if report/community artifacts are needed:
   graphify cluster-only <path> --no-viz
   ```

4. **Existing graph and code-only delta:** use `graphify update`.
   ```bash
   graphify update <path>
   graphify update <path> --no-cluster  # faster; writes raw graph.json only
   graphify update <path> --force       # only after verifying a legitimate shrink/deletion
   ```
   `graphify update` is AST/code-oriented and prints that doc/paper/image changes need semantic re-extraction. It is the right choice for code-only changes after an existing graph has been built.

5. **Existing graph, no file re-extraction, only community/report changes:** use `cluster-only` or `label`.
   ```bash
   graphify cluster-only <path>
   graphify cluster-only <path> --no-viz
   graphify cluster-only <path> --resolution 1.5 --exclude-hubs 99
   graphify cluster-only <path> --graph <path-to-graph.json> --no-label
   graphify label <path> --backend=openai --model gpt-4o
   graphify label <path> --missing-only
   ```

## What `graphify extract` writes

`graphify extract <path>` is a headless CLI pipeline. In the verified version it writes the primary graph artifacts under `<output-root>/graphify-out/`, where `<output-root>` is `<path>` unless `--out DIR`/`--output DIR` is supplied.

Common outputs:

| Artifact | When it appears | How to use it |
|---|---|---|
| `graphify-out/graph.json` | Always on successful extraction/update. | Primary graph in NetworkX node-link JSON. Required by query, cluster-only, exports, and serving. |
| `graphify-out/.graphify_analysis.json` | Clustered `extract` and `cluster-only`. | Communities, cohesion, god nodes, surprises, and questions sidecar. |
| `graphify-out/GRAPH_REPORT.md` | `cluster-only`, assistant `/graphify` full flow, or update with clustering. | Human-readable corpus summary, community hubs, god nodes, and confidence audit. |
| `graphify-out/graph.html` | `cluster-only` unless `--no-viz`, or assistant full flow. | Interactive visualization; large graphs may fall back to community aggregation or be skipped. |
| `graphify-out/manifest.json` | Successful path-based extract/update. | Portable relative-path manifest for incremental detection. Commit-safe. |
| `graphify-out/cache/` | AST/semantic cache when extraction uses cached paths. | Optional to commit for speed; omit if you want a smaller repo. |
| `graphify-out/converted/` | Office or Google Workspace conversion. | Markdown sidecars generated from pointer/binary input formats. |
| `graphify-out/transcripts/` | Video/audio transcription. | Text transcripts generated for semantic extraction. |

`graphify extract --no-cluster` writes raw graph JSON and skips report/community/HTML generation. Run `cluster-only` later to get `GRAPH_REPORT.md` and communities.

## Ignore and exclude controls

Graphify has three layers of corpus shaping:

1. `.gitignore` and `.git/info/exclude` are honored by default.
2. `.graphifyignore` is read with gitignore-like syntax and is evaluated after `.gitignore`; it can exclude more, but it does not re-include files already excluded by `.gitignore`.
3. CLI `--exclude PATTERN` appends root-anchored patterns for a build and persists them in `graphify-out/.graphify_build.json` for later update/watch/hook rebuilds. Passing a new explicit list replaces the persisted list.

Commands:

```bash
# Include generated or transpiled code ignored by git while still honoring .graphifyignore.
graphify extract <path> --code-only --no-gitignore

# Exclude a subtree without editing ignore files; persisted for future updates.
graphify extract <path> --code-only --exclude vendor --exclude dist

# Persisted --exclude and --no-gitignore apply to later updates unless replaced.
graphify update <path>
```

Use `.graphifyignore` when the exclusion should live with the project, and `--exclude` for one workflow or generated output path. Scan from the intended project root, and if expected files are missing from a subdirectory scan, inspect parent `.graphifyignore` files plus persisted `.graphify_build.json` before assuming an extractor bug.

## Code-only extraction recipe

Use this when the corpus is code-only, or the user has docs/media but asks for a local/offline/code graph.

```bash
graphify extract . --code-only --no-cluster
python - <<'PY'
import json
from pathlib import Path
p = Path('graphify-out/graph.json')
data = json.loads(p.read_text(encoding='utf-8'))
links = data.get('links', data.get('edges', []))
print(f"{len(data.get('nodes', []))} nodes, {len(links)} edges")
if not data.get('nodes'):
    raise SystemExit('graph is empty')
PY
# Optional report/community pass.
graphify cluster-only . --no-viz
```

Expected console signals include:

- `--code-only: skipping N non-code file(s)` for mixed corpora.
- `AST extraction on N code files`.
- `wrote ... graphify-out/graph.json` with node and edge counts.

If the user expected docs/images/PDFs to appear, explain that `--code-only` intentionally skipped semantic extraction and rerun without that flag after installing/configuring the selected provider/extra.

## Semantic extraction recipe

Use semantic extraction when docs, papers, images, or generated transcripts must contribute concepts and inferred edges.

```bash
# Pick one configured backend. Gemini example:
uv tool install "graphifyy[gemini]"
export GEMINI_API_KEY=...
graphify extract ./docs --backend gemini --token-budget 30000 --max-concurrency 2

graphify cluster-only ./docs --no-viz
```

Useful flags:

- `--backend NAME`: provider backend. Verified backend registry includes `gemini`, `kimi`, `claude`, `openai`, `deepseek`, `ollama`, `azure`, `bedrock`, and `claude-cli`.
- `--model NAME`: model override for the chosen backend.
- `--mode deep`: richer semantic extraction with more aggressive inferred edges.
- `--token-budget N`: smaller chunks for local/small models.
- `--max-concurrency N`: limit parallel semantic calls; use `1` or low values for local inference.
- `--api-timeout S`: longer timeout for slow HTTP/local providers.
- `--dedup-llm`: optional LLM tiebreaker for ambiguous entity deduplication; it uses the same provider credentials.

If no key/backend is configured and non-code files are present, the CLI errors and points at `--code-only`. Use that hint unless semantic docs/media are required.

## Incremental update recipe

For an existing `graphify-out/graph.json` after code edits:

```bash
graphify update .
# or, for a fast raw update without reclustering/report generation:
graphify update . --no-cluster
```

What happens:

- Re-extracts code/AST files without LLM calls.
- Preserves unchanged nodes from the existing graph.
- Uses `manifest.json`, stored source files, and saved root information to identify changed/deleted/excluded sources.
- Rebuilds `graph.json`; clustered mode also updates `GRAPH_REPORT.md` and usually `graph.html`.
- Prints a tip that doc/paper/image changes require semantic extraction.

Choose `--no-cluster` when a code-only delta is small and the next step only needs raw graph JSON, or when you want to postpone report/community work. Choose normal `update` when the user will inspect `GRAPH_REPORT.md`, god nodes, or community labels immediately.

Use `--force` only after confirming that a graph shrink is expected, such as deleted files or a major refactor. If extraction crashed or files were skipped unexpectedly, fix the cause and rerun instead of forcing.

## Cluster-only and labeling recipe

Use `cluster-only` when graph extraction already succeeded and you only need community/report/HTML regeneration.

```bash
graphify cluster-only .
graphify cluster-only . --no-viz
graphify cluster-only . --resolution 1.5
graphify cluster-only . --exclude-hubs 99
graphify cluster-only . --graph path/to/graphify-out/graph.json
graphify cluster-only . --no-label
```

Notes:

- `--resolution > 1.0` tends to create more, smaller communities; `< 1.0` tends to create fewer, larger communities.
- `--exclude-hubs PERCENTILE` removes super-hubs from partitioning and reattaches them afterward, useful when utility nodes dominate rankings.
- `--no-label` keeps placeholder `Community N` names and should not be used when human-friendly community names are required.
- Existing labels are reused when signatures show communities did not change; if you pass `--backend`/`--model` and labels are reused, rerun `graphify label` to force relabeling.

Use `label` when you need to regenerate community names without changing extraction:

```bash
graphify label . --backend=gemini --model gemini-3-flash-preview
graphify label . --missing-only
```

## Add URL/media input

Use `add` when the user wants to fetch a paper, PDF, page, image, tweet, or video URL into a corpus and then merge it into an existing graph.

```bash
graphify add https://arxiv.org/abs/1706.03762 --author "Author Name" --contributor "Your Name"
graphify add https://example.com/file.pdf --dir ./raw
# Then update with the appropriate semantic route:
graphify extract ./raw --backend gemini
# or, inside an assistant workflow that owns semantic extraction:
# /graphify --update
```

`graphify add` saves to `./raw` by default and prints `Run /graphify --update in your AI assistant to update the graph.` Videos and many media URLs require the `video` extra. Invalid URLs or failed fetches exit non-zero and should not be silently ignored.

## Watch mode

Use watch mode when code changes should keep the graph fresh during agent or developer edit waves.

```bash
uv tool install "graphifyy[watch]"   # or install the watch extra in the active env
graphify watch ./src
# Custom debounce is available through the module entry point:
python -m graphify.watch ./src --debounce 3
```

Behavior:

- Code changes trigger local AST rebuilds with no LLM.
- Deletions trigger a rebuild so stale nodes can be removed.
- Surviving doc/paper/image changes write `graphify-out/needs_update` and notify that semantic extraction is required.
- Press `Ctrl+C` to stop.

For non-code updates, run a semantic update/extract route after the watch notification. Do not assume watch mode semantically extracts docs or media.

## Validate the resulting artifacts

Use the bundled smoke helper first when you need to prove the local install can build a graph without touching user files. From the `graphify` repo-skill root directory:

```bash
python sub-skills/graph-building/scripts/build_tiny_graph.py
python sub-skills/graph-building/scripts/build_tiny_graph.py --json
python sub-skills/graph-building/scripts/build_tiny_graph.py --keep-temp
```

When validating a user's graph, run read-only checks from the project root:

```bash
python - <<'PY'
import json
from pathlib import Path
base = Path('graphify-out')
required = [base / 'graph.json']
missing = [str(p) for p in required if not p.exists()]
if missing:
    raise SystemExit('missing required graph artifact(s): ' + ', '.join(missing))
data = json.loads((base / 'graph.json').read_text(encoding='utf-8'))
links = data.get('links', data.get('edges', []))
print(f"graph.json: {len(data.get('nodes', []))} nodes, {len(links)} edges")
print('hyperedges:', len(data.get('hyperedges', [])))
print('directed:', bool(data.get('directed', False)))
if not data.get('nodes'):
    raise SystemExit('graph.json has no nodes')
if (base / 'GRAPH_REPORT.md').exists():
    print('GRAPH_REPORT.md: present')
else:
    print('GRAPH_REPORT.md: missing; run graphify cluster-only <path>')
PY
```

A valid post-cluster graph normally has node `community` fields and often `community_name` fields. If `GRAPH_REPORT.md` is missing but `graph.json` exists, the common fix is `graphify cluster-only <path> --no-viz`.

## Handoff after graph creation

Once graph artifacts validate:

- For natural-language codebase questions, hand off to [query-navigation](../../query-navigation/SKILL.md) and use `graphify query`, `path`, or `explain` rather than rebuilding.
- For visualizations, database pushes, wiki/Obsidian, GraphML/SVG/Cypher, or multi-repo merges, hand off to [exports-integrations](../../exports-integrations/SKILL.md).
- For missing language support or parser/extractor failures that survive a normal rebuild, hand off to [extractor-troubleshooting](../../extractor-troubleshooting/SKILL.md).
