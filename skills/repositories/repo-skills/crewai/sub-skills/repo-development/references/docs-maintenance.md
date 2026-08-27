# Docs Maintenance

CrewAI docs are Mintlify MDX sources with one rolling Edge channel and frozen release snapshots. Use this reference whenever a code change needs docs updates, navigation updates, or release-docs risk assessment.

## Edit Targets

| Path class | Normal action | Reason |
| --- | --- | --- |
| `docs/edge/<lang>/...` | Edit here for active docs changes. | Edge follows main and ships under the Edge version selector as soon as merged. |
| `docs/v<X.Y.Z>/...` | Do not edit during normal development. | Frozen release snapshots are immutable except for release-cut PRs using the docs-freeze escape hatch. |
| `docs/images/...` | Add new assets only. | Frozen snapshots share this image directory; deleting or renaming existing assets breaks old docs. |
| `docs/docs.json` | Update only when navigation, redirects, or version entries need it. | Mintlify reads navigation and redirects from this file. |

Canonical URL behavior:

- Edge pages live under `/edge/<lang>/<page>`.
- Frozen pages live under `/v<X.Y.Z>/<lang>/<page>`.
- Legacy unversioned `/<lang>/<page>` URLs redirect to the current latest frozen version through wildcard redirects in `docs/docs.json`.

## Version Model

`docs/docs.json` contains language blocks with version entries. The Edge entry points at `edge/<lang>/...` pages. Frozen entries point at `v<X.Y.Z>/<lang>/...` pages. Search and sidebar contents are scoped to the selected version.

During a release cut, Edge is copied into a new frozen snapshot. The release docs process also:

1. Copies `docs/edge/en`, `docs/edge/pt-BR`, `docs/edge/ko`, `docs/edge/ar`, and `enterprise-api.*.yaml` files into `docs/v<X.Y.Z>/` when present.
2. Rewrites `openapi:` references inside the snapshot so frozen pages read the snapshot YAML, not the current root YAML.
3. Inserts the new version after Edge in each language's `versions[]`, marks it default and `Latest`, and demotes the previous default.
4. Rewrites canonical redirects so `/<lang>/:slug*` lands on the new default version.

This is release-cut behavior, not routine docs validation.

## Safe Docs Editing Checklist

Before editing docs:

- Confirm the target file is under `docs/edge/<lang>/...` for normal changes.
- If a new page is added, add the Edge page path to `docs/docs.json` under the appropriate language/version navigation.
- Keep MDX components and frontmatter style consistent with nearby Edge pages.
- Prefer relative or version-aware docs links already used by the docs set; avoid hard-coding frozen snapshot paths in Edge content unless intentionally linking historical docs.
- If an image is needed, add a new file under `docs/images/` and reference it from Edge. Do not rename or remove existing image files.

After editing docs:

```bash
cd docs
mintlify broken-links
```

If using the local preview:

```bash
cd docs
mintlify dev
```

These commands require Mintlify tooling to be installed. They validate/render docs but do not perform release freezing.

## AGENTS.md Rules to Preserve

- Edit MDX under `docs/edge/<lang>/...`.
- Do not modify files under `docs/v*/` except in a release-cut PR with the expected docs-freeze context.
- Do not delete or rename existing files under `docs/images/`; images are append-only.
- Adding new images is safe; replacing an image means adding a new filename and updating Edge references.
- Docs snapshots and image rules are enforced by CI guards.

## Docs Scripts and Devtools

The docs-related scripts are maintainer/reference artifacts:

| Artifact | Runtime skill decision | Reason |
| --- | --- | --- |
| `scripts/docs/freeze_current_edge.py` | Reference-only; no-run by default. | It freezes Edge into a release snapshot and rewrites `docs/docs.json`; safe only in release-cut context. |
| `scripts/docs/freeze_historical_versions.py` | Excluded from runtime helper scripts. | It is a one-time historical migration from git tags. |
| `scripts/docs/prefix_version_paths.py` | Excluded from runtime helper scripts. | It is a one-time migration to directory-based versioning and Edge paths. |
| `crewai_devtools.docs_versioning.freeze()` | Reference-only; test via devtools tests. | It copies snapshots, rewrites OpenAPI refs, mutates navigation, and updates redirects. |
| `crewai_devtools.docs_check` | Credential/LLM-backed maintainer tooling. | It can analyze diffs and generate/translate docs through OpenAI calls; not default validation. |

## Release-Freeze No-Run Guidance

Do not run release freeze commands unless all of these are true:

- The task is explicitly a release-cut or docs-freeze task.
- The target version is a plain `X.Y.Z` string, not `vX.Y.Z`, a prerelease, or a partial version.
- The change is expected to create or reuse `docs/v<X.Y.Z>/` and mutate `docs/docs.json`.
- The PR/title/workflow context is expected to use the docs-freeze escape hatch.

Devtools tests prove that invalid versions such as `v1.15.0`, `1.15`, and prerelease strings are rejected by the freeze implementation.

## Safe Native Verification Candidates

For docs/versioning code changes, prefer tests over scripts:

```bash
uv run pytest lib/devtools/tests/test_docs_versioning.py -q
uv run pytest lib/devtools/tests/test_toml_updates.py -q
```

For docs-only content changes, prefer Mintlify validation if available:

```bash
cd docs
mintlify broken-links
```

For a mixed CLI plus docs change, combine focused CLI tests with docs validation. Use [../scripts/select_native_tests.py](../scripts/select_native_tests.py) to suggest commands from changed paths without running them.

## Common Docs Change Patterns

- New user-facing CLI option: update the relevant Edge CLI docs page, ensure `docs/docs.json` navigation already includes the page or add it if new, run CLI focused tests and docs link checks.
- New concept or guide: add `docs/edge/en/...` first, update `docs/docs.json`, and decide whether translations are in scope for the task. Do not edit frozen snapshots.
- Broken screenshot or diagram: add a replacement file under `docs/images/` and update Edge MDX references. Leave the old image in place.
- Release version update: use devtools tests to verify versioning logic; do not run `freeze_current_edge.py` unless the task is explicitly a release-cut workflow.
