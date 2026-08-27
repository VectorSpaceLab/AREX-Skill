# Troubleshooting Events Blocks Assets And Concurrency

Use this when a workflow involving events, automations, blocks, assets, variables, or concurrency limits fails. Start with local payload validation and CLI help before running server-mutating commands.

## Event Emission Fails Or Returns `None`

Symptoms:

- `emit_event(...)` returns `None`.
- `prefect events emit` exits with a validation or API error.
- Event does not appear in the UI or stream.

Likely causes and fixes:

- Missing `prefect.resource.id`: every primary `resource` must include a non-empty `prefect.resource.id`.
- Invalid related resource: every `related` entry must include non-empty `prefect.resource.id` and `prefect.resource.role`.
- Payload is not JSON object: CLI `--payload` must parse to a JSON object, not a string or list.
- Event too large: reduce payload size; send a pointer to large data instead of embedding it.
- Event worker/API disabled or unavailable: check profile/API URL/server status in `../cli-server-operations/SKILL.md`.
- Expecting immediate UI visibility from local code: event delivery depends on the configured server or Cloud event pipeline.

Validation snippet:

```python
from prefect.events import Event

Event(
    event="external.invoice.received",
    resource={"prefect.resource.id": "invoice.2026-0001"},
    related=[{"prefect.resource.id": "customer.acme", "prefect.resource.role": "customer"}],
    payload={"amount": 125.5},
)
```

## Event Stream Does Not Show Expected Events

Symptoms:

- `prefect events stream --run-once` waits indefinitely.
- Stream closes or reconnects.
- `--account` returns unexpected audit/account events.

Likely causes and fixes:

- No events are being emitted to the active workspace; emit a small test event with `prefect events emit ...`.
- Wrong profile or API URL; run profile/config diagnostics from `../cli-server-operations/SKILL.md`.
- Account-wide streaming is Cloud-specific and may require permissions.
- Output file permission error; write to a known writable path or omit `--output-file`.
- Streaming is a live subscription, not a historical query; use UI/API queries for already-emitted events.

## Automation Payload Fails Validation

Symptoms:

- `prefect automation create --from-file ...` reports Pydantic validation errors.
- Bundled validator reports an index-specific failure.
- Selected action says an ID is required or not allowed.

Likely causes and fixes:

- Missing `name`, `trigger`, or `actions`.
- `trigger.type` omitted unintentionally; omitted trigger type defaults to `event`, so metric/compound/sequence fields may be misread.
- `actions` is empty or misspelled; use at least `[{"type": "do-nothing"}]` while testing.
- `source: selected` without the required `deployment_id`, `work_pool_id`, `work_queue_id`, or `automation_id`.
- `source: inferred` with an ID present; remove the selected ID or switch to `selected`.
- Proactive event trigger `within` is below 10 seconds.
- Metric trigger `range` or `firing_for` is below 300 seconds.
- `compound.require` is less than 1 or greater than the number of child triggers.
- IDs are placeholders or invalid UUID strings; local validation catches UUID shape but not resource existence.

Safe checks:

```bash
python ../scripts/validate_automation.py --file automation.yaml
python ../scripts/validate_automation.py --example deployment-event
```

## Automation Creates But Never Fires

Symptoms:

- Automation exists and is enabled but no action runs.
- Deployment event trigger does not react to a completed upstream run.
- A proactive trigger fires unexpectedly or not at all.

Likely causes and fixes:

- Event names do not match exactly; use names like `prefect.flow-run.Completed` and check capitalization.
- `match` filters primary resources while the desired deployment is a related resource; use `match_related` for `prefect.deployment.<uuid>` with role `deployment`.
- Missing `for_each` causes events from different flow runs to satisfy one trigger bucket; add `for_each: [prefect.resource.id]` for per-run evaluation.
- `threshold > 1` without an adequate `within` window means events are not counted together.
- Automation is disabled; run `prefect automation inspect NAME --output json` and resume if needed.
- Action target does not exist; local validation checks shape, but the server enforces whether deployments, blocks, work pools, queues, or automations exist.
- `send-notification` or `call-webhook` points at a missing or incompatible block document.
- Deployment ownership and worker availability belong to `../deployments-workers/SKILL.md` after the event trigger matches correctly.

## Block Load Or Save Fails

Symptoms:

- `Block.load("type/name")` or `MyBlock.load("name")` raises `ValueError` about missing document or type.
- `Block.save(...)` fails to connect to the API.
- Loaded block warns about schema mismatch or fails Pydantic validation.
- Placeholder generation fails for an unsaved block.

Likely causes and fixes:

- Block was never saved in the active workspace; save it first or switch to the correct profile/API URL.
- Loading with the wrong class; import the concrete block class and call `ConcreteBlock.load("document-name")`, or use `Block.load("type-slug/document-name")` when the slug is known.
- Block document exists in a different profile/workspace; inspect with `prefect block ls --output json` under the intended profile.
- Custom block type not registered or class not importable in runtime; register with `prefect block register --module ...` or ensure the package is installed.
- Integration block type requires an optional integration package; install the package in the runtime that loads the block.
- Local class schema added required fields after the document was saved; load with `validate=False`, set missing values, then save with `overwrite=True` after reviewing the migration.
- `get_block_placeholder()` on an unsaved block; call `.save("name")` first.

## Notification Or Webhook Automation Fails

Symptoms:

- `send-notification` or `call-webhook` action validation passes but runtime action fails.
- Webhook/audit/incident workflow works in Cloud docs but not on local server.

Likely causes and fixes:

- `block_document_id` is missing, invalid, deleted, or belongs to another workspace.
- Notification/webhook block is saved but the runtime lacks the integration dependency needed to execute it.
- The block stores invalid external credentials or a bad URL; test the block independently before automation use.
- `declare-incident`, account-wide audit logs, and some webhook/audit workflows are Cloud-only.
- Do not log secret block values; use `SecretStr`, `SecretDict`, or built-in secret-aware blocks.

## Asset Materialization Surprises

Symptoms:

- `@materialize()` raises `TypeError`.
- `add_asset_metadata()` raises outside task execution.
- Asset metadata disappears or appears overwritten.
- Asset event or lineage is missing from UI.

Likely causes and fixes:

- `@materialize` requires at least one asset string or `Asset` object.
- `Asset.add_metadata()` and `add_asset_metadata()` require an active asset context inside a materializing task.
- Asset properties overwrite the full property set at runtime; include `name`, `description`, `owners`, and `url` every time you are authoritative for that asset.
- Use string keys for assets materialized by other workflows to avoid duplicate/conflicting metadata definitions.
- UI lineage and asset health require server/Cloud event ingestion; local task execution alone may not surface asset views.
- Asset keys must be stable and valid; avoid run-specific random IDs unless each run truly produces a distinct asset.

## Variable Set Or Get Fails

Symptoms:

- `Variable.get` returns the default unexpectedly.
- `Variable.set` says the variable already exists.
- CLI `prefect variable set` stores a value with surprising quoting.

Likely causes and fixes:

- Wrong profile/workspace; list variables with `prefect variable ls` under the active profile.
- Missing `overwrite=True` or CLI `--overwrite` when updating.
- Shell quoting changed the JSON/string value; quote strings explicitly and prefer small JSON-compatible values.
- Variables are not secret storage; use blocks for credentials.

## Concurrency Limit Timeout Or No-Op

Symptoms:

- `concurrency(..., timeout_seconds=...)` times out.
- Code logs that limits do not exist and continues.
- `rate_limit(...)` errors.
- Long-running task fails or warns about lease renewal.

Likely causes and fixes:

- The named global concurrency limit does not exist. With `strict=False`, acquisition warns and skips; with `strict=True`, it raises. Create it with `prefect global-concurrency-limit create NAME --limit N`.
- All slots are occupied; inspect active slots with `prefect global-concurrency-limit inspect NAME --output json` or increase the limit deliberately.
- Limit is inactive; enable it with `prefect global-concurrency-limit enable NAME`.
- `rate_limit` requires `slot_decay_per_second`; create or update the limit with a non-zero decay.
- Acquisition timeout too short for expected queueing; increase `timeout_seconds` or reduce parallelism.
- Lease renewal failed because the API/server was unavailable; set `raise_on_lease_renewal_failure` intentionally based on whether strict enforcement or resilient execution matters more.
- The API URL/profile/server issue is outside the concurrency code; route to `../cli-server-operations/SKILL.md`.

## Cloud-Only Or Credentialed Features

Treat these as requiring explicit user confirmation, credentials, and Cloud context:

- `prefect events stream --account` for account-wide/audit logs.
- Automation action `declare-incident`.
- Webhook or notification actions that call external services.
- Integration block types requiring provider credentials, packages, or network access.
- Cloud UI-specific asset health, audit log, and workspace-level permission behavior.
