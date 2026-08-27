# Maintainer reference: platform skill packaging

This page is for maintainers changing Graphify's packaged assistant skills. It is not needed for ordinary users installing Graphify. The `tools/skillgen` renderer is build-time reference evidence only and is not a runtime dependency for future agents.

## Packaged artifact model

Graphify ships platform integrations as package data:

- `graphify/skill*.md`: the committed `SKILL.md` bodies installed into assistant-specific skill directories.
- `graphify/skills/<platform>/references/*.md`: progressive-disclosure sidecars installed next to `SKILL.md` for split platforms.
- `graphify/always_on/*.md`: always-on instruction blocks injected into `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, VS Code instructions, Antigravity rules, and Kiro steering.
- `.graphify_version`: written at install time next to the installed `SKILL.md` and covering both `SKILL.md` and the `references/` sidecar.

In the verified package version, split/progressive hosts render eight references: `add-watch.md`, `exports.md`, `extraction-spec.md`, `github-and-merge.md`, `hooks.md`, `query.md`, `transcribe.md`, and `update.md`. Aider and Devin are monolithic hosts and do not require a `references/` sidecar.

## Renderer workflow

From a Graphify source checkout, maintainers regenerate committed artifacts with:

```bash
python -m tools.skillgen
python -m tools.skillgen --platform claude
python -m tools.skillgen --check
python -m tools.skillgen --audit-coverage
python -m tools.skillgen --schema-singleton
python -m tools.skillgen --monolith-roundtrip
python -m tools.skillgen --always-on-roundtrip
python -m tools.skillgen --bless
```

Use these commands only when doing source maintenance. Do not tell ordinary Graphify users to run them.

What the renderer enforces:

- Stable, LF-only, idempotent output with no timestamps.
- A unified frontmatter description for all rendered platform skills.
- A single six-value `file_type` enum across split and monolith artifacts.
- Per-host coverage audits against each host's own pre-split baseline, so platform-specific sections do not disappear silently.
- PowerShell translation checks for Windows variants.
- Always-on roundtrip checks against the former inline constants, with intentional edits recorded explicitly.
- Monolith roundtrip checks for Aider and Devin, allowing only sanctioned differences.

## Platform manifest fields

`tools/skillgen/platforms.toml` declares how each platform is rendered. Important fields:

| Field | Meaning |
|---|---|
| `bucket` | `split` for lean core plus sidecar references, `monolith` for one inline body. |
| `skill_dst` | Committed package artifact path, not the user's install destination. Runtime destinations are controlled by the installer. |
| `refs_dst` | Committed references bundle path for split platforms. |
| `name` | Skill frontmatter name. Defaults to `graphify`; variants should not invent names such as `graphify-windows`. |
| `description` | Frontmatter description preserved verbatim. |
| `dispatch` | Host-specific execution/dispatch fragment. Examples include Agent-tool, Codex spawn-agent, OpenCode mention, task-tool, manual-paste, and PowerShell variants. |
| `extraction` | Verbose or compact extraction reference. |
| `shell` | POSIX or PowerShell command rendering. |
| `claude_md` | Whether installer-side Claude-style guidance is expected. |
| `hooks_variant` | Which hooks reference wording to render. `agents-md` is used for AGENTS.md platforms such as Trae, Amp, and generic Agent Skills. |
| `extra_sections` | Optional tail fragments for platform deltas. |
| `monolith` / `roundtrip_ref` | Monolith source fragment and pinned baseline reference. |

## Maintainer change checklist

When adding or changing a platform:

1. Update the platform manifest and relevant fragments.
2. Update installer routing and destination logic so `graphify install --platform <platform>` and any `graphify <platform> install` subcommand match the rendered reference text.
3. Decide whether the platform is split or monolith. Prefer split when the host supports sidecar references; use monolith only when required by host constraints.
4. If split, ensure the package data includes the platform's `references/` files and that `_packaged_skill_refs_dir` can find them.
5. If the platform has always-on guidance, add or reuse a packaged always-on block rather than embedding large constants in code.
6. Add focused install/uninstall tests using temporary HOME/project roots. Never rely on a developer's real assistant config.
7. Run the renderer checks and focused tests before release.

Useful focused tests for packaging and install drift:

```bash
pytest tests/test_skillgen.py -q
pytest tests/test_install_references.py -q
pytest tests/test_install_roundtrip.py -q
pytest tests/test_agents_platform.py -q
pytest tests/test_install.py -q
```

## Failure modes the packaging checks prevent

- A wheel ships `SKILL.md` but omits `references/`, leaving dead `references/*.md` pointers.
- A progressive reinstall leaves an orphan sidecar for a monolith host, or a monolith install leaves stale `references/` from an older split host.
- The installed skill is stamped with a version older or newer than the current package.
- A hand-edited generated artifact differs from the source fragments or the blessed expected snapshot.
- A host-specific install reference says to use a command that the CLI does not dispatch.
- Windows/PowerShell variants accidentally ship POSIX shell syntax.

## Boundary

Do not copy `tools/skillgen` into runtime skill trees. Future agents using Graphify only need the installed package and CLI. Use this page to understand maintainer packaging evidence or to plan a source change in the Graphify repository.
