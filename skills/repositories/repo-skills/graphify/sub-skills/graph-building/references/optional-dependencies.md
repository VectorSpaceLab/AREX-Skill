# Optional dependencies for graph building

## Purpose

Graphify's base package can build code graphs locally. Optional extras are only needed for selected input types, semantic providers, watch mode, or advanced clustering/export surfaces. Install the smallest extra set that matches the user's requested graph-building workflow.

Default verification for this generated skill covered the base CPU package and code-only graph construction. The optional extras below are public package surfaces, but live provider/media/database/service behavior should be treated as unverified until a focused environment check is run.

## Install pattern

The public package name is `graphifyy` even though the CLI is `graphify`.

```bash
# Fresh isolated tool install with one extra.
uv tool install "graphifyy[gemini]"
pipx install "graphifyy[gemini]"

# Existing Python environment.
python -m pip install "graphifyy[gemini]"

# Run without installing a persistent command.
uvx --from "graphifyy[gemini]" graphify --help
```

If a tool was already installed without the needed extra, reinstall/upgrade it with the same installer and the desired extra. Do not install `graphifyy[all]` unless the user explicitly wants broad optional coverage.

## What needs no extra

Base install covers:

- Local AST/code extraction for the default language set.
- `graphify extract <path> --code-only`.
- `graphify update <path>` for code changes.
- `graphify cluster-only` with NetworkX Louvain fallback when Leiden/graspologic is absent.
- Detection, manifest/cache handling, graph JSON build/merge, and report generation.

A code-only corpus requires no API key and no provider extra.

## Semantic provider extras

Use a provider extra only when docs, papers, images, or semantic dedup/labeling must call a provider from the headless CLI.

| Backend | Extra / install | Credentials or service | Notes |
|---|---|---|---|
| `gemini` | `graphifyy[gemini]` | `GEMINI_API_KEY` or `GOOGLE_API_KEY` | Common choice for docs/images. Supports model override with `--model` or provider env vars. |
| `kimi` | `graphifyy[kimi]` | `MOONSHOT_API_KEY` | Routes to Moonshot/Kimi services; consider data residency. |
| `claude` | `graphifyy[anthropic]` | `ANTHROPIC_API_KEY` | Uses Anthropic SDK/API for headless semantic extraction. |
| `openai` | `graphifyy[openai]` | `OPENAI_API_KEY`; optional `OPENAI_BASE_URL` and model env for compatible servers | Also used for Azure-compatible/OpenAI-compatible endpoints in documented flows. |
| `deepseek` | Provider-compatible dependency path | `DEEPSEEK_API_KEY` | CLI backend exists; verify the selected install has the needed SDK before live use. |
| `ollama` | `graphifyy[ollama]` | Local Ollama service; loopback can run without cloud API key | Use low `--max-concurrency`, set `OLLAMA_BASE_URL`/model vars as needed. |
| `bedrock` | `graphifyy[bedrock]` | AWS IAM/profile/region credentials | Optional live cloud route; do not verify without user-approved AWS context. |
| `claude-cli` | Base package plus `claude` CLI on PATH | Authenticated Claude Code CLI | No API key, but requires the external CLI already authenticated. |

Useful flags:

```bash
graphify extract ./docs --backend gemini --model gemini-3-flash-preview
graphify extract ./docs --backend ollama --max-concurrency 1 --token-budget 4000
graphify extract ./docs --mode deep --backend openai
```

If no provider key/service is available and the user's goal is code architecture, use `--code-only` instead of stopping.

## File-format and media extras

| Input type | Extra | Command/use | Failure symptom | Recovery |
|---|---|---|---|---|
| PDF files | `pdf` | `graphify extract ./docs --backend <provider>` | PDF skipped or parser import error. | Install `graphifyy[pdf]`; rerun semantic extraction. |
| Office `.docx` / `.xlsx` | `office` | Converts to Markdown sidecars under `graphify-out/converted/`. | `office conversion failed - pip install graphifyy[office]`. | Install `graphifyy[office]`; rerun. |
| Google Workspace shortcuts `.gdoc` / `.gsheet` / `.gslides` | `google` for Sheets rendering, plus authenticated `gws` CLI | `graphify extract ./docs --google-workspace` or `GRAPHIFY_GOOGLE_WORKSPACE=1`. | Shortcut skipped by default or Google Workspace export failed. | Authenticate `gws`, install needed extra, then rerun with `--google-workspace`. |
| Video/audio files and video URLs | `video` | `graphify add <video-url>` or extract a corpus with video files; transcription uses faster-whisper/yt-dlp. | `Video transcription requires faster-whisper` or `YouTube/URL download requires yt-dlp`. | Install `graphifyy[video]`; ensure model/cache/network budget is acceptable. |
| Watch mode | `watch` | `graphify watch ./src`. | `watchdog not installed`. | Install `graphifyy[watch]`. |

Video/audio transcription is local by default but may download models or URL media. Ask for budget/network approval before running large media workflows.

## Optional language/source-format extras

Some source formats are recognized by detection but need optional parser packages for AST-quality extraction. For deeper source-format troubleshooting, route to [../extractor-troubleshooting/SKILL.md](../../extractor-troubleshooting/SKILL.md).

| Extra | Adds | Notes |
|---|---|---|
| `sql` | SQL parser support via `tree-sitter-sql`. | SQL schema/source files may otherwise contribute little or warn about missing dependency. |
| `postgres` | Live PostgreSQL introspection with `--postgres DSN`. | Requires a live database and credentials; avoid default verification. |
| `terraform` | Terraform/HCL `.tf`, `.tfvars`, `.hcl`. | Install before claiming Terraform graph coverage. |
| `pascal` | Pascal/Delphi AST-quality extraction. | Regex fallback may exist when absent, but AST-quality edges need the extra. |
| `dm` | BYOND DreamMaker `.dm`/`.dme`. | May require C compiler and Python headers on non-Windows platforms. |
| `chinese` | Chinese query segmentation. | Mostly query/navigation relevance, not needed for building ordinary code graphs. |

## Clustering and visualization-related extras

| Extra | Adds | Graph-building note | Owning route for deeper use |
|---|---|---|---|
| `leiden` | Graspologic Leiden community detection. | Without it, Graphify falls back to NetworkX Louvain. Python `<3.13` only per package metadata. | This sub-skill for `cluster-only`; advanced analysis stays here only if build-related. |
| `svg` | Matplotlib-backed SVG export. | Not needed for `graph.json` or `GRAPH_REPORT.md`. | [exports-integrations](../../exports-integrations/SKILL.md). |
| `mcp` | MCP stdio/HTTP serving dependencies. | Not needed to build a graph. | [query-navigation](../../query-navigation/SKILL.md). |
| `neo4j`, `falkordb` | Live database push clients. | Not needed to build a graph; local Cypher generation may be enough. | [exports-integrations](../../exports-integrations/SKILL.md). |

## Choosing the smallest install

- **Code-only repo:** base `graphifyy`.
- **Code + Markdown docs with cloud semantic extraction:** base + one provider extra, usually `gemini`, `openai`, `anthropic`, or `kimi`.
- **PDF corpus:** `pdf` + one provider extra.
- **Office corpus:** `office` + one provider extra.
- **Google Workspace shortcuts:** `google`, authenticated `gws`, and one provider extra.
- **Video/audio:** `video`, local model/cache budget, and provider only if the transcript/docs then need semantic extraction.
- **Continuous code update:** `watch` if using `graphify watch`; no provider for code-only changes.
- **Language-specific parser gap:** install only the relevant language extra, then rerun a focused extraction.

## Verification after installing an extra

Run the lowest-cost command that exercises only the selected capability. The bundled smoke path is relative to the `graphify` repo-skill root directory:

```bash
# Provider metadata/help only.
graphify --help
python - <<'PY'
import graphify
print('graphify import ok')
PY

# Code-only smoke after any install change.
python sub-skills/graph-building/scripts/build_tiny_graph.py

# Watch extra.
python -m graphify.watch --help

# Optional parser/import probe examples.
python - <<'PY'
# Replace with the optional module you intentionally installed.
import importlib
for name in ['tree_sitter_sql', 'tree_sitter_hcl']:
    try:
        importlib.import_module(name)
        print(name, 'ok')
    except ImportError:
        print(name, 'not installed')
PY
```

Do not run live provider calls, DB pushes, Google Workspace auth, or large media downloads as a default smoke check. Ask for explicit credentials, network, and budget approval first.
