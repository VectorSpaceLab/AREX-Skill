# Monke E2E Overview

Monke is Airweave's connector end-to-end framework. It validates the complete path from an external application to Airweave search by creating live test data, triggering Airweave syncs, and searching for unique verification tokens after create/update/delete phases.

The framework name mirrors its split of responsibilities: the Monke runner orchestrates the test, while a bongo is the connector-specific external API actor that plays the source system.

## Scope and safety

Monke covers:

- connector test selection and changed-connector discovery;
- runner orchestration, concurrency, progress events, and logs;
- connector YAML configs and auth mode validation;
- bongo create/update/delete/cleanup lifecycle;
- generated test-data schemas and LLM-backed content generation;
- Airweave test collection/source-connection creation, sync triggering, and search verification;
- optional Monke web UI for observing local runs.

Monke does not own production connector implementation semantics. Use sibling [source-connectors](../../source-connectors/SKILL.md) for source class, registry, auth/config schema, browse-tree, ACL, federated-search, and incremental-sync implementation details. Monke also does not start the Airweave stack; use sibling [local-development](../../local-development/SKILL.md) for Docker Compose services, ports, health checks, and local `.env` setup.

A real Monke run is not a smoke-only unit test. It can mutate external accounts, consume API quotas, create Airweave collections/source connections, trigger Temporal sync work, generate OpenAI-backed content, and delete test data. The safe default is discovery/help only.

## Runtime surfaces

### Bundled discovery helper

Use `scripts/monke-list-connectors.sh` for safe listing and branch-aware connector discovery. It reads a checkout's `monke/configs`, optional git diffs, and matching connector filenames. It never imports Python modules or loads credentials.

### Shell wrapper

The repo-owned shell wrapper provides user-friendly Monke entrypoints:

- `--list` lists connector configs.
- `--print-connectors` prints the connector set used for CI matrices. With `--changed`, the original wrapper combines core connectors (`github`, `asana`), detected changed connectors, and extra connectors until its minimum connector count is met.
- specific connector arguments, `--changed` without print mode, and `--all` run real connector tests.

The wrapper can create a Python virtualenv, install Monke requirements, check backend health outside CI, load an env file, and call the Python runner. Treat every mode other than list/print/help as credentialed and stateful.

### Python runner

The Python runner is the low-level orchestrator. It accepts connector names, `--all`, `--max-concurrency`, `--env`, `--run-id-prefix`, and `--no-ui`. It loads a local env file outside CI when `python-dotenv` is installed, configures file logging, optionally sets up Composio provider state when `MONKE_COMPOSIO_API_KEY` is present, and runs one `TestRunner` per connector config.

Important limitation: the Python runner exposes `--changed` in help, but in the inspected implementation it prints that changed detection is not implemented and exits. Use the shell wrapper or bundled helper for changed-connector discovery.

### Optional Monke backend and frontend

The optional Monke web backend exposes local run-management endpoints such as test listing, run listing, starting one config, starting all configs, run details, and WebSocket streams for run logs/state. It stores in-process run records and local `.runs` state for the UI. The Vite frontend proxies API and WebSocket calls to the local Monke backend and is useful for visual run monitoring, not for safe discovery.

Use the CLI runner as the canonical execution path unless a task specifically concerns the Monke UI.

## Flow orchestration

A `TestRunner` loads a validated `TestConfig`, creates a `TestFlow`, initializes services, sets up infrastructure, executes configured steps, and then cleans up.

The default flow shape is:

1. `collection_cleanup` when configured for a current collection;
2. `cleanup` to remove leftover external test data for the current bongo;
3. `create` to create source entities with unique tokens;
4. `sync` or `force_full_sync` to run the Airweave source connection;
5. `verify` or raw/deletion-specific verification steps;
6. `update` to modify a subset of created entities;
7. another sync and verify cycle;
8. `partial_delete`, sync, partial-deletion verification, and remaining-entity verification;
9. `complete_delete`, sync, complete-deletion verification;
10. final external cleanup and optional collection cleanup.

Configured steps are mapped by `TestStepFactory`; unknown step names fail fast. `force_full_sync` uses the sync step with `force_full_sync=true`, which is important for connectors where deletion detection requires a full-source pass.

## Services and Airweave interaction

Service initialization creates:

- an Airweave HTTP client configuration from `AIRWEAVE_API_URL` and optional `AIRWEAVE_API_KEY`;
- a connector bongo from the bongo registry after credentials are resolved.

Infrastructure setup then creates:

- a test collection with a `monke-<connector>-test-<timestamp>` style name;
- a source connection with `short_name` equal to the connector type;
- a disabled schedule (`cron: null`) so syncs are explicitly triggered by the test.

Sync steps call Airweave root-relative endpoints: source-connection run and job-list endpoints, collection search endpoints, and delete endpoints for source connections/collections during teardown. Keep API version prefixes out of these calls; sibling `backend-api` owns the broader endpoint contract.

## Verification model

Monke verifies indexing by searching the Airweave collection for unique tokens embedded in generated test entities. The inspected search helper uses keyword retrieval, disables rerank/filter interpretation/query expansion/answer generation, and uses a high result limit for comprehensive token matching.

Some connectors intentionally disable deletion verification in their YAML because the source or Airweave entity model preserves immutable audit/event records or does not reliably report deletions incrementally. Do not turn those booleans on without confirming connector semantics in `source-connectors` and the source-specific bongo.

Raw-data verification is local-only. It checks local storage for a captured sync ID, manifest, entity JSON files, and optional raw files. It skips when `AIRWEAVE_API_URL` points at a non-local backend.

## Prerequisites for real runs

Before a real run, confirm:

- a healthy Airweave backend (`AIRWEAVE_API_URL`, default `http://localhost:8001`); use `local-development` if the local stack must be started or diagnosed;
- a Python environment with Monke requirements (`fastapi`, `httpx`, `pydantic`, `python-dotenv`, `rich`, `pyyaml`, `tenacity`, `openai`, `uvicorn`, `websockets`, and document libraries where relevant);
- `OPENAI_API_KEY` when LLM-backed generators are used;
- Composio or direct connector credentials, never both for one connector config;
- connector-specific test workspace/config fields such as repo name, branch, rate limits, or source-specific folders;
- acceptable external side effects, cleanup plan, concurrency, and timeout budget.

No accelerator backend is required for the Monke scope. External services, network access, local Airweave services, and credentials are the primary gates.

## Safe native anchors

Safe anchors for later verification are discovery/help only:

```bash
./monke.sh --list
./monke.sh --print-connectors
./monke.sh --print-connectors --changed
python monke/runner.py --help
bash skills/disco/airweave/sub-skills/monke-e2e/scripts/monke-list-connectors.sh --help
```

Do not treat a passing discovery/help anchor as proof that any connector E2E test can run. It only proves that connector discovery or argument parsing is usable without credentials.
