# Installation and Entrypoints

## Purpose

Use this reference when a task asks how to install `gptme`, choose extras, verify an installed runtime, or find the correct console script. It is distilled from the package metadata, public docs, and installed-package inspection.

## Supported Python and distribution

- Distribution name: `gptme`.
- Import root: `gptme`.
- Verified package version for this skill: `0.32.1`.
- Python support in package metadata: `>=3.10`.
- The generated skill verified an editable install with selected extras `server`, `acp`, and `tui` in a private inspection environment.

## Installation patterns

End-user isolated installs:

```bash
pipx install gptme
uv tool install gptme
```

Common extras:

```bash
pipx install 'gptme[server]'
pipx install 'gptme[server,browser]'
pipx install 'gptme[acp]'
pipx install 'gptme[tui]'
```

Editable checkout install for maintainers:

```bash
pipx install -e .
pipx install -e '.[server,acp,tui]'
```

Do **not** recommend `[all]` by default. Choose extras from the task:

| Extra | Use when | Notes |
| --- | --- | --- |
| `server` | Running `gptme-server`, bundled Web UI, REST/SSE API, server metrics/auth. | Installs Flask-related dependencies. |
| `browser` | Browser tool with Playwright. | Python dependency is not enough; browser binaries may still need `playwright install`. |
| `acp` | ACP-compatible editor/agent integration or `gptme-acp`. | The separate `gptme-acp` shim can be launched with `uvx gptme-acp`. |
| `tui` | `gptme-tui`. | Installs Textual. |
| `telemetry` | OpenTelemetry/metrics development or deployment. | Requires additional collector configuration for real traces/metrics. |
| `datascience`, `sounds`, `sandbox` | Optional tool-specific capabilities. | Install only for tasks that need them. |
| `eval`, `swebench`, `dspy` | Benchmark execution and specialized eval integrations. | May require provider keys, network, Docker, and long runtimes. |

## Optional system dependencies

Common system-level dependencies are task-specific:

- `tmux` for long-running terminal sessions and tmux tool support.
- `gh` for GitHub issue/PR workflows.
- `shellcheck` for shell command validation and pre-commit checks.
- `playwright install` or a configured `lynx` binary for browser workflows.
- X11/VNC/Docker/system packages for computer-use workflows.
- Node/npm for Web UI development in a checkout.

Treat these as optional surface requirements, not core package import requirements.

## Console script map

Installed-package inspection found these console scripts:

| Script | Use for | Owning route |
| --- | --- | --- |
| `gptme` | Main terminal chat CLI. | `cli-and-conversations` |
| `gptme-util` | Utility commands for chats, MCP, skills, profiles, and related management. | `cli-and-conversations`, `tools-and-extensibility` |
| `gptme-server` | REST/SSE server and bundled Web UI. | `server-webui-and-protocols` |
| `gptme-acp` | Agent Client Protocol stdio agent. | `server-webui-and-protocols` |
| `gptme-tui` | Textual terminal UI. | `server-webui-and-protocols` |
| `gptme-agent` | Persistent/autonomous agent workspace management. | `cli-and-conversations` |
| `gptme-auth` | OAuth/device-flow and provider authentication helpers. | `configuration-and-providers` |
| `gptme-doctor` | System diagnostics and health checks. | `configuration-and-providers` |
| `gptme-mcp-server` | Expose selected gptme tools as an MCP server. | `tools-and-extensibility` |
| `gptme-eval`, `gptme-eval-swebench`, `gptme-eval-tbench`, `gptme-eval-trends`, `gptme-dspy` | Eval and benchmark workflows. | `evals-and-benchmarks` |
| `gptme-attest`, `gptme-checkpoint`, `gptme-init`, `gptme-onboard`, `gptme-resume`, `gptme-status`, `gptme-stats`, `gptme-tutorial`, `gptme-wut` | Focused convenience or status commands. | Start from `cli-and-conversations`; route by the task. |

## Safe installed-runtime checks

Use these generated helpers first:

```bash
python scripts/check_gptme_environment.py --check-server-app
python scripts/run_gptme_help_matrix.py
```

They check imports, entry points, help output, and server route registration without making model calls, starting browsers, starting Docker, or running benchmark suites.

## When not to keep going

Stop and ask for user authorization before:

- installing browser binaries, Node dependencies, Docker images, or system services;
- launching OAuth flows or browser/device authentication;
- running evals that consume model credits or external datasets;
- exposing `gptme-server` beyond loopback;
- mutating an existing user-owned Python environment.
