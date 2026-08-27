# Monke Troubleshooting

Start with the least invasive check. Monke discovery/help commands are safe; real connector runs are credentialed and mutate external systems.

## Safe first checks

```bash
# Bundled helper syntax/help.
bash -n skills/disco/airweave/sub-skills/monke-e2e/scripts/monke-list-connectors.sh
bash skills/disco/airweave/sub-skills/monke-e2e/scripts/monke-list-connectors.sh --help

# Connector discovery in a checkout.
bash skills/disco/airweave/sub-skills/monke-e2e/scripts/monke-list-connectors.sh \
  --repo-root "$AIRWEAVE_REPO" --list
bash skills/disco/airweave/sub-skills/monke-e2e/scripts/monke-list-connectors.sh \
  --repo-root "$AIRWEAVE_REPO" --print-connectors --changed --base-ref origin/main

# Native discovery/help anchors.
./monke.sh --list
./monke.sh --print-connectors
python monke/runner.py --help
```

If these fail, fix discovery/config/tooling before trying any external-system E2E run.

## Discovery and base-ref failures

### `Cannot find Airweave repo root`

The bundled helper could not find a directory with Monke configs and bongos. Pass an explicit checkout root:

```bash
bash skills/disco/airweave/sub-skills/monke-e2e/scripts/monke-list-connectors.sh \
  --repo-root "$AIRWEAVE_REPO" --list
```

### `Cannot find base ref` or `Cannot diff <base>...HEAD`

Changed detection needs a valid git base ref and merge base. Try:

```bash
git fetch origin main
bash skills/disco/airweave/sub-skills/monke-e2e/scripts/monke-list-connectors.sh \
  --repo-root "$AIRWEAVE_REPO" --print-connectors --changed --base-ref origin/main
```

For local branches, `--base-ref main` works when `main` exists locally. In CI, prefer `origin/main` or the actual pull-request base.

### Changed connector expected but not reported

Check the mapping rules in [connector-registry.md](connector-registry.md#changed-file-mapping-rules). The helper reports only testable connector names with matching `monke/configs/<name>.yaml`. If a backend source/entity file uses an alias such as a legacy or versioned name with no matching Monke config, the helper ignores it rather than inventing a runnable test.

Use `--include-worktree` when the changed files are uncommitted, staged, or untracked. Without it, discovery uses committed branch diff behavior.

## Runner command mismatch

The repo shell wrapper implements changed detection and CI matrix printing. The Python runner advertises `--changed`, but the inspected implementation exits because changed detection is not implemented there. If you need changed connectors:

1. use the bundled helper for safe planning; or
2. use the repo shell wrapper's print mode for the native CI-style connector set; then
3. pass the resulting connector names to the Python runner only after credentialed execution is approved.

Do not call `python monke/runner.py --changed` expecting it to run changed connectors.

## Config validation failures

### `auth_mode must be 'composio' or 'direct'`

Set `connector.auth_mode` to exactly `composio` or `direct`.

### `Cannot use both Composio and direct auth`

A connector config must choose one auth path. Remove `auth_fields` from Composio configs or remove `composio_config` from direct-auth configs.

### `account_id must start with 'ca_'` or `auth_config_id must start with 'ac_'`

Either the IDs are malformed or env substitution left an unresolved placeholder. For public configs, prefer placeholders such as `${MONKE_EXAMPLE_COMPOSIO_ACCOUNT_ID}` and set them in the run environment before executing. Do not hard-code private account IDs in new public examples.

### `Environment variable '<name>' for field '<field>' must start with 'MONKE_'`

Direct auth env names are deliberately constrained. Rename the env var mapping to a `MONKE_` prefix and set that variable outside version control.

### Airweave rejects source config fields

Monke passes filtered `connector.config_fields` to Airweave source-connection creation. If a Monke-only knob is leaking into the Airweave config payload, add it to the Monke-only filter or move it out of `config_fields` before creating the source connection.

## Auth resolution failures

### Missing Composio API key

For Composio configs, set `MONKE_COMPOSIO_API_KEY` before a real run. The runner uses it to connect a provider and the broker uses it to fetch credentials. Discovery helpers do not need it.

### Missing `MONKE_COMPOSIO_PROVIDER_ID`

This usually means a lower-level flow was invoked without the Python runner's Composio provider setup. Run through the normal runner path or set the provider ID only if you know it matches the target Airweave auth provider.

### No connected account or account/auth mismatch

Confirm the Composio account exists for the connector's toolkit slug and that the YAML `account_id`/`auth_config_id` match it. Some Airweave source names map to non-identical Composio slugs, especially Google and Microsoft variants.

### Missing direct-auth variable

Direct auth fails precisely with the missing `MONKE_*` env name and target credential field. Set the variable in the env file used by the run or in the process environment, then retry. Do not place actual secret values in generated skill files, examples, or committed configs.

## Backend and local stack failures

### Backend not accessible

Real runs need Airweave backend health. The wrapper checks `AIRWEAVE_API_URL/health` outside CI and defaults to `http://localhost:8001`. Use sibling [local-development](../../local-development/SKILL.md) to start or diagnose the local stack, ports, Docker daemon, Vespa, Temporal, Redis, Postgres, and env seeding.

### Source connection creation fails

Check:

- `connector.type` matches an Airweave source `short_name`;
- the collection was created and has a `readable_id`;
- auth payload matches the connector auth mode;
- `connector.config_fields` after Monke-only filtering match the source config schema;
- the backend is using the expected organization/API key context.

For source schema and implementation questions, route to [source-connectors](../../source-connectors/SKILL.md). For backend endpoint request/response questions, route to sibling `backend-api`.

## Sync and verification failures

### Sync already running or timeout

The sync step detects active jobs, waits for them, then launches its own sync. If it times out:

- inspect backend and Temporal worker logs;
- verify the source connection's job list and status transitions;
- confirm the external source API can see newly created test data;
- increase connector delays only when the source API needs propagation time;
- use `force_full_sync` when deletion detection requires ignoring cursor state.

### Low relevance or token not found

Monke verifies exact tokens with keyword search and high limits, but misses can still happen when:

- generated content did not include the token;
- source API had not indexed the new entity before sync;
- Airweave sync did not ingest the entity due to config, permissions, or filters;
- vector/search indexing lagged beyond retries;
- `OPENAI_API_KEY` or embedding settings are missing for generation/sync paths;
- source-specific deletion/audit semantics keep or hide tokens unexpectedly.

First inspect the created entity descriptor and bongo logs to confirm the token is in source content. Then inspect sync job status and backend logs. Only rerun after confirming cleanup state.

### Deletion verification fails

Do not blindly enable or retry deletion checks. Some configs intentionally disable deletion verification because source deletions are not surfaced or immutable event data keeps deleted entity content searchable. Confirm the connector's deletion semantics in its config, bongo, and sibling `source-connectors` before changing flow steps.

## Cleanup and external state

Cleanup is best-effort. If a run fails mid-test, external artifacts may remain. Before retrying:

1. identify the connector and run ID;
2. inspect bongo logs for created external IDs/paths/tokens;
3. run the connector's approved cleanup path only when credentials are present and the user accepts mutation;
4. delete the Airweave test source connection and collection if they still exist;
5. avoid deleting broad source-account data based only on names such as `test` or `monke` unless the bongo's cleanup logic is proven scoped to its own artifacts.

Be careful with logs. Some bongo implementations log credential field names or short token previews for debugging. Do not paste full credentialed logs into public artifacts.

## Raw-data verification failures

`verify_raw_data` only works for local backends. It needs a captured `sync_id` and local storage access. If it skips or fails:

- confirm `AIRWEAVE_API_URL` points to a local host;
- confirm the backend writes raw storage to the expected local storage location;
- check for `manifest.json` and entity JSON files under the sync's raw-data directory;
- do not treat a remote-backend skip as a connector failure.

## Monke web UI issues

The optional Monke backend/frontend are run-monitoring tools. If the UI cannot list or stream runs:

- confirm the Monke backend is serving its local API and WebSocket endpoints;
- confirm the frontend proxy points at the Monke backend port;
- check in-process run state rather than assuming Airweave backend state is wrong;
- fall back to CLI logs for canonical test status.

The CLI runner is still the primary execution path.

## Escalation checklist before rerun

Before rerunning a failed real connector test, record:

- connector name and config used;
- exact flow step that failed;
- whether external data was created, updated, partially deleted, or fully deleted;
- Airweave collection/source-connection/job IDs if available;
- credential mode and missing-variable/provider status without secret values;
- cleanup already attempted and remaining artifacts;
- whether a retry changes external state or can safely reuse/clean previous state.
