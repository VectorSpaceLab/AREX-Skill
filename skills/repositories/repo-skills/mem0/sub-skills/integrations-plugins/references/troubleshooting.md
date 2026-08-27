# Integrations Troubleshooting

Use this reference for Mem0 integration failures in Vercel AI SDK, editor/agent plugins, MCP configs, OpenClaw, Pi Agent, and framework cookbooks.

## Triage Order

1. Identify the integration surface: Vercel provider, MCP-only, full editor plugin, OpenClaw, Pi Agent, or framework code.
2. Check install/package versions and host compatibility.
3. Check secrets without printing them: `MEM0_API_KEY` and upstream provider keys.
4. Check scope: `user_id`, `app_id`, `agent_id`, and `run_id` on both write and search paths.
5. Validate config shape with bundled scripts before proposing edits.
6. Restart the host after plugin/MCP changes.
7. Escalate SDK CRUD details to `../sdk-memory/SKILL.md`, provider/backend details to `../provider-configuration/SKILL.md`, CLI issues to `../cli-memory/SKILL.md`, and self-hosted server/OpenMemory issues to `../self-hosted-openmemory/SKILL.md`.

## Install and Import Failures

- `Cannot find module '@mem0/vercel-ai-provider'`: install the package in the application workspace, not only at repo root.
- AI SDK type errors around `LanguageModelV2`/`LanguageModelV3`: provider v3.0.0 targets AI SDK v6 and provider v3. Upgrade `ai` and `@ai-sdk/*` packages together or pin the older Mem0 provider intentionally.
- `createMem0 is not a function`: check ESM/CJS bundling and import from `@mem0/vercel-ai-provider`, not from `mem0ai`.
- `MemoryClient` import errors in Python framework docs: install `mem0ai` in the active Python environment and route direct SDK diagnostics to `../sdk-memory/SKILL.md`.
- OpenClaw installed but inactive: set `plugins.slots.memory` to `openclaw-mem0`; OpenClaw memory plugins use an exclusive slot.
- Pi Agent plugin not loading: verify `pi install npm:@mem0/pi-agent-plugin`, peer package compatibility, and startup errors.

## API Keys and Environment Variables

- Mem0 Platform integrations require `MEM0_API_KEY` unless a trusted config field passes `mem0ApiKey`/`apiKey` explicitly.
- Vercel provider also needs the upstream model key for the selected provider.
- Desktop/editor apps may not inherit shell profile variables. Use the host’s environment editor or persistent config mechanism.
- Do not paste real keys into generated code, shared config, logs, issue comments, or memory contents.
- MCP auth failures often come from wrong interpolation syntax: `${MEM0_API_KEY}`, `${env:MEM0_API_KEY}`, `{env:MEM0_API_KEY}`, and `bearer_token_env_var` are host-specific.

## MCP and Plugin Tool Failures

Run the read-only validator first:

```bash
python scripts/validate_mcp_config.py --kind auto ~/.codex/config.toml .cursor/mcp.json .mcp.json opencode.json
```

Common findings:

- Duplicate `mem0` registrations: remove the manual MCP entry if a full plugin also registers Mem0.
- No tools appearing: restart the editor/agent after install or config change.
- 401/unauthorized: verify env var availability in the host process and token header format.
- Wrong URL: use `https://mcp.mem0.ai/mcp` or the trailing-slash variant accepted by the host; avoid stale local MCP URLs unless intentionally self-hosting.
- Hooks not firing: MCP-only installs do not include hooks; full plugin installs may still require host feature flags or restart.

## Codex-Specific Issues

- Direct MCP must be configured in `config.toml`; `codex mcp add` supports stdio and is not the right path for Mem0’s remote HTTP MCP server.
- Do not combine direct `[mcp_servers.mem0]` with the full Mem0 plugin; the plugin manifest registers MCP itself.
- Hook config is separate from MCP config. Lifecycle hooks require the Codex hooks feature flag:

```toml
[features]
codex_hooks = true
```

- Hook installers mutate user config and write absolute plugin paths. Only run or emulate them after the user approves config mutation.
- On native Windows, shell-hook paths may require WSL or Git Bash rather than direct `.sh` execution.

## Cursor and Claude Issues

- Cursor duplicate tools usually mean both manual MCP/deeplink and marketplace plugin are installed. Remove one path.
- Cursor no tools: check Settings > MCP and confirm `mem0` is connected, then restart.
- Claude/Cowork inactive banner: key is not visible in the host process; set it persistently through shell profile or the desktop environment editor.
- Marketplace/full-plugin installs provide hooks and skills; npx/manual MCP installs only provide memory tools.

## OpenCode, Antigravity, OpenClaw, and Pi Agent Issues

- OpenCode full plugin uses native SDK-backed tools, not remote MCP. Do not add a standalone MCP server unless the user wants MCP-only behavior.
- OpenCode wrong project: launch from inside the repository and check the resolved project scope with `/mem0-status` or equivalent.
- Antigravity MCP 401: check whether the host supports `${MEM0_API_KEY}` interpolation in the plugin config; prefer host secrets over literal shared tokens.
- OpenClaw no memory: install plus activate the memory slot; check `openclaw --version` is compatible.
- OpenClaw open-source mode failures usually involve provider/vector dependencies; route backend details to `../provider-configuration/SKILL.md`.
- Pi Agent dream not running: all gates must pass (`minHours`, `minSessions`, `minMemories`); run `/mem0-status` to see gate progress.
- Pi Agent wrong scope: project scope is based on git root; start Pi from the intended repository.

## Vercel Provider Failures

Run the static checker first:

```bash
node scripts/check_vercel_mem0_usage.mjs app/api/chat/route.ts
```

Common findings:

- Missing `user_id`: wrapped provider and standalone utilities need stable scope to retrieve the same memories they store.
- Empty retrieved memories: no prior writes, mismatched scope, too-strict threshold, different host, or wrong app/agent/run filter.
- Duplicate writes: route uses `createMem0` and also manually calls `addMemories` for the same turn.
- Browser secret leak: `MEM0_API_KEY` appears in client-side code or a literal `m0-` key is committed.
- Provider key mismatch: `provider: "anthropic"` with only `OPENAI_API_KEY`, or similar upstream key omissions.
- Unsupported AI SDK version: package still on `ai@5` while using provider v3.0.0.

## Framework Integration Failures

- LangChain/LangGraph context missing: retrieve before model invocation and insert memory text into the actual prompt/state used by the model.
- LlamaIndex no recall: verify `Mem0Memory.from_client(context={...})` has at least one of `user_id`, `agent_id`, or `run_id`.
- CrewAI memory ignored: set `memory=True` and `memory_config={"provider": "mem0", "config": {"user_id": ...}}`.
- OpenAI Agents SDK tools using arbitrary user IDs: derive scope from trusted application state or constrain schemas.
- Google ADK async errors: wrap sync `MemoryClient` calls with `asyncio.to_thread` or use an async client where appropriate.
- Multi-agent duplicate memories: store final conversation once per turn or include agent metadata and dedup in retrieval.

## Data and Safety Checks

- Redact keys in all diagnostics. It is enough to report presence, source, and apparent prefix shape.
- Do not store secrets, access tokens, raw `.env` contents, or private credentials in Mem0 memories.
- Confirm scope before delete-all/entity-delete calls. Global scopes can affect multiple projects.
- Keep memory context concise; avoid dumping hundreds of memories into prompts.
- If memory capture is automatic, verify categories/metadata are appropriate for the project before relying on it.
