# Headroom operator CLI reference

Use this reference for non-application operational commands. Commands that mutate user configuration or long-running services are marked explicitly.

## Install and durable runtime commands

| Command | Purpose | Side effects |
| --- | --- | --- |
| `headroom deploy` | Choose a turnkey local deployment plan, create a persistent proxy profile, and configure detected tools. | Mutates deployment state and may mutate agent/shell config. |
| `headroom install apply` | Install a named persistent deployment profile with explicit preset/runtime/provider options. | Mutates deployment state; may install supervisor files and config blocks. |
| `headroom install status` | Show profile, runtime, supervisor, port, and health information. | Read-only. |
| `headroom install start` / `stop` / `restart` | Control an existing persistent deployment profile. | Starts/stops processes and toggles managed config mutations. |
| `headroom install remove` | Remove a persistent deployment and undo managed config. | Destructive to the managed profile and its config blocks. |
| `headroom init` | Install durable Headroom integrations for supported agents. | Mutates local or user-level agent config and creates a persistent profile. |
| `headroom init claude/codex/copilot/openclaw` | Install durable hooks/provider routing for a specific agent. | Mutates that agent's config. |
| `headroom update` | Detect install method and upgrade Headroom when safe. | Mutates the Python or tool install if supported. |

Important update behavior:

- Editable/source checkouts and Docker images are not self-updated by `headroom update`; use git or image update flows.
- Externally managed system Python installs are refused with guidance instead of force-pip installing.
- Windows update code protects the native `_core.pyd` against corruption when it is locked by a running proxy.

## Diagnostics and reports

| Command | Purpose | Safe when |
| --- | --- | --- |
| `headroom doctor [--json]` | Correlate proxy liveness, version drift, client routing, deployment state, and savings flow. | Always safe; exit code 0 healthy, 1 warnings, 2 failures. |
| `headroom dashboard [--port]` | Open or print the local dashboard URL. | Safe; browser opening is the only side effect. |
| `headroom inspect --last N [--full]` | Diff original vs compressed message snapshots from a running proxy with message logging enabled. | Safe; requires proxy `/transformations/feed`. |
| `headroom perf [--hours N] [--raw] [--format text|json|csv]` | Analyze `PERF` records from proxy logs. | Safe; empty logs are normal before traffic. |
| `headroom savings [--json] [--days N]` | Aggregate durable savings ledger. | Safe unless `--reset` is used. |
| `headroom output-savings` | Report estimated/measured output-token reduction from output shaper data. | Safe. |
| `headroom agent-savings` | Render or verify coding-agent token-savings profiles. | Safe unless a profile write/apply option is explicitly used. |
| `headroom audit-reads` | Audit Read-tool traffic for compression opportunities. | Safe; reads recorded session/log data. |
| `headroom capture network-diff --direct A --headroom B` | Compare two JSONL network captures. | Safe; writes reports only if output paths are supplied. |

## Tools and evals

| Command | Purpose | Notes |
| --- | --- | --- |
| `headroom sg ...` | Pass through to bundled `ast-grep`. | Lets agents use AST-aware structural search/replace. |
| `headroom diff ...` | Pass through to bundled `difftastic`. | Useful for semantic diffs. |
| `headroom loc ...` | Pass through to bundled `scc`. | Useful for quick repo-shape probes. |
| `headroom tools list` | Show tool registry and cache dir. | Read-only. |
| `headroom tools doctor [--json]` | Check bundled tool availability. | Read-only. |
| `headroom tools install` | Prefetch binary tools into the per-user cache. | Downloads/writes to cache; ask first on locked-down systems. |
| `headroom evals memory` / `memory-v2` | Run LoCoMo memory evaluation flows. | Often requires LLM API keys and can be expensive. |
| `headroom evals adversarial` | Measure compression robustness against adversarial payloads. | Potentially long-running; confirm budget. |
| `headroom evals probes` | Offline retention probes over recorded compression events. | Safe when using local recorded data. |

## Canonical paths

Headroom separates read-mostly config from read-write state:

- `HEADROOM_CONFIG_DIR` defaults to `~/.headroom/config`.
- `HEADROOM_WORKSPACE_DIR` defaults to `~/.headroom`.
- Resource-specific overrides such as `HEADROOM_SAVINGS_PATH`, `HEADROOM_SAVINGS_EVENTS_PATH`, `HEADROOM_TOIN_PATH`, `HEADROOM_SETTINGS_PATH`, and `HEADROOM_SUBSCRIPTION_STATE_PATH` win over the canonical roots.

Do not assume a user's workspace is under the current project. Use `headroom.paths` helpers or `scripts/diagnose_headroom_install.py --json` when inspecting paths.
