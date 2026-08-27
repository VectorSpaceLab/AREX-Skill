# Harness Support Reference

This reference is the operating map for Observal harness support. It distills the registry, adapters, scan/doctor/layer behavior, config generation, hook specs, and verification surfaces into one self-contained guide.

## Architecture invariants

- Canonical harness identity is the registry key in `packages/observal-shared/observal_shared/harness_registry.py`.
- CLI-side harness behavior lives in `observal_cli/harness/<harness>.py` and registers itself through `register_adapter(...)`; `observal_cli/harness/load_all.py` imports every adapter.
- Server-side install/config generation lives in `observal-server/services/harness/<harness>.py` and registers itself through `register_adapter(...)`; `observal-server/services/harness/load_all.py` imports every adapter.
- Shared orchestration uses adapters. Avoid adding harness-specific if/elif chains to `cmd_scan.py`, config generation, or pull/install code when an adapter method is the right home.
- `BaseAdapter` gates CLI methods with `METHOD_FEATURE_MAP`: `generate_hook_config`, `detect_hooks`, and `get_hook_spec` require `hooks`; `scan_home` and `scan_project` require `mcp_servers`.
- Server config generation enters through `services.harness.generate_agent_config(...)`, builds `ConfigContext` and `McpConfigContext`, then delegates to the selected server adapter.
- `/api/v1/config/harnesses` returns harness names, display names, capabilities, and supported model ids from the shared registry. Frontend harness pickers should consume this endpoint rather than hardcoding names.

## Current harness matrix

| Harness id | Display | Capabilities | Default scope | Parser id | CLI adapter | Server adapter | Dedicated hook spec |
|---|---|---|---|---|---|---|---|
| `cursor` | Cursor | hooks, mcp_servers | project | `cursor` | `observal_cli/harness/cursor.py` | `observal-server/services/harness/cursor.py` | no; doctor code patches directly |
| `kiro` | Kiro | hooks, mcp_servers | user | `kiro` | `observal_cli/harness/kiro.py` | `observal-server/services/harness/kiro.py` | `kiro_hooks_spec.py` |
| `claude-code` | Claude Code | hooks, mcp_servers, skills | project | `claude-code` | `observal_cli/harness/claude_code.py` | `observal-server/services/harness/claude_code.py` | `claude_code_hooks_spec.py` |
| `codex` | Codex | hooks, mcp_servers, skills | project | `codex` | `observal_cli/harness/codex.py` | `observal-server/services/harness/codex.py` | `codex_hooks_spec.py` |
| `copilot` | Copilot | hooks, mcp_servers, prompts, skills | project | `copilot-cli` | `observal_cli/harness/copilot.py` | `observal-server/services/harness/copilot.py` | `copilot_hooks_spec.py` |
| `copilot-cli` | Copilot CLI | hooks, mcp_servers, prompts, skills | project | `copilot-cli` | `observal_cli/harness/copilot_cli.py` | `observal-server/services/harness/copilot_cli.py` | `copilot_cli_hooks_spec.py` |
| `opencode` | OpenCode | hooks, mcp_servers, skills | user | `opencode` | `observal_cli/harness/opencode.py` | `observal-server/services/harness/opencode.py` | `opencode_hooks_spec.py` |
| `antigravity` | Antigravity | hooks, mcp_servers, skills | user | `antigravity` | `observal_cli/harness/antigravity.py` | `observal-server/services/harness/antigravity.py` | `antigravity_hooks_spec.py` |
| `goose` | Goose | hooks, mcp_servers, skills | user | `goose` | `observal_cli/harness/goose.py` | `observal-server/services/harness/goose.py` | `goose_hooks_spec.py` |
| `pi` | Pi | hooks, mcp_servers, skills | user | `pi` | `observal_cli/harness/pi.py` | `observal-server/services/harness/pi.py` | no; Pi uses a bundled extension |

Notes:

- Copilot and Copilot CLI share the `copilot-cli` parser id while retaining separate CLI source adapters.
- Cursor and Pi still have `hooks` capability in the registry even though they do not have dedicated `harness_specs/*_hooks_spec.py` files.
- Kiro is the most complete reference harness for registry + adapter + config generation + session parser + Playwright coverage.

## Registry fields to audit

Every harness registry entry should provide, as applicable:

- `display_name`: human label shown in CLI/web.
- `capabilities`: set of `hooks`, `mcp_servers`, `skills`, `prompts`; this drives feature gating and compatibility warnings.
- `session_parser`: parser id used by server read and ingest dispatch.
- `scopes`, `default_scope`, `scope_labels`: install scope behavior.
- `agent_profile` and `agent_profile_format`: where agent profiles are written and how to serialize them.
- `mcp_config` and `mcp_servers_key`: native MCP config location and top-level key.
- `skills` and `skill_format`: native skill file layout.
- `hooks`, `hook_type`, `hook_scripts_dir`, `hook_events_map`: managed hook config layout and canonical event mapping.
- `guidance_files`: files scanned as context but not overwritten.
- `model_catalog_file` and `supported_models`: added from `harness_models/*.json` through `harness_models.py`.

Use the bundled helper to catch obvious omissions:

```bash
python skills/disco/observal/sub-skills/harness-telemetry/scripts/check_harness_registry.py --repo-root . --pretty
```

Expected signal: `registry_count` is `10`; parser coverage lists no missing read parsers, ingest classifiers, or timestamp extractors; adapter files are present for every registry key.

## CLI adapter contract

A CLI adapter usually owns all of the following:

- `harness_name`: exact registry key.
- `home_markers`: reliable markers for installed-harness detection.
- `managed_agent_profiles`, `managed_skills`, `managed_mcp_files`: layer attribution patterns consumed by `BaseAdapter.get_observal_managed_files(...)`.
- `scan_home(home=None)` and `scan_project(project_dir)`: return `ScanResult` with discovered MCPs, skills, hooks, and agents.
- `get_hook_spec()` and `generate_hook_config(...)`: expose installable hook metadata/config for this harness.
- `detect_hooks(config_dir)`: return `installed`, `partial`, `missing`, or `none` without modifying files.
- `patch_hooks(dry_run)` and `cleanup_hooks(dry_run)`: delegate to `cmd_doctor.py` implementations for user-visible patch/cleanup.
- `resolve_session_source(event, home=None)` and `discover_session_sources(home=None, since_hours=168)`: map hook/reconcile wake-ups to `SessionSource` records.
- `related_session_sources(...)`, `session_extra_fields(...)`, `session_extra_records(...)`, `defer_session_delivery()`, `aged_recovery_final()`, and `is_session_final(...)`: opt into subagents, metadata-only rows, synthetic source rows, detached delivery, recovery finalization, and final lifecycle detection.
- `resolve_session_agent_identity(...)` or `requires_explicit_agent_id()`: keep attribution accurate when agent identity cannot be inferred safely.

Adapter examples to mirror:

- `ClaudeCodeAdapter`: JSONL discovery under projects, subagent source handling, managed settings hooks, plugin/skill scanning.
- `KiroAdapter`: per-agent UUID-attributed hooks, companion metadata for cwd/credits, explicit-agent-id requirement.
- `CursorAdapter`: transcript path resolution, subagent handling, synthetic usage rows, detached delivery.
- `GooseAdapter`: read-only SQLite export to append-only JSONL mirrors, plugin scan/patch, Goose path resolution.
- `CopilotAdapter`: materializes VS Code hook payloads into JSONL-compatible local source files.
- `CopilotCliAdapter`: reads `events.jsonl`, discovers via session state/store, and rewrites hook commands with per-agent attribution.
- `AntigravityAdapter`: resolves native transcript paths, caches missing Stop session id, returns host-required hook response through a bridge.
- `PiAdapter`: harness-centric config and extension detection; no Python source adapter is used for Pi extension telemetry.

## Server adapter contract

Server adapters format install responses for `observal agent pull` and component installs. Typical result keys include:

- `agent_profile`: native path and content for the harness profile.
- `mcp_config`: native MCP config path/content, using the registry's key/format.
- `hooks_config`: hook config path/content and optional `merge: True`.
- `hook_files`: scripts, plugin manifests, wrappers, or hook component files.
- `skill_components`, `skills`, `prompt_files`: generated component files for harnesses with first-class support.
- `_warnings`: compatibility or model warnings surfaced to the caller.

Important format examples:

- Kiro writes JSON agent profiles with `hooks.userPromptSubmit` and `hooks.stop` containing `OBSERVAL_AGENT_ID=<uuid> python3 -m observal_cli.hooks.session_push --harness kiro` on non-Windows systems.
- Cursor writes `.cursor/hooks.json` with `beforeSubmitPrompt` and `stop`, and merges custom hook components into that JSON.
- Goose writes `.agents/plugins/observal/plugin.json` plus `.agents/plugins/observal/hooks/hooks.json`; MCP servers become Goose `extensions` in `config.yaml`.
- Copilot/Copilot CLI write `.github/agents/{name}.agent.md`; Copilot MCP uses `.vscode/mcp.json` with `servers`, while Copilot CLI uses the Copilot MCP config path/key from the registry.
- OpenCode writes agent Markdown and `opencode.json`/`~/.config/opencode/opencode.json` with an `mcp` map; custom hook components become plugin files.
- Pi rewrites global/user paths into per-agent Pi profile directories.

When generated server hook commands use a generic interpreter (`python3`) or a stale bridge name, the CLI pull path must rewrite them to the local interpreter and the current shared hook entrypoint before writing files.

## Scan, doctor, and layer surfaces

### Scan

`observal scan` is read-only. It calls every loaded adapter unless `--harness` is supplied, merges home and project results, deduplicates MCPs first-discovered-wins, and emits either tables or JSON.

Verification:

```bash
observal scan --harness kiro --output json
```

Expected signal: JSON includes `harnesses`, `mcps`, `skills`, `hooks`, and `agents`; an unknown harness is rejected before scanning.

### Doctor

`observal doctor` diagnoses auth/server reachability, lockfile drift, hook installation status, stale legacy hooks, and missing bundled Observal skills. `observal doctor patch` and `observal doctor cleanup` route through adapter `patch_hooks`/`cleanup_hooks` methods.

Safe verification:

```bash
observal doctor patch --harness goose --dry-run --output json
observal doctor cleanup --harness goose --dry-run --yes --output json
```

Expected signal: JSON has `action`, `dry_run`, `changed`, and `targets` fields; dry run does not write files.

Harness-specific doctor notes:

- Claude Code: reconciles `.claude/settings.json`; removes legacy `OBSERVAL_*` env keys on cleanup.
- Kiro: repairs UUID-attributed hooks for agents recorded in the lockfile; it does not install a generic global Kiro hook.
- Cursor: direct doctor patch writes `~/.cursor/hooks.json`; scan hook status may not be the final authority for Cursor.
- Codex: writes `~/.codex/hooks.json` and ensures `codex_hooks = true` in `~/.codex/config.toml`.
- Copilot VS Code: writes `.github/hooks/observal.json` and a PowerShell wrapper for Windows/VS Code behavior.
- Copilot CLI: writes `~/.copilot/hooks/observal.json` or project hook files in pull flows.
- OpenCode: installs or updates `observal-plugin.ts` by content hash.
- Antigravity: writes the named `observal-telemetry` entry in Gemini/Antigravity hooks config.
- Goose: writes the Observal plugin directory and preserves non-Observal rules in that plugin.
- Pi: installs or refreshes the bundled `observal.ts` extension and removes legacy `npm:observal-pi` registration.

### Layer and managed files

`observal_cli/layer.py` computes a layer hash from user/project files that shape AI behavior. Add each new harness to `HARNESS_LAYER_CONFIGS`, add reliable adapter `home_markers`, and set managed file patterns for layer source attribution. If the simple `{name}` patterns cannot describe installed files, override `get_observal_managed_files(...)` in the adapter.

Verification:

```bash
cd observal-server && uv run pytest ../tests/test_cli_harness_adapters.py::TestManagedLayerFiles -q
```

Expected signal: tests prove Observal-owned files are attributed distinctly from user-created rules/config.

## Add or promote a harness checklist

1. Research the host's native MCP, skills, agent profile, hooks, session source, lifecycle events, model selection, and user/project scope behavior.
2. Add or update the registry entry and model catalog file.
3. Implement/update the CLI adapter, including scans, hook detection, session source discovery, managed file attribution, and doctor delegation.
4. Add imports in both `observal_cli/harness/load_all.py` and `observal-server/services/harness/load_all.py`.
5. Implement/update the server adapter's `format_config(...)` and MCP formatting.
6. Add a hook spec module when the harness uses a reusable managed hook config; otherwise document why doctor handles it directly.
7. Add or update `cmd_doctor.py` `_check_*`, `_patch_*`, and `_cleanup_*` behavior.
8. Add `cmd_scan.py` home display path if needed.
9. Add `HARNESS_LAYER_CONFIGS` globs and managed file patterns.
10. Add or reuse a server session parser and ingest classifier; registry `session_parser` must match.
11. Add tests for registry keys, adapter registration, scanning, hook detection, doctor dry-run, config generation, session delivery/reconcile, parser output, and layer attribution.

## Verification command set

Run the smallest safe set for the changed surface:

```bash
# Registry, parser, hook-spec, and adapter-file coverage
python skills/disco/observal/sub-skills/harness-telemetry/scripts/check_harness_registry.py --repo-root . --pretty

# Registry invariants
cd observal-server && uv run pytest ../tests/test_harness_registry.py -q

# CLI adapter registration, feature gating, managed-file attribution
cd observal-server && uv run pytest ../tests/test_cli_harness_adapters.py -q

# Hook spec builders and Observal hook markers
cd observal-server && uv run pytest ../tests/test_harness_specs.py -q

# Install/config-generation behavior
cd observal-server && uv run pytest ../tests/test_harness_config_e2e.py -q
```

Expected signal: all selected tests pass; the helper shows no missing parser coverage. If only one harness changed, also run that harness's focused tests such as `tests/test_goose_adapter.py`, `tests/test_antigravity_adapter.py`, or session-delivery/parser tests named for the harness.
