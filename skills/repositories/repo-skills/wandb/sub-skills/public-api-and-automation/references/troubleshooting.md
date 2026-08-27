# Troubleshooting

## Authentication and host settings

Symptoms:

- `No authentication configured. Use wandb login to log in.`
- `relogin required`, unauthorized, or forbidden GraphQL errors.
- Requests go to the wrong W&B deployment.

Fixes:

- Run `wandb login` or configure credentials through the normal W&B environment/settings mechanisms before running Public API scripts.
- For self-hosted/dedicated cloud, use `wandb login --host URL` or construct `wandb.Api(overrides={"base_url": URL})`.
- Check `wandb status` and the configured base URL if API calls are unexpectedly hitting public cloud or another host.
- Never paste credentials into skill files, generated examples, or committed scripts.

## Incorrect path shape

Symptoms:

- `api.run(...)` cannot find a run.
- `api.sweep(...)` resolves the wrong resource.
- A default entity/project masks a typo.

Fixes:

- Use full run paths: `entity/project/run_id`.
- Use full project paths for list calls: `entity/project`.
- Use full sweep paths: `entity/project/sweep_id`.
- Avoid relying on `overrides={"entity": ..., "project": ...}` in reusable scripts unless documented.

## Pagination assumptions

Symptoms:

- Only the first page of runs/files/reports/automations is processed.
- Large exports hang or consume too much memory.
- Resume logic duplicates or skips automations.

Fixes:

- Treat `api.runs`, `run.files`, `api.reports`, `api.automations`, and integration list methods as lazy iterables.
- Stream rows/items as they arrive instead of converting huge iterators to lists.
- For automation resume, save the iterator `.cursor` only after consuming the intended page, then pass it as `start=cursor`.
- Keep `per_page` moderate; increasing it reduces requests but can increase server/client memory pressure.

## Large or incomplete history exports

Symptoms:

- History export is slow, huge, or missing recent rows from a live run.
- CSV columns are inconsistent or missing fields.
- `keys` argument raises a validation error.

Fixes:

- Use `run.scan_history(keys=[...])` for complete unsampled exports; `keys` must be a list of strings.
- Use `run.history(samples=...)` only for sampled previews.
- Bound with `min_step`, `max_step`, and `--max-rows` before full exports.
- Prefer JSONL for sparse or heterogeneous metric keys; CSV is best when columns are known.
- If a run is still live, recent data may not be fully available in exported history; retry after the run finishes or note that the export is partial.
- Include `_step` explicitly in `--keys` if downstream consumers need a step column and the selected metric rows do not include it automatically.

## Missing fields and lazy runs

Symptoms:

- `run.config` or `run.summary` looks empty on a listed run.
- Accessing a heavy field triggers extra network calls.

Fixes:

- `api.run("entity/project/run_id")` loads a single run fully by default.
- `api.runs(..., lazy=True)` loads essential metadata first; accessing `run.config` or `run.summary` can trigger full data loading.
- Use `api.runs(..., lazy=False)` when a small filtered result set needs config/summary for every run.
- Convert summaries with `dict(run.summary)` before JSON serialization.

## GraphQL, network, and timeout errors

Symptoms:

- `WandbApiFailedError`, gateway timeout, request timeout, or transient GraphQL failure.
- A query works for a small project but fails for a large one.

Fixes:

- Construct `wandb.Api(timeout=120)` or another explicit timeout for long reads.
- Narrow `filters`, `keys`, `per_page`, and export step ranges.
- Retry idempotent reads; do not blindly retry destructive updates/deletes.
- For self-hosted servers, check feature support and server version if newer automation fields fail GraphQL validation.

## Automation scope/action mismatch

Symptoms:

- Automation creation raises validation errors.
- Server says event or action is unsupported.
- Webhook/Slack action fails because the integration is missing.

Fixes:

- Pair run metric/state events with project scope: `project = api.project("project", entity="entity")`.
- Pair artifact events with an artifact collection scope; do not use project-only run filters with artifact events.
- Create actions from existing integrations: `SendWebhook.from_integration(webhook)` or `SendNotification.from_integration(slack)`.
- Check `api._supports_automation(event=event.event_type, action=action.action_type)` for older/self-hosted servers.
- On name conflicts, decide whether to fail, fetch existing with `fetch_existing=True`, update the existing automation, or choose a new name.
- Use `api.automation(name=..., entity=...)` only when exactly one automation should match; otherwise iterate `api.automations(...)` and disambiguate.

## Destructive operations

- `run.delete(...)`, `api.delete_automation(...)`, file overwrites, and broad automation updates require explicit user confirmation.
- Prefer dry-run output that lists matched run IDs, automation IDs, or filenames before mutation.
- Record what was changed in task output, but keep credentials and private host details out of generated artifacts.
