# Agent integration troubleshooting

Use this page for Graphify assistant install, uninstall, platform artifact, hook, scope, and PATH problems. For package import problems that also affect graph building, cross-check the root troubleshooting page when the complete runtime tree includes one.

## `graphify: command not found` / PATH problems

Likely causes:

- The package was not installed in the shell or assistant runtime that is running the command.
- The package was installed under the wrong PyPI name. The distribution is `graphifyy`; the CLI and import package are `graphify`.
- `uv tool install graphifyy` or `pipx install graphifyy` succeeded, but the tool bin directory is not on `PATH` yet.
- Plain `pip install graphifyy` installed into a Python environment different from the one used by git hooks, GUI tools, or the assistant.

Recovery:

```bash
# Recommended isolated install.
uv tool install graphifyy

# If the command is still missing after uv tool install:
uv tool update-shell
# then open a new shell.

# pipx alternative:
pipx install graphifyy
pipx ensurepath

# One-shot without permanent install: name the package, then the command.
uvx --from graphifyy graphify --help
uvx --from graphifyy graphify install --platform codex

# If the import works but the command is missing:
python -m graphify --help
```

Do not recommend `uvx graphify ...`; uv treats the first word as a package name, and the public package name is `graphifyy`.

## Package name: `graphifyy` vs `graphify`

Symptoms:

- `No solution found ... no versions of graphify` from uv.
- `ModuleNotFoundError: No module named 'graphify'` from hooks or assistant commands.
- `graphify` works in an interactive shell but not in GUI Git clients, CI, or assistant hooks.

Recovery:

1. Install or upgrade the official package: `uv tool install graphifyy`, `uv tool upgrade graphifyy`, `pipx install graphifyy`, or `pip install -U graphifyy` in the intended environment.
2. Prefer uv tool or pipx on macOS/Windows so the executable and package are bundled in one isolated runtime.
3. If using plain pip, ensure both the Python executable and scripts directory are active wherever the assistant/hook runs.
4. Rerun `graphify hook install` after reinstalling or upgrading so git hooks embed the current interpreter path.

## Wrong platform alias or command form

Symptoms:

- `error: unknown platform ...`.
- The install succeeds but writes a different platform's files than expected.
- `graphify install --platform vscode` or a dedicated subcommand behaves differently than expected.

Rules:

- `skills` is an alias for `agents`: `graphify install --platform skills` and `graphify skills install` target the generic Agent-Skills ecosystem.
- `vscode` is a dedicated command family (`graphify vscode install` / `graphify vscode uninstall`) for VS Code Copilot Chat, not a universal user-scope skill location.
- `windows` and `antigravity-windows` are packaging variants. They install a skill named `graphify`, not `graphify-windows`.
- Hyphenated names must be exact: `trae-cn`, `antigravity-windows`.
- Cursor uses `.cursor/rules/graphify.mdc` rather than a separate user-scope `SKILL.md` in the current installer path.

Recovery:

1. Check [platforms.md](platforms.md) for the target assistant.
2. Probe the command safely before touching real config from the `graphify` repo-skill root:

   ```bash
   python sub-skills/agent-integration/scripts/install_platform_probe.py --platform codex --scope project --json
   ```

3. For aliases, rerun with the canonical platform when you need clearer output, e.g. `--platform agents` instead of `--platform skills`.
4. If a platform has both `graphify install --platform <name>` and `graphify <name> install`, prefer the command shown in [platforms.md](platforms.md) for the exact skill-only versus always-on behavior you need.

## User scope vs project scope confusion

Symptoms:

- A user-scope install did not create `AGENTS.md` in the repository.
- A project install wrote files that are now dirty in git.
- Uninstall removed a personal skill when the user only wanted a project cleanup, or vice versa.

Decision guide:

| Desired outcome | Use | Verify |
|---|---|---|
| Personal assistant skill available across repositories | `graphify install --platform <platform>` | Files under the temp or real HOME assistant config root. Ask before using a real HOME. |
| Team-visible project guidance that can be committed | `graphify install --project --platform <platform>` or the platform project subcommand | Files under the current project such as `AGENTS.md`, `.codex/`, `.claude/`, `.agents/`, `.cursor/`, or `.kiro/`. |
| Inspect artifacts without mutation | `python sub-skills/agent-integration/scripts/install_platform_probe.py --platform <platform> --scope user|project` from the `graphify` repo-skill root | Relative file lists under temporary `home/` and `project/`. |
| Remove only project files | `graphify uninstall --project --platform <platform>` | Real user-scope skill remains untouched. |

Project-scoped installs may print a `git add ...` hint. Treat it as a checklist, not an instruction to commit automatically. Inspect generated files first if the project already had hand-written assistant config.

## Stale installed skill version

Graphify checks known skill install locations and may warn:

- `skill is from graphify <old>, package is <new>. Run 'graphify install' to update.`
- `skill is from graphify <newer>, but the package is <older>. Upgrade the package ...; running 'graphify install' would downgrade the skill.`
- `skill dir exists but SKILL.md is missing. Run 'graphify install' to repair.`

Recovery:

- If the installed skill is older than the package, rerun the matching install command in the same scope.
- If the installed skill is newer than the package, upgrade the package first (`uv tool upgrade graphifyy`, `pipx upgrade graphifyy`, or `pip install -U graphifyy`) before reinstalling the skill.
- If `SKILL.md` is missing, reinstall the platform skill or uninstall and reinstall only that platform/scope.

## Missing `references/` sidecar

Symptoms:

- Warning: `skill references/ sidecar is missing. Run 'graphify install' to repair.`
- An assistant skill file links to `references/extraction-spec.md`, `references/query.md`, or `references/hooks.md`, but the files are absent.
- A partial upgrade left `SKILL.md` without sidecar references.

Recovery:

1. Rerun the exact platform install command in the same scope.
2. Verify `SKILL.md`, `.graphify_version`, and `references/` are siblings in the installed skill directory.
3. If repair fails, uninstall the platform scope and reinstall.
4. Do not expect a `references/` sidecar for monolith hosts such as Aider and Devin.

## Strict mode and assistant hook behavior

Strict mode is opt-in and meaningful for Claude Code project hooks.

```bash
graphify install --project --strict
graphify query "what am I trying to inspect?"
```

Expected non-blocking cases:

- Strict mode was not installed. Use `graphify install --project --strict` or `graphify claude install --strict` for Claude Code project hooks.
- Runtime kill switch is set: `GRAPHIFY_HOOK_STRICT=0`.
- The tool call is search/Glob, not a raw Claude Read.
- The read is outside the project, the target file is not indexed, or the graph is stale for that file.
- `graphify-out/needs_update` exists; the hook should nudge, not deny.
- A recent `graphify query`, `graphify path`, or `graphify explain` stamp is still fresh.
- The session already received its one strict denial.

If strict mode blocks unexpectedly, set `GRAPHIFY_HOOK_STRICT=0`, run a graph query, or uninstall/reinstall the Claude project hook.

## Codex hook appears to do nothing

This is usually expected. Codex always-on behavior comes from `AGENTS.md`. The `.codex/hooks.json` entry calls `graphify hook-check`, which intentionally emits no additional PreToolUse context because Codex Desktop rejects that hook payload and would break Bash tool calls.

Check instead:

- `AGENTS.md` contains the `## graphify` section.
- Project-scoped install wrote `.codex/skills/graphify/SKILL.md`, `.graphify_version`, and its `references/` sidecar.
- The user understands that the hook file is present for compatibility, while the practical nudge is the persistent project instruction.

## Trae has no PreToolUse hook

Trae and Trae CN use `AGENTS.md` as the always-on mechanism. Do not wait for hook nudges or treat their absence as a failed install. Verify the `AGENTS.md` section and route graph use through the installed skill/instructions.

## Git hooks are installed but graph is stale

Check:

```bash
graphify hook status
```

Common causes:

- The command ran outside a Git work tree or inside the wrong directory. Run `git rev-parse --show-toplevel` first; initialize/use a Git repository before `graphify hook install`.
- The changed files were docs, images, video, or provider-backed semantic inputs. Git hooks rebuild code only; run `graphify update .` or a full rebuild for semantic inputs.
- The hook was installed before moving or upgrading Graphify. Rerun `graphify hook install`.
- A commit happened during rebase, merge, cherry-pick, or in a linked worktree; hooks intentionally skip these cases.
- `GRAPHIFY_SKIP_HOOK=1` was set.
- The project uses a custom hooks path. Graphify respects Git's resolved hooks directory but fails loudly on invalid Windows-style paths from POSIX/WSL.
- The graph legitimately shrank after deletions; use `GRAPHIFY_FORCE=1` or a force rebuild when appropriate.

Hook failures should not cause automatic deletion of graph artifacts. Fix the hook/runtime cause first, then update or rebuild.

## Accidental real-HOME or project mutation risk

Before running an install for a user, answer these questions:

1. Which platform and scope did the user request?
2. Should generated files be committed to the current project?
3. Is a user-global assistant config mutation acceptable?
4. Is this only an inspection task?

For inspection, run:

```bash
python sub-skills/agent-integration/scripts/install_platform_probe.py --platform codex --scope project
```

The probe sets temporary HOME/project roots and deletes them by default. Do not simulate installs by pointing Graphify at a real HOME unless the user approved that scope.

## Uninstall surprises

- `graphify uninstall` removes Graphify from detected user/platform installs and current-project guidance. It does not uninstall the Python package; use `uv tool uninstall graphifyy`, `pipx uninstall graphifyy`, or `pip uninstall graphifyy` separately.
- `graphify uninstall --project` removes project-scoped install files without touching user-global skills.
- `graphify uninstall --project --platform codex` removes only that platform's project artifacts.
- `graphify hook uninstall` only removes git hooks and merge-driver registration; it does not remove assistant skills or instruction files.
- Shared files such as `AGENTS.md`, `CLAUDE.md`, and settings JSON are edited by removing graphify-owned sections/hooks. If a settings file cannot be parsed safely, Graphify refuses to modify it rather than clobbering unrelated config.

## When not to purge `graphify-out/`

Do **not** use `graphify uninstall --purge` just because:

- `graphify-out/` is dirty after hooks or an incremental update. Dirty graph files are expected.
- The graph is stale. Prefer `graphify update .`, `graphify update . --force` when the graph legitimately shrank, or a fresh extraction if semantic/media inputs changed.
- A platform install, hook, or PATH problem occurred. Fix the integration problem first; graph data is a separate artifact.
- A future agent has not queried the graph yet. The existing graph may still be useful for `graphify query`, `path`, `explain`, wiki navigation, or architecture review.
- You are preserving evidence for debugging, review, or reproducibility.

Only purge when the user explicitly wants graph artifacts removed, the graph contains sensitive data that must be deleted, or the graph is known-corrupt and the user accepts losing it before rebuilding.

## Platform-specific artifact not present

Use the platform table in [platforms.md](platforms.md). Some apparent omissions are expected:

- `graphify install --platform agents` is skill-only; `graphify agents install` also writes `AGENTS.md` guidance.
- `graphify install --platform codex` is user-scope skill-only; project `--project` or `graphify codex install` writes `AGENTS.md` guidance.
- `graphify vscode install` is the VS Code Copilot Chat path; `vscode` is not a universal user-scope `--platform` target.
- Cursor uses `.cursor/rules/graphify.mdc` rather than a separate installed `SKILL.md` file in the current installer path.
- Aider and Devin are monolith skill bodies; missing `references/` is not automatically an error for them.
