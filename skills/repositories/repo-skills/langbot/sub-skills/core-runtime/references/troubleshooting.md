# Core Runtime Troubleshooting

## `uv run main.py` Reinstalls or Reverts SDK Changes

Use `uv run --no-sync main.py` after installing a local sibling SDK checkout.
Otherwise `uv` may restore the pinned `langbot-plugin` package from metadata.

## Port or Health Check Fails

Symptoms: `/healthz` refuses connection, Hypercorn logs bind errors, web UI is
blank.

Actions:
1. Confirm `api.port` and whether another process owns it.
2. Run `langbot --help` to verify the expected environment.
3. Check startup logs before HTTP controller initialization.
4. For source checkouts, verify frontend build/dev-server expectations.
5. For containers, check service port mapping and health endpoint path.

## Missing Generated Config or Data

First startup should create missing files under the runtime data directory. If
it cannot, check write permissions, current working directory, and container
volume ownership.

## False Box "No Backend" Startup Signal

If Box is enabled but reports no backend, inspect Docker/nsjail/E2B availability
and permissions. Docker installed but inaccessible to the current user is a
common cause. Route detailed Box diagnosis to `plugin-box-skills`.

## Slow or Failing Dependency Install

LangBot has large optional-adjacent dependencies in the base package. Preserve
resolver/download errors. Retry with local proxy guidance if networking fails,
but do not bake proxy commands into code or generated runtime guidance.

## Startup E2E Fails

The backend E2E test starts a real LangBot process with temporary config,
SQLite, local storage, and embedded vector paths. If it fails, inspect:

- generated temporary config values,
- migration logs,
- `/healthz` response,
- route-registration availability,
- subprocess stdout/stderr before broad unit tests.
