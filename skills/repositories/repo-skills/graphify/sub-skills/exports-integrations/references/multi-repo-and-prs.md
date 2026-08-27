# Multi-repo, merge, PR, affected, and god-node workflows

Use this reference when a user wants to combine several Graphify outputs, track a persistent cross-project graph, resolve graph JSON merge conflicts, clone GitHub repos for graphing, or use PR/impact helper commands. Initial graph creation still belongs to [graph-building](../../graph-building/SKILL.md); this reference starts once per-repo `graphify-out/graph.json` files are available or the user has explicitly chosen a clone/PR helper.

## Merge local service graphs

For a monorepo or multi-service layout, build each service graph in its own output directory, then merge the resulting graph JSON files:

```bash
# Dependency step owned by graph-building: create one graph per service.
graphify extract ./api --code-only
graphify extract ./web --code-only

# Integration step owned here: merge the graph JSON files.
graphify merge-graphs \
  ./api/graphify-out/graph.json \
  ./web/graphify-out/graph.json \
  --out graphify-out/merged-graph.json
```

What Graphify does during `merge-graphs`:

- Reads both `links` and legacy `edges` node-link shapes.
- Normalizes mixed `Graph`/`DiGraph`/`MultiGraph` inputs to one simple undirected merged graph for composition.
- Prefixes node ids with unique repo tags such as `api::handler` and records `repo` plus `local_id` on nodes.
- Widens same-named repo tags (for example two different `src/graphify-out/graph.json` inputs) to avoid silent node collapse.
- Preserves stored edge direction using `_src`/`_tgt` markers when present.
- Carries and prefixes hyperedges from all inputs, writing both top-level and nested graph hyperedge slots.

Validate a merge before using it for query/navigation:

```bash
python - <<'PY'
import json
from pathlib import Path
p = Path('graphify-out/merged-graph.json')
data = json.loads(p.read_text(encoding='utf-8'))
print('nodes', len(data.get('nodes', [])), 'links', len(data.get('links', data.get('edges', []))))
print('sample ids', [n.get('id') for n in data.get('nodes', [])[:5]])
print('repo tags', sorted({n.get('repo') for n in data.get('nodes', []) if n.get('repo')}))
PY
```

After validation, hand interpretation to [query-navigation](../../query-navigation/SKILL.md) with `--graph graphify-out/merged-graph.json`.

## Clone GitHub repos for graphing

`graphify clone` is a convenience wrapper around a shallow Git clone cache:

```bash
graphify clone https://github.com/owner/repo
graphify clone https://github.com/owner/repo --branch main
graphify clone https://github.com/owner/repo --out ./vendor/repo
```

Default behavior:

- Clones to `~/.graphify/repos/<owner>/<repo>`.
- Reuses an existing clone by running `git pull`.
- Uses `git clone --depth 1` for new clones.
- Rejects unrecognized GitHub URLs and branch names beginning with `-`.

Cloning performs network I/O. Ask before cloning if the user has not already supplied a URL and does not expect network access.

## Persistent global graph

Use the global graph only when the user wants a persistent local cross-project index under their Graphify home, not merely a one-off merged file.

```bash
graphify global add graphify-out/graph.json --as myrepo
graphify global list
graphify global path
graphify global remove myrepo
```

Important behavior:

- The global graph lives under `~/.graphify/`.
- `global add` prefixes imported nodes with the supplied repo tag and prunes stale nodes for that tag before updating.
- A manifest tracks source graph path, hash, node count, edge count, and add time.
- If the manifest is corrupt, Graphify backs it up before starting fresh and reports the problem.

Validate with `graphify global list` and, if needed, query the printed global graph path using [query-navigation](../../query-navigation/SKILL.md).

## Git merge-driver for `graph.json`

`graphify merge-driver <base> <current> <other>` is meant for Git merge-driver integration on committed Graphify graph artifacts:

```bash
graphify merge-driver %O %A %B
```

Behavior to rely on:

- Union-merges `current` and `other` graph nodes/edges and writes the result back to `current`.
- Reads both `links` and `edges` node-link shapes.
- Fails closed on corrupt input, unreadable files, graphs above the hard size cap, or merged graphs above the node cap, so Git surfaces the conflict instead of accepting a poisoned graph.

Do not silently install Git hooks or edit `.git/config` from this route. If the user wants Graphify hook setup or platform assistant install behavior, route to [agent-integration](../../agent-integration/SKILL.md).

## Pull request and impact helpers

`graphify prs` is a graph-aware PR dashboard. It depends on the GitHub CLI and may perform network calls.

```bash
graphify prs                         # open PR dashboard
graphify prs 42                      # deep dive on one PR
graphify prs --worktrees             # branch/worktree mapping
graphify prs --conflicts             # PRs sharing graph communities
graphify prs --base main             # filter target base branch
graphify prs --repo owner/repo       # query a different GitHub repo
graphify prs --graph graphify-out/graph.json --conflicts
GRAPHIFY_TRIAGE_BACKEND=kimi graphify prs --triage
```

Preflight and boundaries:

- Requires `gh` on PATH and authenticated; otherwise Graphify reports `gh CLI not found or not authenticated. Run: gh auth login`.
- Base branch is auto-detected through `gh repo view`, then `git symbolic-ref`, then fallback `main`.
- Graph impact is computed only when a graph exists and the requested mode needs it, such as PR detail, triage, or conflicts.
- `--triage` uses a configured LLM backend; do not run it by default in an offline or no-credentials environment.

## Affected and god-node helpers

These commands are local graph readers and are safe once the graph path is confirmed.

### `affected`

```bash
graphify affected "PaymentService" --graph graphify-out/graph.json
graphify affected "src/api/routes.py" --relation calls --depth 3 --graph graphify-out/graph.json
```

What it does:

- Resolves a unique seed by node id, label, bare callable label, Unicode-normalized label, or source-file path when unambiguous.
- Reverse-traverses impact edges from the seed to callers/importers/users.
- Default relation set includes `calls`, `indirect_call`, `references`, `imports`, `imports_from`, `dynamic_import`, `re_exports`, `inherits`, `extends`, `implements`, `uses`, `mixes_in`, `embeds`, and `requires`.
- Reports the traversed edge's call/import/reference site when available, not just the affected node's definition line.

If it prints `No unique node match`, ask the user for a more specific label, source path, or node id; do not guess between ambiguous nodes.

### `god-nodes`

```bash
graphify god-nodes --graph graphify-out/graph.json
graphify god-nodes --graph graphify-out/graph.json --top 20 --json
```

What it does:

- Lists highly connected architectural hubs.
- Supports both `god-nodes` and `god_nodes` spellings.
- Excludes file-level nodes from the ranking.
- Emits text by default or JSON with `id`, `label`, and `degree` fields.

Use god-node output as a prioritization signal, not as a complete architecture explanation. For interpretation, route to [query-navigation](../../query-navigation/SKILL.md).

## Difficult usability cases to plan for verification

1. Two local services both have a `src/graphify-out/graph.json` and both contain an `app` node. The expected guidance builds/locates each graph separately, runs `merge-graphs`, verifies distinct widened repo tags, and confirms both `app` nodes survive instead of collapsing.
2. A user asks for PR conflict risk while unauthenticated to GitHub. The expected guidance explains the `gh auth login` requirement, avoids `--triage` without backend credentials, and offers local `affected`/`god-nodes` checks against the existing graph as an offline fallback.