# Bundled skills

This reference covers the Observal-managed skills packaged with the CLI and installed into supported harness skill directories. These are agent-facing runtime instructions, so CLI command changes must keep them synchronized.

## Bundled skill inventory

The CLI packages six Observal-managed skill directories under `observal_cli/skills`:

| Skill directory | Intended use |
| --- | --- |
| `observal` | Core account, setup, config, scan, doctor, outdated, inbox, teamspaces, and API escape hatch. |
| `observal-agents` | Agent create, author, validate, publish, release, pull, lifecycle, ownership, and co-author workflows. |
| `observal-registry` | Component discovery, submission, installation, lifecycle, versions, bulk submission, recommendations, and ownership. |
| `observal-ops` | Sessions, traces, telemetry health, logs, ratings, rankings, and insight reports. |
| `observal-admin` | Reviews, users, settings, security, SAML, SCIM, audit, local server operations, migrations, upgrades, rollback. |
| `observal-advanced` | Reconciliation, CLI version recovery, rollback, and explicit local fallback after confirmed CLI/server unavailability. |

Each directory must include a `SKILL.md` and may include `references/` files. The installer copies the complete directory tree, not only the top-level skill file.

## Synchronization lifecycle

The CLI manages bundled skill drift automatically:

1. The root CLI callback calls the bundled-skill synchronizer before normal command work.
2. The synchronizer computes a deterministic SHA-256 hash of each packaged skill directory and the installed copy.
3. A mismatched managed directory is replaced as a complete directory using a staged replacement with rollback on failure.
4. Only the six Observal-managed skill directories are replaced. User-created skills outside these names are not touched.
5. Stale extra files inside a managed Observal skill directory are removed because the entire directory is replaced from the packaged source.
6. Older unchanged duplicates may be cleaned up after the replacement is proven identical; divergent copies are preserved with warnings.
7. The Antigravity legacy flat-file layout is cleaned up after migration to skill directories.
8. `observal doctor` reports installed harnesses missing the core `observal` skill. `doctor --yes` repairs fixable warnings and installs the skills.
9. Human `auth login` performs post-login setup including skill sync and doctor unless `--no-setup` is used. JSON login skips post-login setup to stay noninteractive and machine-clean.
10. `agent pull` also installs packaged skills as part of a successful harness installation workflow.

The sync process is a CLI behavior contract. If a skill's references or scripts change, tests must prove the installed copy preserves those files.

## When CLI changes require skill changes

Update bundled skills when any of these change:

- A command path is added, removed, moved, or renamed.
- An argument or flag name changes, including confirmation, dry-run, output, file-destination, pagination, or filtering options.
- A command's JSON shape, list envelope, JSON Lines stream, exit code, pending-state semantics, warning fields, or verification signal changes.
- A command becomes interactive or noninteractive in a different way.
- A workflow changes from write to preview, preview to write, pull/install behavior, or review/publish lifecycle behavior.
- A safety rule changes for secrets, registry identities, row-number use, mutation retries, or local fallback.
- A command is moved between specialized skills, such as from core to admin or from registry to advanced.

At minimum, update:

1. The matching command reference page under `docs/cli`.
2. Any affected bundled skill `SKILL.md` or reference file under `observal_cli/skills`.
3. The generated core command reference in `observal_cli/skills/observal/references/commands.md` by running the sync script from the repository root.
4. Static bundled-skill tests and focused command tests.

## Generated command reference

The core bundled skill contains `references/commands.md`, which has a generated block delimited by sentinels. The generator walks the Typer app and renders every root command, group, subgroup, and leaf command with one-line help.

Run after command inventory or help-summary changes:

```bash
python scripts/sync_observal_skill.py
```

Expected healthy signals:

- The script reports the command reference is already in sync or regenerated.
- The generated block lists every visible top-level group.
- The sync test compares the on-disk generated block to a fresh generator run and passes.

If the generated block moves or the sentinels are missing, restore the sentinels before regeneration.

## Skill authoring constraints

Bundled Observal skills should remain compact routers with detailed procedures in direct `references/` files. Follow these rules when editing them:

- Frontmatter must include `name`, `description`, `version`, and usually `command: observal`.
- The frontmatter `name` must match the skill directory name and use lowercase kebab-case.
- Descriptions are agent-routing text: include "Use when", avoid first-person wording, avoid placeholders, and keep them short enough for harness loaders.
- Every skill should state that commands must be executed, JSON output is preferred, `--help` should be used when uncertain, and results must be verified.
- Keep references self-contained. Do not make a reference depend on reading another reference before it can be used.
- Prefer direct links from `SKILL.md` to `references/*.md`; avoid nested reference links.
- Every fenced `observal ...` command in bundled skills and references should resolve to a real command path and valid long flags.
- Examples intended for agents should use `--output json` when the target command supports it and should include noninteractive inputs.
- Do not show secrets, tokens, password values, header values, DB URLs with credentials, invitation URLs, or generated plaintext credentials in examples.
- Do not teach telemetry wrappers or `OTEL_*` environment variables. Session telemetry is through Observal-managed hooks/extensions and reconciliation.

## Which skill to update

| CLI change | Skill files likely affected |
| --- | --- |
| Root command, `auth`, `config`, `scan`, `doctor`, `outdated`, `inbox`, `team`, or `api` behavior | Core `observal` skill and relevant core references. |
| Agent create/build/publish/release/pull/lifecycle/co-author behavior | `observal-agents` skill references. |
| Registry component list/show/submit/install/edit/archive/version/recommend/bulk behavior | `observal-registry` skill references. |
| Traces, telemetry status, logs, feedback/rating, top, or insight-report behavior | `observal-ops` skill references. |
| Review, users, settings, audit, security, SAML, SCIM, server operations, or migrations | `observal-admin` skill references, and sometimes `observal-advanced` for recovery/version flows. |
| Reconcile, self upgrade/downgrade/rollback, version mismatch recovery, or local fallback | `observal-advanced` skill references. |
| Any command inventory change | Core generated `references/commands.md` plus whichever specialized skill describes the workflow. |

When in doubt, search the bundled skill tree for the exact command path and flag names, then update every affected occurrence.

## Tests that protect bundled skills

| Test area | What it proves |
| --- | --- |
| Bundled skill existence | All six managed skill directories and `SKILL.md` files exist at the installer source paths. |
| Frontmatter validation | Required fields exist, names match directories, descriptions route properly, and versions look like semver. |
| Progressive disclosure | `SKILL.md` links point to direct bundled reference files. |
| Installer preservation | Installing into a harness preserves `SKILL.md`, references, and any scripts; a later sync repairs stale managed copies. |
| Command reference sync | The on-disk generated command reference equals a fresh Typer-app walk. |
| Command resolution | Every fenced `observal ...` command in the bundled skills resolves to a real command path. |
| Flag resolution | Every documented long flag in fenced commands exists on the target leaf command. |
| Agent behavior contracts | Skills continue to require execution, JSON preference, help checks, canonical identifiers, verification, redaction, and explicit fallback. |

Run these after skill or CLI surface changes:

```bash
python scripts/sync_observal_skill.py
uv run pytest tests/test_observal_skill.py tests/test_observal_skill_sync.py -q
uv run pytest observal_cli/tests/test_cmd_component_submit_flags.py -q
```

Expected healthy signals: sync script reports in sync or regenerated, bundled skill tests pass, and the help-example regression passes.

## Practical update checklist

Before declaring a CLI-facing change complete:

- [ ] The canonical command path is registered in the correct Typer group.
- [ ] Help screens contain one to three current examples that parse.
- [ ] The command uses `OutputMode`, `output_json`, shared errors, and shared client helpers.
- [ ] JSON mode is noninteractive and stdout-clean.
- [ ] Destructive JSON mutations require confirmation and mutations are not auto-retried.
- [ ] The matching `docs/cli` page is updated.
- [ ] The appropriate bundled skill router/reference text is updated.
- [ ] The generated command reference is regenerated if inventory/help changed.
- [ ] Focused command tests cover table output, JSON output, empty output, failures, confirmations, and side effects.
- [ ] `tests/test_cli_errors.py`, bundled skill tests, and the relevant `observal_cli/tests/test_cmd_*.py` file pass.
