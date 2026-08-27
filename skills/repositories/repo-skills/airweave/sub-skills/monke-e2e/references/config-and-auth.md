# Monke Config, Auth, and Test-Data Lifecycle

Monke connector tests are driven by validated YAML configs. A real run resolves credentials, creates a bongo, creates Airweave test infrastructure, creates source data, syncs, verifies tokens through search, updates/deletes source data, and cleans up.

## YAML config schema

Top-level config fields are validated by the Monke `TestConfig` model:

| Field | Purpose | Notes |
| --- | --- | --- |
| `name` | Human-readable test name | Required. Some configs use display names; some use slug-style names. |
| `description` | Human-readable test description | Required. |
| `connector` | Connector identity, auth, and source config | Required; see below. |
| `test_flow.steps` | Ordered step names | Defaults to cleanup/create/sync/verify/update/delete cycles when omitted. Unknown step names fail fast. |
| `deletion` | Partial/complete deletion verification controls | Use conservative booleans when a source does not propagate deletions reliably. |
| `entity_count` | Number of generated entities for relevant bongo loops | Must be at least 1. Some bongos create additional fixed entities beyond this count. |
| `collection`, `verification`, `cleanup` | Backward-compatible keys | The loader maps them to `collection_config`, `verification_config`, and `cleanup_config`. |
| Extra fields | Allowed at top level | Connector-specific legacy data may survive here, but prefer explicit sections. |

Environment substitution supports `${VAR}` and `${VAR:-default}` before YAML parsing. If a required variable is absent and no default is provided, the literal `${VAR}` remains in the processed config and may fail validation later. This is useful for precise failures, but do not mistake unresolved placeholders for real IDs.

## Connector block schema

`connector` is validated with `extra="forbid"`, so unknown keys inside this block are errors.

| Field | Purpose | Validation |
| --- | --- | --- |
| `name` | Connector instance name | Required. |
| `type` | Connector short name | Required; should match config filename and bongo `connector_type`. |
| `auth_mode` | `composio` or `direct` | Defaults to `composio`; any other value is rejected. |
| `composio_config` | Composio account/auth-config IDs | Required for `auth_mode: composio`; `account_id` must start with `ca_`, `auth_config_id` with `ac_`. |
| `auth_fields` | Direct credential field-to-env mapping | Required for `auth_mode: direct`; every env var name must start with `MONKE_`. |
| `config_fields` | Source and Monke-specific runtime knobs | Passed to the bongo; a filtered subset is sent to Airweave source-connection creation. |
| `rate_limit_delay_ms` | Connector-level rate limit delay | Defaults to 1000 ms in the model; some configs place per-source delay inside `config_fields`. |

Auth consistency is strict:

- `auth_mode: composio` requires `composio_config` and forbids `auth_fields`.
- `auth_mode: direct` requires non-empty `auth_fields` and forbids `composio_config`.

## Composio auth path

For Composio-auth configs:

1. Config validation checks `composio_config.account_id` and `auth_config_id` shapes.
2. The Python runner connects a Composio provider when `MONKE_COMPOSIO_API_KEY` is set and stores `MONKE_COMPOSIO_PROVIDER_ID` in the process environment.
3. Service initialization creates a `ComposioBroker` with the configured account/auth IDs and fetches connector credentials from Composio.
4. The bongo receives resolved external API credentials plus the Composio account/auth config for token-refresh-aware implementations.
5. Airweave source-connection creation sends provider auth data using `provider_readable_id`, `auth_config_id`, and `account_id`.

Common Composio failures:

- `Missing Composio API key (MONKE_COMPOSIO_API_KEY)`: set the Monke-specific API key before a real run.
- `No Composio connected accounts for slug '<slug>'`: the connected account for that toolkit is missing or mapped differently.
- `No Composio account found for provided auth_config_id/account_id`: the YAML IDs do not match the account available to the API key.
- `Composio auth mode configured but MONKE_COMPOSIO_PROVIDER_ID not set`: the lower-level flow was invoked without the runner's provider-setup step or the provider setup failed.

The broker maps some Airweave short names to Composio slugs, for example Google/Microsoft variants such as `google_drive`, `outlook_mail`, `onedrive`, `sharepoint`, `teams`, `word`, and `powerpoint`. If adding a new source whose Composio slug is not a simple underscore-stripped short name, update the mapping before relying on Composio resolution.

## Direct auth path

For direct-auth configs:

1. Config validation requires `auth_fields` and ensures every mapped env var starts with `MONKE_`.
2. Runtime resolution reads each env var and builds a credential dict using the YAML field names.
3. If any required env var is missing, resolution fails with a message naming both the env var and target credential field.
4. The bongo receives those resolved credentials and validates source-specific required fields.
5. Airweave source-connection creation sends `authentication.credentials` with the same resolved credential dict.

Example direct-auth shape with placeholders:

```yaml
connector:
  name: Example
  type: example
  auth_mode: direct
  auth_fields:
    api_key: MONKE_EXAMPLE_API_KEY
  config_fields:
    openai_model: gpt-4.1-mini
```

Direct auth is convenient for local dev, but it still runs against live external systems. Never commit real values to YAML; keep them in an env file or the invoking environment.

## Source-connection payload filtering

Monke bongo config fields are not always Airweave source config fields. Before creating the Airweave source connection, infrastructure setup filters out known Monke-only fields, including:

- `openai_model`
- `rate_limit_delay_ms`
- `max_concurrency`
- `post_create_sleep_seconds`
- source-test-only fields such as audio/transcript/event/time-zone knobs used by specific bongos

The remaining `connector.config_fields` are sent as the Airweave source connection `config`. If a new bongo adds a Monke-only control and Airweave rejects it as an unknown source config field, add it to the filter or move it out of the source config path.

The source-connection payload uses:

- `name`: generated test connection name;
- `short_name`: connector type;
- `readable_collection_id`: test collection readable ID;
- `config`: filtered source config;
- `schedule: {cron: null}` so Monke owns when syncs run;
- `authentication`: direct credentials or Composio provider metadata.

## Generated test-data lifecycle

Bongos create real external artifacts and return descriptors that Monke later searches for. A useful descriptor includes:

- a stable external identifier such as `id` or `path`;
- `type` or `name` for logs;
- a unique `token` embedded in the source data;
- `expected_content` when a bongo needs a source-specific verification hint.

The generation layer uses connector-specific Pydantic schemas and LLM adapters for realistic content. Examples include:

- GitHub artifacts rendered as markdown, Python, or JSON with a token in body/metadata;
- SharePoint files, folders, lists, list items, and pages with token-bearing text;
- Stripe customer data with token-bearing names/descriptions/metadata.

Because token search is the verification backbone, every generator must force the literal token into uploaded content even if the LLM omits it. Prefer deterministic post-processing over trusting the model instruction alone.

## Flow-specific data handling

- `create` stores returned descriptors in runtime context and on the bongo for later deletion.
- `verify` waits for indexing, searches for each token, retries misses, and can trigger one rescue sync when configured.
- `update` should preserve tokens while changing content so incremental sync can be verified without losing search keys.
- `partial_delete` records actually deleted and remaining descriptors. Some bongos may cascade-delete additional entities; Monke accounts for returned identifiers.
- deletion verification searches for absence of deleted tokens and presence of remaining tokens when enabled.
- `complete_delete` removes remaining entities and then checks that Monke test tokens are gone when enabled.
- `cleanup` is best-effort. It should not mask a failed verification, but it should try to avoid leaving orphaned external artifacts.

## Deletion verification semantics

Do not assume all connectors can verify deletion with the same steps. Examples from the inspected configs:

- GitHub and SharePoint use full or regular syncs plus deletion checks because their data model can expose deleted files/lists/pages appropriately.
- Asana and Notion disable deletion verification because their incremental behavior does not reliably detect deletions in the configured flow.
- Stripe disables deletion verification because immutable event entities can preserve deleted customer data, so tokens may remain searchable by design.

When changing these booleans, confirm both Monke bongo behavior and source implementation semantics in `source-connectors`.

## Minimal config examples

Composio with placeholder IDs:

```yaml
name: example_test
description: End-to-end test for Example source using Monke

connector:
  name: Example
  type: example
  auth_mode: composio
  composio_config:
    account_id: ${MONKE_EXAMPLE_COMPOSIO_ACCOUNT_ID}
    auth_config_id: ${MONKE_EXAMPLE_COMPOSIO_AUTH_CONFIG_ID}
  config_fields:
    openai_model: gpt-4.1-mini
    rate_limit_delay_ms: 500

test_flow:
  steps:
    - cleanup
    - create
    - sync
    - verify
    - update
    - sync
    - verify
    - partial_delete
    - sync
    - verify_partial_deletion
    - verify_remaining_entities
    - complete_delete
    - sync
    - verify_complete_deletion
    - cleanup

entity_count: 3

deletion:
  partial_delete_count: 1
  verify_partial_deletion: true
  verify_remaining_entities: true
  verify_complete_deletion: true
```

Direct auth with a single API key:

```yaml
connector:
  name: Example
  type: example
  auth_mode: direct
  auth_fields:
    api_key: MONKE_EXAMPLE_API_KEY
  config_fields:
    openai_model: gpt-4.1-mini
```

Both examples are structural only. A real connector may need source-specific config fields and a bongo that can safely create/delete test data in the chosen external workspace.
