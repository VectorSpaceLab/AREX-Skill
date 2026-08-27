# Always-on guidance and hooks

Graphify's assistant integrations are meant to make future agents query an existing graph before grepping or reading raw source. This reference covers persistent instruction files, assistant hooks, strict mode, and Git hooks that keep `graphify-out/` current.

## Always-on instruction contract

Installed guidance consistently tells the assistant:

- If `graphify-out/graph.json` exists, answer codebase and architecture questions by first running `graphify query "<question>"`.
- Use `graphify path "<A>" "<B>"` for relationship questions and `graphify explain "<concept>"` for focused concepts.
- Use `graphify-out/wiki/index.md` for broad navigation when it exists.
- Read `graphify-out/GRAPH_REPORT.md` only for broad architecture review or when query/path/explain do not surface enough detail.
- After modifying code, run `graphify update .` to refresh the graph with AST-only extraction.
- Dirty `graphify-out/` files after hooks or incremental updates are expected; dirty graph files are not a reason to skip Graphify.

If the user's real task is to build or update the graph, switch to [graph-building](../../graph-building/SKILL.md). If the task is to answer from the graph, switch to [query-navigation](../../query-navigation/SKILL.md).

## Assistant always-on mechanisms

| Platform family | Installed guidance | Hook behavior |
|---|---|---|
| Claude Code | `CLAUDE.md` and `.claude/CLAUDE.md` skill registration/project settings | PreToolUse hooks for `Bash|Grep` search and `Read|Glob` source reads. Search is always nudge-only. Read can be strict when explicitly installed strict. |
| CodeBuddy | `CODEBUDDY.md` | Same shell-agnostic PreToolUse hook style as Claude Code. |
| Codex | `AGENTS.md` | `.codex/hooks.json` registers `graphify hook-check`, intentionally a no-op because Codex Desktop rejects `hookSpecificOutput.additionalContext` for PreToolUse. Do not treat absence of Codex hook nudges as a broken install if `AGENTS.md` is present. |
| Gemini CLI | `GEMINI.md` | `.gemini/settings.json` BeforeTool hook calls `graphify hook-guard gemini`; it always allows and only appends context when a graph exists. |
| OpenCode | `AGENTS.md` | `.opencode/plugins/graphify.js` plus `.opencode/opencode.json` register a `tool.execute.before` plugin that prepends a graph reminder to bash commands when a graph exists. |
| Kilo Code | `AGENTS.md`; native `/graphify` command in user config | `.kilo/plugins/graphify.js` plus `.kilo/kilo.json` or `.kilo/kilo.jsonc` registration. Automated writes target `.kilo/kilo.json` so existing JSONC can remain untouched. |
| Cursor | `.cursor/rules/graphify.mdc` with `alwaysApply: true` | No hook required; Cursor includes the rule in conversations automatically. |
| VS Code Copilot Chat | `.github/copilot-instructions.md` | No Graphify PreToolUse hook; `/graphify` in the chat panel builds/updates the graph. |
| Kiro IDE/CLI | `.kiro/steering/graphify.md` with `inclusion: always` | Project steering is the always-on mechanism. |
| Antigravity | `.agents/rules/graphify.md` and `.agents/workflows/graphify.md` | Native rules/workflow provide query-first behavior. MCP can be configured separately when wanted. |
| AGENTS.md platforms such as Aider, OpenClaw, Factory Droid, Trae, Trae CN, Hermes, Amp, and generic Agent Skills | `AGENTS.md` | No native PreToolUse hook unless separately listed above. Trae specifically has no PreToolUse hook; AGENTS.md is the source of truth. |

## Claude strict mode

Strict mode is opt-in and intended for Claude Code project hooks.

```bash
graphify install --project --strict
# or, when the skill is already handled and only the project hook/guidance is being refreshed:
graphify claude install --strict
```

Behavior verified by the package tests and hook implementation:

- The default install is a soft nudge. It does not block reads.
- Strict mode adds `--strict` to the Claude `Read|Glob` hook.
- The first raw `Read` of an indexed, in-project, fresh source file in a session is denied with a message instructing the assistant to run `graphify query`, `graphify explain`, or `graphify path` first.
- The denial is at most once per session; subsequent reads fall back to the normal nudge so the agent cannot get stuck.
- Search commands and Glob never deny, even in strict mode.
- Reads outside the project are ignored.
- If the graph is stale for the target file or `graphify-out/needs_update` exists, the hook emits a softer stale-graph nudge rather than denying.
- A recent query/path/explain creates a freshness stamp that suppresses the denial for the configured TTL.
- Runtime override: `GRAPHIFY_HOOK_STRICT=1` forces strict on and `GRAPHIFY_HOOK_STRICT=0` disables it without reinstalling. `GRAPHIFY_HOOK_STRICT_TTL` controls query-stamp freshness seconds.

## Project Git hooks

These are separate from assistant PreToolUse hooks. They live in the Git hooks directory for the nearest repository.

```bash
graphify hook install
graphify hook status
graphify hook uninstall
```

What `graphify hook install` sets up:

- `post-commit` hook: detects changed files after a commit and launches a detached code-only rebuild.
- `post-checkout` hook: after branch switches, rebuilds code when `graphify-out/` already exists.
- `merge=graphify` driver for `graphify-out/graph.json` through Git config and `.gitattributes`.
- A pinned Python interpreter captured at install time, so uv-tool and pipx installs still work in GUI Git clients or CI where `~/.local/bin` is absent.
- A background rebuild log at the user's Graphify rebuild log location. Hook failures should not block normal Git usage unnecessarily.

Important limits and environment toggles:

- Hooks are code/AST oriented. Documentation, image, video, or provider-backed semantic changes still require an explicit `graphify update .` or rebuild.
- Hooks skip rebase, merge, cherry-pick, linked-worktree, graph-output-only, and `GRAPHIFY_SKIP_HOOK=1` situations.
- `GRAPHIFY_FORCE=1` or force-rebuild behavior is needed after refactors that legitimately shrink the graph.
- `GRAPHIFY_REBUILD_TIMEOUT` controls the detached rebuild timeout.
- `GRAPHIFY_OUT` affects the runtime output directory, but `.gitattributes` can only express a repo-relative graph path; absolute output overrides fall back to the default graph path for merge-driver registration.
- If Graphify was upgraded or reinstalled, rerun `graphify hook install` so the embedded interpreter path and hook payload are refreshed.

## Project-scoped git-add hints

Project-scoped installs print a hint such as:

```bash
Project-scoped install. Add to version control:
  git add .codex/ AGENTS.md
```

Do not blindly run the hint unless the user wants those files committed. It is a useful checklist of the files Graphify expects to be project-owned. Inspect platform-specific generated files first if the project already had hand-written assistant config.

## Uninstall behavior

- `graphify uninstall` removes Graphify from detected user/platform installs and current-project guidance; add `--purge` only when the user also wants `graphify-out/` deleted.
- `graphify uninstall --project` removes project-scoped artifacts without touching user-scope skill installs.
- `graphify uninstall --project --platform codex` removes only that platform's project artifacts.
- Per-platform forms such as `graphify claude uninstall`, `graphify codex uninstall`, `graphify vscode uninstall`, and `graphify hook uninstall` are more precise when the user names one integration.
- Assistant uninstall removes `SKILL.md`, `.graphify_version`, `references/`, and graphify-owned instruction sections. It preserves unrelated content in shared config files when the file can be parsed safely.
