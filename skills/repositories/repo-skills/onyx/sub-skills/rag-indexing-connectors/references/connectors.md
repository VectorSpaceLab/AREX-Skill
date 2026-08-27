# Connectors

Use this reference when you are changing connector class shape, registry/factory wiring, source enums, credentials, attachment policy, or connector-specific tests.

## Connector interface map

| Interface | Main method(s) | Use when | Notes |
|---|---|---|---|
| `LoadConnector` | `load_from_state()` | You need a full snapshot or dump-file load. | Emits full `Document` batches. |
| `PollConnector` | `poll_source(start, end)` | You need time-window incremental syncs. | Keep the time filter idempotent. |
| `SlimConnector` | `retrieve_all_slim_docs(start=None, end=None, callback=None)` | You need pruning / existence checks. | Emits ids only; must mirror main-pass admission. |
| `SlimConnectorWithPermSync` | `retrieve_all_slim_docs_perm_sync(...)` | You need permission sync plus pruning ids. | Slim docs must carry the ACL view needed by sync. |
| `CheckpointedConnector` | `load_from_checkpoint(start, end, checkpoint)` | You need resumable crawling. | Pair with `build_dummy_checkpoint()` and `validate_checkpoint_json()`. |
| `CheckpointedConnectorWithPermSync` | `load_from_checkpoint_with_perm_sync(...)` | You need resumable crawling plus ACL sync. | Same checkpoint rules as the non-perm variant. |
| `CredentialsConnector` | `set_credentials_provider(provider)` | Credentials can rotate while a run is active. | The factory injects a DB-backed provider. |
| `Resolver` | `reindex(errors, include_permissions=False)` | You need targeted recovery for failed docs. | Useful for source-specific repair flows. |

## Factory, registry, and source wiring

- `DocumentSource` is the canonical source enum. Add the new value there first, then add the matching entry in the connector registry.
- The connector registry is a `DocumentSource -> module path / class name` map. Keep the module path lazy-loadable and keep the class name stable.
- The factory instantiates the class with `connector_specific_config`, validates the requested `InputType`, and raises a missing-connector error when the mapping or import fails.
- `InputType.LOAD_STATE` requires `LoadConnector`; `InputType.POLL` requires `PollConnector` or `CheckpointedConnector`; `InputType.EVENT` requires `EventConnector`.
- `CredentialsConnector` bypasses direct `load_credentials()` and receives a DB-backed `CredentialsProviderInterface` instead. Static connectors load the credential JSON directly and may return refreshed JSON to persist.
- The factory also sets the image-analysis flag and, when provided, the raw-file callback used for staged tabular files.
- Keep `connector_specific_config` JSON-friendly and stable across saved connector rows.

## Attachment and slim-doc admission

- Use `include_attachments` for sources that can index page/ticket/file attachments. New connectors should default it to `False`.
- If you retrofit a connector that already indexed attachments unconditionally, default `include_attachments` to `True` so older saved configs keep their historical behavior.
- Gate every attachment enumeration path on the same flag, including the slim-doc path.
- If image attachments are additionally gated by `allow_images`, the slim pass must use the same admission rule as the main pass. Otherwise the slim path can create ghost rows or miss pruning targets.
- For permission-sync-enabled connectors, slim docs must expose the same `external_access` and parent hierarchy data needed by pruning and ACL updates.
- If a connector has attachments but no slim path, add one before turning on pruning support.

## Credential and permission behavior

- Dynamic credentials should use the provider path so refreshes are locked and audited.
- Static credentials should be loaded once, treated as immutable for the run, and never logged in raw form.
- Credential refresh is best-effort: if the connector produces updated credential JSON, the factory persists it after a successful load.
- `validate_connector_settings()` should fail fast on missing credentials, bad scopes, invalid base URLs, or unsupported settings.
- `validate_perm_sync()` is for the permission-sync path only; use it to catch ACL-specific failures that would otherwise appear mid-sync.
- Checkpointed connectors should make `validate_checkpoint_json()` strict and round-trip their checkpoint model exactly.

## Frontend, docs, and tests

- Mirror the backend defaults in the web connector form and source metadata so the admin UI and stored connector config stay aligned.
- Add or update the docs page for the source with credential setup, scopes, screenshots, and any attachment or permission notes.
- Prefer unit tests for registry/input-type/attachment gating, daily connector tests for live source behavior, and external-dependency or integration tests only when a running service is genuinely required.
- For a new source, cover at least: registry mapping, validation, one main-pass shape test, and one slim/perms test if the connector supports them.
- See [data-formats.md](data-formats.md) for the exact `Document` and `SlimDocument` payload fields that these tests should assert.
