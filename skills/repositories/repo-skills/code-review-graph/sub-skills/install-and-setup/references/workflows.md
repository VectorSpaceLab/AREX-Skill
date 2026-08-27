# Setup and Graph Lifecycle Workflows

## Purpose

Read this when installing `code-review-graph`, configuring an MCP client, building/updating the graph, checking freshness, serving MCP, visualizing the graph, or uninstalling CRG-owned artifacts.

## Installation choices

Use one package install path per user environment:

```bash
pip install code-review-graph
# or
pipx install code-review-graph
# or no persistent install
uvx code-review-graph --help
```

Requirements:

- Python 3.10 or newer.
- A source-code directory to analyze. Git repositories are best because CRG can use tracked files and diffs, but non-git directories can still be built.
- Optional `uv` improves portability because generated MCP configs can call `uvx` when appropriate.

After installation, run the project-scoped setup from the repository root:

```bash
code-review-graph install
code-review-graph build
code-review-graph status
```

`install` writes CRG-owned MCP config, hooks, and platform instructions for detected clients. It is repeatable and merges known CRG-owned blocks instead of blindly replacing unrelated entries.

## Platform-specific install

Use `--platform` to target one surface instead of auto-detecting all:

```bash
code-review-graph install --platform codex
code-review-graph install --platform claude-code
code-review-graph install --platform cursor
code-review-graph install --platform codebuddy
code-review-graph install --platform copilot-cli
```

Supported platform names include: `codex`, `claude`, `claude-code`, `cursor`, `windsurf`, `zed`, `continue`, `opencode`, `antigravity`, `gemini-cli`, `qwen`, `kiro`, `qoder`, `copilot`, `copilot-cli`, `codebuddy`, and `all`.

Important platform behavior:

- Claude Code uses project `.mcp.json`; hooks and session instructions remind agents to prefer graph tools when `.code-review-graph/graph.db` exists.
- Codex and GitHub Copilot CLI have user-scoped config files but still analyze the current repo.
- CodeBuddy installs CodeBuddy-native skill and hook files rather than Claude-specific files.
- Re-run `install` after changing virtual environments if the previous MCP config captured an old executable path.

## Graph lifecycle commands

| Command | Use when | Notes |
| --- | --- | --- |
| `code-review-graph build` | First graph creation, branch changes, parser/schema suspicion. | Full parse; can be slower on large repos. |
| `code-review-graph update` | Graph may be stale after edits or rebases. | Incremental parse; resolves the last-synced base when possible. |
| `code-review-graph update --brief` | Need a quick update plus risk/token-savings panel. | Useful before reviewing a small diff. |
| `code-review-graph status` | Need graph health: files, nodes, edges, languages, built/current VCS metadata. | `--json` is suitable for scripts. |
| `code-review-graph watch` | Keep one repo fresh on file save. | Avoid running multiple build/watch processes against the same DB. |
| `code-review-graph forget PATH ...` | Remove already-parsed paths without a full rebuild. | Use for tracked generated/vendor files that should no longer appear. |

The graph database lives under `.code-review-graph/graph.db` by default. Commands that read status should not create a missing external data directory; this is tested behavior.

## MCP server workflows

Start stdio MCP for clients that launch CRG directly:

```bash
code-review-graph serve
# alias:
code-review-graph mcp
```

Serve a specific repo:

```bash
code-review-graph serve --repo /path/to/repo
```

Start local HTTP MCP only when a client explicitly needs Streamable HTTP:

```bash
code-review-graph serve --http --host 127.0.0.1 --port 5555
```

The HTTP mode applies a loopback Host/Origin guard for loopback binds. Same-origin and no-Origin non-browser clients are allowed, while foreign Origins and DNS-rebinding Host headers are rejected.

Long-running MCP tools such as build, postprocess, embed, detect-changes, and wiki generation are registered asynchronously and offload blocking work, so stdio clients remain responsive.

## Visualization workflow

After a graph exists:

```bash
code-review-graph visualize
```

This generates a self-contained local HTML visualization. A JSON export path is also available through the CLI's visualization options. Use visualization for architecture inspection, but use MCP graph tools for token-efficient answers.

## Uninstall workflow

Preview before removing CRG-owned files:

```bash
code-review-graph uninstall --dry-run
```

Apply after confirming the preview:

```bash
code-review-graph uninstall --yes
```

Useful flags include:

- `--all-repos` to clean registered repositories as well.
- `--keep-data` to remove integrations while preserving graph databases.
- `--keep-user-configs` when shared user config files should not be edited.
- `--repo <path>` to target a specific repository.

## Minimal smoke checks

Run from any shell after install:

```bash
python -c "import code_review_graph; print(code_review_graph.__version__)"
code-review-graph --version
code-review-graph status
```

If the import works but the command is not found, use `python -m code_review_graph ...`, fix PATH, or reinstall with `pipx`/`uvx`.