# Graph-building troubleshooting

## Purpose

Use this when Graphify cannot install, cannot find files, skips semantic extraction, writes stale or incomplete graph artifacts, fails optional media/provider work, or refuses to overwrite an existing graph.

## Quick triage order

1. Check command/package identity: `graphifyy` is the package; `graphify` is the CLI/import package.
2. Run the bundled smoke helper from the generated skill tree:
   ```bash
   python sub-skills/graph-building/scripts/build_tiny_graph.py
   ```
3. For a user graph, validate `graphify-out/graph.json` shape and counts with the snippet in [workflows.md](workflows.md#validate-the-resulting-artifacts).
4. Decide whether the failure is build/update related (this sub-skill), query/navigation related ([query-navigation](../../query-navigation/SKILL.md)), export/service related ([exports-integrations](../../exports-integrations/SKILL.md)), assistant install related ([agent-integration](../../agent-integration/SKILL.md)), or extractor/parser-maintainer related ([extractor-troubleshooting](../../extractor-troubleshooting/SKILL.md)).

## Install and command failures

| Symptom | Likely cause | Recovery |
|---|---|---|
| `graphify: command not found` | Tool bin directory is not on `PATH`. | Run `uv tool update-shell` for uv installs, `pipx ensurepath` for pipx, reopen the shell, or use `python -m graphify ...`. |
| `uvx graphify ...` reports no package versions | The PyPI package is `graphifyy`, not `graphify`. | Use `uvx --from graphifyy graphify ...`. |
| `python -m graphify` works but `graphify` does not | CLI entry point not on PATH. | Use `python -m graphify` or fix PATH for the install method. |
| Imported version behaves older than expected | Another environment's `graphifyy` is being imported first. | Check `python -c "import graphify; print(graphify.__file__)"`; run the installed tool directly or remove the stale package. |
| `ModuleNotFoundError: No module named 'graphify'` | Installed in a different Python than the one running the command. | Prefer `uv tool install graphifyy`/`pipx install graphifyy`; otherwise reinstall into the active Python and use that interpreter consistently. |

## No files or wrong files in the graph

| Symptom | Likely cause | Recovery |
|---|---|---|
| `No supported files found` or empty graph | Unsupported extensions, all files ignored, binary-only corpus, or sensitive-file filter removed candidates. | Run detection via `graphify extract <path> --code-only --no-cluster` and inspect console messages for skipped/unclassified files. Add supported files or choose a supported subfolder. |
| Expected generated code is missing | `.gitignore` or `.git/info/exclude` hid it. | Rerun with `--no-gitignore` if generated/transpiled code should be indexed; `.graphifyignore` still applies. |
| Expected files still missing after `--no-gitignore` | `.graphifyignore` or persisted `--exclude` excluded them. | Inspect `.graphifyignore` and `graphify-out/.graphify_build.json`; remove/replace persisted excludes by running `graphify extract <path> --exclude <new-pattern> ...` or deleting stale build config with care. |
| Sensitive files skipped by name | Secret/token/credential heuristics matched. | Do not force-index real secrets. If it is a false positive documentation/source file, rename or move it, then rerun. |
| Google Workspace `.gdoc`/`.gsheet`/`.gslides` skipped | Workspace shortcut conversion is opt-in. | Install/authenticate `gws`, install `graphifyy[google]` when Sheets are needed, and rerun with `--google-workspace` or `GRAPHIFY_GOOGLE_WORKSPACE=1`. |
| Office files skipped/converted poorly | Missing `office` extra or unsupported content. | Install `graphifyy[office]`, rerun, and inspect `graphify-out/converted/` sidecars. |

## No-key and semantic extraction failures

| Symptom | Likely cause | Recovery |
|---|---|---|
| Mixed repo fails with `no LLM API key found` and mentions `--code-only` | Docs/papers/images need semantic extraction, but no provider is configured. | If the user only needs code architecture, rerun `graphify extract <path> --code-only`. If semantic docs/media are required, install/configure one provider extra and rerun with `--backend`. |
| User asks for code-only graph but docs are present | The correct behavior is to skip non-code files. | Use `--code-only`; explain that skipped docs/media can be added later with semantic extraction. |
| `error: backend '<name>' requires ...` | Selected provider extra/key/service is missing. | Install the provider extra, set the right key/service, or choose a local/backend that is available. |
| All semantic chunks fail | Missing provider SDK, bad key, network outage, unsupported model, or local provider unavailable. | Fix the provider, reduce `--max-concurrency`, increase `--api-timeout`, or switch to `--code-only` if semantic content is not required. Do not write a partial semantic graph over a good graph. |
| Partial semantic extraction with shrink warning | Some chunks failed or were omitted. | Rerun after fixing the failure. Use `--allow-partial` only when the user knowingly accepts overwriting with incomplete output. |
| `LLM returned invalid JSON` or truncation warnings | Model output hit limits; Graphify may split/retry. | Raise output cap through provider env vars where supported, reduce `--token-budget`, or use a stronger provider/model. |
| Ollama VRAM/context failures | Local model context window too large or service not healthy. | Set smaller context/model options, reduce `--token-budget`, set `--max-concurrency 1`, and verify the Ollama endpoint. |

## Optional dependency failures

| Symptom | Likely cause | Recovery |
|---|---|---|
| `watchdog not installed` | Watch extra missing. | Install `graphifyy[watch]`; rerun `graphify watch <path>`. |
| `Video transcription requires faster-whisper` or `yt-dlp` import error | Video extra missing. | Install `graphifyy[video]`; confirm media/network/model-cache budget. |
| Parser warning: files contributed nothing because dependency is missing | Optional source-format parser not installed, e.g. SQL/Terraform/DreamMaker/Pascal. | Install the smallest relevant extra and rerun. For deeper format routing, use [extractor-troubleshooting](../../extractor-troubleshooting/SKILL.md). |
| PDF/Office/Google conversion errors | Missing optional parser/renderer/auth. | Install only the relevant extra and authenticate external tools before rerun. |
| SVG/MCP/database errors encountered during build conversation | The user has moved beyond graph building. | Route SVG/database exports to [exports-integrations](../../exports-integrations/SKILL.md) and MCP serving to [query-navigation](../../query-navigation/SKILL.md). |

## Update, manifest, and stale graph failures

| Symptom | Likely cause | Recovery |
|---|---|---|
| `graphify update` says nothing to update but graph is stale | Wrong path, missing `.graphify_root`, stale/poisoned manifest, or changed files are non-code. | Run `graphify update <explicit-path>`; if still stale, run `graphify extract <path> --code-only --force` for code-only rebuild or semantic extraction for docs/media. |
| Code changes update, but docs/media changes do not | `graphify update` is AST/code-oriented. | Run a semantic extraction route: `graphify extract <path> --backend <provider>` or an assistant `/graphify --update` workflow that owns semantic subagents. |
| Deleted files linger as ghost nodes | Manifest/root mismatch or update did not prune sources. | Run `graphify update <path> --force` for code-only changes, or full `graphify extract <path> --force` when semantic/docs are involved. Validate node counts afterward. |
| Excluded files appear as deleted on every run | Ignore/exclude changed after older manifest state. | Rerun a full extraction so `scan_corpus` prunes alive-but-excluded manifest rows. Check `.graphify_build.json`. |
| Manifest missing but graph exists | Existing graph can still serve as incremental baseline. | A current `graphify extract` prints that it is using `graph.json` as baseline. If behavior is confusing, run a full rebuild with `--force`. |
| Portable checkout moved and every file re-extracts | Legacy absolute manifest or wrong root. | Rebuild once with current version so `manifest.json` stores relative keys. |
| Cache appears stale after package upgrade | AST cache is versioned, semantic cache depends on prompt fingerprint. | Use `--force` to skip cache reads, or remove `graphify-out/cache/` if you intentionally want a cold rebuild. |

## Shrink guard and overwrite protection

Graphify intentionally refuses some writes that would replace a larger/valid graph with a smaller or unparseable result.

| Symptom | Likely cause | Recovery |
|---|---|---|
| Warning: new graph has fewer nodes; refusing to overwrite | Possible partial extraction, missing chunks, wrong path, or legitimate deletion/refactor. | First verify path and errors. If legitimate, rerun with `--force` for full rebuild/update. Do not force after an unresolved extractor/provider failure. |
| Existing graph cannot be read; refusing to overwrite | Corrupt or mid-write `graph.json`. | Back up the file, inspect/repair JSON if possible, or delete it only after the user accepts losing that graph baseline. Then rebuild. |
| `extraction was incomplete ... refusing to overwrite` | AST/semantic pass failed and output would be smaller or unsafe. | Fix the failing pass and rerun. Use `--allow-partial` only for a user-approved best-effort graph. |
| `build_merge would drop ... sources neither re-extracted nor pruned` | Incremental merge root/prune mismatch or unexpected graph loss. | Pass an explicit root in API usage; for CLI, rerun with explicit path or full rebuild. |

Before advising `--force`, state what will be overwritten and why the shrink is expected. `--force` is appropriate after intentional deletions/refactors; it is not a fix for missing optional dependencies, provider crashes, or skipped files.

## Cluster/report/HTML failures

| Symptom | Likely cause | Recovery |
|---|---|---|
| `GRAPH_REPORT.md` is missing but `graph.json` exists | Extraction wrote graph JSON but cluster/report pass was not run. | Run `graphify cluster-only <path> --no-viz`. |
| `cluster-only` says no graph found | Wrong path or custom `--out` location. | Pass the path whose child is `graphify-out/`, or use `--graph <actual graph.json>`. |
| `--backend`/`--model` seems ignored during `cluster-only` | Existing labels were reused. | Run `graphify label <path> ...` or delete `.graphify_labels.json` if you intentionally want relabeling. |
| Placeholder `Community N` labels | `--no-label` was used or no LLM label backend available; deterministic hub labels may be used when possible. | Run `graphify label <path> --backend=<provider>` when human-friendly labels are required. |
| `graph.html` missing after cluster-only | `--no-viz` was used, graph was oversized, or HTML generation failed. | `graph.json` and `GRAPH_REPORT.md` are the core artifacts. Omit `--no-viz` or route visualization/export issues to [exports-integrations](../../exports-integrations/SKILL.md). |
| Large graph makes HTML unusable | Browser/visualization size. | Use `graphify cluster-only <path> --no-viz` and query the JSON instead; route query tasks to [query-navigation](../../query-navigation/SKILL.md). |

## Add/watch failures

| Symptom | Likely cause | Recovery |
|---|---|---|
| `graphify add` exits with `error: ...` | Invalid URL, blocked scheme/redirect, network fetch failure, or missing media extra. | Fix URL/network/extra. Do not continue to update if the save failed. |
| `graphify add` saved a file but graph did not change | Add only writes to corpus; update/extract must run afterward. | Run semantic update/extraction for the target directory, usually `graphify extract ./raw --backend <provider>` or assistant `/graphify --update`. |
| Watch starts but docs/images do not update graph | Watch only rebuilds code immediately; non-code writes a `needs_update` flag. | Run `graphify check-update <path>` to see the flag, then run semantic extraction/update. |
| Watch rebuild already in progress | Per-repo rebuild lock is active; changes may queue. | Wait for current rebuild to finish. If lock persists after a crash, inspect process state before deleting anything. |
| GUI/commit hook updates wrong corpus | Saved graph root or path mismatch. | Run explicit `graphify update <path>` or reinstall hooks after package/environment changes via the agent-integration route. |

## Invalid graph shape

| Symptom | Likely cause | Recovery |
|---|---|---|
| Graph JSON lacks `nodes` or edge list | Wrong file, corrupt file, or non-Graphify JSON. | Rebuild with `graphify extract`; avoid using arbitrary JSON as `graph.json`. |
| Edges use `edges` not `links` | Both forms are accepted by readers; current JSON writer usually emits `links`. | Validation scripts should check `data.get('links', data.get('edges', []))`. |
| Dangling edges or missing endpoints | External imports are sometimes expected, but many dangling edges can signal stale IDs or bad semantic output. | Rebuild with current version; use extractor-troubleshooting if source format/parser issue persists. |
| Unexpected reverse edge direction in graph queries | This is a query/path interpretation issue, not a build failure if `source`/`target` are correct. | Route to [query-navigation](../../query-navigation/SKILL.md). |

## When to stop and ask

Stop before continuing when recovery requires:

- Live provider credentials or budget for semantic extraction.
- Network downloads or model cache for media/video.
- Deleting or overwriting an existing `graphify-out/graph.json` after a shrink/corruption warning.
- Installing broad optional extras such as `graphifyy[all]`.
- Running database, serving, or export workflows outside this sub-skill's build scope.
