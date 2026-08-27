# Graphify assistant platform installs

Use this reference to choose an install command and predict which artifacts should appear. The public package name is `graphifyy`; the command and import package are `graphify`.

## Scope decision

| Scope | Use when | Command shape | Safety note |
|---|---|---|---|
| User/global | The user wants Graphify available in their personal assistant across projects. | `graphify install --platform <platform>` or a platform subcommand documented below. | Ask before mutating a real HOME. Probe first with the bundled `install_platform_probe.py --scope user` when uncertain. |
| Project | The user wants a repo-local, commit-able integration for a team or a single project. | `graphify install --project --platform <platform>` when supported; some platforms use a dedicated subcommand. | Prefer this for shared guidance. Graphify prints `git add` hints for files it expects the user to commit. |
| Probe/dry-run | You need to inspect what a platform creates without touching real config. | From the `graphify` repo-skill root: `python sub-skills/agent-integration/scripts/install_platform_probe.py --platform codex --scope project` | The probe uses temporary HOME and project directories and deletes them by default. |

`graphify install` with no platform is intentionally single-platform: Claude Code on Linux/macOS, and the Windows Claude variant on Windows. Use a named platform when the user wants anything else.

## Platform command map

| Platform | Skill install command | Primary user-scope skill location | Project-scope artifact root | Always-on / hook command and notes |
|---|---|---|---|---|
| Claude Code | `graphify install` or `graphify install --platform claude` | `~/.claude/skills/graphify/SKILL.md` | `.claude/skills/graphify/SKILL.md`, `.claude/CLAUDE.md`, `.claude/settings.json`, and root `CLAUDE.md` | `graphify claude install`; PreToolUse search/read hooks. Use `graphify install --project --strict` for strict mode. |
| Claude Code on Windows | Auto-selected on Windows, or `graphify install --platform windows` | `~/.claude/skills/graphify/SKILL.md` | `.claude/skills/graphify/SKILL.md` plus Claude guidance/settings | Uses the PowerShell-aware packaged skill body and the same Claude hook model. |
| CodeBuddy | `graphify install --platform codebuddy` | `~/.codebuddy/skills/graphify/SKILL.md` | `.codebuddy/skills/graphify/SKILL.md` when project-installed | `graphify codebuddy install` writes `CODEBUDDY.md` and `.codebuddy/settings.json` PreToolUse hooks in the current project. |
| Codex | `graphify install --platform codex` | `~/.codex/skills/graphify/SKILL.md` | `.codex/skills/graphify/SKILL.md`, `AGENTS.md`, `.codex/hooks.json` | `graphify codex install` writes `AGENTS.md`. The Codex PreToolUse hook is intentionally a no-op; guidance comes from `AGENTS.md`. |
| OpenCode | `graphify install --platform opencode` | `~/.config/opencode/skills/graphify/SKILL.md` | `.opencode/skills/graphify/SKILL.md`, `AGENTS.md`, `.opencode/plugins/graphify.js`, `.opencode/opencode.json` | `graphify opencode install` wires `AGENTS.md` and a `tool.execute.before` plugin. |
| Kilo Code | `graphify install --platform kilo` | `~/.config/kilo/skills/graphify/SKILL.md`; command at `~/.config/kilo/command/graphify.md` | Project skill copy when installed with `--project`; native always-on files under `AGENTS.md` and `.kilo/` when using `graphify kilo install` | `graphify kilo install` installs native skill/command plus `AGENTS.md` and `.kilo` plugin registration. |
| GitHub Copilot CLI | `graphify install --platform copilot` | `~/.copilot/skills/graphify/SKILL.md` | `.copilot/skills/graphify/SKILL.md` with `--project` | Skill install only; use VS Code row for Copilot Chat instructions. |
| VS Code Copilot Chat | `graphify vscode install` | `~/.copilot/skills/graphify/SKILL.md` | `.github/copilot-instructions.md` in the current project | Dedicated subcommand, not a `--platform vscode` target. Uninstall with `graphify vscode uninstall`. |
| Aider | `graphify install --platform aider` | `~/.aider/graphify/SKILL.md` | `.aider/graphify/SKILL.md` with project install | `graphify aider install` writes `AGENTS.md` guidance. Aider uses a monolithic skill body; no `references/` sidecar is expected. |
| OpenClaw | `graphify install --platform claw` | `~/.openclaw/skills/graphify/SKILL.md` | `.openclaw/skills/graphify/SKILL.md`, `AGENTS.md` | `graphify claw install` writes `AGENTS.md`; no native PreToolUse hook. |
| Factory Droid | `graphify install --platform droid` | `~/.factory/skills/graphify/SKILL.md` | `.factory/skills/graphify/SKILL.md`, `AGENTS.md` | `graphify droid install` writes `AGENTS.md`; task dispatch uses Droid's Task tool style. |
| Trae | `graphify install --platform trae` | `~/.trae/skills/graphify/SKILL.md` | `.trae/skills/graphify/SKILL.md`, `AGENTS.md` | `graphify trae install` writes `AGENTS.md`. Trae does not support PreToolUse hooks. |
| Trae CN | `graphify install --platform trae-cn` | `~/.trae-cn/skills/graphify/SKILL.md` | `.trae-cn/skills/graphify/SKILL.md`, `AGENTS.md` | Reuses the Trae skill/reference bundle and no-hook guidance. |
| Gemini CLI | `graphify install --platform gemini` | `~/.gemini/skills/graphify/SKILL.md` on Linux/macOS; Windows uses the generic agents skill location | `.gemini/skills/graphify/SKILL.md`, `GEMINI.md`, `.gemini/settings.json` | `graphify gemini install`; BeforeTool hook always allows and adds graph guidance when a graph exists. |
| Hermes | `graphify install --platform hermes` | `~/.hermes/skills/graphify/SKILL.md` on Linux/macOS; Windows uses the Hermes local-app-data skill root | `.hermes/skills/graphify/SKILL.md`, `AGENTS.md` | `graphify hermes install` writes `AGENTS.md` guidance. Hermes reuses the OpenClaw-style skill bundle. |
| Kimi Code | `graphify install --platform kimi` | `~/.kimi/skills/graphify/SKILL.md` | `.kimi/skills/graphify/SKILL.md` | Reuses the Claude-style split skill bundle. |
| Amp | `graphify install --platform amp` | `~/.config/agents/skills/graphify/SKILL.md` | `.agents/skills/graphify/SKILL.md`, `AGENTS.md` | `graphify amp install` also wires `AGENTS.md`. Old `~/.amp/skills/graphify` installs are legacy and should be cleaned by current install. |
| Agent Skills / generic | `graphify install --platform agents` | `~/.agents/skills/graphify/SKILL.md` | `.agents/skills/graphify/SKILL.md` | Alias: `--platform skills` and `graphify skills install`. `graphify agents install` also writes `AGENTS.md`; `graphify install --platform agents` is skill-only. |
| Kiro IDE/CLI | `graphify install --platform kiro` for user skill; `graphify kiro install` for project steering | `~/.kiro/skills/graphify/SKILL.md` for user-scope skill-only | `.kiro/skills/graphify/SKILL.md`, `.kiro/steering/graphify.md` | Dedicated `graphify kiro install` writes project steering with `inclusion: always`. |
| Pi coding agent | `graphify install --platform pi` or `graphify pi install` | `~/.pi/agent/skills/graphify/SKILL.md` | `.pi/agent/skills/graphify/SKILL.md` | Progressive split skill with references; no special hook layer. |
| Cursor | `graphify cursor install` or `graphify install --platform cursor` | No separate user skill file in the current installer path | `.cursor/rules/graphify.mdc` | Cursor rule has `alwaysApply: true`; no hook needed. |
| Devin CLI | `graphify install --platform devin` or `graphify devin install` | `~/.config/devin/skills/graphify/SKILL.md` | `.devin/skills/graphify/SKILL.md`; project mode can also write `.windsurf/rules/graphify.md` | Devin skill is monolithic; project rules are for Windsurf-style always-on guidance. |
| Google Antigravity | `graphify install --platform antigravity` or `graphify antigravity install` | `~/.gemini/config/skills/graphify/SKILL.md` | `.agents/skills/graphify/SKILL.md`, `.agents/rules/graphify.md`, `.agents/workflows/graphify.md` | On Windows, `antigravity-windows` uses the Windows skill body. Antigravity may also be configured for MCP separately. |

## Aliases and naming rules

- `skills` is a CLI alias for `agents`: `graphify install --platform skills` and `graphify skills install` both target the generic Agent-Skills ecosystem.
- The installed assistant skill folder and frontmatter name are `graphify` for all platform variants, including Windows. `windows` and `antigravity-windows` are packaging variants, not user-facing skill names.
- `vscode` is a top-level subcommand (`graphify vscode install`) and is not listed by `graphify install --help` as a universal platform value.
- The package is `graphifyy`, not `graphify`. For one-shot uvx usage, use `uvx --from graphifyy graphify install`.

## What to verify after install

1. The expected `SKILL.md` exists at the selected scope.
2. Split/progressive platforms also have `references/` and `.graphify_version` next to `SKILL.md`. Aider and Devin are monolithic and should not require `references/`.
3. Project always-on files contain a single `## graphify` section or equivalent platform frontmatter/rule.
4. Platform hooks/settings are present only where expected:
   - Claude/CodeBuddy: PreToolUse settings.
   - Gemini: BeforeTool settings.
   - Codex: no-op `hook-check` entry plus `AGENTS.md` guidance.
   - OpenCode/Kilo: native plugin files and config registration.
5. For project installs, record or show the emitted `git add` hint so the user knows what can be committed.
