# Connector Registry and Safe Discovery

Monke has two connector discovery concepts that future agents should keep separate:

1. **Runtime bongo registry**: Python autodiscovery imports bongo modules and registers `BaseBongo` subclasses for real test execution.
2. **Safe connector discovery**: listing testable connector names from config and changed files without importing code, installing packages, loading env files, or contacting external systems.

Use safe discovery first. Use the runtime registry only when a real Monke run is approved and dependencies/credentials are ready.

## Connector identity contract

A testable Monke connector should keep one canonical connector short name across these surfaces:

| Surface | Required identity | Why it matters |
| --- | --- | --- |
| Connector config | `monke/configs/<short_name>.yaml` | The shell wrapper and bundled helper treat configs as the safe list of available tests. |
| YAML connector block | `connector.type: <short_name>` | Airweave source connection payload uses this as `short_name`; bongo creation uses it to select a bongo class. |
| Bongo class | `connector_type = "<short_name>"` | `BongoRegistry.create()` uses this key after autodiscovery. |
| Generation module | `monke/generation/<short_name>.py` when needed | Bongos import generator functions for realistic token-bearing data. |
| Generation schema | `monke/generation/schemas/<short_name>.py` when needed | LLM structured-generation adapters validate generated content shape. |
| Airweave source/entity files | matching source/entity short names when applicable | Changed backend connector implementation can imply a Monke E2E candidate if a config with the same name exists. |

A connector with a bongo but no config is not safely discoverable as a runnable Monke test. A connector with a config but no registry entry will be listed, but a real run will fail when `BongoRegistry` cannot create its bongo.

## Runtime bongo registry behavior

`BongoRegistry.autodiscover()` imports every module under the bongo package and inspects classes. Any subclass of `BaseBongo` with a `connector_type` attribute is registered under that connector type.

Key implications:

- Import errors are logged and skipped, so a missing optional dependency can hide a bongo from runtime registration.
- `BongoRegistry.get(connector_type)` triggers autodiscovery lazily, then fails with `Unknown connector type: <name>` if no class registered.
- `BongoRegistry.create(connector_type, credentials, **kwargs)` instantiates the bongo with resolved credentials, `entity_count`, optional `composio_config`, and connector `config_fields`.
- `BongoRegistry.list_available()` imports code. Do not use it for safe CI matrix discovery or credential-free planning when config-file discovery is enough.

Every bongo inherits the same lifecycle methods from `BaseBongo`:

- `create_entities()` creates real source data and returns descriptors with IDs/paths/tokens;
- `update_entities()` modifies a subset while preserving verification tokens when possible;
- `delete_entities()` deletes all tracked data;
- `delete_specific_entities(entities)` deletes only selected descriptors and returns deleted identifiers;
- `cleanup()` performs best-effort orphan cleanup.

## Safe bundled helper

The bundled `scripts/monke-list-connectors.sh` intentionally avoids Python imports and credentials. It discovers available connectors from `monke/configs/*.yaml` and maps changed files to connector names only when a matching config exists.

Examples:

```bash
# List every test config as pretty lines.
bash skills/disco/airweave/sub-skills/monke-e2e/scripts/monke-list-connectors.sh \
  --repo-root "$AIRWEAVE_REPO" --list

# Print all available test configs as a space-separated matrix value.
bash skills/disco/airweave/sub-skills/monke-e2e/scripts/monke-list-connectors.sh \
  --repo-root "$AIRWEAVE_REPO" --print-connectors

# Print only changed testable connector names versus a base ref.
bash skills/disco/airweave/sub-skills/monke-e2e/scripts/monke-list-connectors.sh \
  --repo-root "$AIRWEAVE_REPO" --print-connectors --changed --base-ref origin/main

# Add core connectors and pad to a minimum candidate count without running tests.
bash skills/disco/airweave/sub-skills/monke-e2e/scripts/monke-list-connectors.sh \
  --repo-root "$AIRWEAVE_REPO" --print-connectors --changed --include-core --min 4
```

The helper never checks backend health, never creates a virtualenv, never installs Monke requirements, and never reads `.env` files.

## Changed-file mapping rules

Changed connector discovery maps each relevant file path to a candidate connector and then removes duplicates. It reports only candidates with matching YAML configs.

| Changed path pattern | Connector candidate |
| --- | --- |
| `monke/bongos/<name>.py` | `<name>` |
| `monke/configs/<name>.yaml` or `.yml` | `<name>` |
| `monke/generation/<name>.py` | `<name>` |
| `monke/generation/schemas/<name>.py` | `<name>` |
| `backend/airweave/platform/sources/<name>.py` | `<name>` when a Monke config exists |
| `backend/airweave/platform/entities/<name>.py` | `<name>` when a Monke config exists |

Ignored examples include `__init__.py`, helper modules such as registry/base classes, generated bytecode, files under `__pycache__`, and backend source/entity modules whose names do not have a Monke YAML config. This is deliberate: safe discovery should not invent a runnable external-system test for an unconfigured source.

Use `--include-worktree` when you want uncommitted, staged, and untracked relevant files included in addition to the base-ref diff. Without that flag, changed detection matches the repo wrapper's committed branch-diff behavior.

## Core connector set

The repo wrapper treats `github` and `asana` as core connectors for a reduced-footprint baseline. The bundled helper can include the same core set with `--include-core`, but it does not run them. Use `--min <N>` to pad the printed candidate set from available connectors when you need a stable matrix width.

Do not assume core connectors are safe to execute. They still require external accounts and credentials.

## Adding or changing a Monke connector

When a future task adds or changes a connector test, keep this checklist:

1. **Config**: add or update `monke/configs/<name>.yaml`; keep `connector.type` equal to `<name>`; choose one auth mode; set deletion verification booleans to match the source's deletion semantics.
2. **Bongo**: implement a `BaseBongo` subclass with `connector_type = "<name>"`; return entity descriptors with stable `id` or `path`, `token`, and `expected_content` fields; make cleanup best-effort and idempotent.
3. **Generation**: add structured generation only when static fixtures are insufficient. Ensure generated output includes the literal token; validators should prevent content that cannot be uploaded to the source.
4. **Config fields**: put source-connection config in `connector.config_fields`. Keep Monke-only knobs there only when the infrastructure payload filter excludes them, or extend that filter before passing them to Airweave.
5. **Auth**: for direct auth, every env var name in `auth_fields` must start with `MONKE_`. For Composio, use placeholder env substitution for account/auth config IDs in public configs rather than hard-coded private values.
6. **Flow**: use `force_full_sync` for deletion-detection checks when the source's incremental cursor does not surface deletions.
7. **Safety**: update changed-file discovery only if the connector's filename convention changes; keep discovery-only helpers separate from runner execution.

## Native discovery anchors

Use these anchors only to prove discovery/help behavior in a checkout:

```bash
./monke.sh --list
./monke.sh --print-connectors
./monke.sh --print-connectors --changed
python monke/runner.py --help
bash skills/disco/airweave/sub-skills/monke-e2e/scripts/monke-list-connectors.sh --help
```

A registry import check or any command that runs connector names is no longer discovery-only; treat it as a real test boundary.
