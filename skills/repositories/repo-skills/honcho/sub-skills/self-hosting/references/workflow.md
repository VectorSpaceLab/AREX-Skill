# Self-hosting workflow

This workflow covers the runtime path for running Honcho as a service.

## 1. Confirm configuration

Check the effective configuration first:

- database URI and schema,
- embedding dimension,
- vector-store mode,
- queue/worker settings,
- provider keys for any reasoning paths that will run,
- observability toggles if you need metrics or tracing.

## 2. Prepare the database

A healthy deployment needs the database schema in place before the API or
worker starts serving traffic. If pgvector is in use, the embedding columns
must already match the configured dimension.

## 3. Start the runtime pieces

Typical runtime pieces are:

- the FastAPI API process,
- the deriver worker,
- optional dreamer / consolidation scheduling,
- any cache or queue backend expected by the deployment.

## 4. Validate the surface

After startup, validate in this order:

1. Health endpoint.
2. Queue status.
3. Workspace-level read operations.
4. Peer/session read operations.
5. Memory write and read operations.

The goal is to catch configuration drift before you debug application logic.

## 5. Check vector-store behavior

Honcho supports multiple vector-store modes. Keep the selected mode aligned
with the environment rather than assuming one backend is always present.

## 6. Treat embedding mismatch as a hard stop

If startup validation reports an embedding mismatch, do not keep serving
traffic. Fix the schema or the configured dimension first.

## Safe inspection helpers

- `scripts/runtime_check.py` — current config and startup-surface summary.
- `../../scripts/surface_report.py` — cross-cutting route and SDK snapshot.

## What a future agent should remember

The server is deliberately defensive: it validates the runtime shape before it
serves traffic. That means the fastest path to a fix is usually to inspect
configuration and schema first, not to start editing business logic.
